# Spec Delta

## MODIFIED Requirements

### Requirement: Números medidos somente
Os números do experimento próprio original nos slides SHALL vir de `metricas.csv` ou de medições registradas pelo notebook e SHALL NOT ser digitados à mão. Os números do novo estudo SHALL vir de seu histórico e resumo registrados. Números do experimento complementar SHALL vir unicamente de seu material de origem e SHALL ser identificados como externos.

#### Scenario: Rastreio dos números
- **WHEN** números do experimento próprio original, do novo estudo ou do experimento complementar aparecem em um slide
- **THEN** cada número do experimento original existe em `resultados/` ou no registro do notebook; cada resultado do novo estudo consta no histórico ou resumo com protocolo e delimitação; e cada número complementar corresponde ao material de origem, com fonte citada e sem ser apresentado como medição própria
