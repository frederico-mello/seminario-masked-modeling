"""Teste de equivalencia entre o MAE proprio e o oraculo vit-pytorch.

Pesos e mascara identicos; tolerancias declaradas aqui:
- perda: diferenca relativa ate 1e-5
- reconstrucao (pixels por patch): erro absoluto maximo ate 1e-4
Relatorio salvo em tests/relatorio_equivalencia.txt.
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo import mae
from vit_pytorch.mae import MAE as MAE_oraculo
from vit_pytorch.vit import ViT

TOLERANCIA_PERDA_REL = 1e-5
TOLERANCIA_RECON_ABS = 1e-4
RELATORIO = Path(__file__).resolve().parent / "relatorio_equivalencia.txt"


def construir_oraculo(taxa: float):
    vit = ViT(
        image_size=32,
        patch_size=8,
        num_classes=0,
        dim=128,
        depth=4,
        heads=4,
        mlp_dim=512,
        pool="mean",
        dim_head=32,
    )
    return MAE_oraculo(
        encoder=vit,
        decoder_dim=64,
        masking_ratio=taxa,
        decoder_depth=2,
        decoder_heads=4,
        decoder_dim_head=64,
    )


def copiar_pesos(proprio, oraculo):
    proprios = dict(proprio.named_parameters())
    oraculos = dict(oraculo.named_parameters())
    mapeamento = {
        "patch_embed.0.weight": "encoder.to_patch_embedding.1.weight",
        "patch_embed.0.bias": "encoder.to_patch_embedding.1.bias",
        "patch_embed.1.weight": "encoder.to_patch_embedding.2.weight",
        "patch_embed.1.bias": "encoder.to_patch_embedding.2.bias",
        "patch_embed.2.weight": "encoder.to_patch_embedding.3.weight",
        "patch_embed.2.bias": "encoder.to_patch_embedding.3.bias",
        "pos_embedding": "encoder.pos_embedding",
        "enc_to_dec.weight": "enc_to_dec.weight",
        "enc_to_dec.bias": "enc_to_dec.bias",
        "mask_token": "mask_token",
        "to_pixels.weight": "to_pixels.weight",
        "to_pixels.bias": "to_pixels.bias",
    }
    for i in range(4):
        for orig in ("norm.weight", "norm.bias", "to_qkv.weight", "to_out.0.weight", "to_out.0.bias"):
            mapeamento[f"encoder.layers.{i}.atencao.{orig}"] = (
                f"encoder.transformer.layers.{i}.0.{orig}"
            )
        for orig in ("net.0.weight", "net.0.bias", "net.1.weight", "net.1.bias", "net.4.weight", "net.4.bias"):
            mapeamento[f"encoder.layers.{i}.ff.{orig}"] = (
                f"encoder.transformer.layers.{i}.1.{orig}"
            )
    for i in range(2):
        for orig in ("norm.weight", "norm.bias", "to_qkv.weight", "to_out.0.weight", "to_out.0.bias"):
            mapeamento[f"decoder.layers.{i}.atencao.{orig}"] = (
                f"decoder.layers.{i}.0.{orig}"
            )
        for orig in ("net.0.weight", "net.0.bias", "net.1.weight", "net.1.bias", "net.4.weight", "net.4.bias"):
            mapeamento[f"decoder.layers.{i}.ff.{orig}"] = (
                f"decoder.layers.{i}.1.{orig}"
            )
    for orig in ("norm.weight", "norm.bias"):
        mapeamento[f"encoder.{orig}"] = f"encoder.transformer.{orig}"
        mapeamento[f"decoder.{orig}"] = f"decoder.{orig}"
    for orig in ("decoder_pos_emb.weight",):
        mapeamento[orig] = orig
    faltantes = [k for k, d in mapeamento.items() if k not in proprios]
    assert not faltantes, f"parametros proprios ausentes: {faltantes}"
    sem_destino = [k for k, o in mapeamento.items() if o not in oraculos]
    assert not sem_destino, f"parametros do oraculo ausentes: {sem_destino}"
    # cls_token existe no oraculo mas e ignorado com pool="mean"
    nao_cobertos = set(oraculos) - set(mapeamento.values()) - {
        "encoder.cls_token"
    }
    assert not nao_cobertos, f"oraculo tem pesos nao cobertos: {nao_cobertos}"

    with torch.no_grad():
        for origem, destino in mapeamento.items():
            tensor = proprios[origem]
            alvo = oraculos[destino]
            if tensor.shape != alvo.shape and alvo.ndim == 2:
                tensor = tensor.reshape(alvo.shape)
            assert tensor.shape == alvo.shape, (
                f"forma divergente {origem}: {tuple(tensor.shape)} vs " f"{tuple(alvo.shape)}"
            )
            alvo.copy_(tensor)


@contextlib.contextmanager
def rand_indices_fixos(indices_rand: torch.Tensor):
    """Forca o oraculo a usar a mesma selecao de patches do MAE proprio."""
    original = torch.rand
    torch.rand = lambda *args, **kwargs: indices_rand
    try:
        yield
    finally:
        torch.rand = original


def test_equivalencia_with_oraculo(tmp_path=None):
    perm = mae.permutacoes_fixas(8)
    linhas = ["relatorio de equivalencia MAE proprio vs vit-pytorch 1.24.1", ""]
    maior_dif_perda = 0.0
    maior_dif_recon = 0.0
    for taxa in (0.5, 0.75):
        proprio = mae.MAE()
        oraculo = construir_oraculo(taxa)
        copiar_pesos(proprio, oraculo)
        proprio.eval()
        oraculo.eval()

        torch.manual_seed(7)
        imagens = torch.rand(8, 3, 32, 32)
        perm_taxa = perm[:8]
        indices = mae.indices_ocultos(perm_taxa, taxa)
        lote = torch.arange(8)[:, None]
        n_ocultos = indices.shape[1]

        # tensor de "rand" que faz o oraculo escolher exatamente os
        # indices da permutacao fixa
        rand_sel = torch.full((8, 16), 1e9)
        for b in range(8):
            for k, i in enumerate(indices[b].tolist()):
                rand_sel[b, i] = float(k)
            for k, i in enumerate(range(16)):
                if rand_sel[b, i] == 1e9:
                    rand_sel[b, i] = 1e9 * 0 + 1000.0 + float(k)

        with rand_indices_fixos(rand_sel):
            perda_oraculo = oraculo(imagens.clone())

        saida = proprio(imagens, indices_mascarados=indices)
        perda_proprio = saida["perda"].detach()
        dif_perda_rel = float((perda_proprio - perda_oraculo).abs() / perda_oraculo.abs())

        # reconstrucao do oraculo refeita com a predicao retornada pelo proprio
        pred_proprio = saida["predicao"].detach()
        n_visiveis = 16 - n_ocultos
        visiveis = torch.ones(8, 16, dtype=torch.bool)
        visiveis.scatter_(1, indices, False)
        indices_vis = torch.argsort((~visiveis).long(), dim=1, stable=True)[:, :n_visiveis]

        # reconstrucao do oraculo, manual, para comparar pixel a pixel
        with torch.no_grad():
            patches = mae.patchify(imagens)
            tokens = oraculo.patch_to_emb(patches)
            tokens = tokens + oraculo.encoder.pos_embedding
            tokens_vis = tokens[lote, indices_vis]
            cod = oraculo.encoder.transformer(tokens_vis)
            dec_vis = oraculo.enc_to_dec(cod)
            dec_vis = dec_vis + oraculo.decoder_pos_emb(indices_vis)
            mtk = oraculo.mask_token.repeat(8, n_ocultos, 1)
            mtk = mtk + oraculo.decoder_pos_emb(indices)
            canvas = torch.zeros(8, 16, dec_vis.shape[-1])
            canvas[lote, indices_vis] = dec_vis
            canvas[lote, indices] = mtk
            decod = oraculo.decoder(canvas)
            decod = decod[lote, indices]
            pred_oraculo_manual = oraculo.to_pixels(decod)

        dif_recon = float(
            (pred_proprio[lote, indices] - pred_oraculo_manual).abs().max()
        )
        maior_dif_perda = max(maior_dif_perda, dif_perda_rel)
        maior_dif_recon = max(maior_dif_recon, dif_recon)
        linhas.append(f"taxa={taxa}")
        linhas.append(f"  perda proprio={float(perda_proprio):.8f} oraculo={float(perda_oraculo):.8f} rel_dif={dif_perda_rel:.3e}")
        linhas.append(f"  forma predicao proprio={tuple(pred_proprio.shape)}")
        linhas.append(f"  max_dif_reconstrucao={dif_recon:.3e}")

        assert pred_proprio.shape == (8, 16, 192)
        assert dif_perda_rel < TOLERANCIA_PERDA_REL, (
            f"perda diverge: rel={dif_perda_rel:.3e}"
        )
        assert dif_recon < TOLERANCIA_RECON_ABS, (
            f"reconstrucao diverge: abs={dif_recon:.3e}"
        )
    linhas.append("")
    linhas.append(f"tolerancia perda: rel < {TOLERANCIA_PERDA_REL}")
    linhas.append(f"tolerancia reconstrucao: abs < {TOLERANCIA_RECON_ABS}")
    linhas.append(f"maior diferenca observada: perda rel={maior_dif_perda:.3e} recon abs={maior_dif_recon:.3e}")
    linhas.append("STATUS: PASSOU")
    RELATORIO.write_text("\n".join(linhas) + "\n")


if __name__ == "__main__":
    test_equivalencia_with_oraculo()
    print(f"relatorio em {RELATORIO}")