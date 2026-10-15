"""Contador cumulativo persistido de orçamento de tempo (D7).

Teto total de 120 minutos: 90 minutos principais (30 por candidato C0/C1/C2,
com envelopes por seed/taxa de 4 minutos, piloto de 2 minutos, consolidação
de 2 minutos e avaliação/registros de 2 minutos; até 6 minutos agregados de
avaliação final e baselines) e 30 minutos de reserva, usada apenas por
repetições justificadas e jamais por C3.

O contador é monotono: durações reais cumulativas nunca diminuem e nenhuma
retomada zera o total. Cada consumo é uma linha JSONL append-only com os
totais depois do consumo; lograr o mesmo arquivo reconstrói os totais e
continua a mesma identidade. `pode_iniciar` é o guard antes (e durante)
de iniciar uma atividade, avaliando o saldo da categoria, do candidato e do
global; tempo real é registrado por `consumir` mesmo quando cruza o limite
(a verificação prévia é obrigatória e a violação aparece no Payload
registrada por quem interrompeu).
"""

from __future__ import annotations

import json
from pathlib import Path

from codigo import configuracao_estudo as cfg

CATEGORIAS_PRINCIPAIS = (
    "piloto",
    "treino_por_seed_taxa",
    "consolidacao",
    "avaliacao",
    "avaliacao_final",
)
CAP_CATEGORIA = {
    "piloto": "por_candidato",
    "treino_por_seed_taxa": "por_chave",
    "consolidacao": "por_candidato",
    "avaliacao": "por_candidato",
    "avaliacao_final": "global",
    "repeticao": "reserva",
}


class ContadorOrcamento:
    """Teto monotono persistido em JSONL; horário é passado por quem chama."""

    def __init__(
        self,
        caminho_registro: Path,
        config: dict | None = None,
    ):
        self.caminho_registro = Path(caminho_registro)
        self.config = config or cfg.CONFIG
        orcamento = self.config["orcamento"]
        self.principal_total = float(orcamento["principal_minutos"])
        self.reserva_total = float(orcamento["reserva_minutos"])
        self.envelope_candidato = float(
            orcamento["envelope_candidato_minutos"]
        )
        self.caps_por_candidato = orcamento["por_candidato"]
        self.cap_treino_chave = float(orcamento["por_candidato"]["treino_por_seed_taxa"])
        self.cap_avaliacao_final = float(
            orcamento["avaliacao_final_baselines_minutos"]
        )
        self.cap_treino_total = float(orcamento["por_candidato"]["treino_total"])
        self.cap_piloto = float(orcamento["por_candidato"]["piloto"])
        self.cap_consolidacao = float(orcamento["por_candidato"]["consolidacao"])
        self.cap_avaliacao = float(orcamento["por_candidato"]["avaliacao"])
        self.caps_especificos = {
            "piloto": self.cap_piloto,
            "consolidacao": self.cap_consolidacao,
            "avaliacao": self.cap_avaliacao,
            "treino_por_seed_taxa": self.cap_treino_chave,
            "treino_total": self.cap_treino_total,
        }
        self.registros: list[dict] = []
        if self.caminho_registro.exists():
            with open(self.caminho_registro, encoding="utf-8") as f:
                for linha in f:
                    linha = linha.strip()
                    if linha:
                        self.registros.append(json.loads(linha))

    # --- consultas -----------------------------------------------------

    def _soma(self, **filtro) -> float:
        total = 0.0
        for r in self.registros:
            if all(r.get(k) == v for k, v in filtro.items() if v is not None):
                total += float(r["minutos"])
        return total

    def gasto(
        self,
        candidato: str | None = None,
        categoria: str | None = None,
        chave: tuple | None = None,
        reserva: bool = False,
    ) -> float:
        return self._soma(
            candidato=candidato,
            categoria=categoria,
            chave=json.dumps(chave, ensure_ascii=False) if chave else None,
            usar_reserva=reserva,
        )

    def gasto_principal(self, candidato: str | None = None) -> float:
        return self._soma(candidato=candidato, usar_reserva=False)

    @property
    def total_principal(self) -> float:
        return self.gasto_principal()

    @property
    def total_reserva(self) -> float:
        return self._soma(usar_reserva=True)

    def saldo_principal(self) -> float:
        return self.principal_total - self.total_principal

    def saldo_reserva(self) -> float:
        return self.reserva_total - self.total_reserva

    def saldo_candidato(self, candidato: str) -> float:
        return self.envelope_candidato - self.gasto_principal(candidato)

    # --- guard -----------------------------------------------------------

    def pode_iniciar(
        self,
        candidato: str,
        categoria: str,
        minutos_previstos: float,
        chave: tuple | None = None,
        usar_reserva: bool = False,
    ) -> tuple[bool, str | None]:
        """Guard: pode a atividade proposta começar com o saldo atual?"""
        if minutos_previstos < 0:
            return False, "minutos previstos negativo"
        if categoria not in CAP_CATEGORIA:
            return False, f"categoria desconhecida: {categoria}"
        if usar_reserva:
            if candidato == "C3":
                return False, "C3 nunca usa a reserva de 30 minutos"
            if categoria != "repeticao":
                return False, "reserva só financia repetições justificadas"
            disponivel = self.saldo_reserva()
            if minutos_previstos > disponivel + 1e-9:
                return False, (
                    f"reserva insuficiente: {minutos_previstos:.2f} > "
                    f"{disponivel:.2f}"
                )
            return True, None
        if categoria == "repeticao" and not usar_reserva:
            return False, "categoria de reserva exige usar_reserva=True"

        # teto por categoria
        if categoria == "avaliacao_final":
            cap = self.cap_avaliacao_final
            escopo_global = True
            gasto_categoria = self.gasto(None, categoria, chave)
        else:
            cap = self.caps_especificos.get(categoria)
            escopo_global = False
            gasto_categoria = self.gasto(candidato, categoria, chave)
        if cap is not None and gasto_categoria + minutos_previstos > cap + 1e-9:
            return False, (
                f"envelope de {categoria} do escopo "
                f"{'global' if escopo_global else 'candidato'} esgotado: "
                f"gasto {gasto_categoria:.2f} + previsto "
                f"{minutos_previstos:.2f} > {cap:.2f}"
            )
        # envelope do candidato (30 min, categorias principais)
        gasto_do_candidato = self.gasto_principal(candidato)
        if (
            categoria != "avaliacao_final"
            and gasto_do_candidato + minutos_previstos
            > self.envelope_candidato + 1e-9
        ):
            return False, (
                f"envelope de 30 minutos do candidato {candidato} esgotado"
            )
        # teto principal global (90 min)
        if self.total_principal + minutos_previstos > self.principal_total + 1e-9:
            return False, (
                f"alocação principal esgotada: gasto {self.total_principal:.2f} "
                f"+ previsto {minutos_previstos:.2f} > {self.principal_total:.2f}"
            )
        return True, None

    # --- registro --------------------------------------------------------

    def consumir(
        self,
        candidato: str,
        categoria: str,
        minutos: float,
        chave: tuple | None = None,
        usar_reserva: bool = False,
        ts: str = "",
        estado: str = "concluido",
        motivo: str | None = None,
    ) -> dict:
        """Registra tempo real consumido (linha JSONL append-only)."""
        if minutos < 0:
            raise ValueError("minutos consumidos negativos")
        if categoria == "repeticao":
            usar_reserva = True
            if candidato == "C3":
                raise ValueError("C3 nunca usa a reserva de 30 minutos")
        registro = {
            "ts": ts,
            "candidato": candidato,
            "categoria": categoria,
            "chave": json.dumps(chave, ensure_ascii=False) if chave else None,
            "usar_reserva": bool(usar_reserva or categoria == "repeticao"),
            "minutos": float(minutos),
            "total_principal": self.total_principal,
            "total_reserva": self.total_reserva,
            "estado": estado,
            "motivo": motivo,
        }
        with open(self.caminho_registro, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
        self.registros.append(registro)
        return dict(
            total_principal=self.total_principal,
            total_reserva=self.total_reserva,
            saldo_principal=self.saldo_principal(),
        )
