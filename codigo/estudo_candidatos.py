"""Candidatos congelados, perdas e elegibilidade do residual (D5, D7).

Declarados antes de qualquer treino: C0 (MAE direto retreinado), C1
(decoder de dimensão 128 e três blocos), C2 (MSE + 0,1 * L1 nos ocultos) e
C3 (residual sobre a média RGB dos visíveis, opcional). Todos preservam
entrada, resolução, patches e codificação dos visíveis do MAE em
codigo/mae.py; somente C1 altera o decoder.

A elegibilidade de C3 é função checável: a mediana de MSE de C0 deve ser
estritamente menor que a de cada baseline nas duas taxas e deve restar ao
menos 30 minutos dos 90 principais, já descontados até 6 minutos de
avaliação final. A reserva de 30 minutos nunca financia C3.
"""

from __future__ import annotations

import torch

from codigo import configuracao_estudo as cfg
from codigo.mae import MAE

ORDEM_DESEMPATE = ("C1", "C2", "C3")


class DeclaracaoCandidato(dict):

    def __hash__(self):
        return hash(tuple(sorted(self.items())))

    def __immutable(self, *args, **kwargs):
        raise TypeError("declaração de candidato é congelada")

    __setitem__ = __immutable


def declaracoes() -> dict[str, DeclaracaoCandidato]:
    return {c: DeclaracaoCandidato(v) for c, v in cfg.CANDIDATOS.items()}


def construir_modelo(declaracao: dict, seed: int | None = None) -> MAE:
    """Instancia o MAE com a arquitetura declarada, sem edição manual.

    A inicialização fica a cargo de quem treina; se seed for passada,
    ela alimenta o gerador apenas nesta construção.
    """
    if seed is not None:
        torch.manual_seed(seed)
    return MAE(
        dim=declaracao["dim"],
        profundidade=declaracao["profundidade"],
        heads=declaracao["heads"],
        dim_head=declaracao["dim_head"],
        dim_decoder=declaracao["dim_decoder"],
        profundidade_decoder=declaracao["profundidade_decoder"],
        heads_decoder=declaracao["heads_decoder"],
        dim_head_decoder=declaracao["dim_head_decoder"],
    )


def perda_candidato(
    declaracao: dict,
    predicao: torch.Tensor,
    patches: torch.Tensor,
    indices_ocultos: torch.Tensor,
) -> torch.Tensor:
    """Perda declarada do candidato, exclusivamente nos patches ocultos.

    'mse': MSE dos pixels ocultos em escala [0,1].
    'mse_l1': MSE + peso_l1 * L1, ambas nos pixels ocultos.
    """
    from codigo.mae import perda_mae

    peso_l1 = declaracao.get("peso_l1")
    mse = perda_mae(predicao, patches, indices_ocultos)
    if declaracao["perda"] == "mse":
        return mse
    if declaracao["perda"] == "mse_l1":
        lote = torch.arange(patches.shape[0], device=predicao.device)[:, None]
        pred_h = predicao[lote, indices_ocultos]
        alvos_h = patches[lote, indices_ocultos]
        l1 = torch.mean(torch.abs(pred_h - alvos_h))
        return mse + peso_l1 * l1
    raise ValueError(f"perda não declarada: {declaracao['perda']}")


def composicao_residual(
    preenchimento: torch.Tensor,
    correcao: torch.Tensor,
    indices_ocultos: torch.Tensor,
) -> torch.Tensor:
    """C3: aplica a correção predita apenas sobre os patches ocultos.

    Visíveis permanecem exatamente os originais; resultado limitado a [0,1].
    """
    if preenchimento.shape != correcao.shape:
        raise ValueError("formatos divergentes entre preenchimento e correção")
    saida = preenchimento.clone()
    lote = torch.arange(preenchimento.shape[0], device=preenchimento.device)[
        :, None
    ]
    ocultos_corrigidos = (
        preenchimento[lote, indices_ocultos] + correcao[lote, indices_ocultos]
    )
    saida[lote, indices_ocultos] = ocultos_corrigidos.clamp(0.0, 1.0)
    return saida


def elegibilidade_c3(
    mse_c0_por_taxa: dict[float, float],
    mse_baselines: dict[str, dict[float, float]],
    minutos_livres: float,
    minimo_minutos: float = 30.0,
    taxas: tuple[float, ...] = (0.5, 0.75),
) -> tuple[bool, str]:
    """C3 só executa se, nas duas taxas, a mediana de MSE de C0 for
    estritamente menor que a de cada baseline e houver ao menos
    minimo_minutos livres nos 90 principais (reserva de 30 nunca conta).

    Retorna (elegível, motivo). O motivo nomeia a condição falha.
    """
    for taxa in taxas:
        mse_c0 = mse_c0_por_taxa[taxa]
        for nome, por_taxa in mse_baselines.items():
            mensagem = (
                f"na taxa {taxa}, a mediana de MSE de C0 ({mse_c0:.6f}) não é "
                f"estritamente menor que a do baseline {nome} "
                f"({por_taxa[taxa]:.6f})"
            )
            if not mse_c0 < por_taxa[taxa]:
                return False, mensagem
    if minutos_livres < minimo_minutos:
        return (
            False,
            f"saldo elegível dos 90 minutos principais insuficiente: "
            f"{minutos_livres:.2f} < {minimo_minutos:.2f} (a reserva de "
            f"30 minutos nunca financia C3)",
        )
    return True, (
        "C0 supera cada baseline nas duas taxas e há "
        f"{minutos_livres:.2f} minutos elegíveis na alocação principal"
    )
