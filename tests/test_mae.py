from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo import mae


def test_permutacao_fixa_e_determinista():
    perm1 = mae.permutacoes_fixas(10, seed=42)
    perm2 = mae.permutacoes_fixas(10, seed=42)
    assert torch.equal(perm1, perm2)
    assert perm1.shape == (10, 16)
    assert set(perm1[0].tolist()) == set(range(16))


def test_mascara_75_contem_50():
    perm = mae.permutacoes_fixas(6)
    ocultos50 = mae.indices_ocultos(perm, 0.5)
    ocultos75 = mae.indices_ocultos(perm, 0.75)
    for b in range(6):
        assert set(ocultos50[b].tolist()).issubset(set(ocultos75[b].tolist()))
        assert ocultos50.shape[1] == 8
        assert ocultos75.shape[1] == 12


def test_encoder_recebe_somente_visiveis():
    torch.manual_seed(0)
    modelo = mae.MAE()
    imagens = torch.rand(2, 3, 32, 32)
    perm = mae.permutacoes_fixas(2)
    out = modelo(imagens, indices_mascarados=mae.indices_ocultos(perm, 0.75))
    for b in range(2):
        visiveis = set(out["indices_visiveis"][b].tolist())
        ocultos = set(out["indices_mascarados"][b].tolist())
        assert len(visiveis) == 4 and len(ocultos) == 12
        assert visiveis.isdisjoint(ocultos)
    assert out["predicao"].shape == (2, 16, 192)


def test_perda_independente_dos_visiveis():
    pred = torch.rand(2, 16, 192)
    perm = mae.permutacoes_fixas(2)
    idx = mae.indices_ocultos(perm, 0.5)
    alvo_a = torch.rand(2, 3, 32, 32)
    alvo_b = alvo_a.clone()
    p_a = mae.patchify(alvo_a)
    p_b = mae.patchify(alvo_b)
    visiveis = torch.ones(2, 16, dtype=torch.bool)
    visiveis.scatter_(1, idx, False)
    p_a[torch.nonzero(visiveis, as_tuple=True)] = 0.0
    assert torch.allclose(
        mae.perda_mae(pred, p_a, idx), mae.perda_mae(pred, p_b, idx)
    )
    oculto_somente = torch.nonzero(~visiveis, as_tuple=True)
    p_b[oculto_somente] = 0.0
    assert not torch.allclose(
        mae.perda_mae(pred, p_a, idx), mae.perda_mae(pred, p_b, idx)
    )


def test_rejeita_valores_fora_do_intervalo():
    modelo = mae.MAE()
    try:
        modelo(torch.full((1, 3, 32, 32), 1.5))
    except ValueError:
        pass
    else:
        raise AssertionError("aceitou entrada fora de [0,1]")


def test_taxa_invalida_rejeitada():
    perm = mae.permutacoes_fixas(2)
    try:
        mae.indices_ocultos(perm, 0.9)
    except ValueError:
        pass
    else:
        raise AssertionError("aceitou taxa 0.9")


def test_patchify_e_unpatchify():
    imagens = torch.rand(3, 3, 32, 32)
    patches = mae.patchify(imagens)
    assert patches.shape == (3, 16, 192)
    assert torch.allclose(mae.unpatchify(patches), imagens)
    assert patches[0, 0].shape == (192,)