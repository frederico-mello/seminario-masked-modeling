# Spec Delta

## Purpose

Define o experimento comparativo entre mascaramento de 50% e 75%, com mesmo orçamento de treino, máscara aninhada e métrica de teste única, para que a diferença observada seja atribuível à taxa de mascaramento.

## ADDED Requirements

### Requirement: Mesmo orçamento de épocas nas duas condições
O experimento SHALL treinar as condições de 50% e 75% com o mesmo número de épocas, o mesmo tamanho de batch e a mesma taxa de aprendizado, e o otimizador SHALL ser AdamW em ambas.

#### Scenario: Orçamento idêntico
- **WHEN** os dois treinos terminam
- **THEN** ambos registram o mesmo número de épocas, batch e learning rate

#### Scenario: Orçamento medido antes do treino final
- **WHEN** o experimento é preparado
- **THEN** o tempo de uma época real na GPU é medido e o orçamento previsto e o medido são registrados

### Requirement: Máscara aninhada por imagem
O experimento SHALL gerar, para cada imagem, uma permutação fixa dos 16 patches com seed 42, de modo que a condição de 50% oculte os 8 primeiros índices e a de 75% oculte os 12 primeiros.

#### Scenario: Inclusão das máscaras
- **WHEN** as máscaras das duas condições são comparadas para a mesma imagem
- **THEN** todos os patches ocultos a 50% também estão ocultos a 75%

#### Scenario: Determinismo da máscara
- **WHEN** as máscaras são geradas duas vezes com seed 42
- **THEN** as permutações são idênticas

### Requirement: Métrica de teste
O experimento SHALL reportar, para cada condição, o erro quadrático médio nos patches ocultos do conjunto de teste, calculado somente após o fim do treino.

#### Scenario: Métrica final
- **WHEN** o treino de uma condição termina
- **THEN** o MSE nos patches ocultos do teste é registrado em `metricas.csv` com a condição correspondente

### Requirement: Curva de perda de validação
O experimento SHALL registrar a perda de validação em cada época para as duas condições e SHALL apresentar as duas curvas no mesmo gráfico.

#### Scenario: Curva comparável
- **WHEN** `curva_perda.png` é gerado
- **THEN** ele mostra a perda de validação por época das duas condições com o mesmo eixo

### Requirement: Figura de reconstruções fixas
O experimento SHALL gerar `reconstrucoes.png` com 8 imagens fixas do conjunto de teste, mostrando para cada condição a original, a versão mascarada e a reconstrução.

#### Scenario: Imagens fixas entre execuções
- **WHEN** o notebook é executado duas vezes com as mesmas sementes
- **THEN** as 8 imagens exibidas são as mesmas

#### Scenario: Conteúdo da figura
- **WHEN** `reconstrucoes.png` é aberto
- **THEN** ele contém, para cada condição, as três visualizações das 8 imagens
