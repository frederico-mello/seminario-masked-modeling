# pacote-entrega (delta)

## MODIFIED Requirements

### Requirement: Conteúdo obrigatório do zip
O sistema SHALL montar o arquivo seminario_masked_modeling.zip contendo os slides em pptx, o código do MAE próprio, os dados do subconjunto, os resultados em `resultados/`, os assets visuais do experimento complementar em `slides/recursos-complementares/` e um README.

#### Scenario: Conteúdo presente
- **WHEN** o zip é montado
- **THEN** ele contém o pptx, o código, os dados do subconjunto, `reconstrucoes.png`, `curva_perda.png`, `metricas.csv` e o README
- **AND** ele contém os assets do experimento complementar sob `slides/recursos-complementares/` (o fluxo do experimento, a grade de mascarado e reconstruído nas quatro taxas e o gráfico do MSE por taxa, em imagem)

#### Scenario: Script de montagem em Python
- **WHEN** o zip é gerado
- **THEN** a montagem é feita por um script Python versionado no repositório

#### Scenario: Assets ausentes
- **WHEN** um asset complementar não está em `slides/recursos-complementares/` no momento da montagem
- **THEN** a montagem falha com erro que nomeia o asset ausente, pelo mesmo caminho de arquivo obrigatório existente