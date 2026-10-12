# Spec Delta

## Purpose

Define como a implementação própria do MAE é validada contra a classe MAE do vit-pytorch usada como oráculo de teste, de forma que a verificação fique fora do código entregue e que as tolerâncias sejam explícitas e auditáveis.

## ADDED Requirements

### Requirement: Oráculo restrito a testes
O projeto SHALL usar vit-pytorch apenas como dependência de desenvolvimento, versão 1.24.1, e SHALL NOT incluir o oráculo nem seus testes no pacote de entrega.

#### Scenario: Dependência de desenvolvimento
- **WHEN** o ambiente de execução é instalado sem o grupo de desenvolvimento
- **THEN** o vit-pytorch não está presente

#### Scenario: Exclusão da entrega
- **WHEN** o zip de entrega é montado
- **THEN** o zip não contém arquivos de teste de equivalência nem referências ao oráculo

### Requirement: Teste de equivalência com pesos iguais
O teste SHALL inicializar a implementação própria e o oráculo com os mesmos pesos, usar a mesma configuração de dimensão, profundidade, cabeças e tamanho de patch, e aplicar a mesma máscara.

#### Scenario: Pesos e máscara compartilhados
- **WHEN** o teste prepara as duas implementações
- **THEN** os pesos e a máscara são idênticos entre elas antes de qualquer forward

### Requirement: Critérios de equivalência
O teste SHALL verificar formas dos tensores, perda e reconstrução, e SHALL falhar se qualquer diferença exceder a tolerância numérica declarada no próprio teste.

#### Scenario: Equivalência dentro da tolerância
- **WHEN** as diferenças de perda e reconstrução estão dentro da tolerância
- **THEN** o teste passa

#### Scenario: Divergência acima da tolerância
- **WHEN** alguma diferença excede a tolerância
- **THEN** o teste falha e a entrega é bloqueada até a causa ser resolvida

### Requirement: Teste executável pelo grupo
O teste de equivalência SHALL rodar com um único comando documentado no README e SHALL registrar sua saída como evidência da validação.

#### Scenario: Execução documentada
- **WHEN** um integrante do grupo executa o comando documentado
- **THEN** o teste roda e produz um relatório com as diferenças medidas
