"""Obtencao do CIFAR-10 com verificação de md5 e subset balanceado.

Ver design.md D3: 500 treino + 100 validacao (disjunta) + 100 teste por
classe, seed 42, indices em CSV e imagens uint8 em .npz comprimido.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import numpy as np

MD5_ESPERADO = "c58f30108f718f92721af3b95e74349a"
SEED = 42
N_POR_CLASSE = {"treino": 500, "validacao": 100, "teste": 100}
NOMES_CLASSES = (
    "aviao",
    "automovel",
    "passaro",
    "gato",
    "veado",
    "cao",
    "sapo",
    "cavalo",
    "navio",
    "caminhao",
)


def md5_arquivo(caminho: Path) -> str:
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def verificar_md5(caminho: Path, esperado: str = MD5_ESPERADO) -> None:
    obtido = md5_arquivo(caminho)
    if obtido != esperado:
        raise ValueError(
            f"md5 divergente em {caminho}: esperado {esperado}, obtido {obtido}"
        )


def obter_cifar10(raiz: Path, download: bool = True):
    """Baixa o CIFAR-10 (se necessario) e falha se o md5 divergir."""
    import torchvision

    arquivo = raiz / "cifar-10-python.tar.gz"
    if download:
        _ = torchvision.datasets.CIFAR10(root=str(raiz), train=True, download=True)
    elif not arquivo.exists():
        raise FileNotFoundError(
            f"arquivo nao encontrado em {arquivo}; rode com download=True"
        )
    verificar_md5(arquivo, MD5_ESPERADO)

    treino = torchvision.datasets.CIFAR10(
        root=str(raiz), train=True, download=False
    )
    teste = torchvision.datasets.CIFAR10(
        root=str(raiz), train=False, download=False
    )
    return treino, teste, arquivo


def gerar_subset(raiz: Path, seed: int = SEED, baixar: bool = False):
    """Seleciona indice por classe com rng fixo e retorna dicionarios."""
    treino_ds, teste_ds, _ = obter_cifar10(raiz, download=baixar)
    rotulos_treino = np.asarray(treino_ds.targets)
    rotulos_teste = np.asarray(teste_ds.targets)
    rng = np.random.default_rng(seed)

    selecao: dict[str, list[tuple[int, int]]] = {
        "treino": [],
        "validacao": [],
        "teste": [],
    }
    for classe in range(10):
        idx_treino = np.flatnonzero(rotulos_treino == classe)
        idx_teste = np.flatnonzero(rotulos_teste == classe)
        escolha_treino = rng.permutation(idx_treino)
        treino_idx = escolha_treino[:500]
        validacao_idx = escolha_treino[500:600]
        teste_idx = rng.permutation(idx_teste)[:100]
        for i in treino_idx:
            selecao["treino"].append((int(i), classe))
        for i in validacao_idx:
            selecao["validacao"].append((int(i), classe))
        for i in teste_idx:
            selecao["teste"].append((int(i), classe))
    return treino_ds, teste_ds, selecao


def salvar_subset(
    treino_ds, teste_ds, selecao: dict[str, list[tuple[int, int]]], saida: Path
) -> None:
    saida.mkdir(parents=True, exist_ok=True)
    conjunto = {}
    with open(saida / "indices.csv", "w", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(["split", "classe", "indice_original"])
        for split, pares in selecao.items():
            pares_ordenados = sorted(pares)
            imagens = np.stack(
                [
                    (teste_ds if split == "teste" else treino_ds).data[i]
                    for i, _ in pares_ordenados
                ]
            )
            conjunto[split] = imagens.astype(np.uint8)
            conjunto[split + "_rotulos"] = np.array(
                [c for _, c in pares_ordenados], dtype=np.int64
            )
            for i, c in pares_ordenados:
                escritor.writerow([split, NOMES_CLASSES[c], i])
    np.savez_compressed(saida / "subset.npz", **conjunto)


def main(argv: list[str] | None = None) -> None:
    import argparse

    raiz_repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--raiz", type=Path, default=raiz_repo / "dados" / "cifar10_raw")
    parser.add_argument("--saida", type=Path, default=raiz_repo / "dados" / "cifar10_subset")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--sem-download",
        action="store_true",
        help="usa apenas arquivo ja presente na raiz (para testes)",
    )
    args = parser.parse_args(argv)

    raiz_repo.mkdir(exist_ok=True)
    treino_ds, teste_ds, selecao = gerar_subset(
        args.raiz, args.seed, baixar=not args.sem_download
    )
    salvar_subset(treino_ds, teste_ds, selecao, args.saida)

    for split, esperado in N_POR_CLASSE.items():
        total = esperado * 10
        obtido = len(selecao[split])
        if obtido != total:
            raise AssertionError(f"{split}: {obtido} != {total}")
    print(f"subset gravado em {args.saida}")


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        sys.exit(1)