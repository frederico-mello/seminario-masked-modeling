"""Configuração isolada da retomada C0 v2.

Os resultados v1 ficam no diretório original. Esta configuração define apenas
a rodada C0 v2, com seu próprio manifesto e contador de reserva.
"""

from __future__ import annotations

import hashlib
import json

from codigo import configuracao_estudo as v1


VERSAO = "c0-v2"
LIMIAR_PILOTO_SEGUNDOS = 1.25
TETO_EXECUCAO_SEGUNDOS = 4 * 60
TETO_PILOTO_TOTAL_SEGUNDOS = 2 * 60
TETO_RESERVA_SEGUNDOS = 30 * 60
TETO_GLOBAL_SEGUNDOS = 120 * 60
EPOCAS_MAXIMAS = 200

DIR_RESULTADOS_RELATIVO = "resultados/estudo-melhorar-reconstrucoes-mae-c0-v2"
DIR_RESULTADOS_V1_RELATIVO = "resultados/estudo-melhorar-reconstrucoes-mae"

CONFIG = {
    "versao": VERSAO,
    "escopo": "somente C0; seeds 10, 20 e 30; taxas 0.5 e 0.75",
    "candidato": dict(v1.CANDIDATOS["C0"]),
    "comum": dict(v1.CONFIG["comum"]),
    "seeds_treino": list(v1.SEEDS_TREINO),
    "taxas": list(v1.TAXAS),
    "epocas_maximas": EPOCAS_MAXIMAS,
    "limiar_piloto_segundos": LIMIAR_PILOTO_SEGUNDOS,
    "teto_execucao_segundos": TETO_EXECUCAO_SEGUNDOS,
    "teto_piloto_total_segundos": TETO_PILOTO_TOTAL_SEGUNDOS,
    "teto_reserva_v2_segundos": TETO_RESERVA_SEGUNDOS,
    "teto_global_segundos": TETO_GLOBAL_SEGUNDOS,
    "mascara_treino": v1.VERSAO_MASCARA,
    "mascara_validacao_seed": v1.SEED_REGUA,
    "regua": {
        "medida": "MSE e SSIM nos mesmos patches ocultos de validação da v1",
        "ssim": dict(v1.CONFIG["ssim"]),
    },
    "comparacao": {
        "escopo": "descritiva e somente na validação",
        "sem_reavaliar_controles": True,
        "sem_inferir_modelos_v1": True,
        "sem_consultar_teste": True,
        "epocas_incompletas_equivalem_a_200": False,
    },
    "diretorios": {
        "v2": DIR_RESULTADOS_RELATIVO,
        "v1_referencia": DIR_RESULTADOS_V1_RELATIVO,
    },
}


def serializacao_canonica(valor: dict) -> str:
    """JSON determinístico para o hash da configuração."""
    return json.dumps(valor, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_configuracao(valor: dict | None = None) -> str:
    conteudo = CONFIG if valor is None else valor
    return hashlib.sha256(serializacao_canonica(conteudo).encode("utf-8")).hexdigest()
