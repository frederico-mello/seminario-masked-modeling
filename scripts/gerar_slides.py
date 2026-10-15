"""
Gera os slides do seminário (pptx + pdf + png) a partir de um mesmo script.
Os números vêm somente de resultados/metricas.csv (sem digitação manual).
Rode: uv run python scripts/gerar_slides.py
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "resultados"
SLIDES = RAIZ / "slides"
PPTX = SLIDES / "seminario_masked_modeling.pptx"
PDF = SLIDES / "seminario_masked_modeling.pdf"


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


def slide_bullets(pr, titulo: str, itens: list[str]):
    slide = pr.slides.add_slide(pr.slide_layouts[1])
    slide.shapes.title.text = titulo
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(30)
    corpo = slide.placeholders[1].text_frame
    for i, item in enumerate(itens):
        par = corpo.paragraphs[0] if i == 0 else corpo.add_paragraph()
        par.text = item
        par.level = 0
        par.font.size = Pt(17)
    return slide


def slide_imagem(pr, titulo: str, caminho_imagem: Path, legenda: str = ""):
    slide = pr.slides.add_slide(pr.slide_layouts[5])
    slide.shapes.title.text = titulo
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(30)
    if caminho_imagem.exists():
        from PIL import Image

        with Image.open(caminho_imagem) as im:
            w, h = im.size
        # area disponivel abaixo do titulo e acima da legenda
        topo_min = 1.5
        base_max = 6.8 if legenda else 7.1
        altura_disp = base_max - topo_min
        largura_disp = 12.0
        escala = min(largura_disp / (w / 96.0), altura_disp / (h / 96.0))
        largura = (w / 96.0) * escala
        altura = (h / 96.0) * escala
        topo = topo_min + max(0.0, (altura_disp - altura) / 2)
        slide.shapes.add_picture(
            str(caminho_imagem), Inches((13.333 - largura) / 2), Inches(topo),
            width=Inches(largura), height=Inches(altura),
        )
    if legenda:
        caixa = slide.shapes.add_textbox(Inches(0.67), Inches(6.95), Inches(12.0), Inches(0.45))
        par = caixa.text_frame.paragraphs[0]
        par.text = legenda
        par.font.size = Pt(14)
    return slide


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

    # fileira superior: imagem -> patches -> mascara -> codificador
    for i, idx_bloco in enumerate(range(4)):
        caixa(blocos[idx_bloco], i, topo1)
        if i < 3:
            seta(
                MSO_SHAPE.RIGHT_ARROW,
                margem + i * passo + largura_box,
                topo1 + (altura_box - altura_seta) // 2,
                largura_seta, altura_seta,
            )
    # descida: codificador -> tokens de mascara
    seta(
        MSO_SHAPE.DOWN_ARROW,
        margem + 3 * passo + (largura_box - largura_seta) // 2,
        topo1 + altura_box + Inches(0.12),
        largura_seta,
        topo2 - topo1 - altura_box - Inches(0.24),
    )
    # fileira inferior em sentido oposto: tokens -> decod -> reconstrucao -> perda
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
    """Tabela comparativa (primeira coluna: dimensao; demais: metodos)."""
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


def slide_duas_imagens(pr, titulo: str, imagens: list[tuple[Path, str]], legenda: str):
    """Empilha ate duas imagens com rotulo proprio para cada uma."""
    from PIL import Image

    slide = pr.slides.add_slide(pr.slide_layouts[5])
    slide.shapes.title.text = titulo
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(30)
    alturas = [2.85, 1.95]
    tops = [1.82, 5.02]
    for i, (caminho, rotulo) in enumerate(imagens):
        _caixa_texto(
            slide, Inches(0.67), Inches(tops[i] - 0.37), Inches(12.0), Inches(0.34),
            [(rotulo, 13, True)],
        )
        if caminho.exists():
            with Image.open(caminho) as im:
                w, h = im.size
            largura_disp, altura_disp = 10.5, alturas[i]
            escala = min(largura_disp / (w / 96.0), altura_disp / (h / 96.0))
            largura = (w / 96.0) * escala
            altura = (h / 96.0) * escala
            slide.shapes.add_picture(
                str(caminho),
                Inches((13.333 - largura) / 2),
                Inches(tops[i] + (altura_disp - altura) / 2),
                width=Inches(largura), height=Inches(altura),
            )
    if legenda:
        _caixa_texto(
            slide, Inches(0.67), Inches(7.0), Inches(12.0), Inches(0.42),
            [(legenda, 13, False)],
        )
    return slide


def verificar_limites(pr) -> None:
    """Falha se qualquer shape sair da area do slide."""
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


def principal():
    m = pd.read_csv(RESULTADOS / "metricas.csv")
    linha50 = m[m["condição"] == "mascara_50"].iloc[0]
    linha75 = m[m["condição"] == "mascara_75"].iloc[0]
    epocas = int(linha50["épocas"])
    batch = int(linha50["batch"])
    lr = float(linha50["lr"])
    tempo_epoca = float(linha50["tempo_epoca_medido_s"])
    orcamento = float(linha50["orcamento_previsto_min"])
    mse50 = float(linha50["mse_teste_ocultos"])
    mse75 = float(linha75["mse_teste_ocultos"])
    variacao = (mse75 - mse50) / mse50 * 100.0

    pr = apresentacao()

    slide_titulo(
        pr,
        "Masked Modeling em Deep Learning",
        "Frederico Maciel de Mello | Luan Pedro de Souza Silva\nSeminário, 16/10",
    )
    slide_bullets(
        pr,
        "Roteiro",
        [
            "O problema: aprender representações com conteúdo incompleto",
            "Panorama: BERT, MAE e SimMIM",
            "Fluxo do MAE: diagrama, equação da perda e pseudocódigo",
            "Arquitetura e nossa implementação",
            "Protocolo e orçamento de treino",
            "Experimento: máscara de 50% contra 75%",
            "Resultados, críticas e próximos passos",
            "Aplicações e referências",
        ],
    )
    slide_bullets(
        pr,
        "O problema",
        [
            "Supervisão cara: rotular milhões de imagens é custoso",
            "Auto-supervisão: a própria imagem fornece o alvo",
            "BERT: prever palavras ocultas do texto",
            "Ideia do vision masking: ocultar partes da imagem e reconstruir",
            "A hipótese (He et al., 2022): reconstruir obrigaria o modelo a representar objetos; exigiria avaliação downstream para confirmar",
        ],
    )
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
    slide_bullets(
        pr,
        "Arquitetura e implementação",
        [
            "Patchify: imagem 32x32x3 em 16 patches de 8x8 (192 valores cada)",
            "Encoder: somente os patches visíveis entram (ViT dim 128, 4 blocos, 4 heads)",
            "Decoder leve: dim 64, 2 blocos, tokens de máscara + embedding posicional",
            "Saída: 192 valores por patch oculto; o decoder é descartado em tarefas posteriores",
            "MAE próprio em PyTorch puro (sem código de terceiros), validado contra oráculo fora do pacote",
            "Máscara aninhada: permutação fixa por imagem com seed 42",
            "50% oculta 8 patches; 75% oculta 12 (todos os da 50% também)",
        ],
    )
    slide_bullets(
        pr,
        "Protocolo e orçamento de treino",
        [
            "CIFAR-10 verificado por md5 antes de qualquer uso",
            "Subset seed 42, balanceado: 500 treino, 100 validação e 100 teste por classe",
            "Validação disjunta do treino; teste sai do split oficial e é usado só no fim",
            "Métrica: MSE nos patches ocultos do conjunto de teste",
        ],
    )
    slide_bullets(
        pr,
        "Experimento: máscara de 50% contra 75%",
        [
            f"Mesmo treino nas duas condições: {epocas} épocas, batch {batch}, lr {lr:.1e} (AdamW)",
            "O custo computacional por época diverge: a 75% o encoder vê 4 tokens, a 50% vê 8",
            f"Tempo medido por época (na condição 75%): {tempo_epoca:.2f} s",
            f"Orçamento previsto: {orcamento:.0f} minutos para as duas condições somadas",
            f"MSE de teste nos ocultos: 50% = {mse50:.4f} | 75% = {mse75:.4f}",
        ],
    )
    slide_duas_imagens(
        pr,
        "Resultados: reconstruções e curva de perda",
        [
            (RESULTADOS / "reconstrucoes.png", "Reconstruções: 8 imagens fixas do teste (seed 42)"),
            (RESULTADOS / "curva_perda.png", "Curva de perda de validação: MSE nos patches ocultos por época"),
        ],
        "Esquerda: original, mascarada e reconstrução por condição; direita: as duas condições no mesmo eixo",
    )
    slide_bullets(
        pr,
        "Resultados, críticas e próximos passos",
        [
            f"75% oculta mais e é mais difícil: MSE {mse75:.4f} contra {mse50:.4f} a 50% ({variacao:+.1f}%)",
            "Épocas, batch e lr igualados; a computação por época diverge (4 contra 8 tokens no encoder)",
            "Máscara aninhada isola o efeito da taxa: os patches ocultos a 50% também estão a 75%",
            "Evidência desta configuração: semente única 42, teste fixo de 1.000 imagens e máscara aninhada",
            "Não generalizar: repetir com mais sementes e avaliar downstream antes de concluir",
            "Qualidade visual da reconstrução não é prova de representações melhores",
            "Dataset pequeno e didático: qualidade absoluta menor que a do paper",
            "Linear probing e classificação downstream fora do escopo; próximo passo: linear probing em mais sementes",
        ],
    )
    slide = pr.slides.add_slide(pr.slide_layouts[5])
    slide.shapes.title.text = "Aplicações e referências"
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(30)
    _caixa_texto(
        slide, Inches(0.67), Inches(1.5), Inches(12.0), Inches(2.3),
        [
            ("Aplicações das representações aprendidas:", 15, True),
            ("BERT: compreensão de linguagem (busca, classificação e diálogo)", 14, False),
            ("MAE: classificação, detecção e segmentação de imagens", 14, False),
            ("SimMIM: classificação, detecção e segmentação em imagens", 14, False),
        ],
    )
    _caixa_texto(
        slide, Inches(0.67), Inches(3.35), Inches(12.0), Inches(3.5),
        [
            ("Referências:", 15, True),
            ("Devlin, J.; Chang, M.; Lee, K.; Toutanova, K. (2019). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. NAACL-HLT.", 12, False),
            ("He, K.; Chen, X.; Xie, S.; Li, Y.; Dollár, P.; Girshick, R. (2022). Masked Autoencoders Are Scalable Vision Learners. CVPR.", 12, False),
            ("Xie, Z.; Zhang, Z.; Lin, Y.; Bian, J.; Lin, L.; Zeng, D. (2022). SimMIM: A Simple Framework for Masked Image Modeling. CVPR.", 12, False),
            ("Krizhevsky, A.; Nair, V.; Hinton, G. (2009). CIFAR-10 (Canadian Institute for Advanced Research). Fonte dos dados, verificado por md5.", 12, False),
        ],
    )

    PPTX.parent.mkdir(exist_ok=True)
    n_slides = len(pr.slides._sldIdLst)
    verificar_limites(pr)
    pr.save(PPTX)
    subprocess.run(
        ["/usr/bin/soffice", "--headless", "--convert-to", "pdf", "--outdir", str(SLIDES), str(PPTX)],
        check=True,
        capture_output=True,
    )
    # gera um PNG por pagina e confere a contagem
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