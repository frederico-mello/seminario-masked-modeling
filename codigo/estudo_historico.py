"""Histórico append-only por épocas e eventos (D8).

um CSV com uma linha por época ou evento computacional, com campos:
'execucao,candidato,seed,taxa,evento,epoca,perda_treino,perda_validacao,
ssim_validacao,tempo_epoca,tempo_acumulado,unidade,config_hash,
split_versao,codigo_hash,regras_hash,estado,motivo'.

Identidade: registros de pilotos e avaliações recebem evento explícito
('piloto', 'epoca', 'checkpoint', 'controle', 'avaliacao_validacao',
'checkpoint', 'selecao', 'orcamento'). O tempo_acumulado é derivado da soma
dos tempo_epoca por execução (o arquivo não registra acumulado errado
previamente, o valor é calculado ao escrever). O resumo derivado mantém
época e hashes dos checkpoints melhor e final, medias/medianas por seed,
métricas dos controles, decisões e tempo total. Todos os números vem do
arquivo, nada digitado manualmente.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

COLUNAS = (
    "execucao",
    "candidato",
    "seed",
    "taxa",
    "evento",
    "epoca",
    "perda_treino",
    "perda_validacao",
    "ssim_validacao",
    "tempo_epoca",
    "tempo_acumulado",
    "unidade",
    "config_hash",
    "split_versao",
    "codigo_hash",
    "regras_hash",
    "estado",
    "motivo",
)

EVENTOS_CONHECIDOS = (
    "piloto",
    "epoca",
    "validacao",
    "checkpoint",
    "controle",
    "avaliacao_validacao",
    "avaliacao_final",
    "selecao",
    "erro",
)


class HistoricoEstudo:
    """CSV append-only: cada registrar() adiciona uma linha; nunca reescreve."""

    def __init__(self, caminho_csv: Path):
        self.caminho_csv = Path(caminho_csv)
        if not self.caminho_csv.exists():
            self.caminho_csv.parent.mkdir(parents=True, exist_ok=True)
            with open(self.caminho_csv, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(COLUNAS)
        self._acumulado: dict[str, float] = {}

    def _acumulado_execucao(self, execucao: str) -> float:
        if execucao not in self._acumulado:
            total = 0.0
            for row in self.linhas():
                if row["execucao"] == execucao:
                    try:
                        total += float(row["tempo_epoca"] or 0.0)
                    except ValueError:
                        pass
            self._acumulado[execucao] = total
        return self._acumulado[execucao]

    def registrar(self, **campos) -> dict:
        faltando = [c for c in COLUNAS if c not in campos]
        extras = [c for c in campos if c not in COLUNAS]
        if extras:
            raise ValueError(f"campos fora do esquema: {extras}")
        valores = {c: campos.get(c, "") for c in COLUNAS}
        if not valores["execucao"]:
            raise ValueError("execucao é campo obrigatório")
        execucao = valores["execucao"]
        try:
            tempo = float(valores["tempo_epoca"] or 0.0)
        except ValueError as erro:
            raise ValueError(f"tempo_epoca não numérico: {valores['tempo_epoca']}") from erro
        acumulado = self._acumulado_execucao(execucao) + tempo
        self._acumulado[execucao] = acumulado
        valores["tempo_epoca"] = tempo
        valores["tempo_acumulado"] = acumulado
        with open(self.caminho_csv, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([valores[c] for c in COLUNAS])
        return valores

    def linhas(self) -> list[dict]:
        with open(self.caminho_csv, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))


def decodificar_motivo(motivo: str) -> dict[str, str]:
    """Motivo com pares 'campo=valor' separados por ';' → dict."""
    saida = {}
    for parte in motivo.split(";"):
        parte = parte.strip()
        if not parte:
            continue
        if "=" not in parte:
            raise ValueError(f"motivo sem campo=valor: {parte}")
        chave, valor = parte.split("=", 1)
        saida[chave.strip()] = valor.strip()
    return saida


def resumo(historico: HistoricoEstudo) -> dict:
    """Resumo derivado integralmente do CSV (números nunca digitados)."""
    linha_eventos = historico.linhas()
    itens: list[dict] = linha_eventos
    total_tempo = 0.0
    for r in itens:
        try:
            total_tempo += float(r["tempo_epoca"] or 0.0)
        except ValueError:
            pass

    # checkpoints por execução: evento 'checkpoint', estado 'melhor'|'final'
    checkpoints: dict[str, dict] = {}
    for r in itens:
        if r["evento"] != "checkpoint":
            continue
        exec_id = r["execucao"]
        slot = checkpoints.setdefault(exec_id, {})
        info = {k: v for k, v in decodificar_motivo(r["motivo"]).items()}
        slot[r["estado"]] = info

    # medianas por (candidato, taxa): por seed, último valor por época do
    # evento 'epoca'; a comparação usa a última registrada nessa execução
    _medias: dict[tuple, list[float]] = {}
    for r in itens:
        if r["evento"] != "epoca":
            continue
        try:
            valor = float(r["perda_validacao"])
        except ValueError:
            continue
        chave = (r["candidato"], r["taxa"], r["seed"])
        _medias.setdefault(chave, []).append(valor)
    medias_seed: dict[str, dict] = {}
    for (candidato, taxa, seed), valores in sorted(_medias.items()):
        medias_seed.setdefault(candidato, {}).setdefault(taxa, {})[seed] = {
            "perda_validacao": valores[-1],  # última época dessa execução
            "epocas": len(valores),
        }

    controles: list[dict] = []
    for r in itens:
        if r["evento"] == "controle":
            controles.append(
                {
                    "candidato": r["candidato"],
                    "seed": r["seed"],
                    "taxa": r["taxa"],
                    "mse": r["perda_validacao"],
                }
            )

    decisoes: list[dict] = []
    for r in itens:
        if r["evento"] == "selecao":
            decisoes.append(
                {"candidato": r["candidato"], "taxa": r["taxa"], "estado": r["estado"]}
            )

    return {
        "linhas": len(itens),
        "tempo_total": total_tempo,
        "checkpoints": checkpoints,
        "medias_seed": medias_seed,
        "controles": controles,
        "decisoes": decisoes,
    }


def serializar_resumo(resumo_dict: dict) -> str:
    return json.dumps(resumo_dict, ensure_ascii=False, sort_keys=True)
