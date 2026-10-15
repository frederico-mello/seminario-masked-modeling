"""Executor isolado da retomada C0 v2.

Não reutiliza caminhos de gravação da v1. A avaliação acessa somente treino e
validação, e o processo filho pode ser encerrado pelo supervisor no teto.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from codigo import configuracao_estudo_c0_v2 as cfg
from codigo.estudo_orcamento_c0_v2 import (
    NS_POR_SEGUNDO,
    ContadorReservaC0V2,
    ErroOrcamento,
    minutos_v1_em_ns,
    piloto_candidato_viavel,
    piloto_viavel,
    sha256_arquivo,
    verificar_prazo,
)


RAIZ = Path(__file__).resolve().parent.parent
DIR_V2 = RAIZ / cfg.DIR_RESULTADOS_RELATIVO
DIR_V1 = RAIZ / cfg.DIR_RESULTADOS_V1_RELATIVO
ARQ_MANIFESTO = DIR_V2 / "manifesto.json"
ARQ_CONTADOR = DIR_V2 / "contador.jsonl"
ARQ_HISTORICO = DIR_V2 / "historico.jsonl"
ARQ_ESTADO = DIR_V2 / "estado.json"
ARQ_RESUMO = DIR_V2 / "resumo.json"
ARQ_RELATORIO = DIR_V2 / "relatorio-c0-v2.md"
ARQ_INDICES = RAIZ / "dados" / "cifar10_subset" / "indices.csv"
ARQ_DADOS = RAIZ / "dados" / "cifar10_subset" / "subset.npz"
ARQ_LOCK = RAIZ / "uv.lock"
ARQ_CONTADOR_V1 = DIR_V1 / "contador.jsonl"
MARGEM_FINALIZACAO_NS = 5 * NS_POR_SEGUNDO
PROTEGER_CONSOLIDACAO_NS = 2 * 60 * NS_POR_SEGUNDO


def _json_canonico(valor: dict) -> bytes:
    return json.dumps(
        valor, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _hash_json(valor: dict) -> str:
    return hashlib.sha256(_json_canonico(valor)).hexdigest()


def _agora() -> str:
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def _gravar_json_atomico(caminho: Path, valor: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp")
    conteudo = json.dumps(
        valor, ensure_ascii=False, sort_keys=True, indent=2
    ).encode("utf-8") + b"\n"
    with temporario.open("wb") as arquivo:
        arquivo.write(conteudo)
        arquivo.flush()
        os.fsync(arquivo.fileno())
    os.replace(temporario, caminho)


def _fontes_python() -> list[Path]:
    caminhos: list[Path] = []
    for diretorio in ("codigo", "scripts", "tests"):
        raiz = RAIZ / diretorio
        if raiz.exists():
            caminhos.extend(p for p in raiz.rglob("*.py") if p.is_file())
    return sorted(set(caminhos), key=lambda p: p.relative_to(RAIZ).as_posix())


def _inventario_fontes() -> dict:
    arquivos = {}
    digest = hashlib.sha256()
    for caminho in _fontes_python():
        relativo = caminho.relative_to(RAIZ).as_posix()
        sha = sha256_arquivo(caminho)
        arquivos[relativo] = sha
        digest.update(relativo.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha.encode("ascii"))
        digest.update(b"\n")
    return {"algoritmo": "sha256 por caminho relativo e conteúdo", "sha256": digest.hexdigest(), "arquivos": arquivos}


def _hash_resultados_v1() -> dict:
    if not DIR_V1.is_dir():
        raise FileNotFoundError(f"diretório v1 ausente: {DIR_V1}")
    arquivos = {}
    digest = hashlib.sha256()
    for caminho in sorted(p for p in DIR_V1.rglob("*") if p.is_file()):
        relativo = caminho.relative_to(RAIZ).as_posix()
        sha = sha256_arquivo(caminho)
        arquivos[relativo] = {"sha256": sha, "bytes": caminho.stat().st_size}
        digest.update(relativo.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha.encode("ascii"))
        digest.update(b"\n")
    return {"sha256_arvore": digest.hexdigest(), "arquivos": arquivos}


def _hash_indices_treino_validacao() -> str:
    digest = hashlib.sha256()
    with ARQ_INDICES.open(newline="", encoding="utf-8") as arquivo:
        for linha in csv.DictReader(arquivo):
            split = linha.get("split", "")
            if split not in ("treino", "validacao"):
                continue
            texto = "|".join(
                (split, linha.get("classe", ""), linha.get("indice_original", ""))
            )
            digest.update(texto.encode("utf-8") + b"\n")
    return digest.hexdigest()


def _hash_dados_treino_validacao() -> dict:
    import numpy as np

    hashes = {}
    with np.load(ARQ_DADOS, allow_pickle=False) as arquivo:
        for split in ("treino", "validacao"):
            array = arquivo[split]
            digest = hashlib.sha256()
            digest.update(str(array.dtype).encode("ascii"))
            digest.update(repr(tuple(array.shape)).encode("ascii"))
            digest.update(memoryview(array).cast("B"))
            hashes[split] = {
                "sha256": digest.hexdigest(),
                "dtype": str(array.dtype),
                "shape": list(array.shape),
            }
    return hashes


def _ambiente() -> dict:
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("sem GPU CUDA; a retomada C0 v2 não inicia")
    if torch.version.cuda is None or int(torch.version.cuda.split(".")[0]) < 13:
        raise RuntimeError(f"CUDA incompatível para a retomada: {torch.version.cuda}")
    return {
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "cuda": str(torch.version.cuda),
        "gpu": torch.cuda.get_device_name(torch.device("cuda")),
    }


def _referencias_v1() -> dict:
    principal_ns, reserva_ns, total_ns = minutos_v1_em_ns(ARQ_CONTADOR_V1)
    estado_v1 = json.loads((DIR_V1 / "estado.json").read_text(encoding="utf-8"))
    codigo_v1 = estado_v1.get("codigo_hash")
    if codigo_v1 != "e13ef0653e119b00":
        raise RuntimeError("hash de código v1 diverge do precheck congelado")
    return {
        "manifesto_sha256": sha256_arquivo(DIR_V1 / "manifesto.json"),
        "contador_sha256": sha256_arquivo(ARQ_CONTADOR_V1),
        "historico_sha256": sha256_arquivo(DIR_V1 / "historico.csv"),
        "resumo_sha256": sha256_arquivo(DIR_V1 / "resumo.json"),
        "estado_sha256": sha256_arquivo(DIR_V1 / "estado.json"),
        "codigo_hash_registrado": codigo_v1,
        "consumo_principal_ns": principal_ns,
        "reserva_consumida_ns": reserva_ns,
        "consumo_total_ns": total_ns,
        "resultados": _hash_resultados_v1(),
    }


def _ler_manifesto() -> tuple[dict, dict]:
    if not ARQ_MANIFESTO.exists():
        raise FileNotFoundError("manifesto C0 v2 ainda não foi congelado")
    manifesto = json.loads(ARQ_MANIFESTO.read_text(encoding="utf-8"))
    gravado = manifesto.pop("hash_manifesto_v2", None)
    if not gravado or gravado != _hash_json(manifesto):
        raise RuntimeError("hash do manifesto C0 v2 diverge")
    manifesto["hash_manifesto_v2"] = gravado
    return manifesto, manifesto["referencias_v1"]


def _verificar_congelamento() -> tuple[dict, ContadorReservaC0V2]:
    manifesto, refs_v1 = _ler_manifesto()
    if manifesto["hash_configuracao"] != cfg.hash_configuracao():
        raise RuntimeError("hash da configuração C0 v2 diverge do manifesto")
    if manifesto["fontes_python"]["sha256"] != _inventario_fontes()["sha256"]:
        raise RuntimeError("hash dos fontes Python diverge do manifesto; execução impedida")
    if manifesto["lockfile_sha256"] != sha256_arquivo(ARQ_LOCK):
        raise RuntimeError("hash do lockfile diverge do manifesto; execução impedida")
    if manifesto["indices_treino_validacao_sha256"] != _hash_indices_treino_validacao():
        raise RuntimeError("hash dos índices diverge do manifesto; execução impedida")
    if manifesto["dados_treino_validacao"] != _hash_dados_treino_validacao():
        raise RuntimeError("hash dos dados de treino ou validação diverge; execução impedida")
    if refs_v1 != _referencias_v1():
        raise RuntimeError("hash ou contador v1 diverge da referência congelada")
    return manifesto, ContadorReservaC0V2(
        ARQ_CONTADOR,
        v1_principal_ns=refs_v1["consumo_principal_ns"],
        v1_reserva_ns=refs_v1["reserva_consumida_ns"],
        hash_referencia_v1=refs_v1["resultados"]["sha256_arvore"],
    )


def congelar(inicio_ns: int | None = None) -> dict:
    """Congela as entradas depois dos checks obrigatórios e antes do piloto."""
    inicio_ns = time.monotonic_ns() if inicio_ns is None else int(inicio_ns)
    if DIR_V2.exists():
        raise FileExistsError(
            f"diretório v2 já existe; não será sobrescrito: {DIR_V2}"
        )
    ambiente = _ambiente()
    referencias = _referencias_v1()
    esperado_minutos = 41.06151396479642
    obtido_minutos = referencias["consumo_total_ns"] / (60 * NS_POR_SEGUNDO)
    if referencias["reserva_consumida_ns"] != 0:
        raise RuntimeError("reserva v1 diverge do precheck autorizado")
    if abs(obtido_minutos - esperado_minutos) > 0.000001:
        raise RuntimeError(
            f"consumo v1 diverge do precheck: {obtido_minutos:.12f} min"
        )
    fontes = _inventario_fontes()
    dados = _hash_dados_treino_validacao()
    manifesto = {
        "versao": cfg.VERSAO,
        "criado_em": _agora(),
        "configuracao": cfg.CONFIG,
        "hash_configuracao": cfg.hash_configuracao(),
        "fontes_python": fontes,
        "lockfile_sha256": sha256_arquivo(ARQ_LOCK),
        "indices_treino_validacao_sha256": _hash_indices_treino_validacao(),
        "dados_treino_validacao": dados,
        "referencias_v1": referencias,
        "ambiente": ambiente,
        "consulta_teste": False,
    }
    manifesto["hash_manifesto_v2"] = _hash_json(manifesto)
    DIR_V2.mkdir(parents=True)
    _gravar_json_atomico(ARQ_MANIFESTO, manifesto)
    estado = {
        "versao": cfg.VERSAO,
        "manifesto_congelado": True,
        "hash_manifesto_v2": manifesto["hash_manifesto_v2"],
        "hash_codigo": fontes["sha256"],
        "hash_configuracao": manifesto["hash_configuracao"],
        "hash_v1": referencias["resultados"]["sha256_arvore"],
        "pilotos": {},
        "treinos": {},
    }
    _gravar_json_atomico(ARQ_ESTADO, estado)
    contador = ContadorReservaC0V2(
        ARQ_CONTADOR,
        v1_principal_ns=referencias["consumo_principal_ns"],
        v1_reserva_ns=referencias["reserva_consumida_ns"],
        hash_referencia_v1=referencias["resultados"]["sha256_arvore"],
    )
    duracao = time.monotonic_ns() - inicio_ns
    contador.registrar(
        evento="preparacao_manifesto",
        duracao_ns=duracao,
        estado="concluido",
        motivo="hashes de código, lockfile, índices, dados e resultados v1 congelados",
        monotonic_inicio_ns=inicio_ns,
    )
    return manifesto


def _atomic_torch_save(payload: dict, caminho: Path) -> None:
    import torch

    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp")
    with temporario.open("wb") as arquivo:
        torch.save(payload, arquivo)
        arquivo.flush()
        os.fsync(arquivo.fileno())
    os.replace(temporario, caminho)


def _carregar_dados_treino_validacao() -> tuple[dict, dict]:
    import numpy as np
    from codigo.estudo_mascaras import COLUNAS_MAPA

    with np.load(ARQ_DADOS, allow_pickle=False) as arquivo:
        treino = arquivo["treino"].astype(np.float32) / 255.0
        validacao = arquivo["validacao"].astype(np.float32) / 255.0
    mapa: dict[str, list[int]] = {"treino": [], "validacao": []}
    with ARQ_INDICES.open(newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        if any(campo not in (leitor.fieldnames or []) for campo in COLUNAS_MAPA):
            raise ValueError("arquivo de índices sem colunas esperadas")
        for linha in leitor:
            nome = linha.get("split", "")
            if nome not in mapa:
                continue
            mapa[nome].append(int(linha["indice_original"]))
    if len(mapa["treino"]) != len(treino) or len(mapa["validacao"]) != len(validacao):
        raise RuntimeError("tamanho dos índices diverge dos arrays carregados")
    return (
        {"imagens": treino, "indices_originais": np.asarray(mapa["treino"], dtype=np.int64)},
        {"imagens": validacao, "indices_originais": np.asarray(mapa["validacao"], dtype=np.int64)},
    )


def _dispositivo_treino():
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("sem GPU CUDA; sem fallback para CPU")
    if torch.version.cuda is None or int(torch.version.cuda.split(".")[0]) < 13:
        raise RuntimeError(f"CUDA incompatível: {torch.version.cuda}")
    return torch.device("cuda")


def _novo_modelo(seed: int, dispositivo):
    import torch
    from codigo import estudo_candidatos as candidatos

    torch.manual_seed(seed)
    declaracao = candidatos.declaracoes()["C0"]
    modelo = candidatos.construir_modelo(declaracao, seed=seed).to(dispositivo)
    comum = cfg.CONFIG["comum"]
    otimizador = torch.optim.AdamW(
        modelo.parameters(),
        lr=comum["lr"],
        weight_decay=comum["weight_decay"],
        betas=(comum["beta1"], comum["beta2"]),
        eps=comum["epsilon_adam"],
    )
    torch.cuda.synchronize()
    return modelo, otimizador, declaracao


def _treinar_epoca(
    modelo,
    dados_treino: dict,
    dispositivo,
    seed: int,
    epoca: int,
    taxa: float,
    declaracao: dict,
    otimizador,
    ordem_rng,
    prazo_ns: int,
) -> float:
    import numpy as np
    import torch
    from codigo import estudo_mascaras as mascaras
    from codigo.estudo_candidatos import perda_candidato

    imagens = dados_treino["imagens"]
    ids = dados_treino["indices_originais"]
    ordem = ordem_rng.permutation(len(imagens))
    perdas: list[tuple[float, int]] = []
    batch = int(cfg.CONFIG["comum"]["batch"])
    modelo.train()
    for inicio in range(0, len(imagens), batch):
        verificar_prazo(time.monotonic_ns(), prazo_ns)
        indices_lote = ordem[inicio : inicio + batch]
        x = torch.from_numpy(
            imagens[indices_lote].transpose(0, 3, 1, 2)
        ).float().to(dispositivo)
        ocultos_np = mascaras.mascaras_lote(
            seed, epoca, ids[indices_lote], taxa
        )
        ocultos = torch.from_numpy(ocultos_np).long().to(dispositivo)
        saida = modelo(x, indices_mascarados=ocultos)
        perda = perda_candidato(
            declaracao, saida["predicao"], saida["patches"], ocultos
        )
        otimizador.zero_grad()
        perda.backward()
        otimizador.step()
        torch.cuda.synchronize()
        perdas.append((float(perda.detach()), len(indices_lote)))
        verificar_prazo(time.monotonic_ns(), prazo_ns)
    total = sum(peso for _, peso in perdas)
    return sum(valor * peso for valor, peso in perdas) / total


def _avaliar_regua(modelo, imagens, dispositivo, taxa: float, prazo_ns: int) -> tuple[float, float]:
    import torch
    from codigo import estudo_avaliacao as avaliacao

    regua = avaliacao.regua_validacao(len(imagens), taxa).to(dispositivo)
    mse_imagens = []
    ssim_imagens = []
    modelo.eval()
    with torch.no_grad():
        for inicio in range(0, len(imagens), 500):
            verificar_prazo(time.monotonic_ns(), prazo_ns)
            fim = min(inicio + 500, len(imagens))
            indices = regua[inicio:fim]
            x = torch.from_numpy(imagens[inicio:fim].transpose(0, 3, 1, 2)).float().to(dispositivo)
            saida = modelo(x, indices_mascarados=indices)
            predicao = saida["predicao"].clamp(0.0, 1.0).detach().cpu()
            alvos = saida["patches"].detach().cpu()
            indices_cpu = indices.cpu()
            mse_imagens.append(
                avaliacao.mse_regua(predicao, alvos, indices_cpu, por_imagem=True).double()
            )
            ssim_imagens.append(
                avaliacao.ssim_regua(predicao, alvos, indices_cpu, por_imagem=True).double()
            )
            torch.cuda.synchronize()
            verificar_prazo(time.monotonic_ns(), prazo_ns)
    return (
        float(torch.cat(mse_imagens).mean()),
        float(torch.cat(ssim_imagens).mean()),
    )


def _estado_cpu(modelo) -> dict:
    return {k: v.detach().cpu().clone() for k, v in modelo.state_dict().items()}


def executar_worker(tipo: str, seed: int, taxa: float, prazo_ns: int, pasta: Path) -> dict:
    """Roda exatamente um piloto ou uma execução de treino em processo filho."""
    import numpy as np
    import torch

    manifesto, _ = _ler_manifesto()
    if manifesto["fontes_python"]["sha256"] != _inventario_fontes()["sha256"]:
        raise RuntimeError("fontes alterados antes de iniciar o processo filho")
    dados_treino, dados_validacao = _carregar_dados_treino_validacao()
    dispositivo = _dispositivo_treino()
    modelo, otimizador, declaracao = _novo_modelo(seed, dispositivo)
    ordem_rng = np.random.default_rng(seed)
    pasta.mkdir(parents=True, exist_ok=True)
    if tipo == "piloto":
        ciclo_inicio = time.monotonic_ns()
        try:
            verificar_prazo(time.monotonic_ns(), prazo_ns)
            perda_treino = _treinar_epoca(
                modelo, dados_treino, dispositivo, seed, 1, taxa, declaracao,
                otimizador, ordem_rng, prazo_ns,
            )
            mse, ssim = _avaliar_regua(
                modelo, dados_validacao["imagens"], dispositivo, taxa, prazo_ns
            )
            arquivo_piloto = pasta / "piloto.pt"
            _atomic_torch_save(
                {"epoca": 1, "state_dict": _estado_cpu(modelo)}, arquivo_piloto
            )
            carregado = torch.load(
                arquivo_piloto, map_location="cpu", weights_only=False
            )
            if set(carregado["state_dict"]) != set(modelo.state_dict()):
                raise RuntimeError("checkpoint de piloto divergente")
        except ErroOrcamento as erro:
            resultado = {
                "tipo": tipo,
                "seed": seed,
                "taxa": taxa,
                "estado": "incompleto",
                "motivo": str(erro),
                "duracao_epoca_ns": None,
            }
            _gravar_json_atomico(pasta / "resultado.json", resultado)
            return resultado
        ciclo_ns = time.monotonic_ns() - ciclo_inicio
        resultado = {
            "tipo": tipo,
            "seed": seed,
            "taxa": taxa,
            "epoca": 1,
            "perda_treino": perda_treino,
            "mse_validacao": mse,
            "ssim_validacao": ssim,
            "duracao_epoca_ns": ciclo_ns,
            "checkpoint_sha256": sha256_arquivo(arquivo_piloto),
        }
        _gravar_json_atomico(pasta / "resultado.json", resultado)
        return resultado
    if tipo != "treino":
        raise ValueError(f"tipo de execução desconhecido: {tipo}")

    progresso = pasta / "progresso.pt"
    epoca = 0
    melhor = None
    estado_melhor = None
    estado_final = None
    motivo = "limite de tempo"
    estado = "interrompido"
    arquivo_eventos = pasta / "epocas.jsonl"
    if arquivo_eventos.exists():
        raise FileExistsError(f"execução v2 já iniciada e não será reiniciada: {pasta}")
    while epoca < cfg.EPOCAS_MAXIMAS:
        proxima = epoca + 1
        inicio_epoca = time.monotonic_ns()
        try:
            verificar_prazo(time.monotonic_ns(), prazo_ns)
            perda_treino = _treinar_epoca(
                modelo, dados_treino, dispositivo, seed, proxima, taxa,
                declaracao, otimizador, ordem_rng, prazo_ns,
            )
            mse, ssim = _avaliar_regua(
                modelo, dados_validacao["imagens"], dispositivo, taxa, prazo_ns
            )
        except ErroOrcamento as erro:
            estado, motivo = "interrompido", str(erro)
            break
        novo_estado = _estado_cpu(modelo)
        metricas = {
            "epoca": proxima,
            "mse_validacao": mse,
            "ssim_validacao": ssim,
        }
        if melhor is None or mse < melhor["mse_validacao"]:
            melhor = dict(metricas)
            estado_melhor = novo_estado
        estado_final = novo_estado
        epoca = proxima
        _atomic_torch_save(
            {
                "epoca": epoca,
                "estado_final": estado_final,
                "metricas_final": metricas,
                "estado_melhor": estado_melhor,
                "metricas_melhor": melhor,
                "perda_treino_final": perda_treino,
                "duracao_epoca_ns": time.monotonic_ns() - inicio_epoca,
            },
            progresso,
        )
        duracao_epoca = time.monotonic_ns() - inicio_epoca
        evento = {
            "execucao": f"C0|{seed}|{taxa}",
            "candidato": "C0",
            "seed": seed,
            "taxa": taxa,
            "evento": "epoca",
            **metricas,
            "perda_treino": perda_treino,
            "duracao_epoca_ns": duracao_epoca,
            "estado": "concluida",
        }
        with arquivo_eventos.open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(evento, ensure_ascii=False, sort_keys=True) + "\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        if epoca >= cfg.EPOCAS_MAXIMAS:
            estado, motivo = "completo", "200 épocas concluídas"
            break
        try:
            verificar_prazo(time.monotonic_ns(), prazo_ns)
        except ErroOrcamento as erro:
            estado, motivo = "interrompido", str(erro)
            break
        if manifesto["fontes_python"]["sha256"] != _inventario_fontes()["sha256"]:
            raise RuntimeError("fontes alterados durante a execução; treino interrompido")
    resultado = {
        "tipo": tipo,
        "seed": seed,
        "taxa": taxa,
        "estado": estado,
        "motivo": motivo,
        "epocas_concluidas": epoca,
        "progresso": str(progresso),
        "melhor": melhor,
        "final": {
            "epoca": epoca,
            "mse_validacao": None if not epoca else evento["mse_validacao"],
            "ssim_validacao": None if not epoca else evento["ssim_validacao"],
        },
    }
    _gravar_json_atomico(pasta / "resultado.json", resultado)
    return resultado


def _ler_estado() -> dict:
    if ARQ_ESTADO.exists():
        return json.loads(ARQ_ESTADO.read_text(encoding="utf-8"))
    return {}


def _salvar_estado(estado: dict) -> None:
    _gravar_json_atomico(ARQ_ESTADO, estado)


def _marcar_inicio_unico(estado: dict) -> None:
    """Impede que uma retomada parcial repita piloto ou treino já iniciado."""
    if estado.get("execucao_iniciada") or estado.get("execucao_finalizada"):
        raise RuntimeError("executor v2 já iniciado; pilotos e treinos não serão repetidos")
    estado["execucao_iniciada"] = True


def _append_jsonl(caminho: Path, linhas: list[dict]) -> None:
    if not linhas:
        return
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("a", encoding="utf-8") as arquivo:
        for linha in linhas:
            arquivo.write(json.dumps(linha, ensure_ascii=False, sort_keys=True) + "\n")
        arquivo.flush()
        os.fsync(arquivo.fileno())


def _ler_eventos_execucao(pasta: Path) -> list[dict]:
    caminho = pasta / "epocas.jsonl"
    if not caminho.exists():
        return []
    saida = []
    with caminho.open(encoding="utf-8") as arquivo:
        for linha in arquivo:
            if not linha.strip():
                continue
            try:
                saida.append(json.loads(linha))
            except json.JSONDecodeError:
                continue
    return saida


def _completar_eventos_checkpoint(
    pasta: Path, eventos: list[dict], seed: int, taxa: float
) -> list[dict]:
    """Recupera a época atômica mais recente se o processo parou durante o log."""
    progresso_path = pasta / "progresso.pt"
    if not progresso_path.exists():
        return eventos
    import torch

    progresso = torch.load(progresso_path, map_location="cpu", weights_only=False)
    epoca = int(progresso["epoca"])
    ultima = max((int(evento["epoca"]) for evento in eventos), default=0)
    if epoca <= ultima:
        return eventos
    metricas = progresso["metricas_final"]
    eventos.append(
        {
            "execucao": f"C0|{seed}|{taxa}",
            "candidato": "C0",
            "seed": seed,
            "taxa": taxa,
            "evento": "epoca",
            "epoca": epoca,
            "mse_validacao": float(metricas["mse_validacao"]),
            "ssim_validacao": float(metricas["ssim_validacao"]),
            "perda_treino": float(progresso["perda_treino_final"]),
            "duracao_epoca_ns": int(progresso.get("duracao_epoca_ns", 0)),
            "estado": "concluida",
        }
    )
    return eventos


def _copiar_checkpoints(pasta: Path, seed: int, taxa: float) -> dict:
    import torch
    from codigo.estudo_checkpoints import copiar_imutavel

    progresso_path = pasta / "progresso.pt"
    if not progresso_path.exists():
        return {}
    progresso = torch.load(progresso_path, map_location="cpu", weights_only=False)
    saida = {}
    pasta_imutavel = DIR_V2 / "checkpoints-imutaveis"
    nome = f"C0_seed{seed}_taxa{taxa:g}"
    for categoria, estado_key, metrica_key in (
        ("melhor", "estado_melhor", "metricas_melhor"),
        ("final", "estado_final", "metricas_final"),
    ):
        fonte = pasta / f"{categoria}-origem.pt"
        _atomic_torch_save(
            {
                "candidato": "C0",
                "seed": seed,
                "taxa": taxa,
                "epoca": progresso[metrica_key]["epoca"],
                "metricas_validacao": progresso[metrica_key],
                "state_dict": progresso[estado_key],
            },
            fonte,
        )
        info = copiar_imutavel(
            fonte,
            pasta_imutavel,
            f"{nome}_{categoria}",
            int(progresso[metrica_key]["epoca"]),
        )
        info["metricas_validacao"] = progresso[metrica_key]
        saida[categoria] = info
    return saida


def _executar_filho(
    tipo: str,
    seed: int,
    taxa: float,
    limite_ns: int,
    pasta: Path,
    inicio_etapa_ns: int,
) -> tuple[dict | None, str, str, int]:
    inicio = time.monotonic_ns()
    margem = min(MARGEM_FINALIZACAO_NS, max(0, limite_ns // 4))
    prazo = inicio_etapa_ns + max(0, limite_ns - margem)
    if time.monotonic_ns() >= prazo:
        return (
            None,
            "sem saldo monotônico para iniciar processo filho",
            "",
            time.monotonic_ns() - inicio,
        )
    script = RAIZ / "scripts" / "executar_estudo_c0_v2.py"
    comando = [
        sys.executable,
        str(script),
        "worker",
        "--tipo",
        tipo,
        "--seed",
        str(seed),
        "--taxa",
        str(taxa),
        "--prazo-ns",
        str(prazo),
        "--pasta",
        str(pasta),
    ]
    try:
        processo = subprocess.Popen(
            comando,
            cwd=RAIZ,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        restante = max(0, prazo - time.monotonic_ns()) / NS_POR_SEGUNDO
        try:
            saida, _ = processo.communicate(timeout=restante)
            retorno = processo.returncode
        except subprocess.TimeoutExpired:
            processo.kill()
            saida, _ = processo.communicate()
            retorno = processo.returncode
            motivo = "interrompido pelo supervisor no limite monotônico"
        else:
            motivo = ""
    except OSError as erro:
        saida = f"falha ao iniciar processo filho: {erro}"
        retorno = 127
        motivo = str(erro)
    duracao_ns = time.monotonic_ns() - inicio
    resultado_path = pasta / "resultado.json"
    resultado = None
    if resultado_path.exists():
        try:
            resultado = json.loads(resultado_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            resultado = None
    if retorno != 0 and not motivo:
        motivo = f"processo filho retornou {retorno}"
    log_path = pasta / "processo.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(saida, encoding="utf-8")
    return resultado, motivo, saida, duracao_ns


def _registrar_evento(
    contador: ContadorReservaC0V2,
    evento: str,
    inicio_ns: int,
    *,
    seed: int | None = None,
    taxa: float | None = None,
    estado: str,
    motivo: str = "",
) -> dict:
    duracao = time.monotonic_ns() - inicio_ns
    return contador.registrar(
        evento=evento,
        duracao_ns=duracao,
        candidato="C0",
        seed=seed,
        taxa=taxa,
        estado=estado,
        motivo=motivo,
        monotonic_inicio_ns=inicio_ns,
    )


def _gravar_historico(
    manifesto: dict,
    evento: dict,
    execucao_ns: int,
) -> None:
    linha = dict(evento)
    linha.update(
        {
            "ts": _agora(),
            "duracao_execucao_ns": execucao_ns,
            "hash_manifesto_v2": manifesto["hash_manifesto_v2"],
            "hash_configuracao": manifesto["hash_configuracao"],
            "hash_codigo": manifesto["fontes_python"]["sha256"],
            "hash_split_treino_validacao": manifesto[
                "indices_treino_validacao_sha256"
            ],
            "regra": cfg.VERSAO,
            "consulta_teste": False,
        }
    )
    _append_jsonl(ARQ_HISTORICO, [linha])


def _resumo_refs_v1() -> dict:
    """Usa somente eventos de época e controle da validação na história v1."""
    caminho = DIR_V1 / "historico.csv"
    candidatos: dict[tuple[str, str, str], list[dict]] = {}
    controles: dict[tuple[str, str], dict] = {}
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        for linha in csv.DictReader(arquivo):
            evento = linha.get("evento")
            nome = linha.get("candidato", "")
            if evento == "epoca" and nome in ("C1", "C2"):
                chave = (nome, linha["seed"], linha["taxa"])
                candidatos.setdefault(chave, []).append(
                    {
                        "epoca": int(linha["epoca"]),
                        "mse": float(linha["perda_validacao"]),
                        "ssim": float(linha["ssim_validacao"]),
                    }
                )
            elif evento == "controle" and nome in (
                "controle_media_rgb",
                "controle_interpolacao",
            ):
                controles[(nome, linha["taxa"])] = {
                    "mse": float(linha["perda_validacao"]),
                    "ssim": float(linha["ssim_validacao"]),
                }
    saida_candidatos = {}
    for (nome, seed, taxa), valores in sorted(candidatos.items()):
        melhor = min(valores, key=lambda x: x["mse"])
        final = valores[-1]
        saida_candidatos.setdefault(nome, {}).setdefault(taxa, {})[seed] = {
            "epocas": len(valores),
            "estado": "completo" if len(valores) == cfg.EPOCAS_MAXIMAS else "incompleto",
            "melhor": melhor,
            "final": final,
        }
    saida_controles = {}
    for (nome, taxa), metricas in sorted(controles.items()):
        saida_controles.setdefault(taxa, {})[nome] = metricas
    return {"candidatos": saida_candidatos, "controles": saida_controles}


def _mediana_metricas(execucao_por_seed: dict, ponto: str) -> dict:
    mse = []
    ssim = []
    for valor in execucao_por_seed.values():
        ponto_valor = valor.get(ponto) or {}
        if ponto_valor.get("mse") is not None and ponto_valor.get("ssim") is not None:
            mse.append(float(ponto_valor["mse"]))
            ssim.append(float(ponto_valor["ssim"]))
    return {
        "n": len(mse),
        "mse_mediano": statistics.median(mse) if mse else None,
        "ssim_mediano": statistics.median(ssim) if ssim else None,
    }


def _coletar_v2() -> dict:
    estado = _ler_estado()
    eventos = []
    if ARQ_HISTORICO.exists():
        with ARQ_HISTORICO.open(encoding="utf-8") as arquivo:
            eventos = [json.loads(linha) for linha in arquivo if linha.strip()]
    candidatos = {}
    for evento in eventos:
        if evento.get("evento") != "epoca":
            continue
        chave = (str(evento["seed"]), str(evento["taxa"]))
        candidatos.setdefault(chave, []).append(
            {
                "epoca": int(evento["epoca"]),
                "mse": float(evento["mse_validacao"]),
                "ssim": float(evento["ssim_validacao"]),
            }
        )
    por_execucao = {}
    for chave, valores in candidatos.items():
        melhor = min(valores, key=lambda x: x["mse"])
        final = valores[-1]
        seed, taxa = chave
        treinos = estado.get("treinos", {})
        status = treinos.get(f"{seed}|{taxa}", {})
        por_execucao[f"{seed}|{taxa}"] = {
            "seed": int(seed),
            "taxa": float(taxa),
            "epocas_concluidas": len(valores),
            "estado": status.get("estado", "incompleto"),
            "motivo": status.get("motivo", ""),
            "melhor": melhor,
            "final": final,
            "checkpoints": status.get("checkpoints", {}),
            "duracao_ns": status.get("duracao_ns", 0),
        }
    return {"estado": estado, "eventos": eventos, "execucoes": por_execucao}


def _tabela_v2(execucao: dict) -> list[str]:
    linhas = [
        "| Seed | Taxa | Estado | Épocas concluídas | Melhor: época / MSE / SSIM | Final: época / MSE / SSIM | Tempo | Hash melhor | Hash final |",
        "|---:|---:|---|---:|---|---|---:|---|---|",
    ]
    for seed in cfg.CONFIG["seeds_treino"]:
        for taxa in cfg.CONFIG["taxas"]:
            item = execucao.get(f"{seed}|{taxa}")
            if not item:
                linhas.append(
                    f"| {seed} | {taxa:g} | não iniciado | 0 | indisponível | indisponível | 0 s | indisponível | indisponível |"
                )
                continue
            melhor = item.get("melhor") or {}
            final = item.get("final") or {}
            checkpoints = item.get("checkpoints", {})
            hash_melhor = checkpoints.get("melhor", {}).get("sha256", "indisponível")
            hash_final = checkpoints.get("final", {}).get("sha256", "indisponível")
            tempo_s = item.get("duracao_ns", 0) / NS_POR_SEGUNDO
            linhas.append(
                f"| {seed} | {taxa:g} | {item['estado']} | {item['epocas_concluidas']} | "
                f"{melhor.get('epoca', 'n/d')} / {melhor.get('mse', 'n/d')} / {melhor.get('ssim', 'n/d')} | "
                f"{final.get('epoca', 'n/d')} / {final.get('mse', 'n/d')} / {final.get('ssim', 'n/d')} | "
                f"{tempo_s:.6f} s | {hash_melhor} | {hash_final} |"
            )
    return linhas


def _gerar_relatorio(manifesto: dict, contador: ContadorReservaC0V2) -> dict:
    v2 = _coletar_v2()
    v1 = _resumo_refs_v1()
    por_taxa = {}
    comparacao = {}
    for taxa in cfg.CONFIG["taxas"]:
        taxa_s = str(taxa)
        v2_seeds = {
            chave.split("|")[0]: valor
            for chave, valor in v2["execucoes"].items()
            if valor["taxa"] == taxa
        }
        v1_refs = {}
        for nome in ("C1", "C2"):
            v1_refs[nome] = v1.get("candidatos", {}).get(nome, {}).get(taxa_s, {})
        por_taxa[taxa_s] = {
            "C0_v2_melhor": _mediana_metricas(v2_seeds, "melhor"),
            "C0_v2_final": _mediana_metricas(v2_seeds, "final"),
            "C1_v1_melhor": _mediana_metricas(v1_refs["C1"], "melhor"),
            "C1_v1_final": _mediana_metricas(v1_refs["C1"], "final"),
            "C2_v1_melhor": _mediana_metricas(v1_refs["C2"], "melhor"),
            "C2_v1_final": _mediana_metricas(v1_refs["C2"], "final"),
            "controles_v1": v1.get("controles", {}).get(taxa_s, {}),
            "por_seed_v1": {nome: v1_refs[nome] for nome in ("C1", "C2")},
        }
        comparacao[taxa_s] = por_taxa[taxa_s]
    refs = manifesto["referencias_v1"]
    dados_contador = {
        "v1_principal_ns": contador.v1_principal_ns,
        "v1_reserva_ns": contador.v1_reserva_ns,
        "v1_total_ns": contador.v1_total_ns,
        "v2_ns": contador.total_v2_ns,
        "global_ns": contador.total_global_ns,
        "saldo_v2_ns": contador.saldo_reserva_ns,
        "saldo_global_ns": contador.saldo_global_ns,
    }
    resumo = {
        "versao": cfg.VERSAO,
        "hash_manifesto_v2": manifesto["hash_manifesto_v2"],
        "hash_codigo": manifesto["fontes_python"]["sha256"],
        "hash_configuracao": manifesto["hash_configuracao"],
        "hash_split_treino_validacao": manifesto["indices_treino_validacao_sha256"],
        "hash_lockfile": manifesto["lockfile_sha256"],
        "referencias_v1": {
            "arvore_sha256": refs["resultados"]["sha256_arvore"],
            "consumo_principal_ns": refs["consumo_principal_ns"],
            "reserva_consumida_ns": refs["reserva_consumida_ns"],
            "codigo_hash_registrado": refs["codigo_hash_registrado"],
        },
        "contador": dados_contador,
        "pilotos": v2["estado"].get("pilotos", {}),
        "viabilidade_piloto_c0": v2["estado"].get("viabilidade_piloto_c0", {}),
        "execucoes": v2["execucoes"],
        "comparacao_validacao_por_taxa": comparacao,
        "consulta_teste": False,
    }
    _gravar_json_atomico(ARQ_RESUMO, resumo)
    linhas = [
        "# Retomada C0 v2",
        "",
        "## Protocolo e alcance",
        "",
        "Esta retomada executa somente C0 no diretório v2 isolado. Mantém dados, máscaras, hiperparâmetros, seeds 10, 20 e 30 e taxas 0,5 e 0,75. O limiar do piloto é 1,25 s. Cada treino tem no máximo 200 épocas e 240 segundos, incluindo setup, validação, SSIM, checkpoints e I/O. Duzentas épocas são um máximo, não uma garantia.",
        "",
        "Uma execução interrompida é relatada como incompleta e contabiliza somente épocas concluídas. Os checkpoints melhor e final são cópias imutáveis distintas com época e SHA-256. MSE e SSIM vêm da mesma régua de validação da v1.",
        "",
        "Não foram iniciados novos treinos C1, C2 ou C3, novos controles ou inferências nos modelos v1. Não houve consulta ao conjunto de teste.",
        "",
        "## Execuções C0 v2",
        "",
        *_tabela_v2(v2["execucoes"]),
        "",
        "## Referências de validação v1",
        "",
        "Valores de C1, C2 e controles são lidos do histórico v1, sem nova inferência. A tabela resume os melhores e finais por seed, quando existem; execução interrompida continua identificada pelo número efetivo de épocas.",
        "",
        "| Taxa | Referência | Seeds disponíveis | MSE mediano melhor | SSIM mediano no melhor | MSE mediano final | SSIM mediano final |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for taxa_s, dados in comparacao.items():
        for nome in ("C0_v2", "C1_v1", "C2_v1"):
            melhor = dados[f"{nome}_melhor"]
            final = dados[f"{nome}_final"]
            linhas.append(
                f"| {taxa_s} | {nome} | {melhor['n']} | {melhor['mse_mediano']} | {melhor['ssim_mediano']} | {final['mse_mediano']} | {final['ssim_mediano']} |"
            )
        for nome, metricas in sorted(dados["controles_v1"].items()):
            linhas.append(
                f"| {taxa_s} | {nome} v1 | 1 | {metricas['mse']} | {metricas['ssim']} | não aplicável | não aplicável |"
            )
    linhas.extend(
        [
            "",
            "## Estado das referências C1 e C2 v1 por seed",
            "",
            "| Taxa | Candidato | Seed | Estado observado | Épocas registradas | Melhor: época / MSE / SSIM | Final: época / MSE / SSIM |",
            "|---:|---|---:|---|---:|---|---|",
        ]
    )
    for taxa_s, dados in comparacao.items():
        for nome in ("C1", "C2"):
            for seed, item in sorted(
                dados["por_seed_v1"][nome].items(), key=lambda par: int(par[0])
            ):
                melhor = item["melhor"]
                final = item["final"]
                linhas.append(
                    f"| {taxa_s} | {nome} v1 | {seed} | {item['estado']} | {item['epocas']} | "
                    f"{melhor['epoca']} / {melhor['mse']} / {melhor['ssim']} | "
                    f"{final['epoca']} / {final['mse']} / {final['ssim']} |"
                )
    linhas.extend(
        [
            "",
            "## Limitações e lacunas",
            "",
            "A v1 não contém uma referência C0 treinada, portanto não há comparação C0 v2 contra C0 v1. A v1 usou o limiar de piloto de 1,2 s, enquanto esta retomada usa 1,25 s. A comparação de C0 v2 com C1, C2 e controles v1 é descritiva: os protocolos, épocas concluídas e estados não são necessariamente equivalentes e não permitem atribuição causal. Ausência de C0 na v1 não é derrota; ausência de referência não é evidência negativa. Nenhuma seleção de vencedor é feita nesta retomada.",
            "",
            "## Contabilização",
            "",
            f"- Consumo principal v1: {dados_contador['v1_principal_ns'] / (60 * NS_POR_SEGUNDO):.9f} min.",
            f"- Reserva consumida v1: {dados_contador['v1_reserva_ns'] / (60 * NS_POR_SEGUNDO):.9f} min.",
            f"- Consumo v2: {dados_contador['v2_ns'] / (60 * NS_POR_SEGUNDO):.9f} min de no máximo 30 min.",
            f"- Total v1 + v2: {dados_contador['global_ns'] / (60 * NS_POR_SEGUNDO):.9f} min de no máximo 120 min.",
            f"- Saldo da reserva v2: {dados_contador['saldo_v2_ns'] / (60 * NS_POR_SEGUNDO):.9f} min.",
            f"- Saldo global: {dados_contador['saldo_global_ns'] / (60 * NS_POR_SEGUNDO):.9f} min.",
            "",
            f"Referências v1: SHA-256 da árvore `{refs['resultados']['sha256_arvore']}`; manifesto `{refs['manifesto_sha256']}`; contador `{refs['contador_sha256']}`. O manifesto C0 v2 é `{manifesto['hash_manifesto_v2']}`.",
            "",
            "## Rastreabilidade",
            "",
            "Os números desta página são derivados do histórico JSONL v2 e dos eventos de época e controle de validação presentes no histórico v1. O resumo legível por máquina está em `resumo.json`; as durações monotônicas completas estão em `contador.jsonl`.",
        ]
    )
    ARQ_RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    ARQ_RELATORIO.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return resumo


def executar(inicio_ns: int | None = None) -> dict:
    """Pilotos C0, treinos elegíveis e consolidação exclusivamente de validação."""
    inicio_ns = time.monotonic_ns() if inicio_ns is None else int(inicio_ns)
    manifesto, contador = _verificar_congelamento()
    estado = _ler_estado()
    inicio_setup = inicio_ns
    _marcar_inicio_unico(estado)
    _salvar_estado(estado)
    setup_ns = time.monotonic_ns() - inicio_setup
    if setup_ns:
        contador.registrar(
            evento="inicio_executor",
            duracao_ns=setup_ns,
            estado="concluido",
            motivo="inicialização do executor v2",
            monotonic_inicio_ns=inicio_setup,
        )

    pilotos = estado.setdefault("pilotos", {})
    for taxa in cfg.CONFIG["taxas"]:
        chave_taxa = str(taxa)
        if chave_taxa in pilotos:
            continue
        gasto_piloto = contador.gasto_evento_ns("piloto")
        restante_piloto = cfg.TETO_PILOTO_TOTAL_SEGUNDOS * NS_POR_SEGUNDO - gasto_piloto
        limite = contador.limite_disponivel_ns(
            restante_piloto, proteger_ns=PROTEGER_CONSOLIDACAO_NS
        )
        if limite <= MARGEM_FINALIZACAO_NS:
            pilotos[chave_taxa] = {
                "estado": "impedido_orcamento",
                "viavel": False,
                "motivo": "saldo insuficiente para iniciar o piloto",
            }
            _salvar_estado(estado)
            continue
        pasta = DIR_V2 / "pilotos" / f"C0_seed10_taxa{taxa:g}"
        etapa_inicio = time.monotonic_ns()
        try:
            _verificar_congelamento()
            resultado, motivo_processo, _, _ = _executar_filho(
                "piloto", 10, taxa, limite, pasta, etapa_inicio
            )
            if resultado is None or resultado.get("duracao_epoca_ns") is None:
                viavel = False
                duracao_epoca = None
                motivo = (
                    (resultado or {}).get("motivo")
                    or motivo_processo
                    or "piloto não concluiu uma época"
                )
                estado_piloto = (
                    "incompleto" if "limite monotônico" in motivo else "erro"
                )
            else:
                duracao_epoca = int(resultado["duracao_epoca_ns"])
                viavel = piloto_viavel(duracao_epoca)
                motivo = "" if viavel else "época completa excedeu 1,25 s"
                estado_piloto = "concluido" if viavel else "inviavel"
            pilotos[chave_taxa] = {
                "estado": estado_piloto,
                "viavel": viavel,
                "motivo": motivo,
                "duracao_epoca_ns": duracao_epoca,
                "resultado": resultado,
            }
            if resultado and duracao_epoca is not None:
                _gravar_historico(
                    manifesto,
                    {
                        "execucao": f"piloto|C0|10|{taxa}",
                        "candidato": "C0",
                        "seed": 10,
                        "taxa": taxa,
                        "evento": "piloto",
                        "epoca": 1,
                        "perda_treino": resultado["perda_treino"],
                        "mse_validacao": resultado["mse_validacao"],
                        "ssim_validacao": resultado["ssim_validacao"],
                        "duracao_epoca_ns": duracao_epoca,
                        "estado": estado_piloto,
                        "motivo": motivo,
                    },
                    etapa_inicio,
                )
        except Exception as erro:
            viavel = False
            motivo = f"{type(erro).__name__}: {erro}"
            pilotos[chave_taxa] = {
                "estado": "erro",
                "viavel": False,
                "motivo": motivo,
                "duracao_epoca_ns": None,
                "resultado": None,
            }
        _salvar_estado(estado)
        duracao_etapa = time.monotonic_ns() - etapa_inicio
        contador.registrar(
            evento="piloto",
            duracao_ns=duracao_etapa,
            seed=10,
            taxa=taxa,
            estado=pilotos[chave_taxa]["estado"],
            motivo=pilotos[chave_taxa]["motivo"],
            monotonic_inicio_ns=etapa_inicio,
            teto_evento_ns=limite,
        )

    c0_viavel = piloto_candidato_viavel(pilotos, tuple(cfg.CONFIG["taxas"]))
    taxas_inviaveis = [
        taxa
        for taxa in cfg.CONFIG["taxas"]
        if not pilotos.get(str(taxa), {}).get("viavel", False)
    ]
    estado["viabilidade_piloto_c0"] = {
        "viavel": c0_viavel,
        "taxas_inviaveis": taxas_inviaveis,
    }
    _salvar_estado(estado)

    treinos = estado.setdefault("treinos", {})
    for seed in cfg.CONFIG["seeds_treino"]:
        for taxa in cfg.CONFIG["taxas"]:
            chave = f"{seed}|{taxa}"
            if chave in treinos:
                continue
            if not c0_viavel:
                treinos[chave] = {
                    "estado": "inviavel_piloto",
                    "epocas_concluidas": 0,
                    "duracao_ns": 0,
                    "motivo": (
                        "C0 inviável para treino completo porque ao menos uma taxa do "
                        f"piloto excedeu 1,25 s ou ficou incompleta: {taxas_inviaveis}; "
                        "nenhum piloto foi repetido"
                    ),
                    "checkpoints": {},
                }
                _salvar_estado(estado)
                continue
            limite = contador.limite_disponivel_ns(
                cfg.TETO_EXECUCAO_SEGUNDOS * NS_POR_SEGUNDO,
                proteger_ns=PROTEGER_CONSOLIDACAO_NS,
            )
            if limite <= MARGEM_FINALIZACAO_NS:
                treinos[chave] = {
                    "estado": "impedido_orcamento",
                    "epocas_concluidas": 0,
                    "duracao_ns": 0,
                    "motivo": "saldo insuficiente para iniciar a execução sem exceder os tetos",
                    "checkpoints": {},
                }
                _salvar_estado(estado)
                continue
            pasta = DIR_V2 / "execucoes" / f"C0_seed{seed}_taxa{taxa:g}"
            etapa_inicio = time.monotonic_ns()
            resultado = None
            motivo_processo = ""
            estado_execucao = "incompleto"
            checkpoints = {}
            try:
                _verificar_congelamento()
                resultado, motivo_processo, _, _ = _executar_filho(
                    "treino", seed, taxa, limite, pasta, etapa_inicio
                )
                eventos = _completar_eventos_checkpoint(
                    pasta, _ler_eventos_execucao(pasta), seed, taxa
                )
                for evento in eventos:
                    _gravar_historico(manifesto, evento, etapa_inicio)
                checkpoints = _copiar_checkpoints(pasta, seed, taxa)
                if resultado is None:
                    progresso_path = pasta / "progresso.pt"
                    epocas = len(eventos)
                    if motivo_processo.startswith("interrompido pelo supervisor"):
                        estado_execucao = "interrompido" if epocas else "sem_epocas_completas"
                    else:
                        estado_execucao = "erro"
                    motivo_execucao = motivo_processo or "processo interrompido antes de concluir época"
                else:
                    epocas = int(resultado.get("epocas_concluidas", 0))
                    estado_execucao = resultado.get("estado", "incompleto")
                    motivo_execucao = resultado.get("motivo", motivo_processo)
                if epocas < cfg.EPOCAS_MAXIMAS and estado_execucao == "completo":
                    estado_execucao = "incompleto"
                    motivo_execucao = "menos de 200 épocas concluídas"
            except Exception as erro:
                eventos = _completar_eventos_checkpoint(
                    pasta, _ler_eventos_execucao(pasta), seed, taxa
                )
                for evento in eventos:
                    _gravar_historico(manifesto, evento, etapa_inicio)
                try:
                    checkpoints = _copiar_checkpoints(pasta, seed, taxa)
                except Exception:
                    checkpoints = {}
                epocas = len(eventos)
                estado_execucao = "erro"
                motivo_execucao = f"{type(erro).__name__}: {erro}"
            treinos[chave] = {
                "estado": estado_execucao,
                "epocas_concluidas": epocas,
                "duracao_ns": 0,
                "motivo": motivo_execucao,
                "resultado": resultado,
                "checkpoints": checkpoints,
            }
            _salvar_estado(estado)
            duracao_etapa = time.monotonic_ns() - etapa_inicio
            treinos[chave]["duracao_ns"] = duracao_etapa
            _salvar_estado(estado)
            duracao_etapa = time.monotonic_ns() - etapa_inicio
            try:
                contador.registrar(
                    evento="treino",
                    duracao_ns=duracao_etapa,
                    seed=seed,
                    taxa=taxa,
                    estado=estado_execucao,
                    motivo=motivo_execucao,
                    monotonic_inicio_ns=etapa_inicio,
                    teto_evento_ns=limite,
                )
            except ErroOrcamento:
                treinos[chave]["estado"] = "erro_teto"
                treinos[chave]["motivo"] = "tempo real registrado ultrapassou o teto"
                _salvar_estado(estado)
                raise

    limite_consolidacao = contador.limite_disponivel_ns(
        PROTEGER_CONSOLIDACAO_NS
    )
    consolidacao_inicio = time.monotonic_ns()
    status_final = "erro"
    motivo_final = "consolidação não concluída"
    try:
        manifesto, contador = _verificar_congelamento()
        resumo = _gerar_relatorio(manifesto, contador)
        estado = _ler_estado()
        estado["execucao_finalizada"] = True
        estado["contador_final"] = resumo["contador"]
        _salvar_estado(estado)
        status_final = "concluido"
        motivo_final = "relatório v2 e comparação de validação gerados"
    except Exception as erro:
        status_final = "erro"
        motivo_final = f"{type(erro).__name__}: {erro}"
        raise
    finally:
        duracao_consolidacao = time.monotonic_ns() - consolidacao_inicio
        contador.registrar(
            evento="consolidacao_avaliacao_relatorio",
            duracao_ns=duracao_consolidacao,
            estado=status_final,
            motivo=motivo_final,
            monotonic_inicio_ns=consolidacao_inicio,
            teto_evento_ns=limite_consolidacao,
        )
    manifesto, contador = _verificar_congelamento()
    resumo = _gerar_relatorio(manifesto, contador)
    estado = _ler_estado()
    estado["execucao_finalizada"] = True
    estado["contador_final"] = resumo["contador"]
    _salvar_estado(estado)
    return resumo


def _argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retomada C0 v2 isolada")
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("congelar", help="congela manifesto e hashes antes do piloto")
    sub.add_parser("executar", help="executa somente a rodada C0 v2 autorizada")
    worker = sub.add_parser("worker", help=argparse.SUPPRESS)
    worker.add_argument("--tipo", choices=("piloto", "treino"), required=True)
    worker.add_argument("--seed", type=int, required=True)
    worker.add_argument("--taxa", type=float, required=True)
    worker.add_argument("--prazo-ns", type=int, required=True)
    worker.add_argument("--pasta", type=Path, required=True)
    return parser.parse_args()


def main(inicio_ns: int | None = None) -> int:
    args = _argumentos()
    try:
        if args.comando == "congelar":
            manifesto = congelar(inicio_ns)
            print(
                json.dumps(
                    {
                        "estado": "congelado",
                        "diretorio": str(DIR_V2),
                        "hash_manifesto_v2": manifesto["hash_manifesto_v2"],
                        "hash_codigo": manifesto["fontes_python"]["sha256"],
                        "hash_v1": manifesto["referencias_v1"]["resultados"]["sha256_arvore"],
                    },
                    ensure_ascii=False,
                )
            )
            return 0
        if args.comando == "executar":
            resumo = executar(inicio_ns)
            print(
                json.dumps(
                    {
                        "estado": "concluido",
                        "relatorio": str(ARQ_RELATORIO),
                        "resumo": str(ARQ_RESUMO),
                        "contador": resumo["contador"],
                    },
                    ensure_ascii=False,
                )
            )
            return 0
        resultado = executar_worker(
            args.tipo, args.seed, args.taxa, args.prazo_ns, args.pasta
        )
        print(json.dumps(resultado, ensure_ascii=False))
        return 0
    except ErroOrcamento as erro:
        print(f"ERRO_ORCAMENTO: {erro}", file=sys.stderr)
        return 3
    except Exception as erro:
        print(f"ERRO: {type(erro).__name__}: {erro}", file=sys.stderr)
        return 2
