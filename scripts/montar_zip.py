"""Monta o zip de entrega, conferindo presença e md5 de cada arquivo obrigatório.

Rode: uv run python scripts/montar_zip.py
Verificações: se algum arquivo obrigatório está ausente, a montagem falha
antes de gravar o zip (incluindo os assets do experimento complementar em
slides/recursos-complementares/). A lista de md5 fica em scripts/md5_pacote.csv.
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
    "slides/recursos-complementares/vitmae-fluxo-experimento.png": "slides/recursos-complementares/vitmae-fluxo-experimento.png",
    "slides/recursos-complementares/vitmae-grade-taxas.png": "slides/recursos-complementares/vitmae-grade-taxas.png",
    "slides/recursos-complementares/vitmae-grafico-mse.png": "slides/recursos-complementares/vitmae-grafico-mse.png",
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
    "resultados/estudo-melhorar-reconstrucoes-mae/manifesto.json": "resultados/estudo-melhorar-reconstrucoes-mae/manifesto.json",
    "resultados/estudo-melhorar-reconstrucoes-mae/historico.csv": "resultados/estudo-melhorar-reconstrucoes-mae/historico.csv",
    "resultados/estudo-melhorar-reconstrucoes-mae/contador.jsonl": "resultados/estudo-melhorar-reconstrucoes-mae/contador.jsonl",
    "resultados/estudo-melhorar-reconstrucoes-mae/resumo.json": "resultados/estudo-melhorar-reconstrucoes-mae/resumo.json",
    "resultados/estudo-melhorar-reconstrucoes-mae/figuras/curvas_validacao.png": "resultados/estudo-melhorar-reconstrucoes-mae/figuras/curvas_validacao.png",
    "resultados/estudo-melhorar-reconstrucoes-mae/figuras/melhores_validacao.png": "resultados/estudo-melhorar-reconstrucoes-mae/figuras/melhores_validacao.png",
    "resultados/estudo-melhorar-reconstrucoes-mae/figuras/avaliacao_final.png": "resultados/estudo-melhorar-reconstrucoes-mae/figuras/avaliacao_final.png",
    "resultados/estudo-melhorar-reconstrucoes-mae/ficha-visual/ficha_50.png": "resultados/estudo-melhorar-reconstrucoes-mae/ficha-visual/ficha_50.png",
    "resultados/estudo-melhorar-reconstrucoes-mae/ficha-visual/ficha_75.png": "resultados/estudo-melhorar-reconstrucoes-mae/ficha-visual/ficha_75.png",
    "resultados/estudo-melhorar-reconstrucoes-mae/ficha-visual/ficha_visual.json": "resultados/estudo-melhorar-reconstrucoes-mae/ficha-visual/ficha_visual.json",
    "openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/apresentacao/ficha-rotulos.json": "resultados/estudo-melhorar-reconstrucoes-mae/ficha-visual/ficha-rotulos.json",
    "scripts/montar_zip.py": "scripts/montar_zip.py",
    "scripts/gerar_slides.py": "scripts/gerar_slides.py",
    "scripts/construir_notebook.py": "scripts/construir_notebook.py",
    "pyproject.toml": "pyproject.toml",
    "uv.lock": "uv.lock",
    "openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/relatorio-fase-b.md": "relatorio-fase-b.md",
}

OBRIGATORIOS.update({
    'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/apresentacao/estado-v1.json': 'resultados/estudo-melhorar-reconstrucoes-mae/estado.json',
    'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/estado.json': 'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/estado.json',
    'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/apresentacao/proveniencia.json': 'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/apresentacao/proveniencia.json',
    'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/fontes-historicas/estudo_execucao_c0_v2.py': 'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/fontes-historicas/estudo_execucao_c0_v2.py',
    'codigo/__init__.py': 'codigo/__init__.py',
    'codigo/estudo_avaliacao.py': 'codigo/estudo_avaliacao.py',
    'codigo/estudo_baselines.py': 'codigo/estudo_baselines.py',
    'codigo/estudo_candidatos.py': 'codigo/estudo_candidatos.py',
    'codigo/estudo_checkpoints.py': 'codigo/estudo_checkpoints.py',
    'codigo/estudo_execucao.py': 'codigo/estudo_execucao.py',
    'codigo/estudo_execucao_c0_v2.py': 'codigo/estudo_execucao_c0_v2.py',
    'codigo/estudo_historico.py': 'codigo/estudo_historico.py',
    'codigo/estudo_mascaras.py': 'codigo/estudo_mascaras.py',
    'codigo/estudo_orcamento.py': 'codigo/estudo_orcamento.py',
    'codigo/estudo_orcamento_c0_v2.py': 'codigo/estudo_orcamento_c0_v2.py',
    'codigo/estudo_selecao.py': 'codigo/estudo_selecao.py',
    'codigo/estudo_ssim.py': 'codigo/estudo_ssim.py',
    'codigo/estudo_visual.py': 'codigo/estudo_visual.py',
    'codigo/configuracao_estudo.py': 'codigo/configuracao_estudo.py',
    'codigo/configuracao_estudo_c0_v2.py': 'codigo/configuracao_estudo_c0_v2.py',
    'scripts/executar_estudo_c0_v2.py': 'scripts/executar_estudo_c0_v2.py',
    'scripts/retificar_validacao.py': 'scripts/retificar_validacao.py',
    'scripts/gerar_relatorio_fase_b.py': 'scripts/gerar_relatorio_fase_b.py',
    'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/notas-finais.md': 'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/notas-finais.md',
    'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/retificacao-validacao.md': 'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/retificacao-validacao.md',
    'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/retificacao-validacao.json': 'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/retificacao-validacao.json',
    'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/relatorio-fase-b.md': 'openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/relatorio-fase-b.md',
    'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/manifesto.json': 'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/manifesto.json',
    'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/historico.jsonl': 'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/historico.jsonl',
    'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/contador.jsonl': 'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/contador.jsonl',
    'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/resumo.json': 'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/resumo.json',
    'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/relatorio-c0-v2.md': 'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/relatorio-c0-v2.md',
})

PROIBIDOS = (
    "cifar-10-python.tar.gz",
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
        if "checkpoints" in Path(destino).parts or Path(destino).suffix in (".pt", ".pth"):
            raise RuntimeError(f"{destino}: pesos proibidos no pacote")
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
                info = zipfile.ZipInfo(destino, date_time=(2026, 10, 15, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, origem.read_bytes())
                linhas.append((destino, md5(origem)))
        # checagem final do zip em memória antes de publicá-lo
        with zipfile.ZipFile(caminho_zip) as z:
            lista = z.namelist()
            assert sorted(lista) == destino_lista
        caminho_zip.rename(ZIP_ALVO)
    REGISTRO_MD5.parent.mkdir(exist_ok=True)
    with open(REGISTRO_MD5, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["arquivo", "md5"])
        for linha in linhas:
            w.writerow(linha)
    print(f"zip gravado em {ZIP_ALVO} ({len(linhas)} arquivos)")


if __name__ == "__main__":
    origem_para_destino = conferir_obrigatorios()
    gravar_zip(origem_para_destino)
    print("lista de md5 em", REGISTRO_MD5)