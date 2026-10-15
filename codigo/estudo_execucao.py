"""Orquestração executável da fase B do estudo melhorar-reconstrucoes-mae.

Subcomandos, nesta ordem, cada um idempotente e retomável:
congelar, piloto, treino, consolidar, controles, decidir-c3, selecao,
congelar-final, avaliacao-final, resumo, figuras, ficha.

Todo consumo de tempo passa pelo ContadorOrcamento (contador.jsonl), todo
evento vai ao historico.csv append-only, e nada consulta o conjunto de teste
antes do congelamento final. Gravação em resultados/estudo-melhorar-reconstrucoes-mae/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import torch

from codigo import configuracao_estudo as cfg
from codigo import estudo_avaliacao as aval
from codigo import estudo_baselines as bas
from codigo import estudo_candidatos as cand
from codigo import estudo_checkpoints as ckpt
from codigo import estudo_historico as hist
from codigo import estudo_mascaras as msk
from codigo import estudo_selecao as sel
from codigo import estudo_visual as vis
from codigo.estudo_orcamento import ContadorOrcamento
from codigo.mae import perda_mae, reconstrucao_completa, unpatchify

RAIZ = Path(__file__).resolve().parent.parent
DIR_ESTUDO = RAIZ / "resultados" / "estudo-melhorar-reconstrucoes-mae"
ARQ_MANIFESTO = DIR_ESTUDO / "manifesto.json"
ARQ_CONTADOR = DIR_ESTUDO / "contador.jsonl"
ARQ_HISTORICO = DIR_ESTUDO / "historico.csv"
ARQ_ESTADO = DIR_ESTUDO / "estado.json"
ARQ_RESUMO = DIR_ESTUDO / "resumo.json"
DIR_CKPT_TRAB = DIR_ESTUDO / "checkpoints-trabalho"
DIR_CKPT_IMUT = DIR_ESTUDO / "checkpoints"
DIR_FIGURAS = DIR_ESTUDO / "figuras"
DIR_FICHA = DIR_ESTUDO / "ficha-visual"
ARQ_INDICES = RAIZ / "dados" / "cifar10_subset" / "indices.csv"

NOME_CONTROLES = ("controle_media_rgb", "controle_interpolacao")


# ------------------------------------------------------------- utilidades


def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _code_hash() -> str:
    digest = hashlib.sha256()
    for caminho in sorted((RAIZ / "codigo").glob("*.py")):
        digest.update(caminho.name.encode("utf-8"))
        digest.update(caminho.read_bytes())
    return digest.hexdigest()


def _versao_split() -> str:
    return hashlib.sha256(ARQ_INDICES.read_bytes()).hexdigest()[:16]


def _carregar_estado() -> dict:
    if ARQ_ESTADO.exists():
        return json.loads(ARQ_ESTADO.read_text(encoding="utf-8"))
    return {}


def _salvar_estado(estado: dict) -> None:
    DIR_ESTUDO.mkdir(parents=True, exist_ok=True)
    ARQ_ESTADO.write_text(
        json.dumps(estado, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _carregar_dados() -> dict[str, dict]:
    npz = np.load(RAIZ / "dados" / "cifar10_subset" / "subset.npz")
    mapa = msk.carregar_mapa_indices(ARQ_INDICES)
    saida: dict[str, dict] = {}
    for split in ("treino", "validacao", "teste"):
        saida[split] = {
            "imagens": npz[split].astype(np.float32) / 255.0,
            "indices_originais": np.asarray(mapa[split], dtype=np.int64),
        }
    return saida


def _dispositivo() -> torch.device:
    if not torch.cuda.is_available():
        raise RuntimeError("sem GPU CUDA; o treino exige GPU, sem fallback")
    dispositivo = torch.device("cuda")
    versao = torch.version.cuda
    if versao is None or int(versao.split(".")[0]) < 13:
        raise RuntimeError(f"torch compilado com CUDA {versao}; exigido cu130")
    return dispositivo


def _validar_mapa_indices() -> None:
    mapa = msk.carregar_mapa_indices(ARQ_INDICES)
    tamanhos = {"treino": 5000, "validacao": 1000, "teste": 1000}
    for split, n in tamanhos.items():
        if len(mapa[split]) != n:
            raise RuntimeError(
                f"split {split}: esperados {n} índices, há {len(mapa[split])}"
            )


def _otimizador(modelo) -> torch.optim.AdamW:
    c = cfg.CONFIG["comum"]
    return torch.optim.AdamW(
        modelo.parameters(),
        lr=c["lr"],
        weight_decay=c["weight_decay"],
        betas=(c["beta1"], c["beta2"]),
        eps=c["epsilon_adam"],
    )


def registrar(
    historico,
    execucao: str,
    candidato: str,
    evento: str,
    seed: int | str = "",
    taxa: float | str = "",
    epoca: int = 0,
    perda_treino: float | None = None,
    perda_validacao: float | None = None,
    ssim_validacao: float | None = None,
    tempo: float = 0.0,
    estado_l: str = "",
    motivo: str = "",
) -> None:
    def fmt(v):
        return "" if v is None else f"{float(v):.6f}"

    historico.registrar(
        execucao=execucao,
        candidato=candidato,
        seed=str(seed),
        taxa=str(taxa),
        evento=evento,
        epoca=epoca,
        perda_treino=fmt(perda_treino),
        perda_validacao=fmt(perda_validacao),
        ssim_validacao=fmt(ssim_validacao),
        tempo_epoca=f"{float(tempo):.3f}",
        tempo_acumulado="",
        unidade="segundos",
        config_hash=cfg.hash_configuracao()[:16],
        split_versao=_versao_split(),
        codigo_hash=_code_hash()[:16],
        regras_hash=cfg.VERSAO_REGRAS,
        estado=estado_l,
        motivo=motivo,
    )


def _guard(
    contador: ContadorOrcamento,
    candidato: str,
    categoria: str,
    segundos_previstos: float,
    chave=None,
) -> tuple[bool, str | None]:
    return contador.pode_iniciar(
        candidato, categoria, segundos_previstos / 60.0, chave=chave
    )


def _consumir(
    contador: ContadorOrcamento,
    candidato: str,
    categoria: str,
    segundos: float,
    chave=None,
) -> dict:
    return contador.consumir(
        candidato, categoria, segundos / 60.0, chave=chave, ts=_ts()
    )


def _caminho_trabalho(candidato: str, seed: int, taxa: float, sufixo: str = "") -> Path:
    return DIR_CKPT_TRAB / f"{candidato}_{seed}_{taxa}{sufixo}.pt"


def _salvar_trabalho(caminho: Path, payload: dict) -> float:
    """Escrita atômica com renome; retorna o tempo do I/O."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(".tmp")
    t0 = time.perf_counter()
    torch.save(payload, tmp)
    tmp.rename(caminho)
    return time.perf_counter() - t0


def _carregar_trabalho(caminho: Path) -> dict:
    return torch.load(caminho, map_location="cpu", weights_only=False)


def _contexto():
    if not ARQ_MANIFESTO.exists():
        raise RuntimeError("manifesto não congelado: rode 'congelar' antes")
    cfg.verificar_manifesto(ARQ_MANIFESTO)
    contador = ContadorOrcamento(ARQ_CONTADOR)
    historico = hist.HistoricoEstudo(ARQ_HISTORICO)
    estado = _carregar_estado()
    if not estado.get("congelado"):
        raise RuntimeError("estado sem registro de congelamento")
    return contador, historico, estado


# ---------------------------------------------------- máscaras, régua, épocas


def _preenchimento(
    patches: torch.Tensor, indices_ocultos: torch.Tensor
) -> torch.Tensor:
    """Preenche patches ocultos com a média RGB dos pixels visíveis (D4).

    patches: (B, 16, 192) na ordem (pixel, canal); indices_ocultos: (B, k).
    Todo patch tem 64 pixels, então a média de pixels visíveis é igual à
    média simples por canal sobre os patches visíveis.
    """
    b, n, _ = patches.shape
    medias = patches.reshape(b, n, 8, 8, 3).mean(dim=(2, 3))  # (B,16,3)
    visiveis = torch.ones(b, n, dtype=torch.bool, device=patches.device)
    visiveis.scatter_(1, indices_ocultos, False)
    soma = (medias * visiveis.unsqueeze(2)).sum(dim=1)
    media = soma / visiveis.sum(dim=1, keepdim=True).clamp(min=1)
    saida = patches.clone()
    lote = torch.arange(b, device=patches.device)[:, None]
    preenchido = media[:, None, None, :].expand(b, n, 64, 3).reshape(b, n, 192)
    saida[lote, indices_ocultos] = preenchido[lote, indices_ocultos]
    return saida


def _avaliar_regua(
    modelo,
    imagens: np.ndarray,
    dispositivo: torch.device,
    taxa: float,
    residual: bool = False,
) -> tuple[float, float]:
    """MSE e SSIM de todo o split na régua fixa (máscara por posição, seed 42)."""
    regua = aval.regua_validacao(len(imagens), taxa).to(dispositivo)
    mses, ssims = [], []
    with torch.no_grad():
        modelo.eval()
        for inicio in range(0, len(imagens), 500):
            fim = min(inicio + 500, len(imagens))
            regua_lote = regua[inicio:fim]
            x = torch.from_numpy(
                imagens[inicio:fim].transpose(0, 3, 1, 2)
            ).float().to(dispositivo)
            saida = modelo(x, indices_mascarados=regua_lote)
            pred = saida["predicao"]
            if residual:
                preench = _preenchimento(saida["patches"].detach(), regua_lote)
                pred = cand.composicao_residual(preench, pred, regua_lote)
            pred = pred.clamp(0.0, 1.0)  # D6: predições limitadas à faixa [0,1] na régua
            # métrica na CPU: o módulo SSIM aprovado usa kernel CPU
            pred_cpu = pred.detach().cpu()
            alvo_cpu = saida["patches"].detach().cpu()
            regua_cpu = regua_lote.cpu()
            mse_img = aval.mse_regua(
                pred_cpu, alvo_cpu, regua_cpu, por_imagem=True
            )
            ssim_img = aval.ssim_regua(
                pred_cpu, alvo_cpu, regua_cpu, por_imagem=True
            )
            mses.append(mse_img.double().cpu())
            ssims.append(ssim_img.double().cpu())
        modelo.train()
    return float(torch.cat(mses).mean()), float(torch.cat(ssims).mean())


def _epoca_treino(
    modelo,
    dados_treino: dict,
    dispositivo: torch.device,
    seed: int,
    epoca: int,
    taxa: float,
    declaracao: dict,
    otimizador,
    ordem_rng: np.random.Generator,
) -> float:
    """Uma época de treino com máscaras por identidade (D1); retorna a perda."""
    imagens = dados_treino["imagens"]
    indices_originais = dados_treino["indices_originais"]
    n = len(imagens)
    batch = cfg.CONFIG["comum"]["batch"]
    residual = bool(declaracao.get("residual"))
    ordem = ordem_rng.permutation(n)
    perdas: list[tuple[float, int]] = []
    modelo.train()
    for inicio in range(0, n, batch):
        idx = ordem[inicio : inicio + batch]
        x = torch.from_numpy(
            imagens[idx].transpose(0, 3, 1, 2)
        ).float().to(dispositivo)
        mascaras_np = msk.mascaras_lote(seed, epoca, indices_originais[idx], taxa)
        mascaras = torch.from_numpy(mascaras_np).long().to(dispositivo)
        saida = modelo(x, indices_mascarados=mascaras)
        if residual:
            preench = _preenchimento(saida["patches"].detach(), mascaras)
            composto = cand.composicao_residual(
                preench, saida["predicao"], mascaras
            )
            perda = perda_mae(composto, saida["patches"], mascaras)
        else:
            perda = cand.perda_candidato(
                declaracao, saida["predicao"], saida["patches"], mascaras
            )
        otimizador.zero_grad()
        perda.backward()
        otimizador.step()
        perdas.append((float(perda.detach()), len(idx)))
    total = sum(p for _, p in perdas)
    return sum(l * p for l, p in perdas) / total


def _melhor_por_execucao(historico) -> dict[tuple, dict]:
    """Por execução de treino: melhor validação no CSV (evento 'epoca')."""
    saida: dict[tuple, dict] = {}
    for r in historico.linhas():
        if r["evento"] != "epoca" or not r["perda_validacao"]:
            continue
        partes = r["execucao"].split("|")
        if partes[0] != "treino":
            continue
        _, nome, seed, taxa = partes
        chave = (nome, int(seed), float(taxa))
        valor = float(r["perda_validacao"])
        registro = {
            "perda_validacao": valor,
            "ssim_validacao": float(r["ssim_validacao"]) if r["ssim_validacao"] else 0.0,
            "epoca": int(r["epoca"]),
        }
        antes = saida.get(chave)
        if antes is None or valor < antes["perda_validacao"]:
            saida[chave] = registro
    return saida


# ------------------------------------------------------------- congelamento


def cmd_congelar(args) -> None:
    """Congela manifesto, versões de código/split/ambiente e IDs visuais."""
    _dispositivo()
    _validar_mapa_indices()
    mapa = msk.carregar_mapa_indices(ARQ_INDICES)
    divergencia = msk.divergencia_mapa_indices(
        mapa, msk.carregar_mapa_indices(ARQ_INDICES)
    )
    if divergencia:
        raise RuntimeError(f"divergência de mapa de índices: {divergencia}")
    v_split = _versao_split()
    ids = vis.selecao_ids_visuais(mapa["validacao"], v_split)
    if ids != vis.selecao_ids_visuais(mapa["validacao"], v_split):
        raise RuntimeError("seleção visual não reproduzível")
    cfg.salvar_manifesto(ARQ_MANIFESTO)
    estado = _carregar_estado()
    estado.update(
        {
            "congelado": True,
            "hash_manifesto": cfg.hash_configuracao(),
            "versao_split": v_split,
            "codigo_hash": _code_hash()[:16],
            "torch": torch.__version__,
            "cuda": str(torch.version.cuda),
            "dispositivo_gpu": torch.cuda.get_device_name(torch.device("cuda")),
            "ids_visuais": {
                "versao": vis.VERSAO_SELECAO,
                "ids": ids,
                "chave": {str(i): vis.chave_visual(i, v_split).hex() for i in ids},
            },
        }
    )
    _salvar_estado(estado)
    print(
        "congelado:",
        f"hash={estado['hash_manifesto'][:16]}",
        f"split={v_split}",
        f"codigo={estado['codigo_hash'][:16]}",
        f"torch={torch.__version__}",
        f"ids={ids}",
    )


# ---------------------------------------------------------------- piloto


def cmd_piloto(args) -> None:
    """Pilotos: uma época completa por taxa, seed 10, com validação, SSIM e I/O."""
    contador, historico, estado = _contexto()
    dados = _carregar_dados()
    dispositivo = _dispositivo()
    _validar_mapa_indices()
    nomes = [args.candidato] if args.candidato else ["C0", "C1", "C2"]
    declaracoes = cand.declaracoes()
    for nome in nomes:
        if estado.get("pilotos", {}).get(nome):
            print(f"{nome}: piloto já registrado; nada a fazer")
            continue
        ok, motivo = _guard(contador, nome, "piloto", 25.0)
        if not ok:
            registrar(
                historico, f"piloto|{nome}", nome, "erro", estado_l="impedido",
                motivo=f"motivo={motivo}",
            )
            _salvar_estado(estado)
            print(f"{nome}: piloto impedido pelo guard: {motivo}")
            continue
        declaracao = declaracoes[nome]
        residual = bool(declaracao.get("residual"))
        seed = cfg.SEEDS_TREINO[0]
        por_taxa: dict[str, dict] = {}
        viavel = True
        for taxa in cfg.TAXAS:
            t0_build = time.perf_counter()
            torch.manual_seed(seed)
            modelo = cand.construir_modelo(declaracao, seed=seed).to(dispositivo)
            otimizador = _otimizador(modelo)
            torch.cuda.synchronize()
            t_build = time.perf_counter() - t0_build
            t1 = time.perf_counter()
            perda_t = _epoca_treino(
                modelo, dados["treino"], dispositivo, seed, 1, taxa,
                declaracao, otimizador, np.random.default_rng(seed),
            )
            mse_val, ssim_val = _avaliar_regua(
                modelo, dados["validacao"]["imagens"], dispositivo, taxa, residual
            )
            t_salvo = _salvar_trabalho(
                _caminho_trabalho(nome, seed, taxa, "piloto"),
                {"epoca": 1, "state_dict": modelo.state_dict()},
            )
            carregado = _carregar_trabalho(
                _caminho_trabalho(nome, seed, taxa, "piloto")
            )
            if set(carregado["state_dict"]) != set(modelo.state_dict()):
                raise RuntimeError("I/O de checkpoint divergente no piloto")
            t_ciclo = time.perf_counter() - t1
            if t_salvo > 5.0:
                raise RuntimeError(f"I/O de checkpoint lento demais: {t_salvo:.1f}s")
            segundos = t_build + t_ciclo
            _consumir(contador, nome, "piloto", segundos)
            registrar(
                historico, f"piloto|{nome}", nome, "piloto", seed=seed, taxa=taxa,
                epoca=1, perda_treino=perda_t, perda_validacao=mse_val,
                ssim_validacao=ssim_val, tempo=t_ciclo, estado_l="piloto",
                motivo=f"construcao={t_build:.3f}",
            )
            excedeu = t_ciclo > cfg.LIMIAR_PILOTO_SEGUNDOS
            por_taxa[str(taxa)] = {
                "t_build": t_build,
                "t_ciclo": t_ciclo,
                "perda_treino": perda_t,
                "mse_validacao": mse_val,
                "ssim_validacao": ssim_val,
                "exedeu_limiar": excedeu,
            }
            if excedeu:
                viavel = False
        motivo_piloto = ""
        if not viavel:
            estouradas = [t for t, v in por_taxa.items() if v["exedeu_limiar"]]
            motivo_piloto = (
                f"época piloto excedeu {cfg.LIMIAR_PILOTO_SEGUNDOS}s em {estouradas}; "
                "treinos completos não começam e o saldo não é gasto"
            )
            treinos = estado.setdefault("treinos", {})
            for seed_i in cfg.SEEDS_TREINO:
                for taxa in cfg.TAXAS:
                    treinos.setdefault(
                        f"{nome}|{seed_i}|{taxa}",
                        {"estado": "inviavel", "motivo": motivo_piloto},
                    )
        estado.setdefault("pilotos", {})[nome] = {
            "viavel": viavel, "taxas": por_taxa, "motivo": motivo_piloto,
        }
        _salvar_estado(estado)
        temps = " ".join(f"{t}={v['t_ciclo']:.2f}s" for t, v in por_taxa.items())
        print(f"{nome}: piloto viavel={viavel} [{temps}]")


# ---------------------------------------------------------------- treino


def cmd_treino(args) -> None:
    """Execução (candidato, seed, taxa): até 200 épocas com guard por época."""
    contador, historico, estado = _contexto()
    dispositivo = _dispositivo()
    chave = f"{args.candidato}|{args.seed}|{args.taxa}"
    treinos = estado.setdefault("treinos", {})
    st = treinos.get(chave, {})
    if st.get("estado") == "inviavel":
        print(f"{chave}: inviável pelo piloto; treino completo não começa")
        return
    if st.get("estado") == "completo":
        print(f"{chave}: já completo")
        return
    declaracao = cand.declaracoes()[args.candidato]
    residual = bool(declaracao.get("residual"))
    seed, taxa = int(args.seed), float(args.taxa)
    dados = _carregar_dados()
    execucao = f"treino|{args.candidato}|{args.seed}|{args.taxa}"
    caminho_final = _caminho_trabalho(args.candidato, seed, taxa)

    t0_carga = time.perf_counter()
    ordem_rng = np.random.default_rng(seed)
    if caminho_final.exists():
        payload = _carregar_trabalho(caminho_final)
        epoca0 = int(payload["epoca"])
        modelo = cand.construir_modelo(declaracao).to(dispositivo)
        modelo.load_state_dict(payload["state_dict"])
        otimizador = _otimizador(modelo)
        otimizador.load_state_dict(payload["otimizador"])
        ordem_rng.bit_generator.state = payload["ordem_rng"]
        melhor = payload["melhor"]
        melhor_state = payload["melhor_state"]
        estimativa = float(payload.get("tempo_ciclo", 2.0))
        torch.cuda.synchronize()
        print(f"{chave}: retomando após época {epoca0}")
    else:
        torch.manual_seed(seed)
        modelo = cand.construir_modelo(declaracao, seed=seed).to(dispositivo)
        otimizador = _otimizador(modelo)
        torch.cuda.synchronize()
        epoca0, melhor, melhor_state = 0, None, None
        estimativa = 2.0
        if estado.get("pilotos", {}).get(args.candidato, {}).get("taxas", {}).get(
            str(taxa)
        ):
            estimativa = float(
                estado["pilotos"][args.candidato]["taxas"][str(taxa)]["t_ciclo"]
            )
    t_carga = time.perf_counter() - t0_carga

    interrompido = False
    motivo_interrupto = ""
    epoca = epoca0
    while epoca < cfg.EPOCAS:
        ok, motivo_guard = _guard(
            contador, args.candidato, "treino_por_seed_taxa", estimativa,
            chave=(args.candidato, seed, taxa),
        )
        if not ok:
            interrompido = True
            motivo_interrupto = motivo_guard or "guard falhou"
            break
        epoca_n = epoca + 1
        t_ini = time.perf_counter()
        perda_t = _epoca_treino(
            modelo, dados["treino"], dispositivo, seed, epoca_n, taxa,
            declaracao, otimizador, ordem_rng,
        )
        mse_val, ssim_val = _avaliar_regua(
            modelo, dados["validacao"]["imagens"], dispositivo, taxa, residual
        )
        if melhor is None or mse_val < melhor["perda_validacao"]:
            melhor = {
                "epoca": epoca_n,
                "perda_validacao": mse_val,
                "ssim_validacao": ssim_val,
            }
            melhor_state = {
                k: v.detach().cpu().clone() for k, v in modelo.state_dict().items()
            }
        t_ciclo = time.perf_counter() - t_ini
        t_salvo = _salvar_trabalho(
            caminho_final,
            {
                "epoca": epoca_n,
                "state_dict": modelo.state_dict(),
                "otimizador": otimizador.state_dict(),
                "ordem_rng": ordem_rng.bit_generator.state,
                "melhor": melhor,
                "melhor_state": melhor_state,
                "tempo_ciclo": t_ciclo,
            },
        )
        dt_total = t_ciclo + t_salvo + t_carga
        t_carga = 0.0
        _consumir(
            contador, args.candidato, "treino_por_seed_taxa", dt_total,
            chave=(args.candidato, seed, taxa),
        )
        registrar(
            historico, execucao, args.candidato, "epoca", seed=seed, taxa=taxa,
            epoca=epoca_n, perda_treino=perda_t, perda_validacao=mse_val,
            ssim_validacao=ssim_val, tempo=dt_total, estado_l="concluido",
        )
        epoca = epoca_n
        estimativa = t_ciclo
        print(
            f"{chave} ep{epoca}/{cfg.EPOCAS}: treino {perda_t:.4f} val {mse_val:.4f} "
            f"ssim {ssim_val:.4f} ({t_ciclo:.2f}s)",
            flush=True,
        )

    if not interrompido and epoca >= cfg.EPOCAS:
        treinos[chave] = {
            "estado": "completo", "epocas": epoca, "melhor": melhor, "motivo": "",
        }
    else:
        treinos[chave] = {
            "estado": "interrompido", "epocas": epoca, "melhor": melhor,
            "motivo": motivo_interrupto,
        }
        registrar(
            historico, execucao, args.candidato, "erro", seed=seed, taxa=taxa,
            epoca=epoca, tempo=0.0, estado_l="interrompido",
            motivo=f"motivo={motivo_interrupto};epocas={epoca}",
        )
    _salvar_estado(estado)
    if melhor is not None:
        _salvar_trabalho(
            _caminho_trabalho(args.candidato, seed, taxa, "melhor"),
            {"epoca": melhor["epoca"], "state_dict": melhor_state},
        )
    print(
        f"{chave}: estado={treinos[chave]['estado']} epocas={epoca} "
        + (
            f"melhor={melhor['perda_validacao']:.6f}@{melhor['epoca']}"
            if melhor is not None
            else "sem época completa"
        )
    )


# ------------------------------------------------------------ consolidação


def cmd_consolidar(args) -> None:
    """Cópias imutáveis do melhor e do final por execução, com hash (D3)."""
    contador, historico, estado = _contexto()
    treinos = estado.get("treinos", {})
    alvo = args.candidato
    t_total = 0.0
    consolidado = estado.setdefault("consolidado", {})
    for chave in sorted(treinos):
        nome, seed, taxa = chave.split("|")
        if alvo and nome != alvo:
            continue
        st = treinos[chave]
        if not st.get("melhor") or consolidado.get(chave):
            continue
        ok, motivo = _guard(contador, nome, "consolidacao", 15.0)
        if not ok:
            print(f"consolidação de {chave}: guard impediu ({motivo}); sem cópia")
            break
        t_ini = time.perf_counter()
        caminho_final = _caminho_trabalho(nome, int(seed), float(taxa))
        caminho_melhor = _caminho_trabalho(nome, int(seed), float(taxa), "melhor")
        if not caminho_melhor.exists():
            if not caminho_final.exists():
                raise RuntimeError(f"trabalho ausente para {chave}")
            _salvar_trabalho(
                caminho_melhor,
                {
                    "epoca": st["melhor"]["epoca"],
                    "state_dict": _carregar_trabalho(caminho_final)["melhor_state"],
                },
            )
        if not caminho_final.exists():
            raise RuntimeError(f"trabalho final ausente para {chave}")
        prefixo = f"{nome}_s{seed}_t{taxa}"
        copia_m = ckpt.copiar_imutavel(
            caminho_melhor, DIR_CKPT_IMUT, f"{prefixo}_melhor",
            epoca=st["melhor"]["epoca"],
        )
        registrar(
            historico, f"checkpoint|{chave}", nome, "checkpoint", seed=seed,
            taxa=taxa, epoca=st["melhor"]["epoca"], tempo=0.0,
            estado_l="melhor", motivo=f"sha256={copia_m['sha256']};papel=melhor",
        )
        copia_f = ckpt.copiar_imutavel(
            caminho_final, DIR_CKPT_IMUT, f"{prefixo}_final", epoca=st["epocas"]
        )
        registrar(
            historico, f"checkpoint|{chave}", nome, "checkpoint", seed=seed,
            taxa=taxa, epoca=st["epocas"], tempo=0.0,
            estado_l="final", motivo=f"sha256={copia_f['sha256']};papel=final",
        )
        t_total += time.perf_counter() - t_ini
        consolidado[chave] = {
            "melhor": copia_m, "final": copia_f, "epoca_melhor": st["melhor"]["epoca"],
        }
    _consumir(contador, alvo or "global", "consolidacao", t_total)
    _salvar_estado(estado)
    print(f"consolidação {alvo or 'todos'}: {t_total:.1f}s em cópias")


# ---------------------------------------------------------------- controles


def _patches_do_split(imagens: np.ndarray) -> torch.Tensor:
    from codigo.mae import patchify

    return patchify(
        torch.from_numpy(imagens.transpose(0, 3, 1, 2)).float()
    )


def _controle_reconstrucoes(
    nome: str,
    imagens: np.ndarray,
    regua_np: np.ndarray,
    media_treino: np.ndarray | None,
) -> np.ndarray:
    funcao = (
        bas.media_rgb_visivel if nome == "controle_media_rgb"
        else bas.interpolacao_espacial
    )
    reconstrucoes = np.stack(
        [
            funcao(
                imagens[i].transpose(2, 0, 1),
                regua_np[i].tolist(),
                media_treino,
            )
            for i in range(len(imagens))
        ]
    ).astype(np.float32)
    return reconstrucoes.transpose(0, 2, 3, 1)  # volta para (N, 32, 32, 3)


def cmd_controles(args) -> None:
    """Controles determinísticos na validação: uma vez por taxa e imagem (D4/D6)."""
    contador, historico, estado = _contexto()
    if estado.get("controles"):
        print("controles de validação já registrados")
        return
    dados = _carregar_dados()
    _dispositivo()
    media_treino = dados["treino"]["imagens"].reshape(-1, 3).mean(axis=0)
    t0 = time.perf_counter()
    por_taxa: dict[str, dict] = {}
    for taxa in cfg.TAXAS:
        regua_t = aval.regua_validacao(
            len(dados["validacao"]["imagens"]), taxa
        )
        alvo = _patches_do_split(dados["validacao"]["imagens"])  # CPU
        registro: dict[str, dict] = {}
        for nome in NOME_CONTROLES:
            rec = _patches_do_split(
                _controle_reconstrucoes(
                    nome, dados["validacao"]["imagens"], regua_t.numpy(), media_treino
                )
            )
            m = aval.mse_regua(rec, alvo, regua_t)
            s = aval.ssim_regua(rec, alvo, regua_t)
            registro[nome] = {"mse": m, "ssim": float(s)}
        por_taxa[str(taxa)] = registro
    dt = time.perf_counter() - t0
    _consumir(contador, "global", "avaliacao", dt)
    for taxa, registro in por_taxa.items():
        for nome, v in registro.items():
            for seed in cfg.SEEDS_TREINO:
                registrar(
                    historico, f"controle|{nome}|{taxa}", nome, "controle",
                    seed=seed, taxa=taxa, perda_validacao=v["mse"],
                    ssim_validacao=v["ssim"], tempo=0.0, estado_l="validacao",
                    motivo="medida_uma_vez_por_taxa_imagem",
                )
    estado["controles"] = por_taxa
    _salvar_estado(estado)
    for taxa, registro in por_taxa.items():
        for nome, v in registro.items():
            print(
                f"controle {nome}@{taxa}: mse={v['mse']:.4f} ssim={v['ssim']:.4f}"
            )
    print(f"controles validação: {dt:.1f}s")


# -------------------------------------------------------------------- C3


def cmd_decidir_c3(args) -> None:
    """C3 só executável se C0 vencer cada baseline nas duas taxas e com saldo."""
    contador, historico, estado = _contexto()
    if estado.get("decisao_c3"):
        print("decisão de C3 já registrada")
        return
    if not estado.get("controles"):
        raise RuntimeError("controles de validação ausentes: rode 'controles'")
    melhor_por = _melhor_por_execucao(historico)
    c0_completos = all(
        ("C0", s, t) in melhor_por for s in cfg.SEEDS_TREINO for t in cfg.TAXAS
    )
    if not c0_completos:
        motivo = (
            "C0 sem treinos completos (inviável pelo limiar de 1,2 s do piloto): "
            "o critério de média de MSE de C0 contra cada baseline não é "
            "verificável; C3 registrado como NÃO EXECUTADO"
        )
        desconto = cfg.CONFIG["orcamento"]["avaliacao_final_baselines_minutos"]
        estado["decisao_c3"] = {
            "elegivel": False,
            "motivo": motivo,
            "minutos_livres": contador.saldo_principal() - desconto,
        }
        registrar(
            historico, "decisao|C3", "C3", "selecao", estado_l="nao_elegivel",
            motivo=f"motivo={motivo}",
        )
        _salvar_estado(estado)
        print(f"C3 elegivel=False: {motivo}")
        return
    mse_c0 = {}
    for taxa in cfg.TAXAS:
        valores = [melhor_por[("C0", s, taxa)]["perda_validacao"]
                   for s in cfg.SEEDS_TREINO if ("C0", s, taxa) in melhor_por]
        if len(valores) != len(cfg.SEEDS_TREINO):
            raise RuntimeError(f"C0 sem execução completa na taxa {taxa}")
        mse_c0[taxa] = statistics.median(valores)
    baselines = {
        nome: {t: estado["controles"][str(t)][nome]["mse"]
               for t in cfg.TAXAS}
        for nome in NOME_CONTROLES
    }
    desconto = cfg.CONFIG["orcamento"]["avaliacao_final_baselines_minutos"]
    minutos_livres = contador.saldo_principal() - desconto
    elegivel, motivo = cand.elegibilidade_c3(
        mse_c0, baselines, minutos_livres
    )
    estado["decisao_c3"] = {
        "elegivel": elegivel,
        "motivo": motivo,
        "minutos_livres": minutos_livres,
    }
    registrar(
        historico, "decisao|C3", "C3", "selecao",
        estado_l="elegivel" if elegivel else "nao_elegivel",
        motivo=f"motivo={motivo}",
    )
    _salvar_estado(estado)
    print(f"C3 elegivel={elegivel}: {motivo}")


# --------------------------------------------------------------- seleção


def _listas_candidato(
    melhor_por: dict[tuple, dict], taxa: float, nome: str
) -> tuple[list[float], list[float]] | None:
    if not all((nome, s, taxa) in melhor_por for s in cfg.SEEDS_TREINO):
        return None
    mse = [melhor_por[(nome, s, taxa)]["perda_validacao"] for s in cfg.SEEDS_TREINO]
    ssim = [melhor_por[(nome, s, taxa)]["ssim_validacao"] for s in cfg.SEEDS_TREINO]
    return mse, ssim


def cmd_selecao(args) -> None:
    """Regra congelada (D6) only validação; nenhum contato com teste."""
    contador, historico, estado = _contexto()
    if estado.get("selecao"):
        print("seleção já registrada")
        return
    melhor_por = _melhor_por_execucao(historico)
    tempos = {
        nome: contador.gasto_principal(nome) for nome in cfg.CANDIDATOS
    }
    selecao: dict[str, dict] = {}
    for taxa in cfg.TAXAS:
        c0 = _listas_candidato(melhor_por, taxa, "C0")
        resultado_taxa: dict = {}
        if c0 is None:
            resultado_taxa = {
                "vencedor": None,
                "elegiveis": [],
                "motivo": (
                    "referência C0 sem treinos completos (inviável pelo limiar "
                    "de 1,2 s do piloto): regra de elegibilidade contra C0 não "
                    "pôde ser aplicada; ausência de melhoria demonstrada"
                ),
                "motivos": {},
            }
            registrar(
                historico, f"selecao|{taxa}|global", "global", "selecao",
                taxa=taxa, estado_l="nao_executada",
                motivo=f"motivo={resultado_taxa['motivo']}",
            )
            selecao[str(taxa)] = resultado_taxa
            continue
        resultado_taxa = {"vencedor": None, "motivo": "sem candidatos treinados"}
        candidatos_ok = [
            nome for nome in ("C1", "C2", "C3")
            if _listas_candidato(melhor_por, taxa, nome) is not None
        ]
        if candidatos_ok:
            mse_cand = {n: _listas_candidato(melhor_por, taxa, n)[0]
                        for n in candidatos_ok}
            ssim_cand = {n: _listas_candidato(melhor_por, taxa, n)[1]
                         for n in candidatos_ok}
            resultado = sel.selecionar(
                mse_cand, ssim_cand, c0[0], c0[1], tempos,
            )
            resultado_taxa = resultado
            for nome, mg in resultado["motivos"].items():
                registrar(
                    historico, f"selecao|{nome}|{taxa}", nome, "selecao", taxa=taxa,
                    estado_l="elegivel" if nome in resultado["elegiveis"]
                    else "nao_elegivel",
                    motivo=f"motivo={mg}",
                )
        registrar(
            historico, f"selecao|{taxa}|global", "global", "selecao", taxa=taxa,
            estado_l="vencedor" if resultado_taxa.get("vencedor")
            else "sem_elegivel",
            motivo=f"motivo={resultado_taxa.get('motivo')}",
        )
        selecao[str(taxa)] = resultado_taxa
    estado["selecao"] = selecao
    _salvar_estado(estado)
    for taxa, res in selecao.items():
        print(f"taxa {taxa}: vencedor={res.get('vencedor')} ({res.get('motivo')})")


def cmd_congelar_final(args) -> None:
    """Barreira de avaliação: congela seleção; nada mais reabre a escolha."""
    contador, historico, estado = _contexto()
    if estado.get("congelamento_final"):
        print("congelamento final já registrado")
        return
    if not estado.get("selecao"):
        raise RuntimeError("seleção ausente: rode 'selecao' antes")
    texto = json.dumps(estado["selecao"], ensure_ascii=False, sort_keys=True)
    hash_selecao = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    estado["congelamento_final"] = {
        "hash_selecao": hash_selecao,
        "ids_visuais": estado.get("ids_visuais", {}),
        "regras": cfg.VERSAO_REGRAS,
        "hash_manifesto": cfg.hash_configuracao(),
    }
    registrar(
        historico, "congelar_final", "global", "selecao",
        estado_l="congelado_final", motivo=f"hash_selecao={hash_selecao[:16]}",
    )
    _salvar_estado(estado)
    print(f"congelamento final: hash={hash_selecao[:16]}")


# -------------------------------------------------------- avaliação final


def cmd_avaliacao_final(args) -> None:
    """Única avaliação de teste, na régua; eventos avaliacao_final."""
    contador, historico, estado = _contexto()
    if estado.get("avaliacao_final"):
        print("avaliação final já registrada")
        return
    if not estado.get("congelamento_final"):
        raise RuntimeError("barreira ausente: rode 'congelar-final' antes")
    t0 = time.perf_counter()
    dados = _carregar_dados()
    dispositivo = _dispositivo()
    imagens_teste = dados["teste"]["imagens"]
    consolidado = estado.get("consolidado", {})
    media_treino = dados["treino"]["imagens"].reshape(-1, 3).mean(axis=0)
    resultado: dict = {"controles": {}, "candidatos": {}}
    for taxa in cfg.TAXAS:
        taxa_s = str(taxa)
        vencedor = estado["selecao"][taxa_s].get("vencedor")
        lista = [vencedor] if vencedor else []
        regua_teste = aval.regua_validacao(len(imagens_teste), taxa)
        regua_np = regua_teste.numpy()
        alvo = _patches_do_split(imagens_teste)  # CPU: módulo SSIM usa kernel CPU
        resultado["controles"][taxa_s] = {}
        for nome in NOME_CONTROLES:
            rec = _patches_do_split(
                _controle_reconstrucoes(nome, imagens_teste, regua_np, media_treino)
            )
            resultado["controles"][taxa_s][nome] = {
                "mse": aval.mse_regua(rec, alvo, regua_teste),
                "ssim": float(aval.ssim_regua(rec, alvo, regua_teste)),
            }
        resultado["candidatos"][taxa_s] = {}
        for nome in lista:
            por_seed = {}
            for seed in cfg.SEEDS_TREINO:
                chave = f"{nome}|{seed}|{taxa}"
                info = consolidado.get(chave) or {}
                caminho = (
                    Path(info["melhor"]["caminho"]) if info.get("melhor") else
                    _caminho_trabalho(nome, seed, taxa, "melhor")
                )
                if not caminho.exists():
                    raise RuntimeError(f"checkpoint melhor ausente: {chave}")
                payload = _carregar_trabalho(caminho)
                modelo = cand.construir_modelo(cfg.CANDIDATOS[nome])
                modelo.load_state_dict(payload["state_dict"])
                modelo = modelo.to(dispositivo)
                residual = bool(cfg.CANDIDATOS[nome].get("residual"))
                mse, ssim = _avaliar_regua(
                    modelo, imagens_teste, dispositivo, taxa, residual
                )
                por_seed[str(seed)] = {
                    "mse": mse, "ssim": ssim, "epoca": int(payload["epoca"]),
                }
            resultado["candidatos"][taxa_s][nome] = {
                "por_seed": por_seed,
                "mediana_mse": statistics.median(
                    v["mse"] for v in por_seed.values()
                ),
                "mediana_ssim": statistics.median(
                    v["ssim"] for v in por_seed.values()
                ),
            }
    dt = time.perf_counter() - t0
    _consumir(contador, "global", "avaliacao_final", dt)
    for taxa_s, por in resultado["candidatos"].items():
        for nome, valores in por.items():
            for seed_str, v in valores["por_seed"].items():
                registrar(
                    historico, f"final|{nome}|{seed_str}|{taxa_s}", nome,
                    "avaliacao_final", seed=seed_str, taxa=taxa_s,
                    epoca=v["epoca"], perda_validacao=v["mse"],
                    ssim_validacao=v["ssim"], tempo=0.0, estado_l="teste",
                    motivo="regime=avaliado_uma_vez_apos_congelamento",
                )
        for nome, v in resultado["controles"][taxa_s].items():
            for seed in cfg.SEEDS_TREINO:
                registrar(
                    historico, f"controle|{nome}|{taxa_s}", nome, "controle",
                    seed=seed, taxa=taxa_s, perda_validacao=v["mse"],
                    ssim_validacao=v["ssim"], tempo=0.0, estado_l="teste",
                    motivo="medida_uma_vez_por_taxa_imagem",
                )
    estado["avaliacao_final"] = resultado
    _salvar_estado(estado)
    print(f"avaliação final: {dt:.1f}s")
    for taxa_s, por in resultado["candidatos"].items():
        for nome, valores in por.items():
            print(
                f" teste {nome}@{taxa_s}: mse med {valores['mediana_mse']:.4f} "
                f"ssim med {valores['mediana_ssim']:.4f}"
            )


# ----------------------------------------------------------------- resumo


def cmd_resumo(args) -> None:
    """Resumo derivado do histórico e do estado; números nunca digitados."""
    contador, historico, estado = _contexto()
    melhor_por = _melhor_por_execucao(historico)
    treinos_resumo = {}
    for chave, info in sorted(estado.get("treinos", {}).items()):
        nome, seed, taxa = chave.split("|")
        melhor = melhor_por.get((nome, int(seed), float(taxa)))
        treinos_resumo[chave] = {
            "estado": info.get("estado"),
            "epocas": info.get("epocas", 0),
            "melhor": melhor,
            "motivo": info.get("motivo", ""),
        }
    por_candidato = {
        nome: contador.gasto_principal(nome) for nome in cfg.CANDIDATOS
    }
    por_categoria: dict[str, float] = {}
    for r in contador.registros:
        por_categoria[r["categoria"]] = (
            por_categoria.get(r["categoria"], 0.0) + float(r["minutos"])
        )
    resumo = {
        "versao_regras": cfg.VERSAO_REGRAS,
        "hash_manifesto": estado.get("hash_manifesto"),
        "versao_split": estado.get("versao_split"),
        "codigo_hash": estado.get("codigo_hash"),
        "pilotos": estado.get("pilotos", {}),
        "treinos": treinos_resumo,
        "controles": estado.get("controles", {}),
        "decisao_c3": estado.get("decisao_c3"),
        "selecao": estado.get("selecao"),
        "congelamento_final": estado.get("congelamento_final"),
        "avaliacao_final": estado.get("avaliacao_final"),
        "tempo": {
            "principal_minutos": contador.total_principal,
            "reserva_minutos": contador.total_reserva,
            "por_candidato": por_candidato,
            "por_categoria": por_categoria,
        },
    }
    ARQ_RESUMO.parent.mkdir(parents=True, exist_ok=True)
    ARQ_RESUMO.write_text(
        json.dumps(resumo, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"resumo em {ARQ_RESUMO}")


# ---------------------------------------------------------------- figuras


def _curvas_validacao(historico) -> dict[tuple, dict[int, list[float]]]:
    """(candidato, taxa) -> {epoca: [mse por seed]} do CSV."""
    saida: dict[tuple, dict[int, list[float]]] = {}
    for r in historico.linhas():
        if r["evento"] != "epoca" or not r["perda_validacao"]:
            continue
        partes = r["execucao"].split("|")
        if partes[0] != "treino":
            continue
        _, nome, seed, taxa = partes
        chave = (nome, taxa)
        dicionario = saida.setdefault(chave, {})
        dicionario.setdefault(int(r["epoca"]), []).append(
            float(r["perda_validacao"])
        )
    return saida


def _fonte_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def cmd_figuras(args) -> None:
    """Figuras derivadas do histórico, do estado e dos contadores."""
    _, historico, estado = _contexto()
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    plt = _fonte_matplotlib()
    curvas = _curvas_validacao(historico)
    melhor_por = _melhor_por_execucao(historico)
    candidatos = [
        n for n in ("C0", "C1", "C2", "C3")
        if any(k.startswith(n) for k in estado.get("treinos", {}))
    ]
    if not candidatos:
        print("sem treinos para figuras")
        return
    rotulos = {
        "C0": "C0 (MAE direto)",
        "C1": "C1 (decoder maior)",
        "C2": "C2 (MSE + 0,1 L1)",
        "C3": "C3 (residual)",
    }
    for figura in list(DIR_FIGURAS.glob("*.png")):
        figura.unlink()
    # 1) curvas de validação mediana por época
    fig, eixos = plt.subplots(1, len(cfg.TAXAS), figsize=(6 * len(cfg.TAXAS), 4.5))
    if len(cfg.TAXAS) == 1:
        eixos = [eixos]
    for eixo, taxa in zip(eixos, cfg.TAXAS):
        for nome in candidatos:
            dicionario = curvas.get((nome, str(taxa)))
            if not dicionario:
                continue
            epocas = sorted(dicionario)
            mediana = [statistics.median(dicionario[e]) for e in epocas]
            eixo.plot(epocas, mediana, label=rotulos.get(nome, nome))
        eixo.set_title(f"validação na régua (mediana de seeds), taxa {taxa}")
        eixo.set_xlabel("época")
        eixo.set_ylabel("mse nos patches ocultos")
        eixo.legend()
        eixo.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(DIR_FIGURAS / "curvas_validacao.png", dpi=120)
    plt.close(fig)
    # 2) melhor de validação: medianas de MSE e SSIM
    taxas_existentes = [
        taxa for taxa in cfg.TAXAS
        if any((nome, s, taxa) in melhor_por for s in cfg.SEEDS_TREINO)
    ]
    if taxas_existentes:
        fig, eixos = plt.subplots(1, len(taxas_existentes), figsize=(7 * len(taxas_existentes), 4.5))
        if len(taxas_existentes) == 1:
            eixos = [eixos]
        for eixo, taxa in zip(eixos, taxas_existentes):
            nomes_com = [
                n for n in candidatos
                if all((n, s, taxa) in melhor_por for s in cfg.SEEDS_TREINO)
            ]
            med_mse = [statistics.median(
                melhor_por[(n, s, taxa)]["perda_validacao"] for s in cfg.SEEDS_TREINO
            ) for n in nomes_com]
            med_ssim = [statistics.median(
                melhor_por[(n, s, taxa)]["ssim_validacao"] for s in cfg.SEEDS_TREINO
            ) for n in nomes_com]
            pos = range(len(nomes_com))
            eixo.bar(pos, med_mse, color="#3b6fb6", width=0.4)
            for p, v in zip(pos, med_mse):
                eixo.text(p, v, f"{v:.4f}", ha="center", va="bottom", fontsize=8)
            eixo.set_title(f"melhor validação na régua (mediana de seeds), taxa {taxa}")
            eixo.set_ylabel("mse mediana por seed")
            eixo.set_ylim(0, max(med_mse) * 1.25 if med_mse else 1)
            eixo2 = eixo.twinx()
            pos2 = len(nomes_com) + np.arange(len(nomes_com))
            eixo2.bar(pos2, med_ssim, color="#b6543b", width=0.4)
            for p, v in zip(pos2, med_ssim):
                eixo2.text(p, v, f"{v:.4f}", ha="center", va="bottom", fontsize=8)
            eixo2.set_ylabel("ssim mediana por seed")
            eixo2.set_ylim(0, max(med_ssim) * 1.25 if med_ssim else 1)
            eixo.set_xticks(list(pos) + list(pos2))
            eixo.set_xticklabels(nomes_com * 2)
        fig.tight_layout()
        fig.savefig(DIR_FIGURAS / "melhores_validacao.png", dpi=120)
        plt.close(fig)
    # 3) avaliação final de teste
    af = estado.get("avaliacao_final")
    if af:
        fig, eixos = plt.subplots(1, len(cfg.TAXAS), figsize=(6 * len(cfg.TAXAS), 4.5))
        if len(cfg.TAXAS) == 1:
            eixos = [eixos]
        for eixo, taxa in zip(eixos, cfg.TAXAS):
            por = af["candidatos"].get(str(taxa), {})
            nomes_com = list(por)
            if not nomes_com:
                continue
            valores = [por[n]["mediana_mse"] for n in nomes_com]
            eixo.bar(nomes_com, valores, color="#3b6fb6")
            for p, v in enumerate(valores):
                eixo.text(p, v, f"{v:.4f}", ha="center", va="bottom", fontsize=8)
            for nome in NOME_CONTROLES:
                icone = af["controles"].get(str(taxa), {}).get(nome)
                if icone:
                    eixo.axhline(
                        icone["mse"], linestyle="--", alpha=0.7,
                        label=f"{nome} (controle)",
                    )
            eixo.set_title(f"avaliação final no teste (mediana de seeds), taxa {taxa}")
            eixo.set_ylabel("mse nos patches ocultos")
            eixo.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(DIR_FIGURAS / "avaliacao_final.png", dpi=120)
        plt.close(fig)
    print(f"figuras em {DIR_FIGURAS}")


# ------------------------------------------------------------------ ficha


def cmd_ficha(args) -> None:
    """Reconstruções dos IDs visuais e ficha cega pronta para humanos."""
    _, historico, estado = _contexto()
    if not estado.get("ids_visuais"):
        raise RuntimeError("ids visuais ausentes no estado congelado")
    dados = _carregar_dados()
    imagens_val = dados["validacao"]["imagens"]
    indices_val = dados["validacao"]["indices_originais"]
    ids = [int(i) for i in estado["ids_visuais"]["ids"]]
    conjunto = set(ids)
    linhas = [i for i, io in enumerate(indices_val) if int(io) in conjunto]
    if len(linhas) != len(ids):
        raise RuntimeError("linhas dos IDs visuais não correspondem ao split")
    dispositivo = _dispositivo()
    consolidado = estado.get("consolidado", {})
    candidatos_rede = [
        "C0", "C1", "C2", "C3",
    ]
    DIR_FICHA.mkdir(parents=True, exist_ok=True)
    rotulos_mapa: dict[str, dict] = {"colunas": {}}
    for taxa in cfg.TAXAS:
        regua = aval.regua_validacao(len(imagens_val), taxa)
        regua_np = regua.numpy()
        colunas = ["original", "controle_media_rgb", "controle_interpolacao"]
        colunas += [
            c for c in candidatos_rede
            if any(k.startswith(f"{c}|") for k in consolidado)
        ]
        letras = {c: chr(65 + k) for k, c in enumerate(colunas)}
        grade = np.zeros((len(ids), len(colunas), 32, 32, 3), dtype=np.float32)
        for k_linha, linha in enumerate(linhas):
            imagem = imagens_val[linha]
            ocultos = regua_np[linha].tolist()
            grade[k_linha, 0] = imagem
            grade[k_linha, 1] = bas.media_rgb_visivel(
                imagem.transpose(2, 0, 1), ocultos, None
            ).transpose(1, 2, 0)
            grade[k_linha, 2] = bas.interpolacao_espacial(
                imagem.transpose(2, 0, 1), ocultos, None
            ).transpose(1, 2, 0)
            for j, nome in enumerate(colunas):
                if j < 3:
                    continue
                chave = next(
                    f"{nome}|{s}|{taxa}" for s in cfg.SEEDS_TREINO
                    if f"{nome}|{s}|{taxa}" in consolidado
                )
                caminho = Path(consolidado[chave]["melhor"]["caminho"])
                payload = _carregar_trabalho(caminho)
                modelo = cand.construir_modelo(cfg.CANDIDATOS[nome])
                modelo.load_state_dict(payload["state_dict"])
                modelo = modelo.to(dispositivo)
                residual = bool(cfg.CANDIDATOS[nome].get("residual"))
                regua_uno = regua[linha : linha + 1].to(dispositivo)
                with torch.no_grad():
                    modelo.eval()
                    x = torch.from_numpy(
                        imagem.transpose(2, 0, 1)[None]
                    ).float().to(dispositivo)
                    saida = modelo(x, indices_mascarados=regua_uno)
                    if residual:
                        preench = _preenchimento(saida["patches"].detach(), regua_uno)
                        composto = cand.composicao_residual(
                            preench, saida["predicao"], regua_uno
                        )
                        rec = unpatchify(composto)[0].cpu().numpy()
                    else:
                        rec = reconstrucao_completa(
                            saida["predicao"], saida["patches"], regua_uno
                        )[0].cpu().numpy()
                grade[k_linha, j] = np.clip(rec.transpose(1, 2, 0), 0.0, 1.0)
        plt = _fonte_matplotlib()
        fig, eixo = plt.subplots(
            len(ids), len(colunas), figsize=(2.2 * len(colunas), 2.6 * len(ids))
        )
        matriz_eixo = np.atleast_2d(eixo)
        for k_linha in range(len(ids)):
            for j in range(len(colunas)):
                aonde = matriz_eixo[k_linha, j]
                aonde.imshow(np.clip(grade[k_linha, j], 0.0, 1.0))
                aonde.set_xticks([])
                aonde.set_yticks([])
                if k_linha == 0:
                    rotulo = (
                        colunas[j] if colunas[j] == "original"
                        else letras[colunas[j]]
                    )
                    aonde.set_title(rotulo, fontsize=9)
        rotulacao = (
            f"taxa {taxa}; rótulos anônimos: "
            + ", ".join(f"{letras[c]}={c}" for c in colunas if c != "original")
        )
        fig.suptitle(
            f"reconstruções dos IDs de inspeção; mapeamento em ficha-rotulos.json "
            f"({rotulacao})",
            fontsize=7,
        )
        fig.tight_layout()
        alvo_png = DIR_FICHA / f"ficha_{int(taxa * 100)}.png"
        fig.savefig(alvo_png, dpi=110)
        plt.close(fig)
        rotulos_mapa["colunas"][str(taxa)] = {
            "arquivo": alvo_png.name,
            "letra_para_candidato": letras,
        }
    ficha = vis.ficha_visual(_versao_split(), indices_val.tolist())
    informacao = vis.salvar_ficha(ficha, DIR_FICHA / "ficha_visual.json")
    rotulos_mapa["ficha_json"] = informacao
    rotulos_mapa["avisos"] = (
        "avaliação humana não realizada nesta fase; as notas ficam para os "
        "avaliadores humano(s); evidência qualitativa, sem alterar a seleção"
    )
    (DIR_FICHA / "ficha-rotulos.json").write_text(
        json.dumps(rotulos_mapa, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"ficha em {DIR_FICHA}: {sorted(p.name for p in DIR_FICHA.iterdir())}")


# ------------------------------------------------------------------- main


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("congelar", help="congela manifesto, split e IDs visuais")
    parser_piloto = sub.add_parser("piloto", help="pilotos de uma época por taxa")
    parser_piloto.add_argument("--candidato", choices=tuple(cfg.CANDIDATOS), default=None)
    parser_treino = sub.add_parser("treino", help="execução completa com guards")
    parser_treino.add_argument("--candidato", required=True, choices=tuple(cfg.CANDIDATOS))
    parser_treino.add_argument("--seed", type=int, required=True)
    parser_treino.add_argument("--taxa", type=float, choices=(0.5, 0.75), required=True)
    parser_consol = sub.add_parser("consolidar", help="cópias imutáveis com hash")
    parser_consol.add_argument("--candidato", choices=tuple(cfg.CANDIDATOS), default=None)
    sub.add_parser("controles", help="controles determinísticos na validação")
    sub.add_parser("decidir-c3", help="critério de elegibilidade do C3")
    sub.add_parser("selecao", help="regra congelada (D6) apenas na validação")
    sub.add_parser("congelar-final", help="barreira antes da única avaliação de teste")
    sub.add_parser("avaliacao-final", help="única avaliação de teste na régua")
    sub.add_parser("resumo", help="resumo derivado do histórico")
    sub.add_parser("figuras", help="figuras derivadas do histórico")
    sub.add_parser("ficha", help="ficha visual cega e reconstruções")
    args = parser.parse_args()
    acoes = {
        "congelar": cmd_congelar,
        "piloto": cmd_piloto,
        "treino": cmd_treino,
        "consolidar": cmd_consolidar,
        "controles": cmd_controles,
        "decidir-c3": cmd_decidir_c3,
        "selecao": cmd_selecao,
        "congelar-final": cmd_congelar_final,
        "avaliacao-final": cmd_avaliacao_final,
        "resumo": cmd_resumo,
        "figuras": cmd_figuras,
        "ficha": cmd_ficha,
    }
    acoes[args.comando](args)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
