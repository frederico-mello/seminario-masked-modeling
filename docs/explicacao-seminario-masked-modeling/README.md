# Seminário: Masked Modeling em Deep Learning

**Em uma frase:** este repositório ensina um modelo a reconstruir partes escondidas de imagens pequenas e compara duas quantidades de conteúdo oculto.

Este guia explica o que o projeto faz, como os arquivos se conectam e o que acontece ao executar o experimento.

## Por onde começar

1. [Visão geral](01-visao-geral.md): o objetivo, a analogia e os limites do experimento.
2. [Anatomia](02-anatomia.md): as pastas e o papel de cada peça.
3. [Jornada](03-jornada.md): o caminho dos dados até os resultados e os slides.
4. [Dados](04-dados.md): os arquivos, campos, tamanhos e métricas.
5. [Componentes](05-componentes.md): o modelo, o treino, os testes e os geradores.
6. [Glossário](glossario.md): termos técnicos explicados em linguagem comum.
7. [Fontes e limites](fontes-pesquisa.md): arquivos consultados, pesquisa externa e limites da leitura.

Uma leitura rápida também está disponível no [pôster](imagens/poster.png) e no [tour interativo](tour.html).

## Diagramas incluídos

Há cinco diagramas Mermaid: um mapa do fluxo geral, dois diagramas de sequência, um mapa dos dados e um diagrama das partes do modelo. Eles ficam nos capítulos 02 a 05. O pôster resume a mesma jornada em uma página.

## Fatos essenciais

- O modelo principal é um Masked Autoencoder, ou MAE, implementado em `codigo/mae.py`.
- Cada imagem CIFAR-10 de 32 por 32 pixels é dividida em 16 quadrados de 8 por 8 pixels.
- O experimento compara ocultar 8 ou 12 desses 16 quadrados.
- Os conjuntos usados têm 5.000 imagens de treino, 1.000 de validação e 1.000 de teste.
- O treino exige uma GPU NVIDIA com CUDA. O código não troca silenciosamente para CPU.
- A apresentação inclui resultados complementares de uma implementação pública. Esses resultados são separados das medições do modelo deste repositório.

## Como interpretar este guia

Os fatos sobre o comportamento vêm do README, do código, das especificações e dos arquivos de resultado do repositório. As pesquisas externas explicam convenções do MAE, do CIFAR-10, do Torchvision, do PyTorch e do uv. Uma leitura marcada como *(inferência)* é uma interpretação, não uma afirmação explícita do repositório.
