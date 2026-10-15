"""Máscaras de treino do estudo, determinísticas por identidade original.

Design D1: para cada imagem, cada época e cada seed de treino, gerar uma
permutação local dos 16 patches a partir da tupla
(versão, seed de treino, época, índice original da imagem no CIFAR-10).
A codificação da tupla e o algoritmo de permutação são versionados: a versão
da máscara entra na chave codificada, a permutação usa numpy com gerador
inicializado por essa chave e sem estado aleatório global. Assim a máscara é
independente de lotes, ordem das amostras, RNG global e retomadas.

O aninhamento é automático: 50% oculta os 8 primeiros índices da permutação e
75% oculta os 12 primeiros, os mesmos mais 4.

O mapa de índices originais de cada split é validado contra o CSV
dados/cifar10_subset/indices.csv (gerado localmente com seed 42); divergência
leva a erro explícito e o projeto principal jamais é alterado.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

VERSAO_PERMUTACAO = "mascara-treino-v1"
N_PATCHES = 16
TAMANHO_PATCH = 8
TAXAS = (0.5, 0.75)
OCULTOS_POR_TAXA = {0.5: 8, 0.75: 12}


def numero_ocultos(taxa: float) -> int:
    if taxa not in OCULTOS_POR_TAXA:
        raise ValueError(f"taxas suportadas: 0.5 ou 0.75; recebido {taxa}")
    return OCULTOS_POR_TAXA[taxa]


def chave_mascara(seed_treino: int, epoca: int, indice_original: int) -> int:
    """Inteiro de 64 bits derivado da tupla versionada (versão, seed, época, id)."""
    texto = f"{VERSAO_PERMUTACAO}|{seed_treino}|{epoca}|{indice_original}"
    return int.from_bytes(hashlib.sha256(texto.encode("utf-8")).digest()[:8], "big")


def permutacao_patch(
    seed_treino: int, epoca: int, indice_original: int
) -> np.ndarray:
    """Permutação local dos 16 índices, determinística por identidade."""
    rng = np.random.default_rng(
        chave_mascara(seed_treino, epoca, indice_original)
    )
    return rng.permutation(N_PATCHES)


def mascara_treino(
    seed_treino: int, epoca: int, indice_original: int, taxa: float
) -> np.ndarray:
    """Índices de patch ocultos para (seed, época, imagem) na taxa."""
    n_ocultos = numero_ocultos(taxa)
    perm = permutacao_patch(seed_treino, epoca, indice_original)
    return perm[:n_ocultos]


def mascaras_lote(
    seed_treino: int,
    epoca: int,
    indices_originais,
    taxa: float,
) -> np.ndarray:
    """Máscaras para uma lista/tensor de índices originais, na ordem dada.

    O resultado depende somente da identidade de cada linha; ordem e
    composição de lotes não alteram a máscara de nenhuma imagem.
    """
    return np.stack(
        [mascara_treino(seed_treino, epoca, int(i), taxa) for i in indices_originais]
    )


COLUNAS_MAPA = ("split", "classe", "indice_original")


def carregar_mapa_indices(caminho_csv: Path) -> dict[str, tuple[int, ...]]:
    """Lê e valida o CSV de índices de um split gerado localmente.

    Valida colunas obrigatórias, valores inteiros e unicidade do
    indice_original dentro de cada split. Retorna dict
    split -> tupla de índices (decimal, ordenado).
    """
    import csv

    caminho_csv = Path(caminho_csv)
    mapa: dict[str, list[int]] = {}
    with open(caminho_csv, newline="") as f:
        leitor = csv.DictReader(f)
        colunas = leitor.fieldnames or []
        for obrigatoria in COLUNAS_MAPA:
            if obrigatoria not in colunas:
                raise ValueError(
                    f"mapa de índices sem a coluna obrigatória {obrigatoria}: {caminho_csv}"
                )
        for linha in leitor:
            split = linha["split"]
            bruto = linha["indice_original"].strip()
            try:
                indice = int(bruto)
            except ValueError as erro:
                raise ValueError(
                    f"indice_original não decimal em {caminho_csv}: {bruto!r}"
                ) from erro
            if indice < 0:
                raise ValueError(f"indice_original negativo em {caminho_csv}: {indice}")
            lista = mapa.setdefault(split, [])
            if indice in lista:
                raise ValueError(
                    f"indice_original {indice} repetido no split {split} em {caminho_csv}"
                )
            lista.append(indice)
    if not mapa:
        raise ValueError(f"mapa de índices vazio: {caminho_csv}")
    return {split: tuple(sorted(v)) for split, v in mapa.items()}


def divergencia_mapa_indices(
    mapa_novo: dict[str, tuple[int, ...]],
    mapa_congelado: dict[str, tuple[int, ...]],
) -> list[str]:
    """Divergências entre o mapa carregado e o congelado, por split."""
    divergencias: list[str] = []
    for split in sorted(set(mapa_novo) | set(mapa_congelado)):
        novo = mapa_novo.get(split)
        congelado = mapa_congelado.get(split)
        if novo is None or congelado is None:
            divergencias.append(f"{split}: mapa ausente em um dos lados")
            continue
        if tuple(novo) != tuple(congelado):
            divergencias.append(f"{split}: conjuntos de índices divergem")
    return divergencias
