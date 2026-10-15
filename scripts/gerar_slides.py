"""
Gera os slides do seminário (pptx + pdf + png) a partir de um mesmo script.
Os números do experimento próprio vêm somente de resultados/metricas.csv
(sem digitação manual). Os números e os visuais do experimento complementar
vem do material complementar do grupo: assets versados em slides/recursos-complementares/
e MSEs documentados no texto do material complementar (0,0476 com 25%; 0,1403 com 75%; 0,3117
com 90%), sempre com crédito; a taxa de 50% aparece sem número porque o
gráfico em imagem cobre o quadro.
Os números do estudo de retreinamento (melhorar-reconstrucoes-mae) vêm somente de
resultados/estudo-melhorar-reconstrucoes-mae/resumo.json, também sem digitação manual.
Roteiro de 13 slides (12 da roteiro anterior + 1 do estudo de retreinamento)
(ver openspec/changes/mesclar-apresentacoes/design.md e
openspec/changes/melhorar-reconstrucoes-mae/relatorio-fase-b.md).
Rode: uv run python scripts/gerar_slides.py
"""

from __future__ import annotations

import json
import subprocess
import re
import zipfile
from pathlib import Path
from statistics import median

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "resultados"
RESULTADOS_ESTUDO = RESULTADOS / "estudo-melhorar-reconstrucoes-mae"
SLIDES = RAIZ / "slides"
RECURSOS_COMPLEMENTARES = SLIDES / "recursos-complementares"
PPTX = SLIDES / "seminario_masked_modeling.pptx"
PDF = SLIDES / "seminario_masked_modeling.pdf"
COLAB = (
    "https://colab.research.google.com/drive/"
    "11BkUg8lzF079vWErYh5plimEVcF16gXN"
)


def apresentacao() -> Presentation:
    pr = Presentation()
    pr.slide_width = Inches(13.333)
    pr.slide_height = Inches(7.5)
    return pr


def slide_titulo(pr, titulo: str, subtitulo: str):
    slide = pr.slides.add_slide(pr.slide_layouts[0])
    slide.shapes.title.text = titulo
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(40)
    slide.placeholders[1].text = subtitulo
    for par in slide.placeholders[1].text_frame.paragraphs:
        par.font.size = Pt(22)
    return slide


def slide_bullets(pr, titulo: str, itens: list[str], tamanho: int = 17):
    slide = pr.slides.add_slide(pr.slide_layouts[1])
    slide.shapes.title.text = titulo
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(30)
    corpo = slide.placeholders[1].text_frame
    for i, item in enumerate(itens):
        par = corpo.paragraphs[0] if i == 0 else corpo.add_paragraph()
        par.text = item
        par.level = 0
        par.font.size = Pt(tamanho)
    return slide


def _imagem_ajustada(slide, caminho_imagem: Path, x: float, y: float,
                     largura_disp: float, altura_disp: float):
    """Insere a imagem centrada na célula (x, y) respeitando a proporção,
    sem ultrapassar a área dada (verificar_limites falha se sair)."""
    from PIL import Image

    if not caminho_imagem.exists():
        raise FileNotFoundError(f"imagem obrigatória ausente: {caminho_imagem}")
    with Image.open(caminho_imagem) as im:
        w, h = im.size
    escala = min(largura_disp / (w / 96.0), altura_disp / (h / 96.0))
    largura = (w / 96.0) * escala
    altura = (h / 96.0) * escala
    slide.shapes.add_picture(
        str(caminho_imagem),
        Inches(x + (largura_disp - largura) / 2),
        Inches(y + (altura_disp - altura) / 2),
        width=Inches(largura), height=Inches(altura),
    )


CAIXA_FUNDO = RGBColor(0xEE, 0xF2, 0xF8)
CAIXA_BORDA = RGBColor(0x2F, 0x4B, 0x6E)
COR_SETA = RGBColor(0x2F, 0x6B, 0xB0)


def _caixa_texto(slide, left, top, width, height, linhas, mono: bool = False):
    """linhas: lista de (texto, tamanho_pt, negrito)."""
    caixa = slide.shapes.add_textbox(left, top, width, height)
    tf = caixa.text_frame
    tf.word_wrap = True
    fonte = "Consolas" if mono else "Arial"
    for i, (texto, tamanho, negrito) in enumerate(linhas):
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.text = texto
        par.font.size = Pt(tamanho)
        par.font.bold = negrito
        par.font.name = fonte
    return caixa


def slide_diagrama(pr, titulo: str, blocos: list[str], nota: str):
    """Diagrama do fluxo do MAE: duas fileiras de 4 caixas com setas,
    fluxo em S (esquerda para direita, descida, direita para esquerda)."""
    slide = pr.slides.add_slide(pr.slide_layouts[5])
    slide.shapes.title.text = titulo
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(30)

    largura_box = Inches(2.72)
    altura_box = Inches(1.5)
    largura_seta = Inches(0.36)
    altura_seta = Inches(0.42)
    margem = Inches(0.67)
    topo1 = Inches(1.6)
    topo2 = Inches(4.4)
    passo = largura_box + largura_seta

    def caixa(texto: str, coluna: int, top):
        forma = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            margem + coluna * passo, top, largura_box, altura_box,
        )
        forma.fill.solid()
        forma.fill.fore_color.rgb = CAIXA_FUNDO
        forma.line.color.rgb = CAIXA_BORDA
        tf = forma.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for i, linha in enumerate(texto.split("\n")):
            par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            par.text = linha
            par.alignment = PP_ALIGN.CENTER
            par.font.size = Pt(10 if i else 11)
            par.font.bold = i == 0
            par.font.color.rgb = CAIXA_BORDA
        return forma

    def seta(forma_setas, left, top, largura, altura):
        forma = slide.shapes.add_shape(forma_setas, left, top, largura, altura)
        forma.fill.solid()
        forma.fill.fore_color.rgb = COR_SETA
        forma.line.fill.background()
        return forma

    # fileira superior: imagem -> patches -> máscara -> codificador
    for i, idx_bloco in enumerate(range(4)):
        caixa(blocos[idx_bloco], i, topo1)
        if i < 3:
            seta(
                MSO_SHAPE.RIGHT_ARROW,
                margem + i * passo + largura_box,
                topo1 + (altura_box - altura_seta) // 2,
                largura_seta, altura_seta,
            )
    # descida: codificador -> tokens de máscara
    seta(
        MSO_SHAPE.DOWN_ARROW,
        margem + 3 * passo + (largura_box - largura_seta) // 2,
        topo1 + altura_box + Inches(0.12),
        largura_seta,
        topo2 - topo1 - altura_box - Inches(0.24),
    )
    # fileira inferior em sentido oposto: tokens -> decoder -> reconstrução -> perda
    ordem = list(reversed(range(4, 8)))
    for i, idx_bloco in enumerate(ordem):
        caixa(blocos[idx_bloco], i, topo2)
        if i < 3:
            seta(
                MSO_SHAPE.LEFT_ARROW,
                margem + i * passo + largura_box,
                topo2 + (altura_box - altura_seta) // 2,
                largura_seta, altura_seta,
            )
    _caixa_texto(
        slide, Inches(0.67), Inches(6.25), Inches(12.0), Inches(1.0),
        [(nota, 13, False)],
    )
    return slide


def slide_tabela(pr, titulo: str, cabecalho: list[str], linhas: list[list[str]], nota: str):
    """Tabela comparativa (primeira coluna: dimensão; demais: métodos)."""
    slide = pr.slides.add_slide(pr.slide_layouts[5])
    slide.shapes.title.text = titulo
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(30)

    n_linhas = len(linhas) + 1
    n_colunas = len(cabecalho)
    tabela = slide.shapes.add_table(
        n_linhas, n_colunas,
        Inches(0.55), Inches(1.5), Inches(12.3), Inches(4.4),
    ).table
    tabela.columns[0].width = Inches(1.9)
    for c in range(1, n_colunas):
        tabela.columns[c].width = Inches((12.3 - 1.9) / (n_colunas - 1))
    for c, texto in enumerate(cabecalho):
        celula = tabela.cell(0, c)
        celula.text = texto
        for par in celula.text_frame.paragraphs:
            par.font.size = Pt(15)
            par.font.bold = True
    for r, linha in enumerate(linhas, start=1):
        for c, texto in enumerate(linha):
            celula = tabela.cell(r, c)
            celula.text = texto
            for par in celula.text_frame.paragraphs:
                par.font.size = Pt(12)
                par.font.bold = c == 0
    _caixa_texto(
        slide, Inches(0.55), Inches(6.15), Inches(12.3), Inches(1.1),
        [(nota, 13, False)],
    )
    return slide


def slide_experimento_proprio(pr, titulo: str, balas: list[str],
                              tabela_mse: list[tuple[str, str]],
                              fonte_tabela: str, rotulo_imagem: str,
                              caminho_imagem: Path):
    """Slide compacto do experimento próprio: balas à esquerda, tabela de MSE
    (lida de metricas.csv) à direita e imagem de reconstruções embaixo."""
    slide = pr.slides.add_slide(pr.slide_layouts[5])
    slide.shapes.title.text = titulo
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(30)
    _caixa_texto(slide, Inches(0.67), Inches(1.45), Inches(6.9), Inches(3.0),
                 [(texto, 14, False) for texto in balas])
    n = len(tabela_mse) + 1
    tabela = slide.shapes.add_table(
        n, 2, Inches(8.0), Inches(1.6), Inches(4.5), Inches(0.55 * n),
    ).table
    tabela.cell(0, 0).text = "Condição"
    tabela.cell(0, 1).text = "MSE de teste (ocultos)"
    for r, (condicao, mse) in enumerate(tabela_mse, start=1):
        tabela.cell(r, 0).text = condicao
        tabela.cell(r, 1).text = mse
    for r in range(n):
        for c in range(2):
            for par in tabela.cell(r, c).text_frame.paragraphs:
                par.font.size = Pt(13)
                par.font.bold = r == 0 or c == 0
    fonte = _caixa_texto(slide, Inches(8.0), Inches(1.7) + Inches(0.55 * n),
                         Inches(4.5), Inches(0.5), [(fonte_tabela, 11, False)])
    fonte.word_wrap = True
    _caixa_texto(slide, Inches(0.67), Inches(4.62), Inches(12.0), Inches(0.3),
                 [(rotulo_imagem, 12, True)])
    _imagem_ajustada(slide, caminho_imagem, 1.3, 4.95, 10.7, 2.4)
    return slide


def slide_experimento_complementar(pr, titulo: str, config: list[str],
                             rotulos: list[str], imagem_taxas: Path,
                             imagem_tabela: Path, imagem_visual: Path,
                             legenda: list[str]):
    """Slide do experimento complementar: banda larga com
    o fluxo em cima; na fileira de baixo, texto de configuração, grade de
    máscaras e reconstruções por taxa e gráfico do MSE; crédito e link do
    Colab na legenda."""
    slide = pr.slides.add_slide(pr.slide_layouts[5])
    slide.shapes.title.text = titulo
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(30)
    _imagem_ajustada(slide, imagem_taxas, 0.87, 1.25, 11.6, 2.25)
    _caixa_texto(slide, Inches(0.67), Inches(3.58), Inches(2.4), Inches(0.44),
                 [(rotulos[0], 11, True)])
    _caixa_texto(slide, Inches(6.45), Inches(3.58), Inches(4.2), Inches(0.44),
                 [(rotulos[1], 11, True)])
    _caixa_texto(slide, Inches(3.05), Inches(3.95), Inches(3.3), Inches(2.8),
                 [(texto, 12, False) for texto in config])
    _imagem_ajustada(slide, imagem_visual, 0.75, 4.05, 2.15, 2.30)
    _imagem_ajustada(slide, imagem_tabela, 6.45, 4.05, 4.15, 2.60)
    _caixa_texto(slide, Inches(0.67), Inches(6.80), Inches(12.0), Inches(0.62),
                 [(texto, 11, False) for texto in legenda])
    return slide


def verificar_limites(pr) -> None:
    """Falha se qualquer shape sair da área do slide."""
    largura_slide = pr.slide_width
    altura_slide = pr.slide_height
    for i, slide in enumerate(pr.slides, start=1):
        for shape in slide.shapes:
            if shape.left is None:
                continue
            dentro = (
                0 <= shape.left
                and 0 <= shape.top
                and shape.left + shape.width <= largura_slide
                and shape.top + shape.height <= altura_slide
            )
            if not dentro:
                raise RuntimeError(
                    f"slide {i}: shape '{shape.name}' fora da area do slide "
                    f"(left={shape.left}, top={shape.top}, right={shape.left + shape.width}, "
                    f"bottom={shape.top + shape.height})"
                )
    print(f"limites ok nas {i} paginas")


def slide_estudo_retreinamento(pr):
    """Slide do estudo de retreinamento: números somente de resumo.json."""
    caminho_resumo = RESULTADOS_ESTUDO / "resumo.json"
    if not caminho_resumo.exists():
        raise FileNotFoundError(
            f"resumo do estudo ausente: {caminho_resumo}; rode o estudo antes"
        )
    r = json.loads(caminho_resumo.read_text(encoding="utf-8"))

    retificacao = json.loads((RAIZ / "openspec/changes/melhorar-reconstrucoes-mae/retificacao-validacao.json").read_text(encoding="utf-8"))
    controles_validacao = retificacao["referencias_validacao"]["controles"]

    def num(v, nd=4):
        return f"{v:.{nd}f}".replace(".", ",")

    def melhor_mediana(nome: str, taxa: str, campo: str) -> float | None:
        valores = []
        for chave, info in r["treinos"].items():
            partes = chave.split("|")
            if partes[0] == nome and partes[2] == taxa and info["melhor"]:
                valores.append(info["melhor"][campo])
        return median(valores) if valores else None

    def piloto(nome: str, taxa: str) -> str:
        pil = r["pilotos"].get(nome, {})
        taxas = pil.get("taxas", {})
        item = taxas.get(taxa)
        if item is None:
            return "não executado"
        rotulo = num(item["t_ciclo"], 2) + " s"
        if not item.get("exedeu_limiar"):
            return rotulo
        return f"{rotulo} (> limiar; candidato inviável)"

    linhas = [["registro", "taxa 50%", "taxa 75%"]]
    for nome, rotulo in (
        ("C0", "C0: época piloto (s)"),
        ("C1", "C1: piloto (s)"),
        ("C2", "C2: piloto (s)"),
    ):
        linhas.append([rotulo, piloto(nome, "0.5"), piloto(nome, "0.75")])
    for nome, rotulo in (
        ("C1", "C1: MSE mediano na melhor validação"),
        ("C2", "C2: MSE mediano na melhor validação"),
    ):
        valores = []
        for taxa in ("0.5", "0.75"):
            valor = melhor_mediana(nome, taxa, "perda_validacao")
            valores.append(num(valor) if valor is not None else "sem treinos")
        linhas.append([rotulo, valores[0], valores[1]])
    col_50 = [
        controles_validacao.get(taxa, {}).get("controle_media_rgb", {}).get("mse")
        for taxa in ("0.5", "0.75")
    ]
    col_int = [
        controles_validacao.get(taxa, {}).get("controle_interpolacao", {}).get("mse")
        for taxa in ("0.5", "0.75")
    ]
    linhas.append([
        "controle média RGB (validação)",
        num(col_50[0]) if col_50[0] is not None else "não calculado",
        num(col_50[1]) if col_50[1] is not None else "não calculado",
    ])
    linhas.append([
        "controle interpolação (validação)",
        num(col_int[0]) if col_int[0] is not None else "não calculado",
        num(col_int[1]) if col_int[1] is not None else "não calculado",
    ])
    contadores = r["tempo"]
    momento = f"{contadores['principal_minutos']:.1f}".replace(".", ",")
    slide_tabela(
        pr,
        "Estudo de retreinamento: protocolo por identidade, época e seed",
        linhas[0],
        linhas[1:],
        (
            "Rodada v1: seeds 10, 20 e 30; máximo planejado de 200 épocas por taxa. "
            "C1, seed 10 a 75%: 185 épocas efetivas. Sem C0 treinado, não há ganho demonstrado contra C0. "
            f"V1: {momento} min principais, reserva intocada naquela rodada. "
            "V2: pilotos inviáveis, seis treinos não iniciados; reserva consumida 0,209334139 min; "
            "total v1 + v2: 41,270848124 min. Avaliação visual aberta de um avaliador humano: "
            "ruim nas duas taxas, objetivo visual não atingido. Fichas não cegas (cabeçalho revela métodos). "
            "Exploratório, sem confirmação ou superioridade universal. Fontes: histórico v1, contador v2, "
            "notas-finais.md e retificacao-validacao.json (controles com estado=validacao)."
        ),
    )


def principal():
    m = pd.read_csv(RESULTADOS / "metricas.csv")
    linha50 = m[m["condição"] == "mascara_50"].iloc[0]
    linha75 = m[m["condição"] == "mascara_75"].iloc[0]
    epocas = int(linha50["épocas"])
    batch = int(linha50["batch"])
    lr = float(linha50["lr"])
    mse50 = float(linha50["mse_teste_ocultos"])
    mse75 = float(linha75["mse_teste_ocultos"])
    variacao = (mse75 - mse50) / mse50 * 100.0

    pr = apresentacao()

    # 1. Capa
    slide_titulo(
        pr,
        "Masked Modeling em Deep Learning",
        "Frederico Maciel de Mello | Luan Pedro de Souza Silva\nSeminário, 16/10",
    )
    # 2. O que é e ideia-chave
    slide_bullets(
        pr,
        "O que é Masked Modeling",
        [
            "Estratégia de aprendizado em que parte dos dados de entrada é propositalmente ocultada (mascarada)",
            "O modelo é treinado para prever ou reconstruir a informação ausente",
            "Ideia-chave: o próprio dado fornece a supervisão",
            "A parte original funciona como referência para verificar o que o modelo previu ou reconstruiu",
            "Quatro etapas: ocultar uma parte da entrada, usar o visível como contexto,",
            "prever ou reconstruir o conteúdo mascarado e aprender representações úteis dos dados",
        ],
    )
    # 3. Por que usar e motivações
    slide_bullets(
        pr,
        "Por que usar: motivações",
        [
            "Treino de deep learning depende de grandes quantidades de dados rotulados, caros e demorados de obter",
            "Masked modeling aproveita dados não rotulados: a tarefa de aprendizado nasce do próprio dado",
            "Reduz a dependência de dados rotulados",
            "Aprende representações relevantes dos dados",
            "Explora o contexto e as relações entre as partes da entrada",
            "Serve de pré-treinamento para modelos adaptados a outras tarefas depois",
        ],
    )
    # 4. Panorama BERT x MAE x SimMIM
    slide_tabela(
        pr,
        "Panorama: BERT, MAE e SimMIM",
        ["Dimensão", "BERT", "MAE", "SimMIM"],
        [
            [
                "Modalidade",
                "Texto (tokens discretos)",
                "Imagem (patches de pixels)",
                "Imagem (patches de pixels)",
            ],
            [
                "Alvo previsto",
                "Palavras (tokens) ocultas",
                "Pixels brutos dos patches ocultos",
                "Pixels brutos dos patches ocultos",
            ],
            [
                "Perda",
                "Entropia cruzada sobre os tokens ocultos",
                "MSE nos pixels normalizados, média por patch oculto",
                "L1 (erro absoluto) nos pixels reconstruídos",
            ],
            [
                "Arquitetura",
                "Encoder Transformer único",
                "Assimétrica: encoder pesado e decoder leve separado",
                "Encoder único com cabeça de predição linear leve",
            ],
        ],
        "Contraste MSE x L1: o MSE do MAE opera em pixels normalizados com média por patch e pede "
        "decoder separado; a L1 do SimMIM faz regressão direta de pixels com cabeça linear leve sobre "
        "um encoder único, que admite proporções altas de máscara também",
    )
    # 5. Diagrama de blocos do MAE
    slide_diagrama(
        pr,
        "Fluxo do MAE: da imagem à perda nos ocultos",
        [
            "Imagem sem rótulo\n32x32x3",
            "Patches\n16 de 8x8\n(192 valores cada)",
            "Máscara aleatória\n50% ou 75% dos patches",
            "Codificador (ViT)\nprocessa apenas\nos patches visíveis",
            "Tokens de máscara\ncom embedding\ndas posições",
            "Decodificador leve\ndim 64, 2 blocos",
            "Reconstrução\ndos pixels dos\npatches ocultos",
            "Perda: MSE\nsomente nos\npatches ocultos",
        ],
        "Arquitetura assimétrica: o codificador só vê os patches visíveis e o decoder leve, "
        "descartado nas tarefas posteriores de reconhecimento (He et al., 2022)",
    )
    # 6. Equação e pseudocódigo
    slide = pr.slides.add_slide(pr.slide_layouts[5])
    slide.shapes.title.text = "Equação da perda e pseudocódigo do treinamento"
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(28)
    _caixa_texto(
        slide, Inches(0.67), Inches(1.5), Inches(6.1), Inches(5.6),
        [
            ("Equação da perda (erro quadrático médio nos ocultos)", 14, True),
            (
                "L_MAE = (1/|M|) · Σ i ∈ M (1/d) · ||x_i − x̂_i||²",
                13, True,
            ),
            ("x_i: vetor de pixels do patch i (d valores)", 13, False),
            ("M: conjunto dos patches mascarados (ocultos)", 13, False),
            ("x̂_i: reconstrução do patch i produzida pelo modelo", 13, False),
            ("d: número de valores de pixel por patch (192);", 13, False),
            ("normaliza pela dimensão da reconstrução", 12, False),
            ("média sobre i ∈ M: a perda ignora os patches visíveis", 13, True),
        ],
    )
    _caixa_texto(
        slide, Inches(7.0), Inches(1.5), Inches(5.66), Inches(5.6),
        [
            ("Pseudocódigo do laço de treinamento", 14, True),
            ("1. dividir o lote em patches", 12, False),
            ("2. amostrar a máscara na razão r", 12, False),
            ("3. codificar somente os patches visíveis", 12, False),
            ("4. decodificar com tokens de máscara e posições", 12, False),
            ("5. calcular a perda somente nos patches ocultos, normalizada por d", 12, False),
            ("6. atualizar os parâmetros por retropropagação", 12, False),
            ("Repetir por época sobre o conjunto de treino", 12, False),
        ],
        mono=True,
    )
    # 7. Experimento próprio CIFAR-10
    slide_experimento_proprio(
        pr,
        "Experimento próprio no CIFAR-10",
        [
            "MAE próprio, escrito do zero em PyTorch puro (sem código de terceiros)",
            f"Mesmo protocolo nas duas condições: {epocas} épocas, batch {batch}, lr {lr:.1e} (AdamW)",
            "Semente única 42; subset balanceado verificado por md5; teste fixo de 1.000 imagens",
            "Máscara aninhada: os patches ocultos a 50% também estão a 75%, isolando o efeito da taxa",
            "50% oculta 8 dos 16 patches; 75% oculta 12 (custo por época diverge: 8 contra 4 tokens no encoder)",
            f"MSE de 75% é {variacao:+.1f}% maior que o de 50%: nesta configuração, mascarar mais elevou o erro",
            "Delimitação: evidência desta configuração, semente única; repetir com mais sementes e avaliar downstream antes de generalizar",
        ],
        [
            ("Máscara 50%", f"{mse50:.4f}"),
            ("Máscara 75%", f"{mse75:.4f}"),
        ],
        "Fonte: resultados/metricas.csv (semente 42)",
        "Reconstruções: 8 imagens fixas do teste (semente 42)",
        RESULTADOS / "reconstrucoes.png",
    )
    # 8. Experimento complementar
    slide_experimento_complementar(
        pr,
        "Experimento complementar: ViT-MAE",
        [
            "Configuração do experimento complementar:",
            "MAE pré-treinado, arquitetura Vision Transformer (ViT)",
            "Entrada de 224x224 pixels, patches de 16x16",
            "Taxas avaliadas: 25%, 50%, 75% e 90%",
            "MSEs documentados (experimento complementar):",
            "25%: 0,0476 | 75%: 0,1403 | 90%: 0,3117",
            "Menos informação visível torna a reconstrução mais desafiadora",
        ],
        [
            "Mascarado e reconstruído em cada taxa",
            "Erro de reconstrução por taxa",
        ],
        RECURSOS_COMPLEMENTARES / "vitmae-fluxo-experimento.png",
        RECURSOS_COMPLEMENTARES / "vitmae-grafico-mse.png",
        RECURSOS_COMPLEMENTARES / "vitmae-grade-taxas.png",
        [
            "Imagem superior: fluxo do experimento com MAE pré-treinado. Experimento complementar do grupo; implementação pública: Hugging Face Transformers, ViTMAE, modelo facebook/vit-mae-base (Meta AI).",
            f"Código do experimento complementar: {COLAB}",
        ],
    )
    # 9. Estudo de retreinamento (melhorar-reconstrucoes-mae)
    slide_estudo_retreinamento(pr)
    # 10. Aplicações por domínio
    slide_bullets(
        pr,
        "Aplicações por domínio",
        [
            "Pré-treinar com grandes volumes de dados não rotulados e transferir as representações",
            "Visão computacional: classificação, detecção de objetos, segmentação semântica, reconhecimento visual",
            "Imagens médicas: radiografias, tomografias e ressonâncias; pré-treinamento sem anotação; extração de características para diagnóstico",
            "Sensoriamento remoto: uso e cobertura do solo, detecção de mudanças, imagens de satélite, monitoramento ambiental e agrícola",
            "Outras modalidades: linguagem natural, vídeos, áudio e aprendizado multimodal",
        ],
    )
    # 11. Pós MAE e downstream
    slide_bullets(
        pr,
        "Pós MAE e tarefas downstream",
        [
            "Pré-treinamento: o MAE usa grandes volumes de imagens não rotuladas; parte dos patches é mascarada e o modelo aprende a reconstruir",
            "Nesse processo, o encoder ViT aprende representações visuais das imagens",
            "Depois do pré-treinamento, o decoder pode ser descartado: sua função principal era auxiliar a reconstrução",
            "O encoder pré-treinado é reutilizado em tarefas downstream: classificação de imagens, detecção de objetos e segmentação semântica",
            "Uso do encoder: extrator de características ou pesos ajustados por fine-tuning para a nova tarefa",
            "Eco do nosso diagrama: o decoder leve sai e o encoder pesado fica",
        ],
    )
    # 12. Conclusões
    slide_bullets(
        pr,
        "Conclusões",
        [
            "Reconstruir o que foi escondido não é o objetivo final: é o mecanismo para o modelo aprender boas representações",
            "O mascaramento aproveita dados não rotulados, em texto (BERT) e em imagens (MAE)",
            "No experimento próprio, 75% mascarado errou mais que 50%: nesta configuração, mascarar mais elevou o erro (semente única 42)",
            "No experimento complementar com MAE pré-treinado público, as taxas maiores de mascaramento elevaram o MSE registrado no material complementar",
            "Leitura delimitada: qualidade visual da reconstrução não é prova de representações melhores",
            "Repetição com mais sementes e avaliação downstream continuam necessárias antes de generalizar",
        ],
    )
    # 13. Referências
    slide = pr.slides.add_slide(pr.slide_layouts[5])
    slide.shapes.title.text = "Referências"
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(30)
    _caixa_texto(
        slide, Inches(0.67), Inches(1.5), Inches(12.0), Inches(5.8),
        [
            ("Devlin, J.; Chang, M.; Lee, K.; Toutanova, K. (2019). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. NAACL-HLT.", 13, False),
            ("Dosovitskiy, A. et al. (2021). An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale. ICLR.", 13, False),
            ("He, K.; Chen, X.; Xie, S.; Li, Y.; Dollár, P.; Girshick, R. (2022). Masked Autoencoders Are Scalable Vision Learners. CVPR.", 13, False),
            ("Bao, H. et al. (2022). BEiT: BERT Pre-Training of Image Transformers. ICLR.", 13, False),
            ("Xie, Z.; Zhang, Z.; Lin, Y.; Bian, J.; Lin, L.; Zeng, D. (2022). SimMIM: A Simple Framework for Masked Image Modeling. CVPR.", 13, False),
            ("Krizhevsky, A.; Nair, V.; Hinton, G. (2009). CIFAR-10 (Canadian Institute for Advanced Research). Fonte dos dados deste trabalho, verificado por md5.", 13, False),
            ("Crédito do experimento complementar do grupo: implementação pública Hugging Face Transformers, ViTMAE, modelo facebook/vit-mae-base (Meta AI).", 13, False),
            (f"Código do experimento complementar: {COLAB}", 12, False),
        ],
    )

    PPTX.parent.mkdir(exist_ok=True)
    n_slides = len(pr.slides._sldIdLst)
    verificar_limites(pr)
    pr.save(PPTX)
    with zipfile.ZipFile(PPTX) as arquivo:
        entradas = [(nome, arquivo.read(nome)) for nome in sorted(arquivo.namelist())]
    with zipfile.ZipFile(PPTX, "w") as arquivo:
        for nome, conteudo in entradas:
            info = zipfile.ZipInfo(nome, date_time=(2026, 10, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            arquivo.writestr(info, conteudo)
    subprocess.run(
        ["/usr/bin/soffice", "--headless", "--convert-to", "pdf", "--outdir", str(SLIDES), str(PPTX)],
        check=True,
        capture_output=True,
    )
    pdf = PDF.read_bytes()
    pdf = re.sub(rb"D:\d{14}", b"D:20261015000000", pdf)
    pdf = re.sub(rb"(?<=/ID \[ )[0-9A-Fa-f<> ]+(?=\])", lambda m: re.sub(rb"[0-9A-Fa-f]", b"0", m.group()), pdf)
    pdf = re.sub(rb"(/ID\s*\[\s*<)([0-9A-Fa-f]+)(>\s*<)([0-9A-Fa-f]+)(>\s*\])",
                 lambda m: m[1] + b"0" * len(m[2]) + m[3] + b"0" * len(m[4]) + m[5], pdf)
    pdf = re.sub(rb"(?<=/DocChecksum /)[0-9A-Fa-f]+", lambda m: b"0" * len(m.group()), pdf)
    PDF.write_bytes(pdf)
    # gera um PNG por página e confere a contagem
    pasta_png = SLIDES / "png"
    pasta_png.mkdir(exist_ok=True)
    for antigo in pasta_png.glob("pagina-*.png"):
        antigo.unlink()
    subprocess.run(
        ["pdftoppm", "-png", "-r", "72", str(PDF), str(pasta_png / "pagina")],
        check=True,
        capture_output=True,
    )
    pngs = sorted(pasta_png.glob("pagina-*.png"))
    if len(pngs) != n_slides:
        raise RuntimeError(
            f"contagem de PNG divergente: {len(pngs)} contra {n_slides} slides"
        )
    print(f"pptx: {PPTX}")
    print(f"pdf: {PDF}")
    print(f"png: {len(pngs)} paginas em {pasta_png}")
    print(f"slides: {n_slides}")


if __name__ == "__main__":
    principal()