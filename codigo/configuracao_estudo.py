"""Manifesto congelável do estudo melhorar-reconstrucoes-mae.

Contém candidatos, seeds, taxas, hiperparâmetros comuns, parâmetros do SSIM,
limiares de ganho, orçamento de tempo e constantes da inspeção visual.
A serialização canônica é JSON com chaves ordenadas e separadores compactos;
o hash SHA256 dessa serialização é o identificador pelo qual as execuções se
referenciam. O congelamento formal se dá ao gravar o arquivo com o hash
incluído (versão das regras) imediatamente antes do primeiro piloto; nenhuma
execução parte de outra versão sem novo hash. Todos os campos referem-se
somente ao conjunto de validação; nada depende do conjunto de teste.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

VERSAO_REGRAS = "regras-estudo-v1"
VERSAO_MASCARA = "mascara-treino-v1"
VERSAO_FICHA_VISUAL = "visual-v1"
SEED_REGUA = 42
SEEDS_TREINO = (10, 20, 30)
TAXAS = (0.5, 0.75)
EPOCAS = 200
LIMIAR_PILOTO_SEGUNDOS = 1.2

_C0 = {
    "nome": "MAE direto retreinado",
    "dim": 128,
    "profundidade": 4,
    "heads": 4,
    "dim_head": 32,
    "dim_decoder": 64,
    "profundidade_decoder": 2,
    "heads_decoder": 4,
    "dim_head_decoder": 64,
    "perda": "mse",
    "peso_l1": None,
    "residual": False,
    "justificativa": "referencia do protocolo novo, isola o efeito do esquema de mascaras por identidade, epoca e seed",
}
_C1 = dict(_C0, nome="decoder reforzado",
           dim_decoder=128, profundidade_decoder=3,
           justificativa="maior capacidade de decodificacao pode ajudar com poucos patches visiveis, em especial a 75%")
_C2 = dict(_C0, nome="perda mista MSE + 0,1 L1",
           perda="mse_l1", peso_l1=0.1,
           justificativa="L1 pode reduzir borramento; MSE nos ocultos continua sendo a metrica comparavel")
_C3 = dict(_C0, nome="residual sobre media RGB",
           residual=True,
           justificativa="correcao predita sobre o preenchimento pela media RGB dos visiveis; so executa se C0 vencer cada baseline nas duas taxas com saldo elegivel de pelo menos 30 minutos")

CANDIDATOS = {"C0": _C0, "C1": _C1, "C2": _C2, "C3": _C3}

CONFIG = {
    "versao_regras": VERSAO_REGRAS,
    "versao_mascara_treino": VERSAO_MASCARA,
    "seeds_treino": list(SEEDS_TREINO),
    "taxas": list(TAXAS),
    "epocas_planejadas": EPOCAS,
    "candidatos": CANDIDATOS,
    "comum": {
        "batch": 64,
        "otimizador": "AdamW",
        "lr": 1e-4,
        "weight_decay": 0.05,
        "beta1": 0.9,
        "beta2": 0.999,
        "epsilon_adam": 1e-8,
        "precisao": "float32",
        "scheduler": None,
        "clipagem_gradiente": None,
        "embaralhamento_treino": True,
        "inicializacao_aleatoria": True,
    },
    "ssim": {
        "janela": 3,
        "sigma": 1.5,
        "faixa_dinamica": 1.0,
        "c1": 1e-4,
        "c2": 9e-4,
        "epsilon_denominador": 1e-12,
        "pad": "reflexao_sem_repetir_borda",
        "divisor": "populacional",
        "variancia_negativa": "limitada_a_zero",
        "entrada": "[0,1]",
        "agregacao": (
            "media_canais_por_pixel:media_pixels_patch:media_patches_ocultos:"
            "media_imagens_seed_taxa:mediana_seeds"
        ),
    },
    "limiares": {
        "razao_mse_maximo": 0.95,
        "ganho_ssim_minimo": 0.02,
        "tolerancia_ssim": 0.01,
        "piloto_segundos_maximo": LIMIAR_PILOTO_SEGUNDOS,
        "saldo_c3_minimo_minutos": 30.0,
    },
    "orcamento": {
        "total_minutos": 120.0,
        "principal_minutos": 90.0,
        "reserva_minutos": 30.0,
        "envelope_candidato_minutos": 30.0,
        "por_candidato": {
            "piloto": 2.0,
            "treino_total": 24.0,
            "treino_por_seed_taxa": 4.0,
            "consolidacao": 2.0,
            "avaliacao": 2.0,
        },
        "avaliacao_final_baselines_minutos": 6.0,
    },
    "regua": {
        "seed_mascara": SEED_REGUA,
        "medida": "mse_somente_patches_ocultos",
        "ssim": True,
        "mascarado_por_posicao": True,
    },
    "visual": {
        "versao_ficha": VERSAO_FICHA_VISUAL,
        "chave_selecao": "sha256(visual-v1|versao_split|indice_decimal) e indice como desempate",
        "n_ids": 8,
        "escala_notas": "1 problema grave a 5 sem problema visivel relevante",
    },
}

CAMPOS_REGRAS = (
    "versao_regras",
    "versao_mascara_treino",
    "seeds_treino",
    "taxas",
    "epocas_planejadas",
    "candidatos",
    "comum",
    "ssim",
    "limiares",
    "orcamento",
    "regua",
    "visual",
)


def serializacao_canonica(config: dict) -> str:
    """JSON canônico (chaves ordenadas, separadores compactos, UTF-8)."""
    return json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_configuracao(config: dict | None = None) -> str:
    """SHA256 hex da serialização canônica da configuração."""
    if config is None:
        config = CONFIG
    return hashlib.sha256(serializacao_canonica(config).encode("utf-8")).hexdigest()


def manifesto(caminho: Path | None = None) -> dict:
    """Configuração completa com o hash do manifesto incluído."""
    conteudo = dict(CONFIG)
    conteudo["hash_manifesto"] = hash_configuracao(CONFIG)
    return conteudo


def salvar_manifesto(caminho: Path) -> dict:
    """Grava o manifesto congelado (versão das regras) em JSON."""
    conteudo = manifesto(caminho)
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(serializacao_canonica(conteudo) + "\n", encoding="utf-8")
    return conteudo


def verificar_manifesto(caminho: Path) -> dict:
    """Verifica o hash gravado; falha se qualquer campo divergir."""
    conteudo = json.loads(Path(caminho).read_text(encoding="utf-8"))
    hash_gravado = conteudo.pop("hash_manifesto")
    if hash_gravado != hash_configuracao(conteudo):
        raise ValueError(
            "manifesto divergente: hash gravado e diferente do hash recalculado"
        )
    return conteudo
