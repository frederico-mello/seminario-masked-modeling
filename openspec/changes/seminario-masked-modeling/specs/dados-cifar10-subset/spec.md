# Spec Delta

## Purpose

Define a obtenção verificada do CIFAR-10 e a construção de um subconjunto balanceado e reproduzível, com separação estrita entre treino, validação e teste, para alimentar o experimento de mascaramento.

## ADDED Requirements

### Requirement: Download verificado por md5
O sistema SHALL obter o CIFAR-10 pelo torchvision e SHALL verificar o md5 do arquivo baixado contra o valor c58f30108f718f92721af3b95e74349a antes de qualquer uso.

#### Scenario: Arquivo íntegro
- **WHEN** o arquivo baixado tem md5 igual ao valor esperado
- **THEN** a construção do subconjunto prossegue

#### Scenario: Arquivo corrompido
- **WHEN** o md5 do arquivo baixado difere do valor esperado
- **THEN** o processo termina com erro que informa o md5 obtido e o esperado
- **AND** nenhum subconjunto é gerado

### Requirement: Subconjunto balanceado por classe
O sistema SHALL gerar um subconjunto com 500 imagens de treino, 100 de validação e 100 de teste por classe, selecionadas com seed 42, totalizando 5.000, 1.000 e 1.000 imagens.

#### Scenario: Contagem por classe
- **WHEN** o subconjunto é gerado
- **THEN** cada uma das 10 classes possui exatamente 500 imagens de treino, 100 de validação e 100 de teste

#### Scenario: Reprodutibilidade da seleção
- **WHEN** o subconjunto é gerado duas vezes com seed 42 a partir do mesmo arquivo verificado
- **THEN** os índices selecionados são idênticos

### Requirement: Separação entre treino, validação e teste
O sistema SHALL garantir que a validação seja disjunta do treino, que o treino e a validação venham do conjunto oficial de treino, e que o teste venha do conjunto oficial de teste.

#### Scenario: Disjunção de validação
- **WHEN** os índices de treino e de validação são comparados
- **THEN** não há nenhum índice em comum

#### Scenario: Origem do teste
- **WHEN** os índices de teste são verificados
- **THEN** todos pertencem ao conjunto oficial de teste do CIFAR-10

#### Scenario: Teste usado somente no fim
- **WHEN** o treino e a seleção de épocas estão em andamento
- **THEN** o conjunto de teste não é lido para nenhuma decisão de treino

### Requirement: Formatos de saída do subconjunto
O sistema SHALL gravar os índices selecionados em CSV, com colunas de split, classe e índice original, e SHALL gravar as imagens em formato uint8 comprimido.

#### Scenario: Índices rastreáveis
- **WHEN** o CSV de índices é lido
- **THEN** cada linha identifica split, classe e índice original da imagem no CIFAR-10

#### Scenario: Imagens uint8
- **WHEN** o arquivo de imagens é carregado
- **THEN** as imagens têm dtype uint8 e formato 32x32x3

### Requirement: Dados brutos fora do controle de versão
O sistema SHALL manter os dados brutos e o arquivo zip de entrega fora do controle de versão do git.

#### Scenario: Ignorados pelo git
- **WHEN** o usuário verifica o status do repositório após gerar os dados
- **THEN** os dados brutos e o zip não aparecem como arquivos a serem versionados
