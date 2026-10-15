"""Contador monotônico e isolado da reserva C0 v2.

O contador v1 é somente leitura. Durações usam nanossegundos inteiros de
``time.monotonic_ns`` e os registros preservam a precisão, sem arredondar
para baixo.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, ROUND_CEILING
from pathlib import Path

from codigo import configuracao_estudo_c0_v2 as cfg


NS_POR_SEGUNDO = 1_000_000_000
NS_POR_MINUTO = 60 * NS_POR_SEGUNDO


class ErroOrcamento(RuntimeError):
    """Consumo recusado ou teto ultrapassado; o trabalho não deve continuar."""


def sha256_arquivo(caminho: Path) -> str:
    digest = hashlib.sha256()
    with Path(caminho).open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            digest.update(bloco)
    return digest.hexdigest()


def minutos_v1_em_ns(caminho: Path) -> tuple[int, int, int]:
    """Soma o contador v1 sem alterar seu arquivo e arredonda cada linha para cima.

    O arredondamento conservador para o nanossegundo impede subcontagem de
    qualquer lançamento decimal do contador anterior.
    """
    principal_ns = 0
    reserva_ns = 0
    if not Path(caminho).exists():
        return 0, 0, 0
    with Path(caminho).open(encoding="utf-8") as arquivo:
        for numero, linha in enumerate(arquivo, start=1):
            if not linha.strip():
                continue
            try:
                registro = json.loads(linha)
                minutos = Decimal(str(registro["minutos"]))
            except (json.JSONDecodeError, KeyError, ValueError) as erro:
                raise ValueError(f"contador v1 inválido na linha {numero}") from erro
            if minutos < 0:
                raise ValueError(f"minutos negativos no contador v1, linha {numero}")
            nanos = int(
                (minutos * Decimal(NS_POR_MINUTO)).to_integral_value(
                    rounding=ROUND_CEILING
                )
            )
            if registro.get("usar_reserva"):
                reserva_ns += nanos
            else:
                principal_ns += nanos
    return principal_ns, reserva_ns, principal_ns + reserva_ns


class ContadorReservaC0V2:
    """Contador v2 separado, persistente e auditável em JSONL."""

    def __init__(
        self,
        caminho: Path,
        *,
        v1_principal_ns: int,
        v1_reserva_ns: int,
        hash_referencia_v1: str,
        teto_reserva_ns: int = cfg.TETO_RESERVA_SEGUNDOS * NS_POR_SEGUNDO,
        teto_global_ns: int = cfg.TETO_GLOBAL_SEGUNDOS * NS_POR_SEGUNDO,
    ):
        self.caminho = Path(caminho)
        self.v1_principal_ns = int(v1_principal_ns)
        self.v1_reserva_ns = int(v1_reserva_ns)
        self.v1_total_ns = self.v1_principal_ns + self.v1_reserva_ns
        self.hash_referencia_v1 = hash_referencia_v1
        self.teto_reserva_ns = int(teto_reserva_ns)
        self.teto_global_ns = int(teto_global_ns)
        self.registros: list[dict] = []
        if self.caminho.exists():
            self._carregar()

    def _carregar(self) -> None:
        total = 0
        with self.caminho.open(encoding="utf-8") as arquivo:
            for numero, linha in enumerate(arquivo, start=1):
                if not linha.strip():
                    continue
                registro = json.loads(linha)
                duracao = int(registro["duracao_ns"])
                if duracao < 0:
                    raise ValueError(f"duração negativa na linha v2 {numero}")
                total += duracao
                if int(registro["total_v2_ns"]) != total:
                    raise ValueError(f"total não monotônico na linha v2 {numero}")
                if registro["hash_referencia_v1"] != self.hash_referencia_v1:
                    raise ValueError("hash de referência v1 diverge no contador v2")
                self.registros.append(registro)

    @property
    def total_v2_ns(self) -> int:
        return sum(int(registro["duracao_ns"]) for registro in self.registros)

    @property
    def total_global_ns(self) -> int:
        return self.v1_total_ns + self.total_v2_ns

    @property
    def saldo_reserva_ns(self) -> int:
        return self.teto_reserva_ns - self.total_v2_ns

    @property
    def saldo_global_ns(self) -> int:
        return self.teto_global_ns - self.total_global_ns

    def gasto_evento_ns(self, evento: str) -> int:
        return sum(
            int(registro["duracao_ns"])
            for registro in self.registros
            if registro["evento"] == evento
        )

    def limite_disponivel_ns(
        self, teto_atividade_ns: int, proteger_ns: int = 0
    ) -> int:
        """Limite executável, sem arredondamento e dentro dos dois tetos."""
        if teto_atividade_ns < 0 or proteger_ns < 0:
            raise ValueError("teto de atividade ou proteção negativo")
        return min(
            int(teto_atividade_ns),
            max(0, self.saldo_reserva_ns - int(proteger_ns)),
            max(0, self.saldo_global_ns - int(proteger_ns)),
        )

    def registrar(
        self,
        *,
        evento: str,
        duracao_ns: int,
        candidato: str = "C0",
        seed: int | None = None,
        taxa: float | None = None,
        estado: str,
        motivo: str = "",
        monotonic_inicio_ns: int | None = None,
        teto_evento_ns: int | None = None,
    ) -> dict:
        duracao_ns = int(duracao_ns)
        if duracao_ns < 0:
            raise ValueError("duração negativa no contador v2")
        total_v2 = self.total_v2_ns + duracao_ns
        total_global = self.v1_total_ns + total_v2
        excedeu = (
            total_v2 > self.teto_reserva_ns
            or total_global > self.teto_global_ns
            or (teto_evento_ns is not None and duracao_ns > int(teto_evento_ns))
        )
        registro = {
            "versao_contador": cfg.VERSAO,
            "evento": evento,
            "candidato": candidato,
            "seed": seed,
            "taxa": taxa,
            "duracao_ns": duracao_ns,
            "duracao_segundos": duracao_ns / NS_POR_SEGUNDO,
            "total_v1_principal_ns": self.v1_principal_ns,
            "total_v1_reserva_ns": self.v1_reserva_ns,
            "total_v1_ns": self.v1_total_ns,
            "total_v2_ns": total_v2,
            "total_global_ns": total_global,
            "teto_v2_ns": self.teto_reserva_ns,
            "teto_global_ns": self.teto_global_ns,
            "teto_evento_ns": teto_evento_ns,
            "hash_referencia_v1": self.hash_referencia_v1,
            "monotonic_inicio_ns": monotonic_inicio_ns,
            "estado": estado,
            "motivo": motivo,
            "excedeu_teto": excedeu,
        }
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with self.caminho.open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(registro, ensure_ascii=False, sort_keys=True) + "\n")
            arquivo.flush()
        self.registros.append(registro)
        if excedeu:
            raise ErroOrcamento(
                "duração real ultrapassou o teto; registrada integralmente no contador v2"
            )
        return registro


def piloto_viavel(duracao_epoca_ns: int) -> bool:
    """Usa comparação exata: igualdade passa; qualquer excesso não passa."""
    limite_ns = int(Decimal(str(cfg.LIMIAR_PILOTO_SEGUNDOS)) * NS_POR_SEGUNDO)
    return int(duracao_epoca_ns) <= int(
        limite_ns
    )


def piloto_candidato_viavel(pilotos: dict, taxas: tuple[float, ...]) -> bool:
    """C0 só inicia os treinos se todas as taxas do piloto forem viáveis."""
    return all(
        bool(pilotos.get(str(taxa), {}).get("viavel", False))
        for taxa in taxas
    )


def verificar_prazo(monotonic_agora_ns: int, prazo_ns: int) -> None:
    """Interrompe no instante do limite, sem conversão para segundos inteiros."""
    if int(monotonic_agora_ns) >= int(prazo_ns):
        raise ErroOrcamento("limite monotônico atingido")
