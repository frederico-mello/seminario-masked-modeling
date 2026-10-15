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


def test_estudo_arquivos_no_pacote():
    do_estudo = [
        caminho for caminho in montar_zip.OBRIGATORIOS
        if caminho.startswith("resultados/estudo-melhorar-reconstrucoes-mae/")
            or caminho.startswith("openspec/changes/melhorar-reconstrucoes-mae/")
    ]
    exigidos = [
        "resultados/estudo-melhorar-reconstrucoes-mae/manifesto.json",
        "resultados/estudo-melhorar-reconstrucoes-mae/historico.csv",
        "resultados/estudo-melhorar-reconstrucoes-mae/contador.jsonl",
        "resultados/estudo-melhorar-reconstrucoes-mae/resumo.json",
        "resultados/estudo-melhorar-reconstrucoes-mae/figuras/curvas_validacao.png",
        "resultados/estudo-melhorar-reconstrucoes-mae/figuras/melhores_validacao.png",
        "resultados/estudo-melhorar-reconstrucoes-mae/figuras/avaliacao_final.png",
        "resultados/estudo-melhorar-reconstrucoes-mae/ficha-visual/ficha_50.png",
        "resultados/estudo-melhorar-reconstrucoes-mae/ficha-visual/ficha_75.png",
        "resultados/estudo-melhorar-reconstrucoes-mae/ficha-visual/ficha_visual.json",
        "openspec/changes/melhorar-reconstrucoes-mae/apresentacao/ficha-rotulos.json",
        "openspec/changes/melhorar-reconstrucoes-mae/relatorio-fase-b.md",
    ]
    for exigido in exigidos:
        assert exigido in montar_zip.OBRIGATORIOS
        assert exigido in do_estudo
        assert (RAIZ / exigido).exists(), f"artefato do estudo ausente: {exigido}"


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
        assert nomes == set(montar_zip.OBRIGATORIOS.values())
        for origem, destino in montar_zip.OBRIGATORIOS.items():
            assert z.read(destino) == (RAIZ / origem).read_bytes()
        # conferencia de cada md5 registrado
        for nome, md5_esperado in registro_dados.items():
            conteudo = z.read(nome)
            import hashlib

            assert hashlib.md5(conteudo).hexdigest() == md5_esperado
        # exclusões
        for nome in nomes:
            baixo = nome.lower()
            assert "cifar-10-python" not in baixo
            assert "checkpoints" not in Path(baixo).parts
            assert Path(baixo).suffix not in (".pt", ".pth")
            assert not baixo.startswith("test")
            assert "equivale" not in baixo
            if nome.endswith(".py") or nome.endswith(".ipynb"):
                texto = z.read(nome).decode()
                # nenhum import do oráculo no pacote
                for linha in texto.splitlines():
                    assert not linha.strip().startswith(
                        ("import vit_pytorch", "from vit_pytorch")
                    ), f"oráculo importado em {nome}"

def test_pacote_inclui_fontes_e_documentos_para_leitura_e_consolidacao():
    fontes = list((RAIZ / 'codigo').glob('estudo_*.py'))
    fontes += [RAIZ / 'codigo/__init__.py', RAIZ / 'codigo/configuracao_estudo.py',
               RAIZ / 'codigo/configuracao_estudo_c0_v2.py']
    for fonte in fontes:
        assert str(fonte.relative_to(RAIZ)) in montar_zip.OBRIGATORIOS
    destinos = set(montar_zip.OBRIGATORIOS.values())
    base = 'openspec/changes/melhorar-reconstrucoes-mae/'
    for documento in ['notas-finais.md', 'retificacao-validacao.md',
                      'retificacao-validacao.json', 'relatorio-fase-b.md']:
        assert base + documento in destinos
    for caminho in ['scripts/retificar_validacao.py', 'scripts/gerar_relatorio_fase_b.py',
                    'resultados/estudo-melhorar-reconstrucoes-mae/estado.json',
                    'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/estado.json',
                    'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/relatorio-c0-v2.md']:
        assert caminho in destinos
    assert montar_zip.OBRIGATORIOS[base + 'apresentacao/estado-v1.json'].endswith('/estado.json')
