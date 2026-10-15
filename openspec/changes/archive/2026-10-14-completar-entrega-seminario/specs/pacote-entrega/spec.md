# Spec Delta: pacote-entrega

## ADDED Requirements

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