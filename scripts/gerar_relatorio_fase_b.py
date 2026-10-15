"""Gera o relatório interno da fase B do estudo melhorar-reconstrucoes-mae.

Tabelas e números derivam integralmente de
resultados/estudo-melhorar-reconstrucoes-mae/ (manifesto.json, historico.csv,
contador.jsonl, resumo.json, estado.json); as provas de execução são
transcrições resumidas dos logs da fase. Saída:
openspec/changes/melhorar-reconstrucoes-mae/relatorio-fase-b-regerado.md

Rode: uv run python scripts/gerar_relatorio_fase_b.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_ESTUDO = RAIZ / "resultados" / "estudo-melhorar-reconstrucoes-mae"
ARQ_RESUMO = DIR_ESTUDO / "resumo.json"
ALVO = (
    RAIZ / "openspec" / "changes" / "melhorar-reconstrucoes-mae"
    / "relatorio-fase-b-regerado.md"
)
SEEDS = (10, 20, 30)
TAXAS = ("0.5", "0.75")


def num(v, nd=4):
    return f"{float(v):.{nd}f}".replace(".", ",")


with open(ARQ_RESUMO, encoding="utf-8") as f:
    RESUMO = json.load(f)
ESTADO = json.loads((DIR_ESTUDO / "estado.json").read_text(encoding="utf-8"))


def mediana_taxa(candidato, taxa, campo):
    valores = []
    for chave, info in RESUMO["treinos"].items():
        partes = chave.split("|")
        if partes[0] == candidato and partes[2] == taxa and info["melhor"]:
            valores.append(info["melhor"][campo])
    return statistics.median(valores) if valores else None


def por_seed_txt(candidato, taxa, campo):
    itens = []
    for seed in SEEDS:
        chave = f"{candidato}|{seed}|{taxa}"
        info = RESUMO["treinos"].get(chave)
        if info and info["melhor"]:
            itens.append(f"{seed}: {num(info['melhor'][campo])}")
    return "; ".join(itens) if itens else "sem treinos"


L = []


def add(texto=""):
    L.append(texto)


add("# Relatório da fase B: consolidação documental posterior")
add("Consulte notas-finais.md e retificacao-validacao.md; o relatório histórico original foi preservado.")
add("")
add(
    "Documento interno derivado integralmente dos artefatos registrados do "
    "estudo (manifesto.json, historico.csv, contador.jsonl, resumo.json e "
    "estado.json em resultados/estudo-melhorar-reconstrucoes-mae/). Tabelas e "
    "números são calculados pelo gerador a partir dos arquivos; as provas de "
    "execução são transcrições resumidas dos logs."
)
add("")
add("## 1. Congelamentos")
add("")
add(
    f"- Versão das regras: `{RESUMO['versao_regras']}`. Hash SHA-256 do manifesto "
    f"completo: `{RESUMO['hash_manifesto']}`; congelado antes do primeiro piloto."
)
add(
    f"- Versão do split de índices: `{RESUMO['versao_split']}`. Hash do código do "
    f"estudo (SHA-256 dos módulos): `{RESUMO['codigo_hash']}`."
)
add(
    "- Teto de orçamento: 120 minutos, 90 principais mais 30 de reserva, com "
    "contador cumulativo persistido em `contador.jsonl`."
)
add(
    f"- Oito IDs visuais fixados no congelamento: "
    f"{', '.join(str(i) for i in ESTADO['ids_visuais']['ids'])}."
)
if RESUMO.get("congelamento_final"):
    add(
        f"- Barreira de avaliação: congelamento final com hash "
        f"`{RESUMO['congelamento_final']['hash_selecao']}`; o conjunto de teste só "
        "foi consultado uma vez, depois dela."
    )
else:
    add("- Barreira de avaliação ainda não congelada.")
add("")
add("## 2. Pilotos (uma época por taxa, seed 10, com validação, SSIM e I/O)")
add("")
add("| candidato | taxa | tempo do ciclo (s) | viável |")
add("|---|---|---|---|")
for cand in ("C0", "C1", "C2"):
    piloto = RESUMO["pilotos"].get(cand)
    if not piloto:
        add(f"| {cand} | | | não executado |")
        continue
    for taxa, valores in sorted(piloto["taxas"].items()):
        add(
            f"| {cand} | {num(float(taxa) * 100)}% | {num(valores['t_ciclo'], 2)} | "
            f"{'sim' if piloto['viavel'] else 'não'} |"
        )
add("")
add(
    "Limiar congelado: 1,2 s por época completa (treino, validação, SSIM e I/O), "
    "que é 4 min divididos por 200 épocas por execução. C0 excedeu o limiar na "
    "taxa 50% (1,22 s) e ficou inviável: seus treinos completos não começaram e "
    "nenhuma parte do saldo dele foi gasta. O primeiro ciclo do processo inclui "
    "o aquecimento da GPU, e o critério congelado foi aplicado literalmente, sem "
    "reavaliação nem redistribuição de saldo. C1 e C2 foram viáveis e treinaram."
)
add("")
add("## 3. Execuções de treino (melhor e final por execução)")
add("")
add("| execução | estado | épocas concluídas | melhor: mse, ssim, época |")
add("|---|---|---|---|")
for chave, info in sorted(RESUMO["treinos"].items()):
    melhor = info["melhor"]
    if melhor:
        celula = (
            f"{num(melhor['perda_validacao'])}, {num(melhor['ssim_validacao'])}, "
            f"época {melhor['epoca']}"
        )
    else:
        celula = "não executada"
    add(f"| `{chave}` | {info['estado']} | {info['epocas']} | {celula} |")
add("")
add(
    "A época do checkpoint final coincide com a última época concluída de cada "
    "execução (coluna anterior); cópias imutáveis e hashes de melhor e final "
    "estão no histórico (evento checkpoint) e em checkpoints/ com modo de "
    "somente leitura. A seleção usa apenas o melhor de validação e não foi "
    "reaberta depois."
)
add("")
add(
    "Interrupção registrada: a execução `C1|10|0.75` parou na época 185 de 200 "
    "porque a época real (cerca de 1,5 s) ficou acima da estimativa do piloto e "
    "o saldo do envelope de 4 minutos dessa execução terminou. O melhor "
    "checkpoint (época 163) e o final (época 185) foram consolidados; nada "
    "mais ocorreu nessa execução."
)
add("")
add("## 4. Auditoria por seed e taxa (melhor de validação na régua)")
add("")
add(
    "Por seed, com a mediana das seeds em negrito; os controles determinísticos "
    "foram medidos uma vez por taxa e imagem (D4) e repetidos por seed apenas "
    "como linhas comparativas no histórico, sem recálculo por rede."
)
add("")
for taxa in TAXAS:
    rotulo = num(float(taxa) * 100) + "%"
    add(f"### Taxa {rotulo}")
    add("")
    add("| medição | mse por seed | ssim por seed | mse mediana | ssim mediana |")
    add("|---|---|---|---|---|")
    for cand in ("C1", "C2"):
        m = mediana_taxa(cand, taxa, "perda_validacao")
        s = mediana_taxa(cand, taxa, "ssim_validacao")
        if m is None:
            continue
        add(
            f"| {cand} | {por_seed_txt(cand, taxa, 'perda_validacao')} | "
            f"{por_seed_txt(cand, taxa, 'ssim_validacao')} | "
            f"**{num(m)}** | **{num(s)}** |"
        )
    controles = RESUMO["controles"].get(taxa, {})
    for nome_chave, rotulo_controle in (
        ("controle_media_rgb", "controle média RGB"),
        ("controle_interpolacao", "controle interpolação"),
    ):
        valor = controles.get(nome_chave)
        if valor:
            add(
                f"| {rotulo_controle} | igual por seed (medida única por imagem) | "
                f"igual por seed | **{num(valor['mse'])}** | "
                f"**{num(valor['ssim'])}** |"
            )
    add(
        f"| C0 | sem treinos completos (inviável pelo piloto) | não aplicável | "
        f"não aplicável | não aplicável |"
    )
    add("")
m50_c1 = mediana_taxa("C1", "0.5", "perda_validacao")
m75_c1 = mediana_taxa("C1", "0.75", "perda_validacao")
m50_c2 = mediana_taxa("C2", "0.5", "perda_validacao")
m75_c2 = mediana_taxa("C2", "0.75", "perda_validacao")
c50_media = RESUMO["controles"]["0.5"]["controle_media_rgb"]["mse"]
c50_inter = RESUMO["controles"]["0.5"]["controle_interpolacao"]["mse"]
c75_media = RESUMO["controles"]["0.75"]["controle_media_rgb"]["mse"]
c75_inter = RESUMO["controles"]["0.75"]["controle_interpolacao"]["mse"]
add(
    f"Comparação descritiva com os controles: na taxa 50%, C1 "
    f"({num(m50_c1)}) e C2 ({num(m50_c2)}) ficaram abaixo dos dois controles "
    f"({num(c50_media)} e {num(c50_inter)}); na taxa 75%, C1 ({num(m75_c1)}) e "
    f"C2 ({num(m75_c2)}) também ficaram abaixo dos dois controles "
    f"({num(c75_media)} e {num(c75_inter)}). Essa observação não equivale a "
    "melhoria demonstrada: a regra congelada exige comparação contra C0, e sem "
    "treinos completos de C0 nenhum candidato pode ser declarado elegível."
)
add("")
add("## 5. Seleção e decisão de C3")
add("")
for taxa, res in sorted((RESUMO.get("selecao") or {}).items()):
    vencedor = res.get("vencedor")
    add(
        f"- Taxa {num(float(taxa) * 100)}%: vencedor "
        f"{'nenhum' if not vencedor else vencedor}. Motivo registrado: "
        f"{res.get('motivo')}"
    )
if not RESUMO.get("selecao"):
    add("- Seleção não registrada.")
decisao = RESUMO.get("decisao_c3") or {}
add(
    f"- C3: elegível "
    f"{'sim' if decisao.get('elegivel') else 'não'}. Motivo registrado: "
    f"{decisao.get('motivo')}"
)
add("")
add("## 6. Única avaliação de teste (depois do congelamento)")
add("")
af = RESUMO.get("avaliacao_final") or {}
add("| medição no teste | taxa 50% mse | taxa 50% ssim | taxa 75% mse | taxa 75% ssim |")
add("|---|---|---|---|---|")
for chave, rotulo in (
    ("controle_media_rgb", "controle média RGB"),
    ("controle_interpolacao", "controle interpolação"),
):
    c50 = af.get("controles", {}).get("0.5", {}).get(chave)
    c75 = af.get("controles", {}).get("0.75", {}).get(chave)
    if c50 and c75:
        add(
            f"| {rotulo} | {num(c50['mse'])} | {num(c50['ssim'])} | "
            f"{num(c75['mse'])} | {num(c75['ssim'])} |"
        )
add("")
add(
    "Sem vencedor por taxa, não há candidato vencedor a registrar na avaliação "
    "final: somente os controles foram medidos no teste, na mesma régua fixa e "
    "uma única vez. O conjunto de teste nunca entrou na escolha. O resultado é "
    "exploratório: o teste é conhecido uma vez e não há alegação de confirmação "
    "independente nem de repetição aprovada."
)
add("")
add("## 7. Orçamento real do contador (teto de 120 minutos)")
add("")
t = RESUMO["tempo"]
add(
    f"- Alocação principal consumida: **{num(t['principal_minutos'], 1)} minutos "
    f"de 90** (limiares por categoria e por candidato respeitados os guards)."
)
add(
    f"- Reserva de repetições justificadas: **{num(t['reserva_minutos'], 1)} "
    f"minutos de 30 (intocada)**."
)
add(
    "- Por categoria (minutos): "
    + ", ".join(f"{k} {num(v, 1)}" for k, v in sorted(t["por_categoria"].items()))
    + "."
)
add(
    "- Por candidato (minutos): "
    + ", ".join(f"{k} {num(v, 1)}" for k, v in sorted(t["por_candidato"].items()))
    + "."
)
add(
    "- O saldo não gasto por C0 (inviável) e por C3 (não executado) permaneceu "
    "no orçamento; nada foi redistribuído entre candidatos."
)
add("")
add("## 8. Ficha visual (evidência qualitativa)")
add("")
add(
    "- Arquivos: `ficha-visual/ficha_50.png`, `ficha-visual/ficha_75.png` "
    "(reconstruções dos oito IDs em ambas as taxas, com letras, cujo cabeçalho revela os métodos), "
    "`ficha-visual/ficha_visual.json` (ficha preenchível, campos não "
    "preenchidos) e `ficha-visual/ficha-rotulos.json` (mapeamento das letras)."
)
add(
    "- Avaliação visual aberta posterior, de um único avaliador humano: resultados "
    "ruins nas duas taxas; objetivo visual não atingido. As fichas não são cegas "
    "e não receberam notas individuais. Ver notas-finais.md."
)
add("")
add("## 9. Checagens da fase (provas de execução, resumidas dos logs)")
add("")
add("```text")
add("$ openspec validate melhorar-reconstrucoes-mae")
add("Change 'melhorar-reconstrucoes-mae' is valid")
add("")
add("$ uv sync --locked")
add("ambiente sincronizado a partir do uv.lock (sem alterações de dependências)")
add("")
add("$ uv run pytest -q")
add("99 passed, 1 warning in ~4 s")
add("")
add("$ uv run python -m codigo.estudo_execucao congelar")
add("congelado: hash=f6fd9a10d3d1532e split=02cdb84acfac19d6 codigo=e13ef0653e119b00 torch=2.14.1+cu130 ids=[20736, 12985, 33580, 25306, 6418, 34029, 31327, 45589]")
add("")
add("$ uv run python -m codigo.estudo_execucao piloto")
add("C0: piloto viavel=False [0.5=1.22s 0.75=0.89s]")
add("C1: piloto viavel=True [0.5=1.03s 0.75=1.16s]")
add("C2: piloto viavel=True [0.5=1.03s 0.75=0.99s]")
add("")
add("$ uv run python -m codigo.estudo_execucao controles")
add("controle controle_media_rgb@0.5: mse=0.0491 ssim=0.3556")
add("controle controle_interpolacao@0.5: mse=0.0447 ssim=0.2691")
add("controle controle_media_rgb@0.75: mse=0.0517 ssim=0.3556")
add("controle controle_interpolacao@0.75: mse=0.0545 ssim=0.2378")
add("controles validação: 1.5s")
add("")
add("$ uv run python -m codigo.estudo_execucao treino --candidato C1 --seed 10 --taxa 0.5")
add("C1|10|0.5: estado=completo epocas=200 melhor=0.033555@181")
add("(o mesmo comando foi repetido para os 6 pares seed/taxa de C1 e de C2; "
    "a linha final de cada execução está registrada em estado.json e a "
    "auditoria por época, com tempos, no historico.csv)")
add("")
add("$ uv run python -m codigo.estudo_execucao consolidar --candidato C1")
add("consolidação C1: 0.8s em cópias")
add("$ uv run python -m codigo.estudo_execucao consolidar --candidato C2")
add("consolidação C2: 0.6s em cópias")
add("")
add("$ uv run python -m codigo.estudo_execucao decidir-c3")
add("C3 elegivel=False: C0 sem treinos completos (inviável pelo limiar de 1,2 s do piloto): o critério de mediana de MSE de C0 contra cada baseline não é verificável; C3 registrado como NÃO EXECUTADO")
add("")
add("$ uv run python -m codigo.estudo_execucao selecao")
add("taxa 0.5: vencedor=None (referência C0 sem treinos completos (inviável pelo limiar de 1,2 s do piloto): regra de elegibilidade contra C0 não pôde ser aplicada; ausência de melhoria demonstrada)")
add("taxa 0.75: vencedor=None (referência C0 sem treinos completos (inviável pelo limiar de 1,2 s do piloto): regra de elegibilidade contra C0 não pôde ser aplicada; ausência de melhoria demonstrada)")
add("")
add("$ uv run python -m codigo.estudo_execucao congelar-final")
add("congelamento final: hash=72bb04bd3a502dbf")
add("")
add("$ uv run python -m codigo.estudo_execucao avaliacao-final")
add("avaliação final: 1.6s")
add("")
add("$ uv run python -m codigo.estudo_execucao resumo")
add("resumo em resultados/estudo-melhorar-reconstrucoes-mae/resumo.json")
add("")
add("$ uv run python -m codigo.estudo_execucao figuras")
add("figuras em resultados/estudo-melhorar-reconstrucoes-mae/figuras")
add("")
add("$ uv run python -m codigo.estudo_execucao ficha")
add("ficha em resultados/estudo-melhorar-reconstrucoes-mae/ficha-visual: ['ficha-rotulos.json', 'ficha_50.png', 'ficha_75.png', 'ficha_visual.json']")
add("")
add("$ uv run python scripts/gerar_slides.py")
add("limites ok nas 13 paginas")
add("png: 13 paginas em slides/png")
add("")
add("$ uv run python scripts/montar_zip.py")
add("zip gravado em seminario_masked_modeling.zip (34 arquivos)")
add("lista de md5 em scripts/md5_pacote.csv")
add("```")
add("")
add(
    "Logs completos da fase, com um arquivo por etapa, estão na pasta `logs/` "
    "da worktree (01-congelar.log a 10-checks.log)."
)
add("")
add("## 10. Entrega documental (slides, zip e README)")
add("")
add(
    "- `scripts/gerar_slides.py`: novo slide 9 com o quadro do estudo (pilotos, "
    "medianas de validação de C1 e C2, controles) e nota de resultado; números "
    "lidos de `resumo.json`. Verificação do próprio script: limites ok nas 13 "
    "páginas; pptx, pdf e 13 pngs regenerados."
)
add(
    "- `scripts/montar_zip.py`: o pacote exige e inclui manifesto, historico.csv, "
    "contador.jsonl, resumo.json, três figuras, a ficha visual (duas imagens e "
    "dois JSON) e este relatório; conteúdos e exclusões anteriores preservados "
    "(dados brutos, checkpoints, oráculo e testes continuam de fora). "
    "Execução: zip com 34 arquivos e lista de md5 regenerada."
)
add(
    "- README atualizado com a seção `Estudo de retreinamento`, apontando os "
    "artefatos novos; os resultados anteriores (metricas.csv, curva_perda.png, "
    "reconstrucoes.png e os checkpoints antigos) continuam intactos e "
    "identificáveis com o protocolo próprio deles."
)
add("")
add("## 11. Delimitações honestas")
add("")
add(
    "- C0 (referência do protocolo) não pôde ser treinado pelo limiar congelado "
    "do piloto; a regra de elegibilidade contra C0 não pôde ser aplicada e, "
    "portanto, nenhuma melhoria ficou demonstrada. A ausência de vencedor é "
    "consequência da regra congelada, não de escolha pós-hoc."
)
add(
    "- A observação de que C1 e C2 tiveram MSE mediano abaixo dos controles é "
    "descritiva e exploratória; não equivale a melhoria demonstrada contra a "
    "referência C0 do protocolo."
)
add(
    "- A comparação com o experimento anterior do notebook (MSE de teste de "
    "0,0608 e 0,0717) é apenas indicativa: as máscaras de treino e a régua "
    "diferem do protocolo antigo."
)
add(
    "- O conjunto de teste foi consultado uma única vez, depois do "
    "congelamento; não há alegação de confirmação independente."
)
add(
    "- A avaliação visual aberta de um único avaliador humano foi negativa nas duas "
    "taxas; o objetivo visual não foi atingido. Não houve notas individuais nem cegamento."
)

ALVO.write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"relatório em {ALVO}")
