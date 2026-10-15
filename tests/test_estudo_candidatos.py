from __future__ import annotations

import json
import sys
from pathlib import Path

import torch
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo import configuracao_estudo as cfg
from codigo import estudo_candidatos as ec
from codigo import estudo_mascaras as em
from codigo.mae import MAE


def test_declaracoes_e_configuracao_coesas():
    decls = ec.declaracoes()
    assert set(decls) == {"C0", "C1", "C2", "C3"}
    for candidato_id, declaracao in decls.items():
        assert declaracao == cfg.CANDIDATOS[candidato_id]
    # C1: decoder 128/3 blocos; C0 e C2: decoder 64/2
    assert decls["C1"]["dim_decoder"] == 128
    assert decls["C1"]["profundidade_decoder"] == 3
    for cid in ("C0", "C2"):
        assert decls[cid]["dim_decoder"] == 64
        assert decls[cid]["profundidade_decoder"] == 2
    # C2 perda mista; C0/C1/C3 mse
    assert decls["C2"]["perda"] == "mse_l1" and decls["C2"]["peso_l1"] == 0.1
    for cid in ("C0", "C1", "C3"):
        assert decls[cid]["perda"] == "mse"
    # C3 residual com arquitetura igual a C0
    assert decls["C3"]["residual"] is True
    assert all(decls[cid]["residual"] is False for cid in ("C0", "C1", "C2"))
    assert decls["C3"]["dim_decoder"] == decls["C0"]["dim_decoder"]
    # declarações congeladas
    with pytest.raises(TypeError):
        decls["C0"]["dim"] = 999


def test_construir_modelo_segue_declaracao():
    modelo_c1 = ec.construir_modelo(cfg.CANDIDATOS["C1"])
    assert isinstance(modelo_c1, MAE)
    assert modelo_c1.enc_to_dec.out_features == 128
    assert len(modelo_c1.decoder.layers) == 3
    modelo_c0 = ec.construir_modelo(cfg.CANDIDATOS["C0"])
    assert modelo_c0.enc_to_dec.out_features == 64
    assert len(modelo_c0.decoder.layers) == 2


def test_forward_c1_e_c0_taxa_75():
    torch.manual_seed(0)
    imagens = torch.rand(2, 3, 32, 32)
    for cid in ("C0", "C1"):
        modelo = ec.construir_modelo(cfg.CANDIDATOS[cid])
        saida = modelo(imagens, taxa=0.75)
        assert torch.isfinite(saida["perda"])
        assert saida["predicao"].shape == (2, 16, 192)


def test_perda_mista_e_somente_nos_ocultos():
    torch.manual_seed(1)
    b = 2
    alvos = torch.rand(b, 16, 192)
    predicao = torch.rand(b, 16, 192)
    mascaras = em.mascaras_lote(10, 0, [5, 99], 0.5)
    indices = torch.from_numpy(mascaras).long()
    declaracao = cfg.CANDIDATOS["C2"]
    perda = ec.perda_candidato(declaracao, predicao, alvos, indices)
    lote = torch.arange(b)[:, None]
    pred_h = predicao[lote, indices]
    alvos_h = alvos[lote, indices]
    mse = torch.mean((pred_h - alvos_h) ** 2)
    l1 = torch.mean(torch.abs(pred_h - alvos_h))
    assert torch.allclose(perda, mse + 0.1 * l1, atol=1e-7)
    # visíveis não entram: zerar todos os pixels visíveis não muda a perda
    visiveis = torch.ones(b, 16, dtype=torch.bool)
    visiveis.scatter_(1, indices, False)
    alvos_zerado = alvos.clone()
    alvos_zerado[torch.nonzero(visiveis, as_tuple=True)] = 0.0
    assert torch.allclose(
        ec.perda_candidato(declaracao, predicao, alvos_zerado, indices),
        perda,
        atol=1e-12,
    )
    # predição igual aos alvos → perda zero
    assert float(ec.perda_candidato(declaracao, alvos, alvos, indices)) == 0.0


def test_perda_mse_simples_em_c0():
    torch.manual_seed(1)
    b = 2
    alvos = torch.rand(b, 16, 192)
    indices = torch.from_numpy(em.mascaras_lote(10, 0, [1, 2], 0.75)).long()
    perda = ec.perda_candidato(cfg.CANDIDATOS["C0"], alvos + 0.5, alvos, indices)
    assert torch.isfinite(perda)
    assert float(ec.perda_candidato(cfg.CANDIDATOS["C0"], alvos, alvos, indices)) == 0.0


def test_composicao_residual():
    torch.manual_seed(2)
    b = 3
    preenchimento = torch.rand(b, 16, 192)
    correcao = torch.full((b, 16, 192), 2.0)  # levaria todo patch a > 1
    indices = torch.from_numpy(em.mascaras_lote(10, 0, [7, 42, 88], 0.5)).long()
    saida = ec.composicao_residual(preenchimento, correcao, indices)
    lote = torch.arange(b)[:, None]
    saida_ocultos = saida[lote, indices]
    visiveis = torch.ones(b, 16, dtype=torch.bool)
    visiveis.scatter_(1, indices, False)
    # visíveis preservados exatamente
    assert torch.allclose(
        saida[torch.nonzero(visiveis, as_tuple=True)],
        preenchimento[torch.nonzero(visiveis, as_tuple=True)],
    )
    # ocultos = preenchimento + correção limitado a [0,1]
    esperado = (preenchimento[lote, indices] + 2.0).clamp(0.0, 1.0)
    assert torch.allclose(saida_ocultos, esperado)
    assert saida.min() >= 0.0 and saida.max() <= 1.0


def test_elegibilidade_c3_elegivel_nas_duas_taxas():
    elegivel, motivo = ec.elegibilidade_c3(
        mse_c0_por_taxa={0.5: 0.05, 0.75: 0.06},
        mse_baselines={
            "media_rgb": {0.5: 0.08, 0.75: 0.10},
            "interpolacao": {0.5: 0.09, 0.75: 0.10},
        },
        minutos_livres=35.0,
    )
    assert elegivel
    assert "35.00" in motivo


def test_elegibilidade_c3_rejeita_baseline_menor_numa_taxa():
    elegivel, motivo = ec.elegibilidade_c3(
        mse_c0_por_taxa={0.5: 0.05, 0.75: 0.06},
        mse_baselines={
            "media_rgb": {0.5: 0.08, 0.75: 0.05},  # 75%: baseline melhor
            "interpolacao": {0.5: 0.09, 0.75: 0.10},
        },
        minutos_livres=40.0,
    )
    assert not elegivel
    assert "0.75" in motivo and "media_rgb" in motivo


def test_elegibilidade_c3_rejeita_saldo_menor_que_30():
    elegivel, motivo = ec.elegibilidade_c3(
        mse_c0_por_taxa={0.5: 0.05, 0.75: 0.06},
        mse_baselines={
            "media_rgb": {0.5: 0.08, 0.75: 0.10},
            "interpolacao": {0.5: 0.09, 0.75: 0.10},
        },
        minutos_livres=29.9,
    )
    assert not elegivel
    assert "saldo" in motivo and "reserva" in motivo
    # igualmente justo a 30: elegível
    elegivel_limitrofo, _ = ec.elegibilidade_c3(
        mse_c0_por_taxa={0.5: 0.05, 0.75: 0.06},
        mse_baselines={
            "media_rgb": {0.5: 0.08, 0.75: 0.10},
            "interpolacao": {0.5: 0.09, 0.75: 0.10},
        },
        minutos_livres=30.0,
    )
    assert elegivel_limitrofo


def test_manifesto_hash_estavel_e_tamper_e_detectado(tmp_path):
    h1 = cfg.hash_configuracao()
    h2 = cfg.hash_configuracao()
    assert h1 == h2 and len(h1) == 64
    caminho = tmp_path / "manifesto.json"
    salvo = cfg.salvar_manifesto(caminho)
    assert salvo["hash_manifesto"] == h1
    conteudo = cfg.verificar_manifesto(caminho)
    assert conteudo["comum"]["lr"] == 1e-4
    alterado = json.loads(caminho.read_text(encoding="utf-8"))
    alterado["comum"]["lr"] = 3e-4
    caminho.write_text(
        json.dumps(alterado, sort_keys=True, separators=(",", ":"))
    )
    with pytest.raises(ValueError, match="divergente"):
        cfg.verificar_manifesto(caminho)
    # serialização canônica idêntica para dicionários em ordem diferente
    proposta = dict(reversed(list(cfg.CONFIG.items())))
    assert cfg.hash_configuracao(proposta) == h1


def test_orcamento_no_manifesto():
    orc = cfg.CONFIG["orcamento"]
    assert orc["total_minutos"] == 120.0
    assert orc["principal_minutos"] == 90.0
    assert orc["reserva_minutos"] == 30.0
    por_candidato = orc["por_candidato"]
    assert por_candidato["piloto"] == 2.0
    assert por_candidato["treino_total"] == 24.0
    assert por_candidato["treino_por_seed_taxa"] == 4.0
    assert por_candidato["consolidacao"] == 2.0
    assert por_candidato["avaliacao"] == 2.0
    assert orc["avaliacao_final_baselines_minutos"] == 6.0
    assert cfg.CONFIG["limiares"]["razao_mse_maximo"] == 0.95
    assert cfg.CONFIG["limiares"]["ganho_ssim_minimo"] == 0.02
    assert cfg.CONFIG["limiares"]["tolerancia_ssim"] == 0.01
    assert cfg.CONFIG["limiares"]["piloto_segundos_maximo"] == 1.2
    assert cfg.CONFIG["seeds_treino"] == [10, 20, 30]
    assert cfg.CONFIG["taxas"] == [0.5, 0.75]
    assert cfg.CONFIG["epocas_planejadas"] == 200
    comum = cfg.CONFIG["comum"]
    assert comum["batch"] == 64 and comum["lr"] == 1e-4
    assert comum["weight_decay"] == 0.05
    assert comum["beta1"] == 0.9 and comum["beta2"] == 0.999
    assert comum["epsilon_adam"] == 1e-8
    assert comum["precisao"] == "float32"
    assert comum["scheduler"] is None and comum["clipagem_gradiente"] is None
