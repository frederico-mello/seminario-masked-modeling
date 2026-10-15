from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo import estudo_mascaras as em


def test_recomputacao_determinista():
    a = em.mascara_treino(seed_treino=10, epoca=3, indice_original=57, taxa=0.75)
    b = em.mascara_treino(seed_treino=10, epoca=3, indice_original=57, taxa=0.75)
    assert np.array_equal(a, b)
    assert a.shape == (12,)


def test_independencia_da_ordem_dos_lotes():
    indices = list(range(300, 320))
    mascaras = em.mascaras_lote(10, 0, indices, 0.5)
    ordem_alternativa = list(reversed(indices))
    mascaras_reversa = em.mascaras_lote(10, 0, ordem_alternativa, 0.5)
    for posicao, indice in enumerate(ordem_alternativa):
        assert np.array_equal(mascaras_reversa[posicao], mascaras[indices.index(indice)])
    # mesma imagem em lote com composição de lote diferente conserva a máscara
    nova = em.mascaras_lote(10, 0, [733, indices[0]], 0.5)[1]
    assert np.array_equal(nova, mascaras[0])


def test_mascara_varia_por_epoca_e_seed():
    for treino_seed in (10, 20, 30):
        por_epoca = [
            tuple(em.mascara_treino(treino_seed, epoca, 123, 0.5))
            for epoca in range(6)
        ]
        assert len(set(por_epoca)) >= 5  # épocas distintas geram máscaras distintas
    por_seed = [
        tuple(em.mascara_treino(s, 0, 123, 0.5)) for s in (10, 20, 30)
    ]
    assert len(set(por_seed)) == 3


def test_aninhamento_8_dentro_de_12():
    rng = np.random.default_rng(0)
    for _ in range(50):
        seed_treino = int(rng.integers(0, 10_000))
        epoca = int(rng.integers(0, 200))
        indice = int(rng.integers(0, 50_000))
        ocultos_50 = set(em.mascara_treino(seed_treino, epoca, indice, 0.5))
        ocultos_75 = set(em.mascara_treino(seed_treino, epoca, indice, 0.75))
        assert len(ocultos_50) == 8
        assert len(ocultos_75) == 12
        assert ocultos_50.issubset(ocultos_75)


def test_todos_indices_validos_e_unicos():
    for taxa, n in ((0.5, 8), (0.75, 12)):
        mascaras = em.mascaras_lote(10, 2, list(range(40)), taxa)
        assert mascaras.shape == (40, n)
        for linha in mascaras:
            valores = set(linha.tolist())
            assert len(valores) == n
            assert valores.issubset(set(range(16)))


def test_taxa_invalida_rejeitada():
    with pytest.raises(ValueError):
        em.mascara_treino(10, 0, 0, 0.9)


def test_chave_mascara_distingue_todos_os_campos():
    base = em.chave_mascara(10, 3, 57)
    assert em.chave_mascara(20, 3, 57) != base
    assert em.chave_mascara(10, 4, 57) != base
    assert em.chave_mascara(10, 3, 58) != base


def _escreve_csv(caminho: Path, linhas: list[tuple[str, str, int]]):
    with open(caminho, "w", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(["split", "classe", "indice_original"])
        for split, classe, indice in linhas:
            escritor.writerow([split, classe, indice])


def test_carregar_mapa_indices_valida_e_ordenada(tmp_path):
    caminho = tmp_path / "indices.csv"
    _escreve_csv(
        caminho,
        [("validacao", "gato", 902), ("validacao", "cao", 12), ("teste", "gato", 7)],
    )
    mapa = em.carregar_mapa_indices(caminho)
    assert mapa["validacao"] == (12, 902)
    assert mapa["teste"] == (7,)


def test_carregar_mapa_indices_rejeita_duplicados(tmp_path):
    caminho = tmp_path / "indices.csv"
    _escreve_csv(caminho, [("validacao", "gato", 5), ("validacao", "cao", 5)])
    with pytest.raises(ValueError, match="repetido"):
        em.carregar_mapa_indices(caminho)


def test_carregar_mapa_indices_rejeita_coluna_ausente(tmp_path):
    caminho = tmp_path / "indices.csv"
    with open(caminho, "w", newline="") as f:
        csv.writer(f).writerow(["split", "classe"])
        csv.writer(f).writerow(["validacao", "gato"])
    with pytest.raises(ValueError, match="obrigat"):
        em.carregar_mapa_indices(caminho)


def test_carregar_mapa_indices_rejeita_nao_decimal(tmp_path):
    caminho = tmp_path / "indices.csv"
    with open(caminho, "w", newline="") as f:
        csv.writer(f).writerow(["split", "classe", "indice_original"])
        csv.writer(f).writerow(["validacao", "gato", "0x1f"])
    with pytest.raises(ValueError, match="decimal"):
        em.carregar_mapa_indices(caminho)


def test_divergencia_mapa_indices(tmp_path):
    caminho = tmp_path / "indices.csv"
    _escreve_csv(caminho, [("validacao", "gato", 5), ("teste", "cao", 6)])
    mapa = em.carregar_mapa_indices(caminho)
    assert em.divergencia_mapa_indices(mapa, mapa) == []
    mapa_outro = {"validacao": (7,), "teste": (6,)}
    divergencias = em.divergencia_mapa_indices(mapa, mapa_outro)
    assert any("validacao" in d for d in divergencias)
    mapa_parcial = {"validacao": (5,)}
    divergencias = em.divergencia_mapa_indices(mapa, mapa_parcial)
    assert any("teste" in d for d in divergencias)
