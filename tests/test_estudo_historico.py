from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo.estudo_historico import (
    COLUNAS,
    HistoricoEstudo,
    decodificar_motivo,
    resumo,
)

RAIZ = Path(__file__).resolve().parent.parent

BASE = {
    "execucao": "regras",
    "config_hash": "config-hash-1",
    "split_versao": "split-v1",
    "codigo_hash": "codigo-hash-1",
    "regras_hash": "regras-hash-1",
    "unidade": "minuto",
}


def test_historico_v1_preserva_bytes_e_crlf_rfc4180():
    caminho = RAIZ / "resultados/estudo-melhorar-reconstrucoes-mae/historico.csv"
    dados = caminho.read_bytes()

    assert hashlib.sha256(dados).hexdigest() == (
        "6d54737fa3e977d906f56a3e4d5fedb2f3b12b94825cfbdf7985512bda6ebdf7"
    )
    assert dados.endswith(b"\r\n")
    assert dados.count(b"\n") == dados.count(b"\r\n") == 2445
    assert dados.count(b"\r") == dados.count(b"\r\n")
    linhas = dados.split(b"\r\n")[:-1]
    assert all(not linha.endswith((b" ", b"\t")) for linha in linhas)

    with caminho.open(encoding="utf-8", newline="") as arquivo:
        registros = list(csv.reader(arquivo))
    assert len(registros) == 2445
    assert {len(registro) for registro in registros} == {18}


def registra(h, **sobrescreve):
    campos = dict(BASE)
    campos.update(sobrescreve)
    return h.registrar(**campos)


def test_esquema_tem_todos_os_campos(tmp_path):
    h = HistoricoEstudo(tmp_path / "historico.csv")
    with open(h.caminho_csv, newline="", encoding="utf-8") as f:
        cabeco = next(csv.reader(f))
    assert tuple(cabeco) == COLUNAS
    for campo in (
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
    ):
        assert campo in COLUNAS


def test_registrar_preenche_padrao_e_exige_execucao(tmp_path):
    h = HistoricoEstudo(tmp_path / "historico.csv")
    registra(h, candidato="C0", seed="10", taxa="0.5", evento="epoca", epoca="1",
             perda_treino="0.2", perda_validacao="0.19", ssim_validacao="0.7",
             tempo_epoca="0.5", estado="concluido")
    linha = h.linhas()[0]
    assert linha["execucao"] == "regras" and linha["unidade"] == "minuto"
    assert linha["motivo"] == ""
    with pytest.raises(ValueError):
        h.registrar(**{"evento": "epoca", "tempo_epoca": "0.1", "execucao": ""})


def test_tempo_acumulado_por_execucao(tmp_path):
    h = HistoricoEstudo(tmp_path / "historico.csv")
    registra(h, execucao="A", evento="epoca", epoca="1", tempo_epoca="0.5")
    registra(h, execucao="A", evento="epoca", epoca="2", tempo_epoca="0.3")
    registra(h, execucao="B", evento="epoca", epoca="1", tempo_epoca="1.0")
    linhas = h.linhas()
    assert [float(l["tempo_acumulado"]) for l in linhas] == [0.5, 0.8, 1.0]


def test_append_only(tmp_path):
    h = HistoricoEstudo(tmp_path / "historico.csv")
    registra(h, evento="piloto", tempo_epoca="0.4", estado="concluido")
    antes = (tmp_path / "historico.csv").read_bytes()
    registra(h, evento="epoca", epoca="1", tempo_epoca="0.5", estado="concluido")
    depois = (tmp_path / "historico.csv").read_bytes()
    assert antes == depois[: len(antes)]  # nada reescrito antes foi alterado
    assert len(depois) > len(antes)
    caminho = tmp_path / "historico.csv"
    # inexistia linha extra: arquivo é o mesmo crescente
    assert caminho.read_text(encoding="utf-8").count("\n") == 3


def test_eventos_explicitos(tmp_path):
    h = HistoricoEstudo(tmp_path / "historico.csv")
    registra(h, evento="piloto", tempo_epoca="1.0", estado="inviavel",
             motivo="epoca piloto de 1,4 s > 1,2 s")
    registra(h, evento="controle", candidato="controle_media_rgb", seed="10",
             taxa="0.5", perda_validacao="0.31")
    eventos = {l["evento"] for l in h.linhas()}
    assert eventos == {"piloto", "controle"}


@pytest.fixture()
def historico_exemplo(tmp_path):
    h = HistoricoEstudo(tmp_path / "historico.csv")
    for seed in ("10", "20", "30"):
        for epoca, perda in (("1", "0.20"), ("2", "0.15")):
            registra(
                h,
                candidato="C0",
                seed=seed,
                taxa="0.5",
                evento="epoca",
                epoca=epoca,
                perda_validacao=perda,
                tempo_epoca="0.2",
                estado="concluido",
            )
    registra(
        h,
        candidato="controle_media_rgb",
        seed="20",
        taxa="0.5",
        evento="controle",
        perda_validacao="0.40",
        tempo_epoca="0.05",
    )
    registra(
        h,
        evento="checkpoint",
        execucao="exec_C0_seed10_taxa05",
        estado="melhor",
        motivo="sha256=ab9ade1b;epoca=2",
        tempo_epoca="0.01",
    )
    registra(
        h,
        evento="checkpoint",
        execucao="exec_C0_seed10_taxa05",
        estado="final",
        motivo="sha256=cd77;epoca=2",
        tempo_epoca="0.01",
    )
    registra(
        h,
        candidato="C2",
        taxa="0.75",
        evento="selecao",
        estado="vencedor",
        tempo_epoca="0.02",
    )
    return h


def test_resumo_derivado(historico_exemplo):
    r = resumo(historico_exemplo)
    # tempo total	assertEquals soma de todos os tempo_epoca do arquivo
    total = 0.2 * 6 + 0.05 + 0.01 + 0.01 + 0.02
    assert abs(r["tempo_total"] - total) < 1e-9
    # mediana por seed entre as três seeds: últimas épocas (0.15)
    medias = r["medias_seed"]["C0"]["0.5"]
    assert set(medias) == {"10", "20", "30"}
    for seed, info in medias.items():
        assert info["perda_validacao"] == 0.15
        assert info["epocas"] == 2
    # checkpoints melhor e final por execução com hash e época
    cp = r["checkpoints"]["exec_C0_seed10_taxa05"]
    assert cp["melhor"] == {"sha256": "ab9ade1b", "epoca": "2"}
    assert cp["final"] == {"sha256": "cd77", "epoca": "2"}
    # controles por seed
    assert r["controles"] == [
        {"candidato": "controle_media_rgb", "seed": "20",
         "taxa": "0.5", "mse": "0.40"}
    ]
    # decisões completas da seleção
    assert r["decisoes"] == [{"candidato": "C2", "taxa": "0.75",
                              "estado": "vencedor"}]


def test_decodificar_motivo():
    assert decodificar_motivo("sha256=ab;epoca=7") == {"sha256": "ab",
                                                       "epoca": "7"}
    with pytest.raises(ValueError):
        decodificar_motivo("texto sem pares")


def test_registrar_rejeita_campos_fora_do_esquema(tmp_path):
    h = HistoricoEstudo(tmp_path / "historico.csv")
    with pytest.raises(ValueError, match="fora do esquema"):
        h.registrar(execucao="x", campo_inexistente="y")
