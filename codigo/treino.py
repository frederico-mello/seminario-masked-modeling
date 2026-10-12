"""Treino e avaliacao do MAE no subset CIFAR-10.

Sem fallback para CPU: se nao houver GPU CUDA, falha imediatamente.
Mascara aninhada: permutacao fixa por imagem (seed 42), consistente entre
epocas e entre as duas condicoes.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from codigo.mae import MAE, indices_ocultos, permutacoes_fixas


def exigir_cuda() -> torch.device:
    if not torch.cuda.is_available():
        raise RuntimeError(
            "Nenhuma GPU CUDA disponivel: este experimento exige a GPU "
            "(torch compilado com cu130). Sem fallback para CPU."
        )
    dispositivo = torch.device("cuda")
    nome = torch.cuda.get_device_name(dispositivo)
    versao_cuda = torch.version.cuda
    if versao_cuda is None or int(versao_cuda.split(".")[0]) < 13:
        raise RuntimeError(
            f"PyTorch compilado com CUDA {versao_cuda}; exigido cu130."
        )
    print(f"GPU: {nome} (CUDA {versao_cuda})", flush=True)
    return dispositivo


@dataclass
class ConfiguracaoTreino:
    epocas: int
    batch: int
    lr: float
    taxa_mascara: float
    seed: int = 42


def metrica_ponderada(perdas_e_pesos) -> float:
    total = sum(w for _, w in perdas_e_pesos)
    return float(sum(l * w for l, w in perdas_e_pesos) / total)


def mse_lote(modelo, imagens_np, dispositivo, num_ocultos, permutacoes):
    """MSE nos patches ocultos, com permutacao fixa por imagem."""
    n = len(imagens_np)
    perdas = []
    with torch.no_grad():
        for inicio in range(0, n, 500):
            fim = min(inicio + 500, n)
            x = torch.from_numpy(
                imagens_np[inicio:fim].transpose(0, 3, 1, 2)
            ).float() / 255.0
            saida = modelo(
                x.to(dispositivo),
                indices_mascarados=permutacoes[inicio:fim, :num_ocultos],
            )
            perdas.append((float(saida["perda"].detach()), fim - inicio))
    return metrica_ponderada(perdas)


def treinar(
    modelo,
    npz_path,
    dispositivo,
    config: ConfiguracaoTreino,
    epocas: int | None = None,
    imprimir: bool = True,
    log_fn=print,
):
    """Treino com AdamW. Retorna historico por epoca."""
    dados = np.load(npz_path)
    imagens_treino = dados["treino"]
    imagens_valid = dados["validacao"]
    n = len(imagens_treino)
    rng = np.random.default_rng(config.seed)

    num_ocultos = int(config.taxa_mascara * 16)
    perm_treino = permutacoes_fixas(n).to(dispositivo)
    perm_valid = permutacoes_fixas(len(imagens_valid)).to(dispositivo)

    otimizador = torch.optim.AdamW(
        modelo.parameters(), lr=config.lr, weight_decay=0.05
    )
    total_epocas = epocas if epocas is not None else config.epocas
    historico = {
        "epoca": [],
        "perda_treino": [],
        "perda_validacao": [],
        "tempo_epoca": [],
    }
    for epoca in range(total_epocas):
        t0 = time.time()
        perdas = []
        modelo.train()
        ordem = rng.permutation(n)
        for inicio in range(0, n, config.batch):
            idx = ordem[inicio : inicio + config.batch]
            x = torch.from_numpy(
                imagens_treino[idx].transpose(0, 3, 1, 2)
            ).float() / 255.0
            x = x.to(dispositivo, non_blocking=True)
            idx_masc = perm_treino[idx][:, :num_ocultos]
            saida = modelo(x, indices_mascarados=idx_masc)
            otimizador.zero_grad()
            saida["perda"].backward()
            otimizador.step()
            perdas.append((float(saida["perda"].detach()), len(idx)))
        treino_m = metrica_ponderada(perdas)
        val_m = mse_lote(
            modelo, imagens_valid, dispositivo, num_ocultos, perm_valid
        )
        dt = time.time() - t0
        historico["epoca"].append(epoca + 1)
        historico["perda_treino"].append(treino_m)
        historico["perda_validacao"].append(val_m)
        historico["tempo_epoca"].append(dt)
        if imprimir:
            log_fn(
                f"cond {config.taxa_mascara} epoca {epoca + 1}/{total_epocas}: "
                f"treino {treino_m:.4f} valid {val_m:.4f} ({dt:.1f}s)",
                flush=True,
            )
    return historico


def medir_epoca(npz_path, batch: int, dispositivo, lr: float = 3e-4) -> float:
    """Mede o tempo real de uma epoca com a config candidata (melhor de 3)."""
    tempo_melhor = float("inf")
    for _ in range(3):
        torch.manual_seed(42)
        modelo = MAE().to(dispositivo)
        config = ConfiguracaoTreino(
            epocas=1, batch=batch, lr=lr, taxa_mascara=0.75
        )
        hist = treinar(modelo, npz_path, dispositivo, config, imprimir=False)
        tempo_melhor = min(tempo_melhor, hist["tempo_epoca"][0])
    return tempo_melhor


def avaliar_teste_mse(
    modelo, npz_path, dispositivo, taxa: float, indices_globais: torch.Tensor
) -> float:
    """MSE nos patches ocultos do teste com a mascara fixa da condicao."""
    dados = np.load(npz_path)
    imagens = dados["teste"]
    perm = indices_globais[: len(imagens)]
    modelo.eval()
    num_ocultos = int(taxa * 16)
    perdas = []
    with torch.no_grad():
        for inicio in range(0, len(imagens), 500):
            fim = min(inicio + 500, len(imagens))
            x = torch.from_numpy(
                imagens[inicio:fim].transpose(0, 3, 1, 2)
            ).float() / 255.0
            saida = modelo(
                x.to(dispositivo),
                indices_mascarados=perm[inicio:fim, :num_ocultos],
            )
            perdas.append((float(saida["perda"].detach()), fim - inicio))
    return metrica_ponderada(perdas)