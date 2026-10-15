"""Controles deterministicos do estudo sem rede e sem pixels ocultos (D4).

Dois controles por imagem e taxa, calculados sem consultar pixels ou valores
dos patches ocultos:

- Media RGB visivel: cada pixel oculto recebe a media de cada canal sobre
  todos os pixels visiveis da imagem.
- Interpolacao espacial visivel: cada patch visivel e uma amostra no centro
  de sua celula na grade 4x4 (coordenadas de pixel: (linha*8 + 3,5,
  coluna*8 + 3,5), unidade: pixel); para cada patch oculto, o preenchimento e
  a media ponderada dos arrays 8x8x3 dos patches visiveis com pesos
  1/d^2, d a distancia euclidiana entre os centros, pesos
  normalizados para somar 1.

Fallbacks explicitos, sem tocar ocultos:
- interpolacao sem patch visivel utilizavel ou com somatorio de pesos invalido
  (nao finito ou nulo): media RGB visível;
- media RGB sem nenhum pixel visivel: media por canal do split de treino,
  informada como argumento (media_treino); se faltar, erro explicito.

As taxas 50% e 75% sempre deixam patches visiveis; os fallbacks existem para
geralidade documentada. Entradas e saidas: ndarray float com forma
(3, 32, 32) em [0,1].
"""

from __future__ import annotations

import numpy as np

GRADE = 4
TAMANHO_PATCH = 8
N_PATCHES = 16
TOLERANCIA_PESOS = 1e-12


def divisoria_patch(indice: int) -> tuple[int, int]:
    """(linha, coluna) do patch na grade 4x4."""
    return divmod(indice, GRADE)


def centro_patch(indice: int) -> tuple[float, float]:
    """Coordenadas (linha, coluna) do centro do patch, em pixels."""
    r, c = divisoria_patch(indice)
    return (r * TAMANHO_PATCH + 3.5, c * TAMANHO_PATCH + 3.5)


def patches_visiveis(ocultos) -> list[int]:
    ocultos = set(int(i) for i in ocultos_para_lista(ocultos))
    return [i for i in range(N_PATCHES) if i not in ocultos]


def ocultos_para_lista(ocultos):
    lista = list(ocultos)
    if len(set(int(i) for i in lista)) != len(lista):
        raise ValueError("indices ocultos repetidos")
    if not 0 <= len(lista) <= N_PATCHES:
        raise ValueError("número de patches ocultos impossível")
    for i in lista:
        if not 0 <= int(i) < N_PATCHES:
            raise ValueError(f"indice de patch invalido: {i}")
    return [int(i) for i in lista]


def _valida_imagem(imagem: np.ndarray) -> None:
    if imagem.shape != (3, 32, 32):
        raise ValueError(f"esperada imagem (3, 32, 32); recebida {imagem.shape}")


def _filtros(linha, coluna):
    """Fatias de pixels do patch (linha, coluna) na imagem (3, 32, 32)."""
    sl = (slice(linha * 8, linha * 8 + 8), slice(coluna * 8, coluna * 8 + 8))
    return np.s_[:, sl[0], sl[1]]


def media_rgb_visivel(
    imagem: np.ndarray,
    ocultos,
    media_treino: np.ndarray | None = None,
) -> np.ndarray:
    """Reconstrói todos os patches: visíveis mantidos; ocultos com a média
    RGB dos pixels visíveis (ou com media_treino se nenhum visível)."""
    _valida_imagem(imagem)
    ocultos = ocultos_para_lista(ocultos)
    recon = imagem.astype(np.float64).copy()
    visiveis = patches_visiveis(ocultos)
    valores = None
    for p in visiveis:
        r, c = divisoria_patch(p)
        bloco = recon[_filtros(r, c)]
        stat = np.asarray(
            [bloco[ch].mean() for ch in range(3)], dtype=np.float64
        )
        valores = stat if valores is None else np.vstack((valores, stat))
    if valores is None:
        # fallback explicito: media por canal do split de treino
        return _preenchimento_treino(recon, ocultos, media_treino)
    media = valores.mean(axis=0)
    for p in ocultos:
        r, c = divisoria_patch(p)
        recon[_filtros(r, c)] = media[:, None, None]
    return recon


def _preenchimento_treino(imagem, ocultos, media_treino: np.ndarray | None):
    if (
        media_treino is None
        or np.asarray(media_treino, dtype=np.float64).shape != (3,)
    ):
        raise ValueError(
            "sem pixels visíveis: media por canal do split de treino "
            "(media_treino, forma (3,)) é obrigatória"
        )
    media = np.asarray(media_treino, dtype=np.float64)
    for p in ocultos:
        r, c = divisoria_patch(p)
        imagem[_filtros(r, c)] = media[:, None, None]
    return imagem


def interpolacao_espacial(
    imagem: np.ndarray,
    ocultos,
    media_treino: np.ndarray | None = None,
) -> np.ndarray:
    """Interpolação espacial por pesos 1/d^2 entre centros de patches."""
    _valida_imagem(imagem)
    ocultos = ocultos_para_lista(ocultos)
    visiveis = patches_visiveis(ocultos)
    if not visiveis:
        return media_rgb_visivel(imagem, ocultos, media_treino)
    centros_v = [centro_patch(p) for p in visiveis]
    recon = imagem.astype(np.float64).copy()
    amostras = np.stack(
        [recon[_filtros(*divisoria_patch(p))] for p in visiveis]
    )  # (n_vis, 3, 8, 8)
    for p in ocultos:
        rh, ch = divisoria_patch(p)
        centro_h = centro_patch(p)
        pesos = np.array(
            [
                1.0 / ((centro_h[0] - c[0]) ** 2 + (centro_h[1] - c[1]) ** 2)
                for c in centros_v
            ]
        )
        if not np.isfinite(pesos).all() or pesos.sum() < TOLERANCIA_PESOS:
            # fallback explicito: media RGB dos visíveis
            recon = media_rgb_visivel(
                imagem, set(ocultos), media_treino
            )
            break
        pesos = pesos / pesos.sum()
        recon[_filtros(rh, ch)] = np.tensordot(
            pesos, amostras, axes=(0, 0)
        )
    return recon
