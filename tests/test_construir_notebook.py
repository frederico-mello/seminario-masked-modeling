from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts import construir_notebook

RAIZ = Path(__file__).resolve().parent.parent


def _ids_markdown(notebook: dict) -> dict[str, str]:
    return {
        titulo: celula["id"]
        for celula in notebook["cells"]
        if celula["cell_type"] == "markdown"
        if (titulo := construir_notebook.titulo_markdown(celula)) is not None
        and "id" in celula
    }


def test_gerador_preserva_ids_markdown_existentes_no_head():
    base = json.loads(
        subprocess.check_output(
            ["git", "show", "HEAD:codigo/notebook.ipynb"], cwd=RAIZ
        )
    )
    ids_base = _ids_markdown(base)
    assert len(ids_base) == 10

    gerado = json.loads(json.dumps(construir_notebook.NOTEBOOK))
    construir_notebook.preservar_ids_markdown(gerado["cells"])

    assert _ids_markdown(gerado) == ids_base


def test_sanitiza_caminho_temporario_sem_alterar_mensagem_do_warning():
    mensagem = (
        "UserWarning: Converting a tensor with requires_grad=True to a scalar "
        "may lead to unexpected behavior.\n"
    )
    celulas = [
        {
            "cell_type": "code",
            "outputs": [
                {
                    "output_type": "stream",
                    "text": [
                        "/tmp/ipykernel_187476/275065010.py:15: " + mensagem
                    ],
                }
            ],
        }
    ]

    construir_notebook.sanitizar_saidas(celulas)

    assert celulas[0]["outputs"][0]["text"] == [mensagem]
