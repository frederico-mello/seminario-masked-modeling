"""SSIM por patch oculto conforme o design D6.

Definição congelada:
- patches RGB 8x8 com entradas limitadas a [0,1];
- janela gaussiana separável 3x3, sigma 1,5, pesos discretos normalizados
  para somar 1, centrados em cada pixel;
- padding por reflexão sem repetir o pixel de borda (modo 'reflect');
- médias, variâncias e covariância locais com os pesos da janela e divisor
  populacional (sem correção de Bessel); variâncias negativas por
  arredondamento são limitadas a zero;
- C1 = (0,01)^2 = 1e-4, C2 = (0,03)^2 = 9e-4, faixa dinâmica 1 e proteção do
  denominador com epsilon 1e-12;
- patch constante usa a mesma fórmula: variâncias e covariância zero dão
  SSIM 1 para canais constantes iguais e o termo de luminância para
  constantes diferentes;
- agregação: média dos 3 canais por pixel, média dos pixels do patch, média
  dos patches ocultos por imagem, média das imagens por seed e taxa e
  mediana das três seeds.
- O cálculo interno usa ponto flutuante duplo para eliminar ruído de
  arredondamento em torno do epsilon (patch constante com SSIM 1 exato para
  valores de entrada float32); a entrada permanece em [0,1] float32.

Sem dependências novas: apenas torch.
"""

from __future__ import annotations

import torch

TAMANHO_PATCH = 8
N_CANAIS = 3
SIGMA = 1.5
C1 = 0.01**2
C2 = 0.03**2
EPSILON = 1e-12


def pesos_janela() -> torch.Tensor:
    """Kernel gaussiano 3x3 separável, normalizado para somar 1 (1,1,3,3)."""
    faixas = torch.arange(3, dtype=torch.float64) - 1.0
    peso_1d = torch.exp(-(faixas**2) / (2.0 * SIGMA**2))
    peso_1d = peso_1d / peso_1d.sum()
    kernel = peso_1d[:, None] * peso_1d[None, :]
    return kernel[None, None]


def _media_local(x: torch.Tensor, kernel: torch.Tensor) -> torch.Tensor:
    """Média local ponderada por canal sobre entrada reflect-padded."""
    canais = x.shape[1]
    peso = kernel.expand(canais, 1, 3, 3)
    x_padded = torch.nn.functional.pad(x, (1, 1, 1, 1), mode="reflect")
    return torch.nn.functional.conv2d(x_padded, peso, groups=canais)


def _limitar_variancia(v: torch.Tensor) -> torch.Tensor:
    return torch.clamp(v, min=0.0)


def ssim_mapa(real: torch.Tensor, pred: torch.Tensor) -> torch.Tensor:
    """Mapa SSIM por pixel com média dos 3 canais.

    real e pred: (..., 3, 8, 8) em [0,1]; retorna (..., 8, 8).
    """
    if real.shape[-2:] != (TAMANHO_PATCH, TAMANHO_PATCH):
        raise ValueError("esperados patches 8x8")
    if real.shape != pred.shape:
        raise ValueError("tamanhos divergentes entre real e pred")
    if real.min() < 0.0 or real.max() > 1.0 or pred.min() < 0.0 or pred.max() > 1.0:
        raise ValueError("entradas fora do intervalo [0,1]")
    kernel = pesos_janela()
    x = real.reshape(-1, N_CANAIS, TAMANHO_PATCH, TAMANHO_PATCH).double()
    y = pred.reshape(-1, N_CANAIS, TAMANHO_PATCH, TAMANHO_PATCH).double()
    mx = _media_local(x, kernel)
    my = _media_local(y, kernel)
    sx = _limitar_variancia(_media_local(x * x, kernel) - mx * mx)
    sy = _limitar_variancia(_media_local(y * y, kernel) - my * my)
    sxy = _media_local(x * y, kernel) - mx * my
    numerador = (2 * mx * my + C1) * (2 * sxy + C2)
    denominador = (mx * mx + my * my + C1) * (sx + sy + C2)
    # denominador protegido com epsilon 1e-12 (não positivo e substituído);
    # denominações regulares não são distorcidas, mantendo SSIM 1 exato
    # para patches idênticos e constantes iguais
    seguro = torch.where(
        denominador > EPSILON, denominador, torch.full_like(denominador, EPSILON)
    )
    mapa = numerador / seguro
    mapa = mapa.mean(dim=1)  # média dos 3 canais por pixel
    formato = real.shape[:-3] + (TAMANHO_PATCH, TAMANHO_PATCH)
    return mapa.reshape(formato)


def ssim_por_patch(real: torch.Tensor, pred: torch.Tensor) -> torch.Tensor:
    """SSIM agregado por patch: média dos pixels após média dos canais.

    real e pred: (..., 3, 8, 8); retorna (...).
    """
    return ssim_mapa(real, pred).mean(dim=(-1, -2))


def ssim_patches_ocultos(
    reais_ocultos: torch.Tensor, preds_ocultos: torch.Tensor
) -> torch.Tensor:
    """SSIM por imagem: média dos patches ocultos da imagem.

    reais_ocultos, preds_ocultos: (n_imagens, patches_ocultos, 3, 8, 8);
    retorna (n_imagens,).
    """
    por_patch = ssim_por_patch(reais_ocultos, preds_ocultos)
    return por_patch.mean(dim=-1)


def media_imagens(valores_por_imagem: torch.Tensor) -> float:
    """Média das imagens por seed e taxa."""
    return float(valores_por_imagem.double().mean())


def mediana_seeds(valores_por_seed) -> float:
    """Mediana das três seeds (sem narrativas: número puro)."""
    import statistics

    return float(statistics.median([float(v) for v in valores_por_seed]))
