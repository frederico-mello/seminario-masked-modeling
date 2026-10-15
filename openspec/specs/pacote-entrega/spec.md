# pacote-entrega Specification

## Purpose
Define o pacote de entrega seminario_masked_modeling.zip: conteúdo obrigatório, exclusões, verificação por md5 e licença, para que o material possa ser avaliado e reexecutado sem depender de arquivos fora do pacote.

## Requirements

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

### Requirement: Pré-requisitos de sistema no README
O README SHALL declarar os programas de sistema requeridos para regenerar a entrega fora do ambiente Python: LibreOffice em modo headless para converter o pptx em pdf e pdftoppm para converter o pdf em png de inspeção; SHALL indicar como conferir a presença de cada um e SHALL explicar que sem eles o script de slides falha com erro explícito.

#### Scenario: Pré-requisitos declarados
- **WHEN** o README é lido
- **THEN** LibreOffice e pdftoppm aparecem como pré-requisitos, com o papel de cada um na geração
- **AND** existe um comando ou caminho indicado para conferir a presença deles no sistema

#### Scenario: Falha explícita sem o pré-requisito
- **WHEN** o script de slides roda em um ambiente sem LibreOffice ou pdftoppm
- **THEN** o processo termina com erro, e o README explica essa dependência como causa provável

### Requirement: Instrução de recuperação do pacote
O README SHALL documentar como regenerar `seminario_masked_modeling.zip` a partir do repositório quando o pacote não chega ao destinatário: ordem de produção (dados verificados, resultados pelo notebook, slides, e então o empacotamento) e comando do script de empacotamento que confere presença e md5 antes de gravar o zip.

#### Scenario: Recuperação documentada
- **WHEN** o README é lido
- **THEN** a ordem de regeneração dos artefatos exigidos pelo zip está documentada
- **AND** o comando de empacotamento está indicado com o comportamento de verificação de presença e md5

#### Scenario: Pacote regenerável
- **WHEN** a sequência documentada é seguida a partir do repositório
- **THEN** o zip é gravado com todos os arquivos obrigatórios e o registro de md5 é atualizado
