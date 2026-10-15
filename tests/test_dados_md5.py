"""Verificação do caso de arquivo corrompido: md5 divergente deve falhar
antes de gerar o subset e o script deve terminar com erro."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from codigo.dados import md5_arquivo, verificar_md5


def test_md5_divergente_rejeitado(tmp_path):
    import hashlib

    esperado = "c58f30108f718f92721af3b95e74349a"
    arquivo = RAIZ / "dados" / "cifar10_raw" / "cifar-10-python.tar.gz"
    if not arquivo.exists():
        # ramo sem arquivo bruto: arquivo sintetico com md5 divergente do
        # esperado exercita a mesma funcao verificar_md5 e a mesma mensagem
        # de erro que o fluxo real (md5 obtido e md5 esperado)
        sintetico = tmp_path / "cifar-10-python.tar.gz"
        conteudo = b"conteudo sintetico de teste"
        sintetico.write_bytes(conteudo)
        try:
            verificar_md5(sintetico)
        except ValueError as e:
            msg = str(e)
            md5_obtido = hashlib.md5(conteudo).hexdigest()
            assert "md5 divergente" in msg
            assert f"esperado {esperado}" in msg
            assert f"obtido {md5_obtido}" in msg
            assert md5_obtido in msg
            assert md5_obtido != esperado
        else:
            raise AssertionError("aceitou arquivo com md5 divergente")
    else:
        corrompido = tmp_path / "cifar-10-python.tar.gz"
        bytes_orig = bytearray(arquivo.read_bytes())
        for i, original in enumerate(reversed(range(len(bytes_orig)))):
            if bytes_orig[i] != 0:
                bytes_orig[i] = (bytes_orig[i] + 1) % 256
                break
        corrompido.write_bytes(bytes(bytes_orig))
        try:
            verificar_md5(corrompido)
        except ValueError as e:
            assert "md5 divergente" in str(e)
        else:
            raise AssertionError("aceitou arquivo corrompido")


def test_script_falha_com_md5_errado_e_nao_gera_subset(tmp_path):
    import hashlib

    esperado = "c58f30108f718f92721af3b95e74349a"
    arquivo = RAIZ / "dados" / "cifar10_raw" / "cifar-10-python.tar.gz"
    raiz_corrompida = tmp_path / "raw"
    raiz_corrompida.mkdir()
    corrompido = raiz_corrompida / "cifar-10-python.tar.gz"
    if not arquivo.exists():
        # ramo sem arquivo bruto: arquivo sintetico com md5 divergente
        # exercita o mesmo caminho do script (verificar_md5 antes do subset)
        conteudo = b"conteudo sintetico divergente do CIFAR-10"
        corrompido.write_bytes(conteudo)
        md5_obtido = hashlib.md5(conteudo).hexdigest()
    else:
        bytes_orig = bytearray(arquivo.read_bytes())
        for i in range(len(bytes_orig)):
            if bytes_orig[i] != 0:
                bytes_orig[i] = (bytes_orig[i] + 64) % 256
                break
        corrompido.write_bytes(bytes(bytes_orig))
        md5_obtido = hashlib.md5(corrompido.read_bytes()).hexdigest()

    processo = subprocess.run(
        [
            sys.executable,
            str(RAIZ / "codigo" / "preparar_dados.py"),
            "--raiz",
            str(raiz_corrompida),
            "--saida",
            str(tmp_path / "subset"),
            "--sem-download",
        ],
        capture_output=True,
        text=True,
    )
    assert processo.returncode != 0
    assert "md5 divergente" in processo.stderr
    assert f"esperado {esperado}" in processo.stderr
    assert f"obtido {md5_obtido}" in processo.stderr
    assert not (tmp_path / "subset" / "subset.npz").exists()
    assert not list((tmp_path / "subset").glob("*")) if (tmp_path / "subset").exists() else True