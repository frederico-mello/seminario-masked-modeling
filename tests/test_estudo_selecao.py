from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo import estudo_selecao as el


def test_elegibilidade_dos_limiares_com_os_dois_criterios():
    mse_c0 = [0.070, 0.072, 0.068]
    ssim_c0 = [0.60, 0.62, 0.58]
    ok, motivo = el.elegivel([0.062, 0.064, 0.060], [0.63, 0.65, 0.61],
                             mse_c0, ssim_c0)
    assert ok
    # MSE mediano 0,062 / mediana C0 0,070 = 0,8857 <= 0,95; SSIM dif 0,01? não
    # as diferenças pareadas de SSIM são 0,03 em cada seed
    assert "SSIM" not in motivo[:5]


def test_rejeita_razao_mse_acima_de_0_95():
    ok, motivo = el.elegivel([0.075, 0.075, 0.075], [0.65, 0.65, 0.65],
                             [0.070, 0.070, 0.070], [0.60, 0.60, 0.60])
    assert not ok and "0.95" in motivo


def test_rejeita_ganho_ssim_menor_que_0_02():
    # razão ok: 0.066/0.070 = 0.94; SSIM pareado: ganho de apenas 0,015
    ok, motivo = el.elegivel([0.066, 0.066, 0.066], [0.615, 0.615, 0.615],
                             [0.070, 0.070, 0.070], [0.60, 0.60, 0.60])
    assert not ok and "SSIM" in motivo


def test_mediana_e_por_seed_e_diferenca_pareada():
    #  por seed; candidato deve vencer no pareado
    mse_c0 = [0.080, 0.060, 0.090]
    ssim_c0 = [0.55, 0.70, 0.45]
    ok, _ = el.elegivel([0.060, 0.060, 0.060], [0.60, 0.75, 0.63],
                        mse_c0, ssim_c0)
    # razão: 0.060/0.080 = 0.75 <= 0.95; difs pareadas = [0.05, 0.05, 0.18]
    assert ok


def test_selecao_escolhe_menor_mse_entre_elegiveis():
    dados_c = {
        "C1": {
            "mse": [0.060, 0.062, 0.058],
            "ssim": [0.66, 0.66, 0.66],
        },
        "C2": {
            "mse": [0.063, 0.063, 0.063],
            "ssim": [0.645, 0.645, 0.645],
        },
    }
    mse_c0 = [0.070, 0.070, 0.070]
    ssim_c0 = [0.60, 0.60, 0.60]
    saida = el.selecionar(
        {k: d["mse"] for k, d in dados_c.items()},
        {k: d["ssim"] for k, d in dados_c.items()},
        mse_c0,
        ssim_c0,
        tempos_acumulados={"C1": 30.0, "C2": 24.0},
    )
    assert saida["vencedor"] == "C1"
    assert set(saida["elegiveis"]) == {"C1", "C2"}
    # maiores SSIM medianos retidos pela tolerância de 0,01: C1 apenas
    # (a 0,015 abaixo do máximo já sai do conjunto retido)
    assert saida["retidos"] == ["C1"]
    assert "C2" not in saida["mediana_mse"]
    assert abs(saida["mediana_mse"]["C1"] - 0.060) < 1e-12


def test_tolerancia_0_01_em_vela_ssins_proximos():
    # C2 com SSIM mediano 0,01 abaixo do máximo: retido pela tolerância;
    # C1 com SSIM maior mas MSE também maior: C2 vence no menor MSE dentro
    # do conjunto retido
    dados = {
        "C1": {"mse": [0.070, 0.070, 0.070], "ssim": [0.760, 0.760, 0.760]},
        "C2": {"mse": [0.062, 0.062, 0.062], "ssim": [0.750, 0.750, 0.750]},
    }
    mse_c0 = [0.075, 0.075, 0.075]
    ssim_c0 = [0.70, 0.70, 0.70]
    saida = el.selecionar(
        {k: d["mse"] for k, d in dados.items()},
        {k: d["ssim"] for k, d in dados.items()},
        mse_c0,
        ssim_c0,
        tempos_acumulados={"C1": 1.0, "C2": 9.0},
    )
    assert saida["vencedor"] == "C2"
    assert set(saida["retidos"]) == {"C1", "C2"}


def test_desempate_por_tempo_depois_ordem_fixa():
    mse = [0.055, 0.055, 0.055]
    ssim = [0.75, 0.75, 0.75]
    mse_c0 = [0.080, 0.080, 0.080]
    ssim_c0 = [0.60, 0.60, 0.60]
    com_tempo = el.selecionar(
        {"C1": mse, "C2": mse},
        {"C1": ssim, "C2": ssim},
        mse_c0,
        ssim_c0,
        tempos_acumulados={"C1": 20.0, "C2": 18.0},
    )
    assert com_tempo["vencedor"] == "C2"  # menor tempo acumulado vence
    com_ordem = el.selecionar(
        {"C1": mse, "C2": mse},
        {"C1": ssim, "C2": ssim},
        mse_c0,
        ssim_c0,
        tempos_acumulados={"C1": 10.0, "C2": 10.0},
    )
    assert com_ordem["vencedor"] == "C1"  # empate total: ordem C1, C2, C3


def test_tempo_desconhecido_vai_para_o_fim_da_comparacao():
    mse = [0.055, 0.055, 0.055]
    ssim = [0.75, 0.75, 0.75]
    saida = el.selecionar(
        {"C1": mse, "C2": mse, "C3": mse},
        {"C1": ssim, "C2": ssim, "C3": ssim},
        [0.080, 0.080, 0.080],
        [0.60, 0.60, 0.60],
        tempos_acumulados={"C2": 10.0},  # C1 e C3 sem tempo informado
    )
    assert saida["vencedor"] == "C2"  # com tempo, desempata primeiro


def test_sem_elegivel_supera_ausencia_de_melhoria():
    saida = el.selecionar(
        {"C1": [0.070, 0.070, 0.070]},
        {"C1": [0.60, 0.60, 0.60]},
        [0.070, 0.070, 0.090],
        [0.60, 0.60, 0.60],
        tempos_acumulados={},
    )
    assert saida["vencedor"] is None
    assert "sem melhoria" in saida["motivo"]
    assert set(saida["elegiveis"]) == set()


def test_tamanho_de_seeds_divergente_e_erro():
    with pytest.raises(ValueError):
        el.elegivel([0.06] * 3, [0.63] * 2, [0.07] * 3, [0.60] * 1)
