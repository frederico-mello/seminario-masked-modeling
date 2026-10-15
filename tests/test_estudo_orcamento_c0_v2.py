from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo.estudo_orcamento_c0_v2 import (
    NS_POR_SEGUNDO,
    ContadorReservaC0V2,
    ErroOrcamento,
    minutos_v1_em_ns,
    piloto_candidato_viavel,
    piloto_viavel,
    verificar_prazo,
)
from codigo.estudo_execucao_c0_v2 import _marcar_inicio_unico


def contador(tmp_path, **kwargs):
    argumentos = {
        "v1_principal_ns": 0,
        "v1_reserva_ns": 0,
        "hash_referencia_v1": "sha-v1",
    }
    argumentos.update(kwargs)
    return ContadorReservaC0V2(
        tmp_path / "contador-v2.jsonl",
        **argumentos,
    )


def test_limiar_piloto_aplica_comparacao_exata():
    limite = int(1.25 * NS_POR_SEGUNDO)
    assert piloto_viavel(limite)
    assert not piloto_viavel(limite + 1)


def test_qualquer_taxa_inviavel_impede_treino_completo_de_c0():
    assert piloto_candidato_viavel(
        {"0.5": {"viavel": True}, "0.75": {"viavel": True}},
        (0.5, 0.75),
    )
    assert not piloto_candidato_viavel(
        {"0.5": {"viavel": False}, "0.75": {"viavel": True}},
        (0.5, 0.75),
    )
    assert not piloto_candidato_viavel(
        {"0.5": {"viavel": True}},
        (0.5, 0.75),
    )


def test_guarda_interrompe_no_instante_do_teto_sem_arredondar():
    verificar_prazo(999, 1000)
    with pytest.raises(ErroOrcamento, match="monotônico"):
        verificar_prazo(1000, 1000)
    with pytest.raises(ErroOrcamento, match="monotônico"):
        verificar_prazo(1001, 1000)


def test_limite_respeita_reserva_global_e_protecao_em_nanossegundos(tmp_path):
    c = contador(
        tmp_path,
        v1_principal_ns=7_199 * NS_POR_SEGUNDO,
        teto_global_ns=7_200 * NS_POR_SEGUNDO,
    )
    assert c.limite_disponivel_ns(240 * NS_POR_SEGUNDO) == NS_POR_SEGUNDO
    assert c.limite_disponivel_ns(240 * NS_POR_SEGUNDO, proteger_ns=1) == (
        NS_POR_SEGUNDO - 1
    )
    c2 = contador(
        tmp_path / "reserva",
        teto_reserva_ns=10,
        teto_global_ns=100,
    )
    assert c2.limite_disponivel_ns(20) == 10
    assert c2.limite_disponivel_ns(20, proteger_ns=10) == 0


def test_contador_v2_append_only_monotono_e_recuperavel(tmp_path):
    c = contador(tmp_path)
    primeiro = c.registrar(
        evento="piloto", duracao_ns=1_250_000_000, estado="concluido"
    )
    segundo = c.registrar(
        evento="treino", duracao_ns=240 * NS_POR_SEGUNDO, estado="incompleto"
    )
    assert primeiro["total_v2_ns"] == 1_250_000_000
    assert segundo["total_v2_ns"] == 241_250_000_000
    recarregado = ContadorReservaC0V2(
        tmp_path / "contador-v2.jsonl",
        v1_principal_ns=0,
        v1_reserva_ns=0,
        hash_referencia_v1="sha-v1",
    )
    assert recarregado.total_v2_ns == 241_250_000_000
    assert recarregado.gasto_evento_ns("treino") == 240 * NS_POR_SEGUNDO


def test_v1_e_contado_sem_modificacao_e_arredondamento_para_baixo(tmp_path):
    caminho = tmp_path / "contador-v1.jsonl"
    caminho.write_text(
        json.dumps({"minutos": 0.000000000000001, "usar_reserva": False})
        + "\n"
        + json.dumps({"minutos": 0.5, "usar_reserva": True})
        + "\n",
        encoding="utf-8",
    )
    antes = caminho.read_bytes()
    principal, reserva, total = minutos_v1_em_ns(caminho)
    assert principal == 1
    assert reserva == 30 * NS_POR_SEGUNDO
    assert total == principal + reserva
    assert caminho.read_bytes() == antes


def test_manifesto_v2_recusa_hash_v1_diferente_no_contador(tmp_path):
    c = contador(tmp_path)
    c.registrar(evento="piloto", duracao_ns=1, estado="concluido")
    with pytest.raises(ValueError, match="hash de referência v1"):
        ContadorReservaC0V2(
            tmp_path / "contador-v2.jsonl",
            v1_principal_ns=0,
            v1_reserva_ns=0,
            hash_referencia_v1="outro-sha",
        )


def test_executor_v2_nao_reinicia_piloto_ou_treino_parcial():
    estado = {}
    _marcar_inicio_unico(estado)
    assert estado["execucao_iniciada"] is True
    with pytest.raises(RuntimeError, match="não serão repetidos"):
        _marcar_inicio_unico(estado)


@pytest.mark.parametrize('teste_primeiro', [False, True])
def test_referencias_controles_somente_validacao_em_ambas_ordens(tmp_path, monkeypatch, teste_primeiro):
    import csv
    import codigo.estudo_execucao_c0_v2 as executor
    campos = ['evento', 'candidato', 'seed', 'taxa', 'estado', 'perda_validacao', 'ssim_validacao']
    validacao = [dict(zip(campos, ['controle', nome, '10', taxa, 'validacao', '.05', '.355630']))
                 for nome in ['controle_media_rgb', 'controle_interpolacao'] for taxa in ['0.5', '0.75']]
    teste = [dict(r, estado='teste', perda_validacao='.9', ssim_validacao='.363144') for r in validacao]
    with (tmp_path / 'historico.csv').open('w', newline='') as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(teste + validacao if teste_primeiro else validacao + teste)
    monkeypatch.setattr(executor, 'DIR_V1', tmp_path)
    refs = executor._resumo_refs_v1()
    for taxa in ['0.5', '0.75']:
        for nome in ['controle_media_rgb', 'controle_interpolacao']:
            assert refs['controles'][taxa][nome] == {'mse': .05, 'ssim': .355630}


def test_referencias_reais_separam_controles_e_preservam_seeds():
    from codigo.estudo_execucao_c0_v2 import _resumo_refs_v1, _mediana_metricas
    refs = _resumo_refs_v1()
    rgb = refs['controles']['0.75']['controle_media_rgb']['ssim']
    assert rgb == .355630
    assert _mediana_metricas(refs['candidatos']['C1']['0.75'], 'melhor')['ssim_mediano'] == .362957
    assert _mediana_metricas(refs['candidatos']['C2']['0.5'], 'melhor')['ssim_mediano'] == .365044
    assert refs['candidatos']['C1']['0.75']['10']['epocas'] == 185
    assert set(refs['candidatos']['C1']['0.75']) == {'10', '20', '30'}
