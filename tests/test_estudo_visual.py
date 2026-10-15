from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo import estudo_ssim as es
from codigo import estudo_visual as ev

C1 = 0.01**2
C2 = 0.03**2
SIGMA = 1.5


def _reflejar(i: int) -> int:
    if i < 0:
        return -i
    if i > 7:
        return 14 - i
    return i


def _kernel_referencia() -> np.ndarray:
    faixa = np.array([-1.0, 0.0, 1.0])
    peso_1d = np.exp(-(faixa**2) / (2 * SIGMA**2))
    peso_1d = peso_1d / peso_1d.sum()
    return peso_1d[:, None] * peso_1d[None, :]


def _ssim_pixel_referencia(a: np.ndarray, b: np.ndarray, r: int, c: int) -> float:
    """SSIM por pixel de referência, com loops explícitos e padding repetido."""
    kernel = _kernel_referencia()
    mx = my = mxx = myy = mxy = 0.0
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            w = kernel[di + 1, dj + 1]
            ii = _reflejar(r + di)
            jj = _reflejar(c + dj)
            x = a[ii, jj]
            y = b[ii, jj]
            mx += w * x
            my += w * y
            mxx += w * x * x
            myy += w * y * y
            mxy += w * x * y
    sx = max(mxx - mx * mx, 0.0)
    sy = max(myy - my * my, 0.0)
    sxy = mxy - mx * my
    num = (2 * mx * my + C1) * (2 * sxy + C2)
    den = (mx * mx + my * my + C1) * (sx + sy + C2)
    den = den if den > 1e-12 else 1e-12
    return num / den


def _patch_imagem(padrao: np.ndarray | None = None, valor: float = 0.4) -> torch.Tensor:
    if padrao is None:
        return torch.full((1, 3, 8, 8), valor)
    t = torch.from_numpy(np.broadcast_to(padrao[None], (1, 3, 8, 8)).copy())
    return t.clone()


def test_janela_gaussiana_normalizada():
    kernel = es.pesos_janela()[0, 0]
    esperado = _kernel_referencia()
    assert abs(kernel[1, 1].item() - esperado[1, 1].item()) < 1e-7
    assert torch.allclose(
        kernel, torch.from_numpy(esperado), atol=1e-6
    )
    a = np.exp(-1.0 / (2 * SIGMA**2))
    norma = 1 + 2 * a
    assert abs(kernel[0, 1].item() - (a / norma) * (1.0 / norma)) < 1e-7
    assert kernel.sum().item() == pytest.approx(1.0)


def test_ssim_patch_identicos_e_um():
    torch.manual_seed(0)
    x = torch.rand(3, 8, 8)
    valores = es.ssim_por_patch(x[None], x[None])
    assert torch.allclose(valores, torch.ones_like(valores))


def test_ssim_patch_constante_igual_e_diferente():
    a = _patch_imagem(valor=0.3)
    b = _patch_imagem(valor=0.7)
    valor = es.ssim_por_patch(a, b)
    mx = float(a[0, 0, 0, 0])
    my = float(b[0, 0, 0, 0])
    esperado = (2 * mx * my + C1) / (mx * mx + my * my + C1)
    assert abs(valor.item() - esperado) < 1e-7
    # constantes iguais mantили SSIM 1
    iguais = es.ssim_por_patch(a, a)
    assert iguais.item() == pytest.approx(1.0, abs=1e-9)


def test_ssim_mapa_corresponde_a_referencia_de_loop():
    rng = np.random.default_rng(7)
    a = rng.random((8, 8)).astype(np.float64)
    b = rng.random((8, 8)).astype(np.float64)
    mapa = es.ssim_mapa(
        torch.from_numpy(np.stack([a, a, a])[None]).double(),
        torch.from_numpy(np.stack([b, b, b])[None]).double(),
    )[0].numpy()
    esperado = np.array(
        [[_ssim_pixel_referencia(a, b, r, c) for c in range(8)] for r in range(8)]
    )
    assert np.allclose(mapa, esperado, atol=1e-9)
    # média dos pixels equivale ao valor por patch
    assert np.allclose(es.ssim_por_patch(
        torch.from_numpy(np.stack([a, a, a])[None]).double(),
        torch.from_numpy(np.stack([b, b, b])[None]).double(),
    ).item(), mapa.mean())


def test_padding_reflete_sem_repetir_a_borda():
    # padrao com borda distinta: a referência de loop usa reflexão sem repetir
    a = np.zeros((8, 8))
    a[0, :] = 1.0  # primeira linha diferente do restante
    b = np.zeros((8, 8))
    b[0, :] = 0.5
    mapa = es.ssim_mapa(
        torch.from_numpy(np.stack([a, a, a])[None]).double(),
        torch.from_numpy(np.stack([b, b, b])[None]).double(),
    )[0].numpy()
    esperado = np.array(
        [[_ssim_pixel_referencia(a, b, r, c) for c in range(8)] for r in range(8)]
    )
    assert np.allclose(mapa, esperado, atol=1e-9)
    # controle: padding 'symmetric' repetiria a borda e nunca daria igual
    diff = np.abs(mapa - esperado).max()
    assert diff < 1e-9


def test_variancia_negativa_limitada_a_zero(tmp_path):
    # caso sintético com ruído mínimo: as duas opções de variância são
    # estabilidade pura (não NaN, não negativa no cálculo da reference)
    t = torch.zeros(1, 3, 8, 8) + 0.5
    assert es.ssim_por_patch(t, t).item() == 1.0
    # verificação direta da função de limitação
    v_negativo = torch.tensor([-1e-12, 0.0, 2.0])
    assert torch.equal(es._limitar_variancia(v_negativo), torch.tensor([0.0, 0.0, 2.0]))


def test_agregacao_canais_por_pixel_depois_patch_e_imagem():
    torch.manual_seed(1)
    real = torch.rand(2, 5, 3, 8, 8)  # 2 imagens, 5 patches ocultos cada
    pred = torch.rand(2, 5, 3, 8, 8)
    por_patch = es.ssim_por_patch(real, pred)
    assert por_patch.shape == (2, 5)
    por_imagem = es.ssim_patches_ocultos(real, pred)
    assert por_imagem.shape == (2,)
    manual = por_patch.mean(dim=1)
    assert torch.allclose(por_imagem, manual, atol=1e-12)
    media = es.media_imagens(por_imagem)
    assert abs(media - float(por_imagem.double().mean())) < 1e-12
    mediana = es.mediana_seeds([0.3, 0.7, 0.5])
    assert mediana == 0.5


def test_fora_do_intervalo_rejeitado():
    with pytest.raises(ValueError):
        es.ssim_mapa(torch.full((1, 3, 8, 8), 1.5), torch.zeros(1, 3, 8, 8))


def _indices_disponiveis() -> list[int]:
    return list(range(6900, 7000))


def test_selecao_ids_visuais_deterministica_e_segundo_sha256():
    versao = "split-v1"
    ids = ev.selecao_ids_visuais(_indices_disponiveis(), versao)
    assert len(ids) == 8
    # recomputação independente: nomeia 'visual-v1' + versão do split + decimal
    esperado = sorted(
        (hashlib.sha256(f"visual-v1|{versao}|{i}".encode("utf-8")).digest(), i)
        for i in _indices_disponiveis()
    )
    assert ids == [i for _, i in esperado[:8]]
    # determinismo
    assert ids == ev.selecao_ids_visuais(_indices_disponiveis(), versao)
    # versão do split diferente muda a lista
    outra = ev.selecao_ids_visuais(_indices_disponiveis(), versao + "-2")
    assert outra != ids
    # poucos índices → erro explícito
    import pytest


    with pytest.raises(ValueError, match="menos de 8"):
        ev.selecao_ids_visuais([1, 2, 3], versao)


def test_ficha_predefinida_sem_avaliacao_humana(tmp_path):
    ficha = ev.ficha_visual("split-v1", _indices_disponiveis())
    assert ficha["versao_ficha"] == "visual-v1"
    assert ficha["avaliacao_humana_realizada"] is False
    assert "avaliação humana foi realizada" in ficha["observacoes"] and ficha["avaliacao_humana_realizada"] is False
    assert ficha["itens"][str(ficha["ids_selecionados"][0])]["C1"] == {
        "cor": None,
        "estrutura": None,
        "borramento": None,
        "artefatos": None,
        "comentario": None,
    }
    assert "C1_vs_C2" in ficha["preferencia_pareada"]
    assert ficha["escala"].startswith("1 problema grave")
    # hash estável e deteção de divergência
    saida = ev.salvar_ficha(ficha, tmp_path / "ficha.json")
    import json

    conteudo = json.loads((tmp_path / "ficha.json").read_text(encoding="utf-8"))
    assert saida["sha256"] == hashlib.sha256(
        json.dumps(ficha, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assert conteudo["hash_ficha"] == saida["sha256"]
