from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo.estudo_orcamento import ContadorOrcamento


def contador(tmp_path, nome: str = "orcamento.jsonl") -> ContadorOrcamento:
    return ContadorOrcamento(tmp_path / nome)


def test_envelopes_por_candidato(tmp_path):
    c = contador(tmp_path)
    ok, _ = c.pode_iniciar("C0", "piloto", 2.0)
    assert ok
    c.consumir("C0", "piloto", 2.0, ts="2026-10-15T00:00:00")
    ok2, motivo = c.pode_iniciar("C0", "piloto", 0.1)
    assert not ok2
    assert "piloto" in motivo
    c.consumir("C0", "treino_por_seed_taxa", 24.0, chave=(10, 0.5))
    c.consumir("C0", "consolidacao", 2.0)
    c.consumir("C0", "avaliacao", 2.0)
    ok3, motivo = c.pode_iniciar("C0", "treino_por_seed_taxa", 0.1, chave=(11, 0.5))
    assert not ok3 and "envelope de 30 minutos" in motivo


def test_envelope_por_seed_taxa_de_4_minutos(tmp_path):
    c = contador(tmp_path)
    chave = (10, 0.5)
    assert c.pode_iniciar("C1", "treino_por_seed_taxa", 4.0, chave=chave)[0]
    c.consumir("C1", "treino_por_seed_taxa", 4.0, chave=chave)
    ok, motivo = c.pode_iniciar("C1", "treino_por_seed_taxa", 4.0, chave=chave)
    assert not ok and "treino_por_seed_taxa" in motivo
    # outra seed continua com saldo
    assert c.pode_iniciar("C1", "treino_por_seed_taxa", 4.0, chave=(10, 0.75))[0]
    assert c.pode_iniciar("C1", "treino_por_seed_taxa", 4.0, chave=(20, 0.5))[0]


def test_epoca_maior_que_o_envelope_e_recusada_antes_de_iniciar(tmp_path):
    c = contador(tmp_path)
    ok, motivo = c.pode_iniciar("C0", "treino_por_seed_taxa", 4.5, chave=(10, 0.5))
    assert not ok
    assert "treino_por_seed_taxa" in motivo
    # guard durante a época: mensuração maior que o previsto cruza o saldo e
    # o consumo é registrado como realidade; a próxima época não começa
    c.consumir("C0", "treino_por_seed_taxa", 4.0, chave=(10, 0.5))
    assert not c.pode_iniciar("C0", "treino_por_seed_taxa", 0.1, chave=(10, 0.5))[0]


def test_teto_global_de_90_minutos(tmp_path):
    c = contador(tmp_path)
    for candidato in ("C1", "C2"):
        # 2 de piloto, 24 de treino, 2 de consolidação e 2 de avaliação:
        # o envelope de 30 minutos chega ao limite exato
        assert c.pode_iniciar(candidato, "piloto", 2.0)[0]
        c.consumir(candidato, "piloto", 2.0)
        for i in range(6):
            chave = (i + 1, 0.5)
            assert c.pode_iniciar(
                candidato, "treino_por_seed_taxa", 4.0, chave=chave
            )[0]
            c.consumir(candidato, "treino_por_seed_taxa", 4.0, chave=chave)
        assert c.pode_iniciar(candidato, "consolidacao", 2.0)[0]
        c.consumir(candidato, "consolidacao", 2.0)
        assert c.pode_iniciar(candidato, "avaliacao", 2.0)[0]
        c.consumir(candidato, "avaliacao", 2.0)
        assert not c.pode_iniciar(candidato, "consolidacao", 0.1)[0]
    assert c.total_principal == 60.0
    # C0 gasta 24 de treino e 6 de avaliação final: global em 90
    for i in range(6):
        chave = (i + 1, 0.5)
        assert c.pode_iniciar("C0", "treino_por_seed_taxa", 4.0, chave=chave)[0]
        c.consumir("C0", "treino_por_seed_taxa", 4.0, chave=chave)
    ok, _ = c.pode_iniciar("C0", "avaliacao_final", 6.0)
    assert ok
    c.consumir("C0", "avaliacao_final", 6.0)
    assert c.total_principal == 90.0
    ok, motivo = c.pode_iniciar("C0", "avaliacao_final", 0.1)
    assert not ok and "6" in motivo
    # com o global em 90 nenhuma atividade principal pode começar: C0
    # chega a 30 (24 de treino + 6 de avaliação final) e o candidato
    # também fica sem saldo; qualquer pedido reinicia a interrupção
    ok_global, motivo_global = c.pode_iniciar("C0", "consolidacao", 0.1)
    assert not ok_global and "esgot" in motivo_global
    # não é permitido continuar depois do teto: nada entra
    antes = c.total_principal
    assert not c.pode_iniciar("C1", "avaliacao_final", 0.1)[0]
    c2 = contador(tmp_path)
    assert c2.total_principal == antes


def test_reserva_protegida_e_c3_ela_nunca_usa(tmp_path):
    c = contador(tmp_path)
    ok, motivo = c.pode_iniciar("C3", "repeticao", 1.0, usar_reserva=True)
    assert not ok and "C3" in motivo and "reserva" in motivo
    # categorias principais não acessam a reserva
    ok2, motivo2 = c.pode_iniciar("C0", "treino_por_seed_taxa", 1.0, chave=(10, 0.5), usar_reserva=True)
    assert not ok2 and "repet" in motivo2
    # repetição justificada de outro candidato gasta só a reserva
    ok3, _ = c.pode_iniciar("C1", "repeticao", 3.0, usar_reserva=True)
    assert ok3
    c.consumir("C1", "repeticao", 3.0, usar_reserva=True)
    assert c.total_reserva == 3.0
    assert c.total_principal == 0.0
    ok4, motivo4 = c.pode_iniciar("C2", "repeticao", 28.0, usar_reserva=True)
    assert not ok4 and "reserva insuficiente" in motivo4


def test_avaliacao_final_tem_teto_agregado_de_6_minutos(tmp_path):
    c = contador(tmp_path)
    assert c.pode_iniciar("C0", "avaliacao_final", 6.0)[0]
    c.consumir("C0", "avaliacao_final", 6.0)
    ok, motivo = c.pode_iniciar("C1", "avaliacao_final", 0.1)
    assert not ok
    assert "avaliacao_final" in motivo


def test_contador_monotono_e_persistido(tmp_path):
    c = contador(tmp_path)
    c.consumir("C0", "piloto", 2.0)
    antes = c.total_principal
    c.consumir("C0", "consolidacao", 2.0)
    assert c.total_principal == antes + 2.0
    c2 = ContadorOrcamento(tmp_path / "orcamento.jsonl")
    assert c2.total_principal == 4.0  # retomada: nada zerado
    c2.consumir("C1", "piloto", 2.0)
    assert json.loads(
        (tmp_path / "orcamento.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )["minutos"] == 2.0
    linhas = (tmp_path / "orcamento.jsonl").read_text(encoding="utf-8").splitlines()
    totals = [json.loads(l)["total_principal"] for l in linhas]
    assert totals == sorted(totals)  # monotono ao longo do arquivo


def test_retomada_mantem_identidade_e_consumo(tmp_path):
    c = contador(tmp_path, "execucao_a.jsonl")
    c.consumir("C0", "treino_por_seed_taxa", 1.5, chave=(10, 0.5))
    c2 = ContadorOrcamento(tmp_path / "execucao_a.jsonl")
    ok, motivo = c2.pode_iniciar("C0", "treino_por_seed_taxa", 3.0, chave=(10, 0.5))
    assert not ok  # mesma identidade consome o mesmo saldo
    ok2, _ = c2.pode_iniciar("C0", "treino_por_seed_taxa", 2.5, chave=(10, 0.5))
    assert ok2  # saldo restante do envelope de 4: 2,5
    c2.consumir("C0", "treino_por_seed_taxa", 2.5, chave=(10, 0.5))
    assert ContadorOrcamento(tmp_path / "execucao_a.jsonl").total_principal == 4.0


def test_campos_do_registro(tmp_path):
    c = contador(tmp_path)
    antes = c.pode_iniciar("C2", "piloto", 2.0)
    assert antes[0]
    c.consumir("C2", "piloto", 2.0, chave=None, ts="t0", motivo="piloto 75")
    linha = json.loads((tmp_path / "orcamento.jsonl").read_text(encoding="utf-8").splitlines()[0])
    for campo in ("ts", "candidato", "categoria", "minutos", "total_principal", "estado", "motivo", "chave", "usar_reserva"):
        assert campo in linha
    assert linha["candidato"] == "C2"
    assert linha["minutos"] == 2.0


def test_categoria_desconhecida_e_minutos_negativos(tmp_path):
    c = contador(tmp_path)
    ok, motivo = c.pode_iniciar("C0", "voo_livre", 1.0)
    assert not ok and "desconhecida" in motivo
    with pytest.raises(ValueError):
        c.consumir("C0", "piloto", -1.0)
