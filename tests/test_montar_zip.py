from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.montar_zip as montar_zip
from scripts.montar_zip import RAIZ, conferir_obrigatorios, gravar_zip


def test_arquivo_ausente_falha_sem_gravar_zip(tmp_path, monkeypatch):
    fake = {"resultados/inexistente.csv": "resultados/inexistente.csv"}
    monkeypatch.setattr(montar_zip, "ZIP_ALVO", tmp_path / "saida.zip")
    monkeypatch.setattr(montar_zip, "conferir_obrigatorios", lambda: fake)
    antes = sorted(p.name for p in tmp_path.iterdir())
    with pytest.raises(FileNotFoundError) as erro:
        montar_zip.gravar_zip(montar_zip.conferir_obrigatorios())
    assert "inexistente.csv" in str(erro.value)
    depois = sorted(p.name for p in tmp_path.iterdir())
    assert "saida.zip" not in depois  # zip final nao gravado


def test_conteudo_proibido_levanta_erro(tmp_path, monkeypatch):
    monkeypatch.setattr(montar_zip, "ZIP_ALVO", tmp_path / "saida.zip")
    arquivo = tmp_path / "dummy.txt"
    arquivo.write_text("x")
    with pytest.raises(RuntimeError):
        gravar_zip({"cifar-10-python.tar.gz": "cifar-10-python.tar.gz"})


def test_zip_conteudo_e_md5():
    alvo = RAIZ / "seminario_masked_modeling.zip"
    registro = RAIZ / "scripts" / "md5_pacote.csv"
    if not alvo.exists():
        montar_zip.conferir_obrigatorios()
        montar_zip.gravar_zip(dict(montar_zip.OBRIGATORIOS))
    assert alvo.exists()
    assert registro.exists()

    esperado = {}
    import csv

    registro_dados = {
        l["arquivo"]: l["md5"]
        for l in csv.DictReader(open(registro))
    }
    with zipfile.ZipFile(alvo) as z:
        nomes = set(z.namelist())
        assert nomes == set(registro_dados)
        # conferencia de cada md5 registrado
        for nome, md5_esperado in registro_dados.items():
            conteudo = z.read(nome)
            import hashlib

            assert hashlib.md5(conteudo).hexdigest() == md5_esperado
        # exclusões
        for nome in nomes:
            baixo = nome.lower()
            assert "cifar-10-python" not in baixo
            assert "checkpoint" not in baixo
            assert not baixo.startswith("test")
            assert "equivale" not in baixo
            if nome.endswith(".py") or nome.endswith(".ipynb"):
                texto = z.read(nome).decode()
                # nenhum import do oráculo no pacote
                for linha in texto.splitlines():
                    assert not linha.strip().startswith(
                        ("import vit_pytorch", "from vit_pytorch")
                    ), f"oráculo importado em {nome}"