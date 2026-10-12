# Spec Delta

## Purpose

Define o pacote de entrega seminario_masked_modeling.zip: conteúdo obrigatório, exclusões, verificação por md5 e licença, para que o material possa ser avaliado e reexecutado sem depender de arquivos fora do pacote.

## ADDED Requirements

### Requirement: Conteúdo obrigatório do zip
O sistema SHALL montar o arquivo seminario_masked_modeling.zip contendo os slides em pptx, o código do MAE próprio, os dados do subconjunto, os resultados em `resultados/` e um README.

#### Scenario: Conteúdo presente
- **WHEN** o zip é montado
- **THEN** ele contém o pptx, o código, os dados do subconjunto, `reconstrucoes.png`, `curva_perda.png`, `metricas.csv` e o README

#### Scenario: Script de montagem em Python
- **WHEN** o zip é gerado
- **THEN** a montagem é feita por um script Python versionado no repositório

### Requirement: Verificação de conteúdo por md5
O script de montagem SHALL conferir a presença de cada arquivo obrigatório e SHALL registrar o md5 de cada arquivo incluído, falhando se algum arquivo obrigatório estiver ausente.

#### Scenario: Arquivo ausente
- **WHEN** um arquivo obrigatório não existe no momento da montagem
- **THEN** a montagem falha com erro que nomeia o arquivo ausente e nenhum zip é gravado

#### Scenario: Registro de md5
- **WHEN** o zip é montado com sucesso
- **THEN** a lista de md5 de cada arquivo incluído fica disponível para conferência

### Requirement: Exclusões do pacote
O zip SHALL NOT conter dados brutos do CIFAR-10, pesos de checkpoint, o validador do oráculo nem os arquivos de teste de equivalência.

#### Scenario: Pesos fora do pacote
- **WHEN** o conteúdo do zip é listado
- **THEN** nenhum arquivo de checkpoint aparece

#### Scenario: Oráculo fora do pacote
- **WHEN** o conteúdo do zip é listado
- **THEN** nenhum arquivo de teste que importe o vit-pytorch aparece

### Requirement: Licença e autoria
O código próprio SHALL ser distribuído sob licença MIT e o README SHALL identificar o grupo formado por Frederico Maciel de Mello e Luan Pedro de Souza Silva.

#### Scenario: Licença presente
- **WHEN** o zip é aberto
- **THEN** existe um arquivo de licença MIT no código próprio

#### Scenario: Autoria no README
- **WHEN** o README é lido
- **THEN** os dois nomes do grupo aparecem

### Requirement: Escopo declarado
O README SHALL declarar que linear probing está fora do escopo e citar He et al. (2022) e o repositório oficial como referências.

#### Scenario: Escopo e referências
- **WHEN** o README é lido
- **THEN** linear probing aparece como próximo passo e as referências estão listadas
