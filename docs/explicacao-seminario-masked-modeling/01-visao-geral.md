# 01. Visão geral

## O que é

O repositório apresenta um seminário sobre aprendizagem a partir de dados sem rótulos e implementa um experimento didático com imagens. O modelo recebe uma imagem, esconde alguns pedaços e tenta reconstruir o que falta.

Essa família de métodos é chamada de *masked modeling*. A ideia é usar o próprio conteúdo como exercício: uma parte fica visível e serve de pista para prever a parte escondida. O projeto compara BERT, MAE e SimMIM na apresentação, mas implementa o experimento principal com MAE.

## Uma analogia

A imagem pode ser comparada a um mosaico de 16 peças. O modelo vê algumas peças e tenta desenhar as que foram cobertas. Nesta implementação, são cobertas 8 peças em uma condição e 12 na outra.

O encoder, que interpreta as peças visíveis, não recebe as peças escondidas. O decoder, que monta a resposta, usa as partes interpretadas e marcadores das posições faltantes para prever os pixels.

## O experimento

As imagens vêm do CIFAR-10, um conjunto conhecido de imagens coloridas pequenas. Cada imagem tem 32 por 32 pixels e uma das 10 classes. O código cria uma seleção balanceada e separa treino, validação e teste.

A comparação esconde quantidades diferentes. As demais condições permanecem iguais: semente aleatória, épocas, tamanho dos lotes e taxa de aprendizado. O otimizador usado é AdamW, uma regra para ajustar os valores internos do modelo durante o treino.

A medida principal é o erro quadrático médio, abreviado MSE. Ele resume a diferença entre os pixels previstos e os pixels corretos, somente nas peças escondidas.

## O que sai do projeto

O notebook registra a medida no teste em `resultados/metricas.csv`. Também grava uma curva de erro por época e imagens com originais, partes cobertas e reconstruções.

Na cópia examinada, o CSV registra MSE arredondado de 0,06084 para a máscara de 50% e 0,07168 para a de 75%. Esses números descrevem esta configuração, com uma semente e um conjunto de teste fixos. Não provam que uma taxa seja melhor em geral.

O gerador de slides monta uma apresentação de 12 páginas em PPTX e PDF. Um script separado reúne arquivos selecionados em um ZIP e calcula um MD5 para cada arquivo incluído.

## O que fica de fora

A qualidade visual das reconstruções não demonstra, por si só, que o modelo aprendeu representações melhores para outras tarefas. O próprio material do projeto delimita os resultados a esta experiência e indica avaliações futuras.

A etapa chamada *linear probing*, que testa as representações com um classificador simples, não está implementada. O treino exige GPU NVIDIA com CUDA 13.0 e falha com erro explícito se a GPU não estiver disponível.

Os slides também mostram resultados de um experimento complementar com MAE pré-treinado público. O README identifica esses resultados como externos, não como medições reproduzidas por este código.

## Onde conferir

- Objetivo e comandos: `README.md`.
- Modelo e perda: `codigo/mae.py`.
- Treino e avaliação: `codigo/treino.py`.
- Números medidos: `resultados/metricas.csv`.
- Limites da comparação: `openspec/specs/experimento-mascaras/spec.md` e `openspec/specs/slides-seminario/spec.md`.
