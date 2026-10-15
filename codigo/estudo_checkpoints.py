"""Checkpoints de melhor validação e final, cópias imutáveis com hash (D3).

Dois artefatos distintos por execução: o checkpoint de menor perda de
validação na régua e o da última época concluída. Atualização do melhor
somente com perda estritamente menor; empate mantém a primeira época. Cada
salvamento copia o arquivo do modelo para um destino único
(determinístico pelo conteúdo e pela época) e registra SHA256 dos bytes e a
época; sobrescrever nunca acontece, e regravar o mesmo conteúdo é idempotente.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Ponto:
    epoca: int
    perda_validacao: float


@dataclass(frozen=True)
class Markador:
    melhor: Ponto | None
    final: Ponto | None

    @property
    def epoca_melhor(self) -> int | None:
        return self.melhor.epoca if self.melhor is not None else None

    @property
    def epoca_final(self) -> int | None:
        return self.final.epoca if self.final is not None else None


class RastreioCheckpoint:
    """Rastreio do melhor checkpoint e do checkpoint final por execução."""

    def __init__(self):
        self._melhor: Ponto | None = None
        self._final: Ponto | None = None
        self.epocas_concluidas: list[int] = []
        self.interrompidas: list[int] = []
        self.motivo_interrupto: str | None = None

    @property
    def melhor(self) -> Ponto | None:
        return self._melhor

    @property
    def final(self) -> Ponto | None:
        return self._final

    def marcar(self, epoca: int, perda_validacao: float) -> Ponto:
        """Registra uma época completa na régua; retorna o melhor atual."""
        ponto = Ponto(int(epoca), float(perda_validacao))
        if self._melhor is None or ponto.perda_validacao < self._melhor.perda_validacao:
            self._melhor = ponto  # estritamente menor; empate mantém a primeira
        self._final = ponto  # última época concluída, qualquer perda
        self.epocas_concluidas.append(int(epoca))
        return self._melhor

    def marcar_interrupto(self, epoca: int, motivo: str) -> None:
        """Marca uma época parcial (limite de tempo) sem violar o histórico."""
        self.interrompidas.append(int(epoca))
        self.motivo_interrupto = motivo

    def copiar(self) -> Markador:
        return Markador(self._melhor, self._final)


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def copiar_imutavel(
    origem: Path, diretorio: Path, prefixo: str, epoca: int
) -> dict:
    """Cópia imutável de checkpoint com hash e época registrados.

    Nome determinístico: prefixo + "epoca" + número + hash dos 16 primeiros
    hexes. Nunca sobrescreve; regresso da mesma combinação conteúdo+época é
    idempotente. Retorna dict com caminho, sha256, época e tamanho.
    """
    origem = Path(origem)
    diretorio = Path(diretorio)
    diretorio.mkdir(parents=True, exist_ok=True)
    h = sha256_arquivo(origem)
    nome = f"{prefixo}_epoca{epoca}_{h[:16]}.pt"
    destino = diretorio / nome
    if destino.exists():
        if sha256_arquivo(destino) == h:
            tamanho = destino.stat().st_size
        else:
            raise FileExistsError(
                f"colisão de nome com conteúdo distinto: {destino}"
            )
    else:
        destino.write_bytes(origem.read_bytes())
        tamanho = destino.stat().st_size
        if sha256_arquivo(destino) != h:
            raise RuntimeError(f"cópia divergente registrada: {destino}")
        # imutabilidade: travar permissões de escrita (chmod a-w)
        destino.chmod(0o444)
    return {
        "caminho": str(destino),
        "sha256": h,
        "epoca": int(epoca),
        "tamanho_bytes": tamanho,
    }
