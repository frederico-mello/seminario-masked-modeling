from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo import estudo_avaliacao as ea
from codigo import estudo_ssim as es
from codigo.mae import permutacoes_fixas


def test_regua_por_posicao_e_aninhada():
    n = 50
    ocultos_50 = ea.regua_validacao(n, 0.5)
    ocultos_75 = ea.regua_validacao(n, 0.75)
    assert ocultos_50.shape == (n, 8)
    assert ocultos_75.shape == (n, 12)
    for b in range(n):
        assert set(ocultos_50[b].tolist()).issubset(set(ocultos_75[b].tolist()))
    # por posição, com a semente 42 da régua (idêntica à avaliação original)
    perm = permutacoes_fixas(n, seed=42)
    assert torch.equal(ea.regua_validacao(n, 0.5), perm[:, :8])


def test_regua_deterministica():
    n = 30
    assert torch.equal(
        ea.regua_validacao(n, 0.75), ea.regua_validacao(n, 0.75)
    )


def test_mse_da_regua_ignora_pixels_visiveis():
    torch.manual_seed(0)
    b = 3
    alvos = torch.rand(b, 16, 192)
    predicao = alvos + 0.01 * torch.randn_like(alvos)
    regua = ea.regua_validacao(b, 0.5)
    base = ea.mse_regua(predicao, alvos, regua)
    # mudar todos os pixels visíveis -- o MSE não pode mudar
    predicao_suja = predicao.clone()
    visiveis = torch.ones(b, 16, dtype=torch.bool)
    visiveis.scatter_(1, regua, False)
    predicao_suja[torch.nonzero(visiveis, as_tuple=True)] = 0.0
    assert abs(ea.mse_regua(predicao_suja, alvos, regua) - base) < 1e-12
    # mudar um patch oculto -- o MSE muda
    predicao_suja = predicao.clone()
    predicao_suja[0, regua[0][0]] = 0.0
    assert ea.mse_regua(predicao_suja, alvos, regua) != base


def test_mse_por_imagem_e_agregado_consistentes():
    torch.manual_seed(1)
    b = 4
    alvos = torch.rand(b, 16, 192)
    predicao = torch.rand(b, 16, 192)
    regua = ea.regua_validacao(b, 0.75)
    por_imagem = ea.mse_regua(predicao, alvos, regua, por_imagem=True)
    agregado = ea.mse_regua(predicao, alvos, regua)
    assert por_imagem.shape == (b,)
    assert abs(float(por_imagem.double().mean()) - agregado) < 1e-12


def test_ssim_da_regua_e_a_medeia_dos_patches_ocultos():
    torch.manual_seed(2)
    b = 2
    alvos = torch.rand(b, 16, 192)
    predicao = torch.rand(b, 16, 192)
    regua = ea.regua_validacao(b, 0.5)
    valores = ea.ssim_regua(predicao, alvos, regua, por_imagem=True)
    assert valores.shape == (b,)
    # referência direta pelos patches ocultos
    lote = torch.arange(b)[:, None]
    pred_h = predicao[lote, regua]
    alvos_h = alvos[lote, regua]
    ref = es.ssim_patches_ocultos(
        alvos_h.reshape(b, -1, 8, 8, 3).permute(0, 1, 4, 2, 3),
        pred_h.reshape(b, -1, 8, 8, 3).permute(0, 1, 4, 2, 3),
    )
    assert torch.allclose(valores, ref, atol=1e-12)
    assert abs(float(valores.double().mean()) - ea.ssim_regua(predicao, alvos, regua)) < 1e-12


def test_regua_igual_para_todos_os_avaliados():
    """A mesma régua garantidamente reutilizável: mesmo objeto de índices."""
    n = 12
    regua = ea.regua_validacao(n, 0.5)
    alvos = torch.rand(n, 16, 192)
    pred_a = alvos.clone()
    candidato_a = ea.mse_regua(pred_a, alvos, regua)
    baseline_b = ea.mse_regua(pred_a, alvos, regua)
    assert candidato_a == baseline_b
