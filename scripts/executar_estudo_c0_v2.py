"""Entrada da execução C0 v2, com relógio iniciado antes dos imports do estudo."""

import time
import sys
from pathlib import Path

INICIO_MONOTONICO_NS = time.monotonic_ns()
RAIZ_PROJETO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROJETO))

from codigo.estudo_execucao_c0_v2 import main


if __name__ == "__main__":
    raise SystemExit(main(INICIO_MONOTONICO_NS))
