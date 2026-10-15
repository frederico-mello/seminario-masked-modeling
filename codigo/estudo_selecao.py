"""Regra de seleção multiobjetivo congelada (D6, tarefa 5.2).

Comparação por taxa e seed na régua comum. C0 e cada controle e candidato
aparecem em cada comparação; controles determinísticos são calculados uma
vez por taxa e imagem e referenciados por seed.

Melhoria contra C0 em uma taxa exige, em cada taxa avaliada: razão entre a
mediana por seed do MSE do candidato e a mediana de C0 <= 0,95 E mediana das
diferenças pareadas de SSIM (candidato menos C0) >= 0,02.

Entre elegíveis: identificar o maior SSIM mediano; manter os que estejam a
no máximo 0,01 abaixo dele (tolerância de desempate; não relaxa o ganho
mínimo de 0,02 contra C0); desse conjunto, menor MSE mediano; empates
exatos resolvidos por menor tempo acumulado e depois ordem fixa C1, C2, C3.
Se nenhum cumprir ambos os limiares, sem vencedor: ausência de melhoria
demonstrada na taxa.

Nenhum acesso ao conjunto de teste nesta decisão.
"""

from __future__ import annotations

from statistics import median

RAZAO_MSE_MAXIMO = 0.95
GANHO_SSIM_MINIMO = 0.02
TOLERANCIA_SSIM = 0.01
ORDEM_DESEMPATE = ("C1", "C2", "C3")


def elegivel(
    mse_por_seed: list[float],
    ssim_por_seed: list[float],
    mse_c0: list[float],
    ssim_c0: list[float],
    razao_mse_maximo: float = RAZAO_MSE_MAXIMO,
    ganho_ssim_minimo: float = GANHO_SSIM_MINIMO,
) -> tuple[bool, str]:
    """Elegibilidade de um candidato contra C0 em uma taxa única.

    mse_por_seed, ssim_por_seed: valores do candidato por seed (mesma ordem
    de seeds); mse_c0, ssim_c0: valores de C0 por seed na mesma ordem.
    """
    if not (len(mse_por_seed) == len(ssim_por_seed) == len(mse_c0) == len(ssim_c0)):
        raise ValueError("listas de seeds com tamanhos divergentes")
    mediana_mse_candidato = median(mse_por_seed)
    mediana_mse_c0 = median(mse_c0)
    razao = mediana_mse_candidato / mediana_mse_c0
    diferenca_ssim = median(
        s - t for s, t in zip(ssim_por_seed, ssim_c0, strict=True)
    )
    if razao > razao_mse_maximo:
        return False, (
            f"razão de medianas de MSE {razao:.6f} > {razao_mse_maximo:.2f} "
            "neste taxa"
        )
    if diferenca_ssim < ganho_ssim_minimo:
        return False, (
            f"mediana das diferenças pareadas de SSIM {diferenca_ssim:.6f} < "
            f"{ganho_ssim_minimo:.2f} nesta taxa"
        )
    return True, f"razão {razao:.6f} e SSIM {diferenca_ssim:.6f} cumprem os limiares"


def selecionar(
    candidato_mse: dict[str, list[float]],
    candidato_ssim: dict[str, list[float]],
    mse_c0: list[float],
    ssim_c0: list[float],
    tempos_acumulados: dict[str, float],
    ordem_fixa: tuple[str, ...] = ORDEM_DESEMPATE,
) -> dict:
    """Seleção congelada dentro de uma taxa.

    candidato_mse / candidato_ssim: {candidato: [valor por seed]}.
    tempos_acumulados: {candidato: tempo cumulativo em minutos}.
    Retorna dict com vencedor (str ou None), elegíveis e motivo.
    """
    elegiveis: list[str] = []
    motivos: dict[str, str] = {}
    for candidato, mse in candidato_mse.items():
        ok, motivo = elegivel(mse, candidato_ssim[candidato], mse_c0, ssim_c0)
        motivos[candidato] = motivo
        if ok:
            elegiveis.append(candidato)
    if not elegiveis:
        return {
            "vencedor": None,
            "elegiveis": [],
            "motivo": "sem melhoria demonstrada na taxa; nenhum candidato cumpre os limiares",
            "motivos": motivos,
            "mediana_ssim": {c: median(candidato_ssim[c]) for c in candidato_mse},
        }
    ssim_mediano = {c: median(candidato_ssim[c]) for c in elegiveis}
    maior_ssim = max(ssim_mediano.values())
    retidos = [c for c in elegiveis if ssim_mediano[c] >= maior_ssim - TOLERANCIA_SSIM]
    mse_mediano = {c: median(candidato_mse[c]) for c in retidos}
    menor_mse = min(mse_mediano.values())
    finalistas = [c for c in retidos if mse_mediano[c] == menor_mse]
    vencedor = min(
        finalistas,
        key=lambda c: (
            tempos_acumulados.get(c, float("inf")),
            ordem_fixa.index(c) if c in ordem_fixa else len(ordem_fixa),
            c,
        ),
    )
    return {
        "vencedor": vencedor,
        "elegiveis": elegiveis,
        "motivo": (
            f"{len(elegiveis)} elegíveis; maior SSIM mediano {maior_ssim:.6f}; "
            f"tolerância retém {len(retidos)}; menor MSE mediano "
            f"{menor_mse:.6f}; vencedor {vencedor}"
        ),
        "motivos": motivos,
        "mediana_ssim": ssim_mediano,
        "mediana_mse": mse_mediano,
        "retidos": retidos,
    }
