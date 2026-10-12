"""Construtor do notebook codigo/notebook.ipynb (fonte unica, pt-BR).

Rode: uv run python scripts/construir_notebook.py
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ALVO = RAIZ / "codigo" / "notebook.ipynb"

MD = "markdown"
CODE = "code"


def md(texto: str):
    return {
        "cell_type": MD,
        "metadata": {},
        "source": texto.splitlines(keepends=True),
    }


def code(texto: str):
    return {
        "cell_type": CODE,
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": texto.splitlines(keepends=True),
    }


CELULAS = []
A = CELULAS.append

A(
    md(
        """# Seminario: Masked Modeling em Deep Learning

Notebook autocontido do experimento didatico de Masked Autoencoder (MAE no estilo
de He et al. (2022)) no CIFAR-10. O notebook roda do zero:

1. baixa e verifica o CIFAR-10 por md5;
2. cria o subset balanceado (seed 42);
3. realiza patchify, mascara aninhada, treino em 50% e 75%;
4. avalia o MSE nos patches ocultos do teste e gera `resultados/`.

Semente global: 42. Dispositivo: somente GPU CUDA (sem fallback para CPU)."""
    )
)
A(
    md(
        """## 1. Ambiente e dispositivo

Sem GPU, o notebook termina com erro explicito: o experimento exige o wheel
cu130 do PyTorch e uma GPU NVIDIA."""
    )
)
A(
    code(
        """import os, sys, hashlib, json, time, platform
from pathlib import Path
import numpy as np

RAIZ = Path(os.getcwd())
while not (RAIZ / "pyproject.toml").exists():
    RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ))

import torch
from codigo.dados import (
    MD5_ESPERADO, obter_cifar10, gerar_subset, salvar_subset, md5_arquivo,
)
from codigo.treino import (
    ConfiguracaoTreino, exigir_cuda, treinar, mse_lote,
    medir_epoca, metrica_ponderada, avaliar_teste_mse,
)
from codigo.mae import (
    MAE, patchify, unpatchify, permutacoes_fixas, indices_ocultos,
    perda_mae, reconstrucao_completa, imagem_com_buracos, SEMENTE_MASCARA,
)

SEMENTE = 42
np.random.seed(SEMENTE)
torch.manual_seed(SEMENTE)

if not torch.cuda.is_available():
    raise RuntimeError(
        "Nenhuma GPU CUDA detectada. O experimento exige o wheel cu130 e "
        "uma GPU NVIDIA; sem fallback silencioso para CPU."
    )

dispositivo = exigir_cuda()
print("torch:", torch.__version__, "| cuda:", torch.version.cuda)"""
    )
)
A(
    md(
        """## 2. Dados: CIFAR-10 verificado por md5 e subset balanceado

O arquivo oficial pesa cerca de 170 MB e tem md5
`c58f30108f718f92721af3b95e74349a`. Se o md5 divergir, o processo falha e o
subset nao e gerado."""
    )
)
A(
    code(
        """RAIZ_DADOS = RAIZ / "dados" / "cifar10_raw"
SAIDA_SUBSET = RAIZ / "dados" / "cifar10_subset"
arquivo_tar = RAIZ_DADOS / "cifar-10-python.tar.gz"

if not arquivo_tar.exists():
    print("Baixando CIFAR-10 (~170 MB)...")
    treino_ds, teste_ds, arquivo = obter_cifar10(RAIZ_DADOS, download=True)
else:
    treino_ds, teste_ds, arquivo = obter_cifar10(RAIZ_DADOS, download=False)

md5_obtido = md5_arquivo(arquivo)
assert md5_obtido == MD5_ESPERADO, (
    f"md5 divergente: obtido {md5_obtido}, esperado {MD5_ESPERADO}"
)
print("md5 conferido:", md5_obtido)"""
    )
)
A(
    code(
        """# gera o subset com seed 42 a cada execucao (determinista)
_, _, selecao = gerar_subset(RAIZ_DADOS, SEMENTE)
salvar_subset(treino_ds, teste_ds, selecao, SAIDA_SUBSET)

ARQUIVO_NPZ = SAIDA_SUBSET / "subset.npz"
lote = np.load(ARQUIVO_NPZ)
for split in ("treino", "validacao", "teste"):
    n = len(lote[split])
    classes = lote[split + "_rotulos"]
    por_classe = {int(c): int((classes == c).sum()) for c in range(10)}
    valores = set(por_classe.values())
    assert len(valores) == 1, f"{split}: contagens por classe divergem: {por_classe}"
    print(f"{split}: {n} imagens, {valores.pop()} por classe, dtype {lote[split].dtype}")"""
    )
)
A(
    md(
        """## 3. Modelo MAE

### Patchify

Cada imagem 32x32x3 vira 16 patches flatteneados de 8x8x3 = 192 valores.
O encoder processa apenas os patches visiveis; o decoder leve (dim 64)
reconstitui os 192 valores de cada patch oculto com tokens de mascara e
embedding posicional do decoder. A perda e MSE somente nos ocultos, em
pixels brutos em [0,1], sem normalizacao (norm_pix_loss desligado)."""
    )
)
A(
    code(
        """torch.manual_seed(SEMENTE)
modelo = MAE().to(dispositivo)
n_params = sum(p.numel() for p in modelo.parameters())
print(f"parametros: {n_params/1e6:.2f}M")

x_exemplo = torch.from_numpy(lote["teste"][:2].transpose(0, 3, 1, 2)).float() / 255.0
p = patchify(x_exemplo)
print("patchify:", tuple(p.shape), "| unpatchify:", tuple(unpatchify(p).shape))

# formas com 8 e 4 tokens visiveis
perm = permutacoes_fixas(2)
for taxa in (0.5, 0.75):
    saida = modelo(x_exemplo.to(dispositivo), indices_mascarados=indices_ocultos(perm, taxa))
    print(f"taxa {taxa}: encoder ve {saida['indices_visiveis'].shape[1]} tokens; "
          f"predicao {tuple(saida['predicao'].shape)}; perda {float(saida['perda']):.4f}")"""
    )
)
A(
    md(
        """### Mascara aninhada

Uma permutacao fixa dos 16 indices por imagem (seed 42) define os patches
ocultos: a 50% ocultam os 8 primeiros e a 75% os 12 primeiros. Assim, tudo
o que e oculto a 50% tambem e oculto a 75% e a comparacao entre condicoes
isola apenas a quantidade de informacao removida."""
    )
)
A(
    code(
        """ocultos50 = indices_ocultos(perm, 0.5)
ocultos75 = indices_ocultos(perm, 0.75)
nested = all(set(ocultos50[b].tolist()).issubset(set(ocultos75[b].tolist())) for b in range(len(perm)))
determinista = torch.equal(permutacoes_fixas(len(perm)), perm)
print("ocultos a 50% contidos nos ocultos a 75%:", nested)
print("duas geracoes com seed 42 identicas:", determinista)"""
    )
)
A(
    md(
        """## 4. Orcamento: previsto versus medido

Antes do treino final, mede-se o tempo real de uma epoca na GPU (melhor de
3 execucoes) com a config candidata. O orcamento previsto e o estimado
antes da medicao (30 minutos para as duas condicoes somadas)."""
    )
)
A(
    code(
        """ORCAMENTO_PREVISTO_MIN = 30.0  # orcamento previsto para as duas condicoes somadas
BATCH = 256
LR = 3e-4

tempo_medido = medir_epoca(ARQUIVO_NPZ, BATCH, dispositivo)
print(f"tempo medido por epoca (batch {BATCH}): {tempo_medido:.3f} s")

# orcamento: gasta ate um terco do previsto por condicao
epocas = int(ORCAMENTO_PREVISTO_MIN * 60 / (3 * tempo_medido))
epocas = max(60, min(200, epocas))
ORCAMENTO = ConfiguracaoTreino(epocas=epocas, batch=BATCH, lr=LR, taxa_mascara=0.75)
print(f"orcamento escolhido: {epocas} epocas, batch {BATCH}, lr {LR}")
print(f"tempo previsto de treino: 2 condicoes x {epocas * tempo_medido:.1f} s")"""
    )
)
A(
    md(
        """## 5. Treino das duas condicoes

As condicoes de 50% e 75% usam exatamente o mesmo numero de epocas, batch
e learning rate, com AdamW. Apenas a taxa de mascarar diverge, sobre a
mesma permutacao fixa."""
    )
)
A(
    code(
        """historicos = {}
modelos = {}
for taxa in (0.5, 0.75):
    torch.manual_seed(SEMENTE)
    modelo = MAE().to(dispositivo)
    config = ConfiguracaoTreino(
        epocas=ORCAMENTO.epocas, batch=ORCAMENTO.batch,
        lr=ORCAMENTO.lr, taxa_mascara=taxa, seed=SEMENTE,
    )
    print(f"=== condicao {int(taxa*100)}% ===")
    historicos[taxa] = treinar(
        modelo, ARQUIVO_NPZ, dispositivo, config,
    )
    modelos[taxa] = modelo"""
    )
)
A(
    md(
        """## 6. Avaliacao: MSE nos patches ocultos do teste

Calculada apenas apos o fim do treino, com a mascara fixa da condicao."""
    )
)
A(
    code(
        """import pandas as pd

perm_teste = permutacoes_fixas(len(lote["teste"]))
metricas = []
for taxa in (0.5, 0.75):
    mse = avaliar_teste_mse(modelos[taxa], ARQUIVO_NPZ, dispositivo, taxa, perm_teste)
    caminho_ckpt = RAIZ / "checkpoints" / f"mae_{int(taxa*100)}.pt"
    caminho_ckpt.parent.mkdir(exist_ok=True)
    torch.save(modelos[taxa].state_dict(), caminho_ckpt)
    sha256 = hashlib.sha256(caminho_ckpt.read_bytes()).hexdigest()
    metricas.append({
        "condicao": f"mascara_{int(taxa*100)}",
        "mse_teste_ocultos": mse,
        "epocas": ORCAMENTO.epocas,
        "batch": ORCAMENTO.batch,
        "lr": ORCAMENTO.lr,
        "tempo_epoca_medido_s": tempo_medido,
        "orcamento_previsto_min": ORCAMENTO_PREVISTO_MIN,
        "sha256": sha256,
    })
df_metricas = pd.DataFrame(metricas)

try:
    import subprocess
    nvidia = subprocess.run(
        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
        capture_output=True, text=True, check=True,
    ).stdout.split()[0]
except Exception:
    nvidia = "desconhecido"
df_metricas["python"] = platform.python_version()
df_metricas["pytorch"] = torch.__version__
df_metricas["cuda"] = torch.version.cuda
df_metricas["driver"] = nvidia
df_metricas["gpu"] = torch.cuda.get_device_name(0)
df_metricas["seed"] = SEMENTE

import os
RESULTADOS = RAIZ / "resultados"
RESULTADOS.mkdir(exist_ok=True)
df_metricas.to_csv(RESULTADOS / "metricas.csv", index=False)
print(df_metricas.to_string(index=False))"""
    )
)
A(
    md(
        """## 7. Figuras

`curva_perda.png`: perda de validacao por epoca das duas condicoes no
mesmo eixo. `reconstrucoes.png`: 8 imagens fixas do teste, por condicao
original, versao mascarada e reconstrucao."""
    )
)
A(
    code(
        """import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.figure(figsize=(8, 5))
for taxa in (0.5, 0.75):
    hist = historicos[taxa]
    plt.plot(hist["epoca"], hist["perda_validacao"], label=f"mascara {int(taxa*100)}%")
plt.xlabel("epoca")
plt.ylabel("MSE de validacao nos ocultos")
plt.title("Curva de perda de validacao")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(RESULTADOS / "curva_perda.png", dpi=150)
plt.close()
print("curva_perda.png gravada")"""
    )
)
A(
    code(
        """def mostrar_figura(taxa):
    modelo = modelos[taxa]
    modelo.eval()
    base = lote["teste"][:8]
    x = torch.from_numpy(base.transpose(0, 3, 1, 2)).float() / 255.0
    x = x.to(dispositivo)
    idx = indices_ocultos(perm_teste[:8], taxa)
    with torch.no_grad():
        saida = modelo(x, indices_mascarados=idx)
    recon = reconstrucao_completa(
        saida["predicao"], saida["patches"], saida["indices_mascarados"]
    ).cpu()
    buracos = imagem_com_buracos(saida["patches"].cpu(), saida["indices_mascarados"])
    return x.cpu(), buracos, recon

fig, eixos = plt.subplots(
    2, 24, figsize=(22, 5.0),
    gridspec_kw={"wspace": 0.04, "hspace": 0.06},
)
for linha, taxa in enumerate((0.5, 0.75)):
    originais, buracos, recons = mostrar_figura(taxa)
    for j in range(8):
        eixos[linha, j].imshow(originais[j].permute(1, 2, 0).numpy())
        eixos[linha, j + 8].imshow(buracos[j].permute(1, 2, 0).numpy())
        eixos[linha, j + 16].imshow(recons[j].permute(1, 2, 0).numpy().clip(0, 1))
for ax in eixos.flat:
    ax.set_xticks([])
    ax.set_yticks([])
for c, rotulo in enumerate(("original", "mascarada", "reconstrucao")):
    fig.text((c * 8 + 4) / 24, 0.94, rotulo, ha="center", fontsize=10)
fig.text(0.012, 0.72, "mascara 50%", rotation=90, va="center", fontsize=11)
fig.text(0.012, 0.30, "mascara 75%", rotation=90, va="center", fontsize=11)
fig.suptitle("Reconstrucoes do teste: 8 imagens fixas (seed 42)", fontsize=13, y=0.995)
fig.subplots_adjust(left=0.04, right=0.995, top=0.885, bottom=0.01)
plt.savefig(RESULTADOS / "reconstrucoes.png", dpi=150)
plt.close()
print("reconstrucoes.png gravada")"""
    )
)
A(
    md(
        """## 8. Encerramento

Arquivos em `resultados/`: `metricas.csv`, `curva_perda.png`,
`reconstrucoes.png`. Checkpoints ficam em `checkpoints/` (fora do zip), com
hash SHA-256 registrado em `metricas.csv`."""
    )
)
A(
    code(
        """print("Arquivos gravados em", RESULTADOS)
for arquivo in sorted(RESULTADOS.iterdir()):
    print(" ", arquivo.name)
print("sha256 dos checkpoints:")
for m in metricas:
    print(" ", m["condicao"], m["sha256"])"""
    )
)

NOTEBOOK = {
    "cells": CELULAS,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
ALVO.parent.mkdir(exist_ok=True)
json.dump(NOTEBOOK, open(ALVO, "w"), ensure_ascii=False, indent=1)
print("notebook gerado em", ALVO)