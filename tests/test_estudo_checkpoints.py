from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from codigo import estudo_checkpoints as eck


def test_melhor_validacao_e_final_separados():
    rastreio = eck.RastreioCheckpoint()
    rastreio.marcar(1, 1.0)
    rastreio.marcar(2, 0.9)
    rastreio.marcar(3, 0.95)
    rastreio.marcar(4, 0.9)
    # melhor: primeira época com 0.9 (a 2); a 4 empata e não substitui
    assert rastreio.melhor.epoca == 2
    assert rastreio.melhor.perda_validacao == 0.9
    # final: última época concluída
    assert rastreio.final.epoca == 4
    markador = rastreio.copiar()
    assert markador.epoca_melhor == 2 and markador.epoca_final == 4


def test_empate_mantem_primeira_epoca():
    rastreio = eck.RastreioCheckpoint()
    rastreio.marcar(1, 1.0)
    rastreio.marcar(2, 1.0)
    rastreio.marcar(3, 1.0)
    assert rastreio.melhor.epoca == 1
    assert rastreio.final.epoca == 3


def test_menor_perda_substitui_apenas_estritamente():
    rastreio = eck.RastreioCheckpoint()
    rastreio.marcar(10, 0.5)
    rastreio.marcar(11, 0.5)  # empate: mantém a 10
    assert rastreio.melhor.epoca == 10
    rastreio.marcar(12, 0.4999999)
    assert rastreio.melhor.epoca == 12
    rastreio.marcar(13, 0.6)
    assert rastreio.melhor.epoca == 12


def test_interrupcao_nao_toca_checkpoints():
    rastreio = eck.RastreioCheckpoint()
    rastreio.marcar(1, 1.0)
    rastreio.marcar(2, 0.8)
    rastreio.marcar_interrupto(3, "teto de tempo por época")
    assert rastreio.melhor.epoca == 2
    assert rastreio.final.epoca == 2  # última época completa
    assert rastreio.motivo_interrupto == "teto de tempo por época"
    assert rastreio.epocas_concluidas == [1, 2]


def test_copia_imutavel_e_hash_e_epoca(tmp_path):
    origem = tmp_path / "modelo.pt"
    origem.write_bytes(b"estado-do-modelo-serializado v1")
    info = eck.copiar_imutavel(origem, tmp_path / "copias", "melhor", 7)
    assert info["epoca"] == 7
    assert info["sha256"] == eck.sha256_arquivo(origem)
    caminho = Path(info["caminho"])
    assert caminho.exists()
    assert caminho.stat().st_size == info["tamanho_bytes"]
    # cópia identica tem bytes iguais à origem
    assert caminho.read_bytes() == origem.read_bytes()
    # regravar com mesmo conteúdo e época é idempotente
    outra = eck.copiar_imutavel(origem, tmp_path / "copias", "melhor", 7)
    assert outra["caminho"] == info["caminho"]
    # época diferente gera destino diferente
    terceira = eck.copiar_imutavel(origem, tmp_path / "copias", "melhor", 8)
    assert terceira["caminho"] != info["caminho"]
    assert terceira["epoca"] == 8


def test_copia_imutavel_levando_os_bytes(tmp_path):
    origem = tmp_path / "modelo.pt"
    origem.write_bytes(b"conteudo-final")
    info = eck.copiar_imutavel(origem, tmp_path / "copias", "final", 12)
    assert info["sha256"] == eck.sha256_arquivo(origem)
    # conteúdo alterado gera outro arquivo com outro hash
    origem.write_bytes(b"conteudo-alterado")
    outro = eck.copiar_imutavel(origem, tmp_path / "copias", "final", 12)
    assert outro["sha256"] != info["sha256"]
    assert outro["caminho"] != info["caminho"]
    # os arquivos agora coexistem (cada um com a época e hash próprios)
    assert Path(info["caminho"]).read_bytes() == b"conteudo-final"
    assert Path(outro["caminho"]).read_bytes() == b"conteudo-alterado"


def test_copia_nunca_sobrescreve_conteudo_divergente(tmp_path):
    origem = tmp_path / "modelo.pt"
    origem.write_bytes(b"conteudo-1")
    info = eck.copiar_imutavel(origem, tmp_path / "copias", "melhor", 3)
    destino = Path(info["caminho"])
    destino.chmod(0o644)
    destino.write_bytes(b"manipulado")
    destino.chmod(0o444)
    violado = destino.read_bytes()
    # destino com nome idêntico e conteúdo diverso nunca é sobrescrito
    with pytest.raises(FileExistsError, match="colis"):
        eck.copiar_imutavel(origem, tmp_path / "copias", "melhor", 3)
    # a função nada tocou: violação permanece como estava antes dela
    assert destino.read_bytes() == violado


def test_copia_fica_somente_leitura(tmp_path):
    origem = tmp_path / "modelo.pt"
    origem.write_bytes(b"x")
    copia = Path(
        eck.copiar_imutavel(origem, tmp_path / "copias", "melhor", 1)["caminho"]
    )
    assert not (copia.stat().st_mode & 0o222)
    import os

    os.chmod(copia, 0o644)  # limpeza para o pytest manter o tmp_path
