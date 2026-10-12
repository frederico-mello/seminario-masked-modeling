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
    linha50 = m[m["condicao"] == "mascara_50"].iloc[0]
    linha75 = m[m["condicao"] == "mascara_75"].iloc[0]
    epocas = int(linha50["epocas"])
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
            "Arquitetura de um Masked Autoencoder",
            "Nossa implementação: patches, máscara aninhada, perda",
            "Protocolo e orcamento de treino",
            "Experimento: máscara de 50% contra 75%",
            "Resultados, críticas e próximos passos",
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
    slide_bullets(
        pr,
        "Panorama: BERT, MAE e SimMIM",
        [
            "BERT (2018): mascarar tokens de texto e prever os ocultos",
            "MAE (He et al., 2022): patches ocultos, encoder assimétrico, decoder leve",
            "SimMIM (2022): mascarar pixels brutos com decoder simples",
            "Diferença chave: o quanto se pode ocultar (75% funciona no MAE)",
        ],
    )
    slide_bullets(
        pr,
        "Arquitetura do MAE",
        [
            "Patchify: imagem 32x32x3 em 16 patches de 8x8 (192 valores cada)",
            "Encoder: somente os patches visíveis entram (ViT dim 128, 4 blocos, 4 heads)",
            "Decoder leve: dim 64, 2 blocos, tokens de máscara + embedding posicional",
            "Saída: 192 valores por patch oculto (a imagem completa)",
            "Perda: MSE somente nos patches ocultos, pixels brutos em [0,1]",
        ],
    )
    slide_bullets(
        pr,
        "Nossa implementação",
        [
            "MAE próprio em PyTorch puro (sem código de terceiros)",
            "Máscara aninhada: permutação fixa por imagem com seed 42",
            "50% oculta 8 patches; 75% oculta 12 (todos os da 50% também)",
            "Validação contra o oráculo vit-pytorch em testes fora da entrega",
        ],
    )
    slide_bullets(
        pr,
        "Dados e protocolo",
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
            f"O custo computacional por época diverge: a 75% o encoder vê 4 tokens, a 50% vê 8",
            f"Tempo medido por época na RTX 3050 (na condição 75%): {tempo_epoca:.2f} s",
            f"Orçamento previsto: {orcamento:.0f} minutos para as duas condições somadas",
            f"MSE de teste nos ocultos: 50% = {mse50:.4f} | 75% = {mse75:.4f}",
        ],
    )
    slide_imagem(
        pr,
        "Resultados: reconstruções",
        RESULTADOS / "reconstrucoes.png",
        "8 imagens fixas do teste (seed 42): original, mascarada e reconstrucao por condicao",
    )
    slide_imagem(
        pr,
        "Resultados: curva de perda de validação",
        RESULTADOS / "curva_perda.png",
        "MSE de validação nos patches ocultos por época",
    )
    slide_bullets(
        pr,
        "Lendo os números",
        [
            f"75% oculta mais e é mais difícil: MSE {mse75:.4f} contra {mse50:.4f} a 50% ({variacao:+.1f}%)",
            "Épocas, batch e taxa de aprendizado foram igualados; a quantidade de computação por época diverge (4 contra 8 tokens no encoder)",
            "A diferença principal entre condições vem da taxa de ocultação",
            "Máscara aninhada isola o efeito da taxa (mesmos patches ocultos a 50%)",
            "Semente única 42: comparação determinística, mas repetição com mais sementes é necessária",
        ],
    )
    slide_bullets(
        pr,
        "Limitações e próximos passos",
        [
            "Dataset pequeno e didático: qualidade absoluta é menor que a do paper",
            "Linear probing e classificação downstream: fora do escopo deste trabalho",
            "Próximo passo: avaliar representações com linear probing em mais sementes",
            "Referência: He et al. (2022), Masked Autoencoders Are Scalable Vision Learners",
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