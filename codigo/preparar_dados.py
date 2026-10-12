"""Script de linha de comando para baixar o CIFAR-10 e gerar o subset."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo.dados import main

if __name__ == "__main__":
    main()