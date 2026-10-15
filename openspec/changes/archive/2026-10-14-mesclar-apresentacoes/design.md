# Design

## Context

A nossa entrega atual (12 slides gerados por `scripts/gerar_slides.py`) cobre o experimento próprio do CIFAR-10, mas não cobre parte dos itens obrigatórios das instruções da disciplina: aplicações por domínio, o fluxo pós MAE e um segundo resultado experimental com resultados visuais distintos. A apresentação complementar (21 slides, `Apresentação_final.pptx`) é sobre o mesmo tema e grupo, inclui o experimento com MAE pré-treinado (taxas 25%, 50%, 75% e 90%) e os tópicos faltantes. Ver proposal.md.

Restrições vigentes: total de 10 a 12 slides conferido por `verificar_limites`; pt-BR acentuado; proibido o caractere de travessão U+2014 (o texto do material complementar usa travessão nos títulos e deve ser reescrito, não copiado); interpretação delimitada nos resultados.

## Goals / Non-Goals

Goals:
- Apresentação única fundida em 12 slides, no roteiro do change, gerada pelo nosso script.
- Assets visuais do experimento complementar extraídos e versionados em um único diretório do repositório.
- Rastreio de todos os números apresentados: os do experimento próprio vêm de `resultados/metricas.csv`; os do experimento complementar vêm do material complementar (texto e três imagens versadas), com crédito da implementação pública e do link do Colab.
- Deltas de especificação nas duas capacidades afetadas.

Non-Goals:
- Reproduzir o experimento complementar localmente no Apply (os números seguem como material creditado).
- Incluir imagens decorativas ou diagramas introdutórios complementares além dos que o mapa exige.
- Modificar `codigo/`, `dados/` ou o protocolo do experimento próprio.

## Inventário do material complementar (somente leitura)

Extração proibida nesta fase; no Apply, extrair de `/tmp/entrada-sem/Apresentação_final.pptx` apenas as imagens usadas.

Imagens em `ppt/media` (11 arquivos, mapeadas por slide via rels):

| Slide de origem | Arquivo | Dimensão | Papel identificado | Entra? |
|---|---|---|---|---|
| 1 | image1.png | 797x315 | decorativa da capa | não |
| 3 | image2.png | 322x267 | ilustração didática da abertura | não |
| 3 | image3.png | 532x282 | ilustração didática da abertura | não |
| 6 | image4.png | 971x297 | linha do tempo BERT para imagens | não (a tabela e o pseudocódigo nossos cobrem o panorama) |
| 7 | image5.png | 525x341 | diagrama de MLM do BERT | não (a tabela nossa cobre a comparação) |
| 8 | image6.png | 687x251 | diagrama de MIM | não (idem) |
| 9 | image7.png | 1127x281 | figura de arquitetura do MAE | não (o item obrigatório de diagrama de blocos é atendido pelo nosso diagrama de 8 etapas; duplicação dispensada) |
| 11 | image8.png | 1008x873 | captura da equação da perda | não (apresentamos a equação termo a termo em texto) |
| 14 | image9.png | 1417x275 | fluxo do experimento em 6 etapas (entrada, patches, mascaramento, MAE, reconstrução, MSE) | sim |
| 15 | image10.png | 567x682 | grade de mascarado e reconstruído nas quatro taxas (25, 50, 75, 90) | sim |
| 16 | image11.png | 737x492 | gráfico do MSE por taxa de mascaramento | sim (complemento visual dos MSEs) |

Texto relevante do material complementar (resumo):
- Slide 5: frase "O próprio dado fornece a supervisão: uma parte é ocultada e a parte original funciona como referência..."
- Slide 10: encoder com ViT processa apenas patches visíveis; decoder reconstrói os pixels dos patches ocultos.
- Slide 11: glossário termo a termo da perda (loss, conjunto mascarado, pixels reais, pixels reconstruídos, erro quadrático).
- Slide 12: fluxo pós MAE: pré-treinamento, decoder pode ser descartado, encoder em downstream (classificação, detecção, segmentação; extrator de características ou fine-tuning).
- Slide 13: experimento com MAE pré-treinado, ViT, entrada 224x224, patches 16x16, taxas 25%, 50%, 75%, 90%.
- Slide 17 (conclusões do material complementar): MSE 0,0476 com 25%; MSE 0,1403 com 75%; MSE 0,3117 com 90%; menos informação visível torna a reconstrução mais desafiadora.
- Slide 18: aplicações por domínio: visão computacional (classificação, detecção, segmentação, reconhecimento); imagens médicas (radiografias, tomografias e ressonâncias, pré-treinamento sem anotação, extração de características para diagnóstico); sensoriamento remoto (uso e cobertura do solo, detecção de mudanças, satélites, monitoramento ambiental e agrícola); outras modalidades (linguagem natural, vídeos, áudio, multimodal).
- Slide 19: fechamento: reconstruir o que foi escondido é o mecanismo para aprender boas representações.
- Slides 20 e 21: referências extras (Dosovitskiy et al., ICLR 2021; Bao et al., ICLR 2022) e crédito da implementação (Hugging Face Transformers, ViTMAE; modelo Meta AI facebook/vit-mae-base); link do Colab do experimento complementar.

## Mapa dos 12 slides (origem de cada conteúdo)

| # | Slide | Conteúdo | Origem |
|---|---|---|---|
| 1 | Capa | "Masked Modeling em Deep Learning", autores Frederico Maciel de Mello e Luan Pedro de Souza Silva, data 16/10 | nossa (atual slide 1) |
| 2 | O que é e ideia-chave | conceito de mascaramento e a frase "O próprio dado fornece a supervisão", com as quatro etapas didáticas (ocultar, usar o visível como contexto, reconstruir, aprender representações) | nossa estrutura; frase e passo a passo do material complementar (slides 2 e 5) |
| 3 | Por que usar e motivações | supervisão cara, dados não rotulados, representações relevantes, contexto e relações, pré-treinamento para tarefas futuras | nossa; reforço com termos do material complementar (slide 4) |
| 4 | Panorama BERT x MAE x SimMIM | tabela nas quatro dimensões, contraste MSE x L1, consequência arquitetural | nossa (atual slide 4); SimMIM só aqui |
| 5 | Diagrama de blocos do MAE | 8 etapas (imagem, patches, máscara, codificador nos visíveis, tokens de máscara, decoder, reconstrução, perda nos ocultos) | nossa (atual slide 5) |
| 6 | Equação e pseudocódigo | equação da perda termo a termo e os seis passos do laço, em um slide; se a legibilidade exigir, dividir em dois e fundir outro par (ex.: 9 e 10), mantendo 12 no total | nossa (atual slide 6) |
| 7 | Experimento próprio CIFAR-10 do zero | modelo do zero, máscara 50% contra 75%, semente 42, 1.000 imagens de teste, resultados visuais (`reconstrucoes.png`) e tabela de MSE de `metricas.csv`, leitura delimitada | nossa (atuais slides de experimento, condensados em 1) |
| 8 | Experimento com MAE pré-treinado | ViT-MAE, entrada 224x224, patches 16x16, taxas 25 a 90, visuais image9 e image10, gráfico image11, MSEs do material complementar, crédito da implementação (ViTMAE, facebook/vit-mae-base) e link do Colab | material complementar (slides 13 a 16 e 21; MSEs do slide 17 do material complementar) |
| 9 | Aplicações por domínio | visão computacional, imagens médicas, sensoriamento remoto, outras modalidades, com pré-treinamento e transferência | material complementar (slide 18), adaptado ao nosso formato |
| 10 | Pós MAE e tarefas downstream | pré-treinamento, decoder descartado, encoder reutilizado como extrator de características ou por fine-tuning | material complementar (slide 12), eco do nosso diagrama |
| 11 | Conclusões | o mascaramento como mecanismo para aprender representações, o que o experimento próprio mostra com delimitação, o que o experimento complementar sugere, limitação de leitura | nossa + fechamento do material complementar (slide 19: reconstruir é o mecanismo, não o objetivo final) |
| 12 | Referências | Devlin et al., 2019; Dosovitskiy et al., 2021; He et al., 2022; Bao et al., 2022; Xie et al., 2022; Krizhevsky, Nair e Hinton (CIFAR-10); crédito da implementação ViTMAE e link do Colab | nossa + referências extras do material complementar e o crédito |

Tempo: 12 slides em ate 20 minutos (cerca de 90 segundos por slide, com mais tempo nos dois slides de experimento).

## Assets complementares: direção de extração (aplicada no Apply)

- Diretório: `slides/recursos-complementares/` (ao lado do script de slides, fora de `codigo/` e `resultados/`).
- Nomes dos arquivos no repositório, fieis ao conteúdo real conferido no Apply (APPLY-FIX):
  - image9.png -> `slides/recursos-complementares/vitmae-fluxo-experimento.png` (fluxo do experimento)
  - image10.png -> `slides/recursos-complementares/vitmae-grade-taxas.png` (grade de mascarado e reconstruído por taxa)
  - image11.png -> `slides/recursos-complementares/vitmae-grafico-mse.png` (gráfico do MSE por taxa)
- Os três arquivos entram no zip do pacote de entrega (entrada em `scripts/montar_zip.py`).
- Legenda obrigatória no slide 8 creditando o material complementar e a implementação pública.

## Decisions

1. **Total fixo em 12 slides, equação e pseudocódigo em um slide.** A alternativa (dividir 6 em dois) obriga a fundir aplicações com pós MAE; a leitura termo a termo usa caixa compacta como hoje. Fallback registrado: se a legibilidade da inspeção visual do pdf falhar, dividir o slide 6 e fundir os slides 9 e 10.
2. **Figura de arquitetura complementar fora do slide 5.** Nosso diagrama de 8 etapas atende o item obrigatório; inserir essa captura duplicaria o mesmo conteúdo no espaço mais apertado do novo roteiro.
3. **Números do experimento complementar com rastreio ao material complementar.** O requisito atual liga todo número a `metricas.csv`; o delta admite uma segunda via de rastreio: MSEs do slide 17 do material complementar e gráfico do MSE por taxa versado em imagem, com crédito, sem apresentá-los como medição nossa.
4. **Diretório de assets em `slides/recursos-complementares/`.** Mantém o material do slide junto ao script que o consome; alternativa (`resultados/`) rejeitada porque o zip separa resultados da nossa medição dos visuais creditados.
5. **Travessão e aspas copiadas do pptx não entram.** Todo texto do material complementar é reescrito em pt-BR acentuado; o link do Colab e os nomes de modelo e repositório públicos são os únicos trechos copiados sem tradução.

## Risks / Trade-offs

- [Slide 8 denso: visuais das taxas, gráfico e crédito no mesmo slide] -> usar layout dedicado com legenda curta e o gráfico image11; se exceder limites, MSEs ficam em texto e o gráfico como segunda imagem.
- [MSE da taxa 50% não aparece no texto do material complementar] -> o slide cita as taxas avaliadas (25, 50, 75, 90) e os MSEs documentados (0,0476 com 25%; 0,1403 com 75%; 0,3117 com 90%); o gráfico em imagem versada cobre o quadro completo (o MSE da taxa de 50% aparece apenas nele), sem redigir número ausente.
- [Espaço vertical de image10 (567x682) estreito na largura] -> ajuste de proporção no helper já existente; `verificar_limites` falha se sair da área.
- [Travessão escondido em texto colado do material complementar] -> verificação do caractere na inspeção de geração (scripts e pdf conferem) e revisão dos rótulos no Apply.

## Migration Plan

1. (Apply) Extrair image9, image10 e image11 de `/tmp/entrada-sem/Apresentação_final.pptx` para `slides/recursos-complementares/` e versionar.
2. Reescrever `scripts/gerar_slides.py` para o mapa de 12 slides, com `verificar_limites` e o crédito no slide 8; regenerar pptx, pdf e PNGs de inspeção.
3. Atualizar `scripts/montar_zip.py` com os três assets e regenerar zip e `scripts/md5_pacote.csv`.
4. Rollback: reverter os dois scripts e remover o diretório de assets; a espinha dorsal atual permanece no histórico.

## Open Questions

- Legibilidade do gráfico do MSE complementar (737x492) no layout de 12 slides: resolvido na inspeção visual do pdf no Apply (legível ao lado dos MSEs em texto).
- Confirmado na inspeção do Apply: image9 (fluxo largo de 1.417x275) e image10 (grade por taxa) entram os dois no slide 8 e cobrem o exigido de resultados visuais.

## Checks deterministicos antecipados (inventário, sem executar)

Registrados em tasks.md com comando, diretório, pré-requisitos e resultado esperado:

1. `uv sync --locked` (raiz): cria o ambiente do lockfile; obrigatório.
2. `uv run pytest -q` (raiz): suíte completa; obrigatório; em CI pela `tests.yml` no push e em PR.
3. `uv run python scripts/gerar_slides.py` (raiz): exige LibreOffice e pdftoppm de sistema; produz pptx, pdf e PNGs de inspeção; obrigatório para o par de slides, condicional para os PNGs (somente inspeção).
4. `uv run python scripts/montar_zip.py` (raiz): exige todos os obrigatórios; produz zip e `scripts/md5_pacote.csv`; obrigatório.

Artefatos que exigem reverificação ao final: `slides/seminario_masked_modeling.pptx`, `.pdf`, os PNGs de inspeção, o zip e `scripts/md5_pacote.csv`.

Lacunas para aprovação: resolvidas no Apply (leia-se Open Questions).