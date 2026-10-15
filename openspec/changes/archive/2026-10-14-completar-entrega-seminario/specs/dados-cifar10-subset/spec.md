# Spec Delta: dados-cifar10-subset

## ADDED Requirements

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