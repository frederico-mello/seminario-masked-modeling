"""MAE proprio em PyTorch puro para o seminario de Masked Modeling.

Arquitetura (ver openspec, spec mae-modelo):
- Entrada: imagem 32x32x3 com valores em [0,1], 16 patches de 8x8.
- Encoder: dim 128, 4 blocos, 4 heads, processa somente os patches visiveis.
- Decoder: dim 64, 2 blocos, 4 heads, previu 192 valores por patch (8x8x3).
- Perda: MSE somente nos patches ocultos, em pixels brutos em [0,1].
- Mascara aninhada: permutacao fixa dos 16 indices por imagem com seed 42.
"""

from __future__ import annotations

import math

import numpy as np
import torch
from torch import nn

SEMENTE_MASCARA = 42


def patchify(imagens: torch.Tensor) -> torch.Tensor:
    """Divide (B, C, H, W) em (B, n_patches, patch*patch*C)."""
    if imagens.ndim != 4:
        raise ValueError(f"esperado tensor 4D (B,C,H,W), obtido {tuple(imagens.shape)}")
    b, c, h, w = imagens.shape
    p = 8
    if h % p != 0 or w % p != 0:
        raise ValueError(f"dimensao {h}x{w} nao divisivel pelo patch {p}")
    if imagens.min() < 0.0 or imagens.max() > 1.0:
        raise ValueError("valores fora do intervalo [0,1]")
    patches = imagens.reshape(b, c, h // p, p, w // p, p)
    patches = patches.permute(0, 2, 4, 3, 5, 1)
    return patches.reshape(b, (h // p) * (w // p), p * p * c)


def unpatchify(patches: torch.Tensor) -> torch.Tensor:
    """Inverte patchify: (B, n_patches, p*p*C) -> (B, C, H, W)."""
    b, n, _ = patches.shape
    p = 8
    h = w = int(math.sqrt(n)) * p
    c = patches.shape[-1] // (p * p)
    x = patches.reshape(b, h // p, w // p, p, p, c)
    x = x.permute(0, 5, 1, 3, 2, 4)
    return x.reshape(b, c, h, w)


def permutacoes_fixas(n_imagens: int, seed: int = SEMENTE_MASCARA) -> torch.Tensor:
    """Permutacao fixa dos 16 indices de patch, uma por imagem, determinista.

    A 50% oculta os 8 primeiros indices; a 75%, os 12 primeiros.
    """
    rng = np.random.default_rng(seed)
    perms = np.stack([rng.permutation(16) for _ in range(n_imagens)])
    return torch.from_numpy(perms).long()


def indices_ocultos(
    permutacoes: torch.Tensor, taxa: float
) -> torch.Tensor:
    """Indices de patch ocultos para a taxa informada, a partir da permutacao fixa."""
    if taxa not in (0.5, 0.75):
        raise ValueError(f"taxa suportada e 0.5 ou 0.75, recebido {taxa}")
    n = permutacoes.shape[1]
    return permutacoes[:, : int(taxa * n)]


class Attencao(nn.Module):
    def __init__(self, dim: int, heads: int, dim_head: int, dropout: float = 0.0):
        super().__init__()
        inner = dim_head * heads
        self.heads = heads
        self.scale = dim_head**-0.5
        self.norm = nn.LayerNorm(dim)
        self.to_qkv = nn.Linear(dim, inner * 3, bias=False)
        self.dropout = nn.Dropout(dropout)
        self.to_out = nn.Sequential(
            nn.Linear(inner, dim), nn.Dropout(dropout)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.norm(x)
        qkv = self.to_qkv(x).chunk(3, dim=-1)
        shape = x.shape[0], x.shape[1], self.heads, -1
        q, k, v = (t.reshape(*shape).transpose(1, 2) for t in qkv)
        out = torch.nn.functional.scaled_dot_product_attention(q, k, v)
        out = out.transpose(1, 2).reshape(x.shape[0], x.shape[1], -1)
        return self.to_out(self.dropout(out))


class FeedForward(nn.Module):
    def __init__(self, dim: int, oculto: int, dropout: float = 0.0):
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, oculto),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(oculto, dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class Bloco(nn.Module):
    def __init__(self, dim, heads, dim_head, mlp_dim, dropout=0.0):
        super().__init__()
        self.atencao = Attencao(dim, heads, dim_head, dropout)
        self.ff = FeedForward(dim, mlp_dim, dropout)

    def forward(self, x):
        x = self.atencao(x) + x
        x = self.ff(x) + x
        return x


class PilhaBlocos(nn.Module):
    def __init__(self, dim, depth, heads, dim_head, mlp_dim):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.layers = nn.ModuleList(
            [Bloco(dim, heads, dim_head, mlp_dim) for _ in range(depth)]
        )

    def forward(self, x):
        for bloco in self.layers:
            x = bloco(x)
        return self.norm(x)


def perda_mae(
    predicao: torch.Tensor,
    patches: torch.Tensor,
    indices_mascarados: torch.Tensor,
) -> torch.Tensor:
    """MSE somente nos patches ocultos, em pixels brutos em [0,1]."""
    if patches.min() < 0.0 or patches.max() > 1.0:
        raise ValueError("alvos fora do intervalo [0,1]")
    lote = torch.arange(patches.shape[0], device=predicao.device)[:, None]
    alvo = patches[lote, indices_mascarados]
    pred_ocultos = predicao[lote, indices_mascarados]
    return torch.nn.functional.mse_loss(pred_ocultos, alvo)


class MAE(nn.Module):
    def __init__(
        self,
        dim: int = 128,
        profundidade: int = 4,
        heads: int = 4,
        dim_head: int = 32,
        dim_decoder: int = 64,
        profundidade_decoder: int = 2,
        heads_decoder: int = 4,
        dim_head_decoder: int = 64,
        tamanho_patch: int = 8,
        canais: int = 3,
    ):
        super().__init__()
        patch_dim = canais * tamanho_patch * tamanho_patch
        num_patches = (32 // tamanho_patch) * (32 // tamanho_patch)
        self.tamanho_patch = tamanho_patch

        self.patch_embed = nn.Sequential(
            nn.LayerNorm(patch_dim),
            nn.Linear(patch_dim, dim),
            nn.LayerNorm(dim),
        )
        self.pos_embedding = nn.Parameter(torch.randn(num_patches, dim))

        self.encoder = PilhaBlocos(dim, profundidade, heads, dim_head, dim * 4)

        self.enc_to_dec = nn.Linear(dim, dim_decoder)
        self.mask_token = nn.Parameter(torch.randn(dim_decoder))
        self.decoder_pos_emb = nn.Embedding(num_patches, dim_decoder)
        self.decoder = PilhaBlocos(
            dim_decoder,
            profundidade_decoder,
            heads_decoder,
            dim_head_decoder,
            dim_decoder * 4,
        )
        self.to_pixels = nn.Linear(dim_decoder, patch_dim)
        self.num_patches = num_patches

    def forward(
        self,
        imagens: torch.Tensor,
        indices_mascarados: torch.Tensor | None = None,
        taxa: float = 0.75,
    ) -> dict:
        """Frente do MAE.

        imagens: (B, C, 32, 32) em [0,1].
        indices_mascarados: (B, n_ocultos) opcional; por padrao usa a
        permutacao fixa com seed 42 (uma por imagem da lote, na ordem).
        Retorna dict com perda, predicao completa (B,16,192) e indices.
        """
        if imagens.min() < 0.0 or imagens.max() > 1.0:
            raise ValueError("valores fora do intervalo [0,1]")

        b = imagens.shape[0]
        device = imagens.device
        patches = patchify(imagens)
        num_patches = patches.shape[1]

        if indices_mascarados is None:
            perm = permutacoes_fixas(b).to(device)
            indices_mascarados = indices_ocultos(perm, taxa)
        indices_mascarados = indices_mascarados.to(device)
        num_ocultos = indices_mascarados.shape[1]

        lote = torch.arange(b, device=device)[:, None]
        visiveis = torch.ones(
            (b, num_patches), dtype=torch.bool, device=device
        )
        visiveis.scatter_(1, indices_mascarados, False)
        n_visiveis = num_patches - num_ocultos
        indices_visiveis = torch.argsort(
            (~visiveis).long(), dim=1, stable=True
        )[:, :n_visiveis]

        tokens = self.patch_embed(patches)
        tokens = tokens + self.pos_embedding

        tokens_vis = tokens[lote, indices_visiveis]

        codificados = self.encoder(tokens_vis)

        dec_vis = self.enc_to_dec(codificados)
        dec_vis = dec_vis + self.decoder_pos_emb(indices_visiveis)

        tokens_mascara = self.mask_token.repeat(b, num_ocultos, 1)
        tokens_mascara = tokens_mascara + self.decoder_pos_emb(
            indices_mascarados
        )

        canvas = torch.zeros(
            b, num_patches, self.mask_token.shape[0], device=device
        )
        canvas[lote, indices_visiveis] = dec_vis
        canvas[lote, indices_mascarados] = tokens_mascara
        decodificados = self.decoder(canvas)

        pred = self.to_pixels(decodificados)

        perda = perda_mae(pred, patches, indices_mascarados)

        return {
            "perda": perda,
            "predicao": pred,
            "indices_mascarados": indices_mascarados,
            "indices_visiveis": indices_visiveis,
            "patches": patches,
        }


def reconstrucao_completa(
    predicao: torch.Tensor,
    patches: torch.Tensor,
    indices_mascarados: torch.Tensor,
) -> torch.Tensor:
    """Monta a imagem (B,C,32,32): visiveis mantidos, ocultos da predicao."""
    recon = patches.clone()
    lote = torch.arange(patches.shape[0], device=predicao.device)[:, None]
    recon[lote, indices_mascarados] = predicao[lote, indices_mascarados]
    return unpatchify(recon)


def imagem_com_buracos(
    patches: torch.Tensor, indices_mascarados: torch.Tensor
) -> torch.Tensor:
    """Imagem com patches ocultos zerados, para visualizacao."""
    buracos = patches.clone()
    lote = torch.arange(patches.shape[0], device=buracos.device)[:, None]
    buracos[lote, indices_mascarados] = 0.0
    return unpatchify(buracos)