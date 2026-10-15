# Spec Delta

## MODIFIED Requirements

### Requirement: Conteúdo obrigatório do zip
O sistema SHALL montar o arquivo `seminario_masked_modeling.zip` com os slides, código do MAE, dados do subconjunto, resultados anteriores, assets visuais complementares, README e artefatos do estudo de melhoria.

#### Scenario: Conteúdo presente
- **WHEN** o zip é montado
- **THEN** contém pptx, código, dados do subconjunto, `reconstrucoes.png`, `curva_perda.png`, `metricas.csv`, README, assets do experimento complementar e histórico, resumo, figuras e relatório do estudo, preservando os resultados anteriores identificados

#### Scenario: Script de montagem em Python
- **WHEN** o zip é gerado
- **THEN** a montagem é feita por um script Python versionado no repositório

#### Scenario: Assets ausentes
- **WHEN** um asset complementar ou artefato obrigatório do estudo está ausente no momento da montagem
- **THEN** a montagem falha com erro que nomeia o arquivo ausente antes de gravar o zip
