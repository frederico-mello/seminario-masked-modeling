# Planejamento do seminário: Masked Modeling em Deep Learning

> Convertido de `Planejamento_Masked_Modeling_em_Deep_Learning.docx` (md5 b4ce40e3aaef918f08bfec4d1693fa6e) para leitura pelos agentes.

# Planejamento do seminário

Masked Modeling em Deep Learning: aprendizagem de representações pela reconstrução de conteúdo oculto

Grupo: [inserir nome e integrantes]

Questão norteadora: Como uma rede neural pode aprender representações úteis a partir de dados sem rótulos, prevendo partes deliberadamente ocultadas da própria entrada?

O seminário apresentará masked modeling como uma família de objetivos de auto-supervisão, não como um único algoritmo. BERT será o exemplo em texto; o foco técnico será o Masked Autoencoder (MAE) para imagens; SimMIM servirá de contraste entre diferentes escolhas de função de perda e arquitetura. BERT prevê tokens ocultos, enquanto MAE e SimMIM predizem conteúdo de imagem, com diferenças no modo de reconstrução (DEVLIN et al., 2019; HE et al., 2022; XIE et al., 2022)[2][4][5].

## Objetivos

Definir masked modeling e relacioná-lo à aprendizagem auto-supervisionada.

Distinguir a previsão de tokens discretos da reconstrução de pixels.

Explicar o fluxo do MAE com diagrama, equação e pseudocódigo.

Comparar experimentalmente duas proporções de máscara, usando métricas e resultados visuais.

## Roteiro, com tempo total de 20 minutos

| Tempo | Conteúdo |
|---|---|
| 00:00 a 02:00 | Título, integrantes, questão norteadora e motivação: aprender com dados sem anotação manual. |
| 02:00 a 05:00 | Conceitos: auto-supervisão, máscara, alvo de predição, pré-treinamento e transferência. Introdução breve a BERT. |
| 05:00 a 08:00 | Comparação de BERT, MAE e SimMIM: modalidade, conteúdo previsto, perda e arquitetura. |
| 08:00 a 11:00 | Diagrama do processo MAE e explicação da arquitetura assimétrica. |
| 11:00 a 15:00 | Derivação da função objetivo e pseudocódigo do treinamento. |
| 15:00 a 18:00 | Experimento, métricas, visualizações e interpretação dos resultados obtidos. |
| 18:00 a 19:00 | Aplicações, limitações e conclusões. |
| 19:00 a 20:00 | Pergunta ou comentário final. |

## Diagrama de blocos proposto

Imagem sem rótulo → divisão em patches → máscara aleatória → codificador ViT sobre patches visíveis → inserção de tokens de máscara e posições → decodificador leve → reconstrução dos pixels → perda nos patches ocultos → atualização dos parâmetros

No MAE, o codificador processa somente os patches visíveis. O decodificador recebe as representações desses patches e tokens que indicam as posições ocultas, e reconstrói os pixels. O artigo apresenta uma proporção alta de máscara, como 75%; para tarefas posteriores de reconhecimento, o decodificador é descartado e o codificador pode ser adaptado (HE et al., 2022)[4].

## Derivação e algoritmo

Seja xᵢ o vetor de pixels do patch i, M o conjunto de patches mascarados e x̂ᵢ a reconstrução produzida pelo modelo. A perda pode ser apresentada como erro quadrático médio aplicado apenas aos patches ocultos:

L_MAE = (1 / |M|) Σ_{i ∈ M} (1 / d) ||xᵢ − x̂ᵢ||²₂

em que d é o número de valores de pixel por patch. O artigo descreve a reconstrução em pixels e o cálculo da perda somente nas regiões mascaradas (HE et al., 2022)[4].

para cada lote de imagens x:    patches = dividir_em_patches(x)    visíveis, ocultos, posições = amostrar_máscara(patches, razão=r)    z = codificador(visíveis, posições_visíveis)    reconstrução = decodificador(z, tokens_de_máscara, posições)    perda = MSE(reconstrução[ocultos], patches[ocultos])    atualizar parâmetros por retropropagação

Como contraste, BERT prevê tokens originais em posições ocultadas do texto. SimMIM também trabalha com imagens, mas apresenta regressão direta de pixels, perda L₁ e uma cabeça de predição linear leve (DEVLIN et al., 2019; HE et al., 2022; XIE et al., 2022)[2][4][5].

## Experimento proposto

Pergunta experimental: como a proporção de patches ocultos afeta o erro e a aparência das imagens reconstruídas?

Dados: CIFAR-10, com imagens coloridas de 32 × 32 pixels. Usar 5.000 imagens de treino e 1.000 de teste. Os rótulos ficam fora do pré-treinamento mascarado. O conjunto completo contém 60.000 imagens em 10 classes (KRIZHEVSKY; NAIR; HINTON, [s. d.])[8].

Modelo: versão didática pequena de MAE com codificador e decodificador Transformer; patches de 8 × 8 pixels, totalizando 16 patches por imagem.

Condições: comparar razões de máscara de 50% e 75%, mantendo arquitetura, épocas, dados e semente aleatória constantes.

Métrica: erro quadrático médio nos patches ocultos do conjunto de teste. Como extensão, pode-se avaliar um classificador linear com o codificador congelado.

Resultados visuais: mostrar a imagem original, a imagem mascarada e a reconstrução; incluir curva de perda de validação e tabela com o erro final por proporção de máscara.

A hipótese a testar é que uma máscara maior pode exigir maior uso do contexto visível, mas também tornar a reconstrução mais difícil. Isso é uma hipótese, não um resultado antecipado. A qualidade visual da reconstrução, isoladamente, não será tratada como prova de que as representações aprendidas são melhores.

## Aplicações e limitações

BERT foi avaliado em tarefas de compreensão de linguagem, incluindo resposta a perguntas e inferência textual. O MAE foi estudado em transferência para tarefas visuais, como classificação, detecção de objetos e segmentação (DEVLIN et al., 2019; HE et al., 2022)[2][4]. Como limitações, discutir que a estratégia de máscara e o alvo de predição precisam ser adequados à modalidade, e que uma reconstrução convincente não garante, por si só, bom desempenho em tarefas posteriores (HE et al., 2022; XIE et al., 2022)[4][5].

## Conteúdo do arquivo compactado

seminario_masked_modeling.zip├── slides.pdf├── slides.pptx                 (se desejarem incluir o arquivo editável)├── codigo/notebook.ipynb├── dados/cifar10_subset/       (subconjunto realmente usado no teste)├── resultados/reconstrucoes.png├── resultados/curva_perda.png├── resultados/metricas.csv└── README.md                   (ambiente, execução, semente e fontes)

O repositório oficial do MAE pode servir como referência de implementação e demonstração visual. Se algum código for reutilizado, a origem deverá ser citada nos slides e no README.md (FACEBOOK RESEARCH, [s. d.])[7].

Status: este é o planejamento, não a apresentação pronta. As reconstruções, métricas e curvas ainda precisam ser produzidas; nenhum resultado experimental foi presumido.

## Referências básicas

DEVLIN, Jacob; CHANG, Ming-Wei; LEE, Kenton; TOUTANOVA, Kristina. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. In: Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies. Minneapolis: Association for Computational Linguistics, 2019. v. 1, p. 4171–4186. DOI: 10.18653/v1/N19-1423. [2] https://aclanthology.org/N19-1423/

FACEBOOK RESEARCH. Masked Autoencoders: A PyTorch Implementation. GitHub, [s. d.]. Disponível em: https://github.com/facebookresearch/mae. Acesso em: 9 out. 2026. [7]

HE, Kaiming; CHEN, Xinlei; XIE, Saining; LI, Yanghao; DOLLÁR, Piotr; GIRSHICK, Ross. Masked Autoencoders Are Scalable Vision Learners. In: 2022 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2022, New Orleans. [S. l.]: IEEE, 2022. p. 15979–15988. DOI: 10.1109/CVPR52688.2022.01553. [4][13]

KRIZHEVSKY, Alex; NAIR, Vinod; HINTON, Geoffrey. CIFAR-10 and CIFAR-100 datasets. [S. l.]: University of Toronto, [s. d.]. Disponível em: https://cave.cs.toronto.edu/kriz/cifar.html. Acesso em: 9 out. 2026. [8]

XIE, Zhenda; ZHANG, Zheng; CAO, Yue; LIN, Yutong; BAO, Jianmin; YAO, Zhuliang; DAI, Qi; HU, Han. SimMIM: A Simple Framework for Masked Image Modeling. In: Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2022, p. 9653–9663. [5] https://openaccess.thecvf.com/content/CVPR2022/html/Xie_SimMIM_A_Simple_Framework_for_Masked_Image_Modeling_CVPR_2022_paper.html
