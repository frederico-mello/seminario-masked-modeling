"""Seleção determinística dos oito IDs visuais e ficha de inspeção (D6).

IDs: ordenar os índices originais disponíveis pelo par
(SHA-256(UTF-8("visual-v1|" + versão_do_split + "|" + índice_original_em
decimal)), índice_original) e tomar os oito primeiros. A lista e o hash
ficam no manifesto antes de qualquer inferência; a mesma lista vale para as
duas taxas. Nenhuma inferência extra ou serviço externo para preparar a
ficha.

Ficha cega: para cada imagem e candidato, notas de 1 a 5 (1 problema grave,
3 mista/aceitável, 5 sem problema visível relevante) de cor, estrutura,
borramento e artefatos, com preferência geral pareada e comentário; dois
avaliadores preenchem, em ordem aleatória e rótulos anonimizados. A ficha
inclui explicitamente que a avaliação humana não foi realizada nesta fase e
não altera a seleção numérica.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

VERSAO_SELECAO = "visual-v1"
N_IDS = 8
NOTAS = (1, 2, 3, 4, 5)
CANDIDATOS_FICHA = ("C0", "C1", "C2", "C3", "controle_media_rgb", "controle_interpolacao")


def chave_visual(indice_original: int, versao_split: str) -> bytes:
    """Resumo SHA-256 da chave da ordenação visual."""
    texto = f"{VERSAO_SELECAO}|{versao_split}|{int(indice_original)}"
    return hashlib.sha256(texto.encode("utf-8")).digest()


def selecao_ids_visuais(
    indices_disponiveis, versao_split: str, n_ids: int = N_IDS
) -> list[int]:
    """Oito índices originais de validação, determinísticos e dependentes
    somente da versão do split e dos índices disponíveis."""
    ordenados = sorted(
        (int(i) for i in indices_disponiveis),
        key=lambda i: (chave_visual(i, versao_split), i),
    )
    if len(ordenados) < n_ids:
        raise ValueError(
            f"menos de {n_ids} índices disponíveis para a ficha visual "
            f"({len(ordenados)})"
        )
    return ordenados[:n_ids]


def ficha_visual(
    versao_split: str,
    indices_disponiveis,
    n_ids: int = N_IDS,
    candidatos: tuple[str, ...] = CANDIDATOS_FICHA,
) -> dict:
    """Cria a ficha de inspeção predefinida, sem marcação alguma.

    Campos ficam sem preencher (None); a ordem de apresentação será
    aleatória e os rótulos anonimizados só no momento da inspeção. O campo
    avaliacao_humana_realizada é False aqui: nada nesta fase deve alegar
    avaliação humana.
    """
    ids = selecao_ids_visuais(indices_disponiveis, versao_split, n_ids)
    pares = [
        (candidatos[i], candidatos[j])
        for i in range(len(candidatos))
        for j in range(i + 1, len(candidatos))
    ]
    return {
        "versao_ficha": "visual-v1",
        "versao_split": versao_split,
        "ids_selecionados": ids,
        "chave_selecao": {
            str(i): chave_visual(i, versao_split).hex() for i in ids
        },
        "avaliadores": 2,
        "ordem_apresentacao": None,  # aleatorizada somente na hora
        "rotulos_anonimizados": None,
        "avaliacao_humana_realizada": False,
        "observacoes": (
            "Evidência qualitativa; não mede reconhecimento e não altera a "
            "seleção numérica. Nenhuma avaliação humana foi realizada nesta "
            "fase; nota(s) somente depois da inferência validada."
        ),
        "itens": {
            str(i): {
                c: {
                    "cor": None,
                    "estrutura": None,
                    "borramento": None,
                    "artefatos": None,
                    "comentario": None,
                }
                for c in candidatos
            }
            for i in ids
        },
        "preferencia_pareada": {f"{a}_vs_{b}": None for a, b in pares},
        "escala": "1 problema grave; 3 mista/aceitável; 5 sem problema visível relevante",
    }


def salvar_ficha(ficha: dict, caminho: Path) -> dict:
    """Grava a ficha em JSON aninhado no hash SHA256 canônico da ficha."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    hash_ficha = hashlib.sha256(
        json.dumps(ficha, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    conteudo = {"hash_ficha": hash_ficha, "ficha": ficha}
    caminho.write_text(
        json.dumps(conteudo, sort_keys=True, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    return {"caminho": str(caminho), "sha256": hash_ficha}
