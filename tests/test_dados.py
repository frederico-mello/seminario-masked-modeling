from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo import dados

RAIZ_DADOS = Path(__file__).resolve().parent.parent / "dados" / "cifar10_raw"
MD5_ESPERADO = dados.MD5_ESPERADO


def test_md5_arquivo_baixado():
    arquivo = RAIZ_DADOS / "cifar-10-python.tar.gz"
    if not arquivo.exists():
        pytest.skip("CIFAR-10 bruto ausente (baixe com codigo/dados.py); verificacao de md5 pulada")
    dados.verificar_md5(arquivo, MD5_ESPERADO)


def test_subset_contagens_e_disjuncao():
    if not (RAIZ_DADOS / "cifar-10-python.tar.gz").exists():
        pytest.skip("CIFAR-10 bruto ausente (baixe com codigo/dados.py); teste de contagens e disjuncao pulado")
    raiz_repo = Path(__file__).resolve().parent.parent
    saida = raiz_repo / "dados" / "cifar10_subset"
    if not (saida / "subset.npz").exists():
        raise AssertionError("subset ausente; rode o script de dados")

    linhas = list(csv.DictReader(open(saida / "indices.csv")))
    contagens: dict[tuple[str, str], int] = {}
    for linha in linhas:
        chave = (linha["split"], linha["classe"])
        contagens[chave] = contagens.get(chave, 0) + 1
    for classe in dados.NOMES_CLASSES:
        assert contagens[("treino", classe)] == 500
        assert contagens[("validacao", classe)] == 100
        assert contagens[("teste", classe)] == 100

    idx_treino = {
        int(l["indice_original"]) for l in linhas if l["split"] == "treino"
    }
    idx_val = {
        int(l["indice_original"]) for l in linhas if l["split"] == "validacao"
    }
    idx_teste = {
        int(l["indice_original"]) for l in linhas if l["split"] == "teste"
    }
    assert idx_treino.isdisjoint(idx_val)
    assert len(idx_treino | idx_val) == 6000
    # teste vem do split oficial de teste
    treino_ds, teste_ds, _ = dados.obter_cifar10(RAIZ_DADOS, download=False)
    npz = np.load(saida / "subset.npz")
    imagens_teste = npz["teste"]
    rotulos_teste = npz["teste_rotulos"]
    refs = np.asarray(teste_ds.data)
    # verificacao direta de que o teste esta no CSV
    teste_csv = {
        int(l["indice_original"]) for l in linhas if l["split"] == "teste"
    }
    assert len(teste_csv) == 1000
    # cada imagem de teste do npz deve vir do split oficial
    rotulos_oficiais = np.asarray(teste_ds.targets)
    for i in range(0, 1000, 149):
        rotulo = int(rotulos_teste[i])
        img = imagens_teste[i]
        candidatos = np.flatnonzero(rotulos_oficiais == rotulo)
        achou = any(np.array_equal(refs[j], img) for j in candidatos)
        assert achou, "imagem de teste nao veio do split oficial"

    # determinismo: nova geracao com seed 42 tem indices identicos
    _, _, selecao2 = dados.gerar_subset(RAIZ_DADOS, 42)
    _, _, selecao1 = dados.gerar_subset(RAIZ_DADOS, 42)
    for split in ("treino", "validacao", "teste"):
        pares1 = sorted(selecao1[split])
        pares2 = sorted(selecao2[split])
        assert pares1 == pares2

    # validacao disjunta do treino tambem nos indices originais por classe
    for classe in range(10):
        t = {i for i, c in selecao1["treino"] if c == classe}
        v = {i for i, c in selecao1["validacao"] if c == classe}
        assert t.isdisjoint(v)
    # uint8 e formato
    assert imagens_teste.dtype == np.uint8 and imagens_teste.shape[1:] == (32, 32, 3)