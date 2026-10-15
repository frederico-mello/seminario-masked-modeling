"""Monta o zip de entrega, conferindo presença e md5 de cada arquivo obrigatório.

Rode: uv run python scripts/montar_zip.py
Verificações: se algum arquivo obrigatório está ausente, a montagem falha
antes de gravar o zip (incluindo os assets do experimento do colega em
slides/recursos-colega/). A lista de md5 fica em scripts/md5_pacote.csv.
Exclusões (spec pacote-entrega): dados brutos, checkpoints, validador do
oráculo e testes de equivalência não entram no zip.
"""

from __future__ import annotations

import csv
import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ZIP_ALVO = RAIZ / "seminario_masked_modeling.zip"
REGISTRO_MD5 = RAIZ / "scripts" / "md5_pacote.csv"

# arquivos obrigatórios: origem no repositório -> destino dentro do zip
OBRIGATORIOS = {
    "slides/seminario_masked_modeling.pptx": "slides/seminario_masked_modeling.pptx",
    "slides/seminario_masked_modeling.pdf": "slides/seminario_masked_modeling.pdf",
    "slides/recursos-colega/vitmae-fluxo-experimento.png": "slides/recursos-colega/vitmae-fluxo-experimento.png",
    "slides/recursos-colega/vitmae-grade-taxas.png": "slides/recursos-colega/vitmae-grade-taxas.png",
    "slides/recursos-colega/vitmae-grafico-mse.png": "slides/recursos-colega/vitmae-grafico-mse.png",
    "README.md": "README.md",
    "LICENSE": "LICENSE",
    "codigo/notebook.ipynb": "codigo/notebook.ipynb",
    "codigo/mae.py": "codigo/mae.py",
    "codigo/dados.py": "codigo/dados.py",
    "codigo/treino.py": "codigo/treino.py",
    "codigo/preparar_dados.py": "codigo/preparar_dados.py",
    "dados/cifar10_subset/indices.csv": "dados/cifar10_subset/indices.csv",
    "dados/cifar10_subset/subset.npz": "dados/cifar10_subset/subset.npz",
    "resultados/metricas.csv": "resultados/metricas.csv",
    "resultados/curva_perda.png": "resultados/curva_perda.png",
    "resultados/reconstrucoes.png": "resultados/reconstrucoes.png",
    "scripts/montar_zip.py": "scripts/montar_zip.py",
    "scripts/gerar_slides.py": "scripts/gerar_slides.py",
    "scripts/construir_notebook.py": "scripts/construir_notebook.py",
    "pyproject.toml": "pyproject.toml",
    "uv.lock": "uv.lock",
}

PROIBIDOS = (
    "cifar-10-python.tar.gz",
    "checkpoints",
    "test_equivalencia",
    "test_mae",
    "test_dados",
    "vit_pytorch",
    "relatorio_equivalencia",
)


def md5(caminho: Path) -> str:
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def conferir_obrigatorios() -> dict[str, Path]:
    ausentes = [c for c in OBRIGATORIOS if not (RAIZ / c).exists()]
    if ausentes:
        raise FileNotFoundError(
            f"arquivos obrigatórios ausentes: {ausentes}; zip NÃO gravado"
        )
    return dict(OBRIGATORIOS)


def gravar_zip(origem_para_destino: dict[str, str]) -> None:
    linhas = []
    destino_para_origem = {d: s for s, d in origem_para_destino.items()}
    destino_lista = sorted(destino_para_origem)
    for destino in destino_lista:
        for proibido in PROIBIDOS:
            if proibido in destino.lower():
                raise RuntimeError(
                    f"{destino} conteúdo proibido no pacote ({proibido})"
                )
    temp = None
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        caminho_zip = ZIP_ALVO.with_suffix(".zip.naogravar")
        with zipfile.ZipFile(caminho_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for destino in destino_lista:
                origem = RAIZ / destino_para_origem[destino]
                z.write(origem, destino)
                linhas.append((destino, md5(origem)))
        # checagem final do zip em memória antes de publicá-lo
        with zipfile.ZipFile(caminho_zip) as z:
            lista = z.namelist()
            assert sorted(lista) == destino_lista
        caminho_zip.rename(ZIP_ALVO)
    REGISTRO_MD5.parent.mkdir(exist_ok=True)
    with open(REGISTRO_MD5, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arquivo", "md5"])
        for linha in linhas:
            w.writerow(linha)
    print(f"zip gravado em {ZIP_ALVO} ({len(linhas)} arquivos)")


if __name__ == "__main__":
    origem_para_destino = conferir_obrigatorios()
    gravar_zip(origem_para_destino)
    print("lista de md5 em", REGISTRO_MD5)