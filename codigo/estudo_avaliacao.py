"""Régua fixa de avaliação do estudo (design D2).

Uma única máscara fixa por posição (seed 42), aninhada entre as taxas,
idêntica à avaliação original, sobre todo o conjunto de validação. Todo
candidato, baseline e controle é avaliado nessa mesma régua, e o MSE é
registrado exclusivamente nos patches ocultos. Nenhum pixel visível entra
na métrica dos candidatos.
"""

from __future__ import annotations

import torch

from codigo.mae import indices_ocultos, permutacoes_fixas
from codigo import estudo_ssim

SEED_REGUA = 42


def regua_validacao(n_imagens: int, taxa: float, seed: int = SEED_REGUA):
    """Máscara fixa da régua por posição: (n_imagens, n_ocultos) int64.

    Determinística, aninhada entre taxas e idêntica para todos os
    candidatos, baselines e controles avaliados.
    """
    perm = permutacoes_fixas(n_imagens, seed=seed)
    return indices_ocultos(perm, taxa)


def patches_ocultos(
    patches: torch.Tensor, indices_regua: torch.Tensor
) -> torch.Tensor:
    """Gather dos patches ocultos: (B, n_ocultos, 192)."""
    lote = torch.arange(patches.shape[0], device=patches.device)[:, None]
    return patches[lote, indices_regua]


def mse_regua(
    predicao: torch.Tensor,
    alvos: torch.Tensor,
    indices_regua: torch.Tensor,
    por_imagem: bool = False,
):
    """MSE exclusivamente nos patches ocultos, em pixels brutos em [0,1].

    predicao e alvos: (B, 16, 192). Retorna o MSE agregado (float) ou,
    com por_imagem=True, um tensor (B,) com o MSE de cada imagem.
    """
    pred_h = patches_ocultos(predicao, indices_regua)
    alvos_h = patches_ocultos(alvos, indices_regua)
    por_imagem_mse = torch.mean((pred_h - alvos_h) ** 2, dim=(1, 2))
    if por_imagem:
        return por_imagem_mse
    return float(por_imagem_mse.double().mean())


def ssim_regua(
    predicao: torch.Tensor,
    alvos: torch.Tensor,
    indices_regua: torch.Tensor,
    por_imagem: bool = False,
):
    """SSIM por imagem do conjunto validado na régua (design D6).

    Retorna tensor (B,) com por_imagem=True ou a média das imagens (float).
    Pixels visíveis não contribuem: apenas patches ocultos entram.
    """
    pred_h = patches_ocultos(predicao, indices_regua)
    alvos_h = patches_ocultos(alvos, indices_regua)
    # patchify armazena 192 valores na ordem (pixels, canal): ajustar para
    # (B, patches_ocultos, 3, 8, 8)
    p = pred_h.reshape(pred_h.shape[0], -1, 8, 8, 3).permute(0, 1, 4, 2, 3)
    t = alvos_h.reshape(alvos_h.shape[0], -1, 8, 8, 3).permute(0, 1, 4, 2, 3)
    valores = estudo_ssim.ssim_patches_ocultos(t, p)
    if por_imagem:
        return valores
    return estudo_ssim.media_imagens(valores)
