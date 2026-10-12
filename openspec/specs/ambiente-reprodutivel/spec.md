# ambiente-reprodutivel Specification

## Purpose
Define como o ambiente de execução do projeto é instalado e verificado, garantindo que o treino rode na GPU indicada e que qualquer pessoa do grupo reproduza os mesmos resultados a partir do repositório.

## Requirements

### Requirement: Gerenciamento de dependências com uv
O projeto SHALL declarar todas as dependências de execução e de desenvolvimento em um único arquivo de projeto gerenciado por uv, com versões fixadas.

#### Scenario: Instalação a partir do zero
- **WHEN** um usuário executa o comando de sincronização do uv no repositório limpo
- **THEN** o ambiente é criado sem passos manuais adicionais e todas as dependências são resolvidas a partir do lockfile

#### Scenario: Dependência de teste separada
- **WHEN** o ambiente de execução é instalado sem o grupo de desenvolvimento
- **THEN** o pacote vit-pytorch não é instalado

### Requirement: PyTorch com CUDA 13.0
O projeto SHALL instalar PyTorch a partir do índice de wheels cu130 e SHALL usar a GPU NVIDIA disponível para o treino.

#### Scenario: GPU disponível
- **WHEN** o treino é iniciado em uma máquina com GPU NVIDIA compatível com cu130
- **THEN** o dispositivo de cálculo selecionado é CUDA e o nome da GPU é registrado nos logs

#### Scenario: Wheel ou GPU ausente
- **WHEN** o wheel cu130 não carrega ou nenhuma GPU CUDA é detectada
- **THEN** o processo termina com erro explícito antes de qualquer treino
- **AND** nenhum fallback silencioso para CPU é executado

### Requirement: Registro de versões do ambiente
O projeto SHALL registrar a versão do Python, do PyTorch, da CUDA e do driver junto com os resultados gerados.

#### Scenario: Metadados nos resultados
- **WHEN** o notebook termina a execução
- **THEN** os resultados em `resultados/` incluem as versões de Python, PyTorch, CUDA e driver usadas
