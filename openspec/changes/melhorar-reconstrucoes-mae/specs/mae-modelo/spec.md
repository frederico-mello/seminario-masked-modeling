# Spec Delta

## MODIFIED Requirements

### Requirement: Arquitetura do encoder e do decoder
O encoder SHALL ter dimensão 128, 4 blocos Transformer e 4 cabeças de atenção na configuração de referência. Candidatos do estudo SHALL declarar explicitamente qualquer variação de dimensão, blocos e cabeças. O decoder SHALL prever os 192 valores de cada patch.

#### Scenario: Saída do decoder
- **WHEN** o decoder recebe tokens visíveis e tokens de máscara
- **THEN** produz uma predição de 192 valores para cada um dos 16 patches; os parâmetros de cada variante são declarados e associados à execução antes do treino

### Requirement: Perda somente nos patches ocultos
O MAE de referência SHALL calcular erro quadrático médio nos pixels brutos dos patches ocultos. Uma candidata pode declarar outra função de perda aplicada aos patches ocultos; pixels visíveis SHALL NOT contribuir para a perda de treino.

#### Scenario: Perda sem patches visíveis
- **WHEN** a perda é calculada para uma imagem com máscara
- **THEN** seu valor depende apenas dos patches ocultos e, para a referência, é o MSE em pixels brutos

#### Scenario: Escala de pixels
- **WHEN** a perda é calculada
- **THEN** os alvos são pixels em [0,1], sem normalização por canal ou por patch; variantes declaram fórmula e ponderações antes do treino

## ADDED Requirements

### Requirement: Configuração comum congelada
O estudo SHALL usar batch 64, AdamW com learning rate 1e-4, weight decay 0,05, betas (0,9; 0,999), epsilon 1e-8, precisão float32, sem scheduler e sem clipping de gradiente em todos os candidatos. O restante da configuração C0 SHALL ser registrado literalmente no manifesto. Código, ambiente/lockfile, splits/índices e configuração completa SHALL ser identificados por versões e hashes antes do piloto e permanecer congelados durante o estudo.

#### Scenario: Configuração comparável
- **WHEN** um candidato é iniciado
- **THEN** recebe a configuração comum congelada; somente a arquitetura de decoder declarada em C1, a função de perda declarada em C2 ou o residual declarado em C3 diferem de C0

#### Scenario: Identidade de execução
- **WHEN** um piloto ou treino é registrado
- **THEN** seu evento aponta para hash Git/código, hash integral da configuração, versão do ambiente e lockfile, versão do split e índices originais
