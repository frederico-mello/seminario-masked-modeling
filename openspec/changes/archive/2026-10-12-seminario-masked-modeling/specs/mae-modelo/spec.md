# Spec Delta

## Purpose

Define o comportamento do modelo Masked Autoencoder usado no seminário: entrada em patches, máscara, codificação apenas dos patches visíveis, reconstrução dos ocultos e perda em pixels brutos, sem depender de código de terceiros em tempo de execução.

## ADDED Requirements

### Requirement: Entrada em patches de 8x8
O modelo SHALL receber imagens de 32x32x3 com valores no intervalo [0,1] e SHALL dividi-las em 16 patches de 8x8.

#### Scenario: Formato da entrada
- **WHEN** uma imagem 32x32x3 é fornecida ao modelo
- **THEN** ela é representada por 16 patches

#### Scenario: Valores fora do intervalo
- **WHEN** uma imagem com valores fora de [0,1] é fornecida
- **THEN** o modelo rejeita a entrada com erro explícito

### Requirement: Codificação somente dos patches visíveis
O encoder SHALL processar apenas os patches não mascarados, e os patches mascarados SHALL NOT ser fornecidos ao encoder.

#### Scenario: Número de tokens do encoder
- **WHEN** a máscara oculta 50% dos patches
- **THEN** o encoder recebe 8 patches

#### Scenario: Máscara de 75%
- **WHEN** a máscara oculta 75% dos patches
- **THEN** o encoder recebe 4 patches

### Requirement: Arquitetura do encoder e do decoder
O encoder SHALL ter dimensão 128, 4 blocos Transformer e 4 cabeças de atenção. O decoder SHALL ter dimensão 64, 2 blocos Transformer e 4 cabeças de atenção, e SHALL prever os 192 valores de cada patch.

#### Scenario: Saída do decoder
- **WHEN** o decoder recebe os tokens visíveis e os tokens de máscara
- **THEN** ele produz uma predição de 192 valores para cada um dos 16 patches

### Requirement: Perda somente nos patches ocultos
O modelo SHALL calcular a perda como erro quadrático médio entre predição e alvo em pixels brutos, somente nos patches ocultos. Patches visíveis SHALL NOT contribuir para a perda.

#### Scenario: Perda sem patches visíveis
- **WHEN** a perda é calculada para uma imagem com máscara
- **THEN** o valor depende apenas dos patches ocultos

#### Scenario: Escala de pixels
- **WHEN** a perda é calculada
- **THEN** os alvos são os pixels em [0,1], sem normalização por canal ou por patch

### Requirement: Mesmo comportamento que a referência de teste
O modelo SHALL produzir, para mesma configuração, mesmos pesos e mesma máscara, formas de saída, perda e reconstrução compatíveis com a classe MAE do vit-pytorch dentro de tolerância numérica explícita.

#### Scenario: Equivalência com o oráculo
- **WHEN** o teste de equivalência compara as duas implementações com pesos iguais e mesma máscara
- **THEN** as formas são iguais e as diferenças de perda e de reconstrução ficam dentro da tolerância definida no teste

#### Scenario: Oráculo fora da execução
- **WHEN** o modelo é usado para treino e avaliação
- **THEN** nenhum código do vit-pytorch é importado
