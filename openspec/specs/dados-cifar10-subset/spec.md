# dados-cifar10-subset Specification

## Purpose
Define a obtenção verificada do CIFAR-10 e a construção de um subconjunto balanceado e reproduzível, com separação estrita entre treino, validação e teste, para alimentar o experimento de mascaramento.

## Requirements

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

### Requirement: Cobertura efetiva dos testes de dados sem o arquivo bruto
A suíte de testes de verificação de dados SHALL exercitar a lógica de md5, de contagens e de integridade mesmo quando o CIFAR-10 bruto não está disponível no ambiente, por meio de arquivo sintético controlado (com md5 intencionalmente divergente do valor esperado) ou do próprio subconjunto já gerado; SHALL NOT depender do download do CIFAR-10 para rodar, e SHALL NOT pular verificação de forma silenciosa.

#### Scenario: Verificação de md5 sem arquivo bruto
- **WHEN** a suíte roda em um ambiente sem `dados/cifar10_raw/cifar-10-python.tar.gz`
- **THEN** o teste de md5 roda sobre um arquivo sintético e valida a rejeição de md5 divergente contra o valor esperado
- **AND** a assinatura da mensagem de erro (md5 obtido e esperado) é verificada pelo teste

#### Scenario: Contagens e integridade sem arquivo bruto
- **WHEN** a suíte roda sem o arquivo bruto, mas com o subconjunto gerado em `dados/cifar10_subset/`
- **THEN** contagens por classe, disjunção entre treino e validação, formato uint8 e reprodutibilidade da seleção são verificados
- **AND** apenas as asserções que comparar contra o arquivo oficial bruto (origem dos índices de teste no split oficial) podem ser omitidas, com o motivo registrado no teste

### Requirement: Condicional declarada nos testes
Todo teste de dados condicionado à presença de um arquivo SHALL declarar explicitamente no código o que verifica quando o arquivo existe e o que deixa de verificar quando não existe; SHALL NOT retornar sem nenhuma verificação em nenhum ramo, e o ramo existente SHALL exercitar a mesma lógica sobre dados de teste quando possível.

#### Scenario: Retorno sem verificação proibido
- **WHEN** um teste de dados é executado em qualquer ambiente
- **THEN** ao menos uma asserção é avaliada em todos os ramos possíveis
- **AND** nenhum ramo encerra o teste apenas com mensagem impressa ou retorno direto

#### Scenario: Branch com arquivo presente permanece
- **WHEN** o CIFAR-10 bruto está disponível
- **THEN** o teste executa a verificação completa contra o arquivo real, inclusive a falha do script com md5 errado sem gerar subconjunto

### Requirement: A suíte não se enfraquece
As alterações nos testes de dados SHALL preservar as verificações existentes (md5 contra o valor esperado, contagens por classe, disjunção, origem oficial do teste, determinismo com seed 42 e formato de saída) e SHALL NOT converter em pulo automático nenhum teste que hoje verifica algo quando os dados estão presentes.

#### Scenario: Suíte existente mantida
- **WHEN** a suíte roda em um ambiente com o CIFAR-10 bruto e o subconjunto gerados
- **THEN** todas as verificações anteriores continuam executando e passando
- **AND** a quantidade de asserções avaliadas não diminui em relação à suíte anterior
