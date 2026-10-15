from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo import estudo_baselines as eb


def imagem_por_patch(valores: np.ndarray) -> np.ndarray:
    """Imagem (3, 32, 32) com cor constante por patch: valores (4, 4, ?)."""
    valores = np.asarray(valores, dtype=np.float64)
    imagem = np.zeros((3, 32, 32), dtype=np.float64)
    for r in range(4):
        for c in range(4):
            imagem[
                :,
                r * 8 : r * 8 + 8,
                c * 8 : c * 8 + 8,
            ] = valores[r, c].reshape(-1, 1, 1)
    return imagem


def test_media_rgb_valores_exatos():
    valores = np.zeros((4, 4, 3))
    for r in range(4):
        for c in range(4):
            valores[r, c] = [0.01 * (4 * r + c + 1), 0.03, 0.05]
    imagem = imagem_por_patch(valores)
    ocultos = [0, 3, 6]
    recon = eb.media_rgb_visivel(imagem, ocultos)
    # média por canal sobre todos os pixels visíveis, calculada de forma
    # independente no teste
    visiveis = [i for i in range(16) if i not in set(ocultos)]
    medias_canal = []
    for ch in range(3):
        tot = 0.0
        n = 0
        for p in visiveis:
            r, c = eb.divisoria_patch(p)
            bloco = imagem[ch, r * 8 : r * 8 + 8, c * 8 : c * 8 + 8]
            tot += bloco.sum()
            n += bloco.size
        medias_canal.append(tot / n)
    esperado = np.array(medias_canal)
    for p in ocultos:
        r, c = eb.divisoria_patch(p)
        assert np.allclose(recon[:, r * 8 : r * 8 + 8, c * 8 : c * 8 + 8], esperado[:, None, None], atol=1e-12)


def test_visiveis_preservados_e_sem_acesso_a_ocultos():
    imagem = imagem_por_patch(np.full((4, 4, 3), 0.5))
    bomba = imagem.copy()
    for p in [2, 9]:
        r, c = eb.divisoria_patch(p)
        bomba[:, r * 8 : r * 8 + 8, c * 8 : c * 8 + 8] = 1e9
    ocultos = [2, 9]
    recon_limpo = eb.media_rgb_visivel(imagem, ocultos)
    recon_bomba = eb.media_rgb_visivel(bomba, ocultos)
    assert np.array_equal(recon_limpo, recon_bomba)
    esp_limpo = eb.interpolacao_espacial(imagem, ocultos)
    esp_bomba = eb.interpolacao_espacial(bomba, ocultos)
    assert np.array_equal(esp_limpo, esp_bomba)
    # patches visíveis permanecem idênticos ao original
    visivel = 5
    r, c = eb.divisoria_patch(visivel)
    assert np.array_equal(
        recon_bomba[:, r * 8 : r * 8 + 8, c * 8 : c * 8 + 8],
        imagem[:, r * 8 : r * 8 + 8, c * 8 : c * 8 + 8],
    )


def test_interpolacao_espacial_valores_exatos_um_oculto():
    romance = np.zeros((4, 4, 1))
    romance[0, 0] = 0.2
    romance[3, 3] = 0.4
    romance[0, 3] = 0.6
    imagem = imagem_por_patch(romance)
    # patch oculto (1, 1), índice 5, na grade 4x4
    ocultos = [5]
    recon = eb.interpolacao_espacial(imagem, ocultos)
    centro_oculto = eb.centro_patch(5)
    pesos = []
    for p in range(16):
        if p == 5:
            continue
        centro = eb.centro_patch(p)
        d2 = (centro[0] - centro_oculto[0]) ** 2 + (centro[1] - centro_oculto[1]) ** 2
        pesos.append((p, 1.0 / d2))
    total = soma = 0.0
    for p, w in pesos:
        r, c = eb.divisoria_patch(p)
        soma += w * romance[r, c][0]
        total += w
    esperado = soma / total
    r, c = eb.divisoria_patch(5)
    bloco = recon[:, r * 8 : r * 8 + 8, c * 8 : c * 8 + 8]
    assert np.allclose(bloco, esperado, atol=1e-12)
    pesos_np = np.array([w for _, w in pesos])
    assert pesos_np.sum() > 0
    assert np.isfinite(pesos_np).all()


def test_interpolacao_espacial_estrutura_por_pixel():
    rng = np.random.default_rng(3)
    imagem = rng.random((3, 32, 32))
    ocultos = [10]
    recon = eb.interpolacao_espacial(imagem, ocultos)
    r, c = eb.divisoria_patch(10)
    centro_oculto = eb.centro_patch(10)
    pesos = np.array(
        [
            1.0
            / (
                (eb.centro_patch(p)[0] - centro_oculto[0]) ** 2
                + (eb.centro_patch(p)[1] - centro_oculto[1]) ** 2
            )
            for p in range(16)
            if p != 10
        ]
    )
    pesos = pesos / pesos.sum()
    amostras = np.stack(
        [
            imagem[:, rp * 8 : rp * 8 + 8, cp * 8 : cp * 8 + 8]
            for p in range(16)
            if p != 10
            for rp, cp in [eb.divisoria_patch(p)]
        ]
    )
    esperado = np.tensordot(pesos, amostras, axes=(0, 0))
    assert np.allclose(recon[:, r * 8 : r * 8 + 8, c * 8 : c * 8 + 8], esperado, atol=1e-9)


def test_fallback_sem_vizinho_usa_media_rgb_visivel():
    todos_ocultos = list(range(16))
    # volta ao caso geral sem oculto visível: interpolação recorre a média por
    # canal do split de treino via fallback duplo
    media_treino = np.array([0.11, 0.22, 0.33])
    imagem = np.ones((3, 32, 32))
    recon = eb.interpolacao_espacial(imagem, todos_ocultos, media_treino)
    assert np.allclose(recon[0], 0.11)
    assert np.allclose(recon[1], 0.22)
    assert np.allclose(recon[2], 0.33)


def test_fallback_media_rgb_sem_pixel_visivel_exige_treino():
    todos_ocultos = list(range(16))
    with pytest.raises(ValueError, match="treino"):
        eb.media_rgb_visivel(np.ones((3, 32, 32)), todos_ocultos)


def test_indices_repetidos_rejeitados():
    with pytest.raises(ValueError, match="repet"):
        eb.media_rgb_visivel(np.ones((3, 32, 32)), [3, 3])
    with pytest.raises(ValueError, match="invalido"):
        eb.media_rgb_visivel(np.ones((3, 32, 32)), [17])


def test_centros_na_grade_4x4():
    assert eb.centro_patch(0) == (3.5, 3.5)
    assert eb.centro_patch(15) == (27.5, 27.5)
    assert eb.centro_patch(6) == (11.5, 19.5)
