# Spec Delta

## Purpose

Define os slides do seminário sobre masked modeling: formato de entrega, tamanho, roteiro de 20 minutos, capa com o grupo e regra de que os números apresentados vêm somente de medições reais do experimento.

## ADDED Requirements

### Requirement: Formato e geração dos slides
O sistema SHALL gerar a apresentação em formato pptx e em pdf a partir de um mesmo script, usando python-pptx para o pptx e LibreOffice headless para o pdf.

#### Scenario: Dois formatos do mesmo script
- **WHEN** o script de geração é executado
- **THEN** são produzidos um arquivo pptx e um arquivo pdf com o mesmo conteúdo

#### Scenario: Inspeção visual
- **WHEN** o pdf é convertido em imagens PNG
- **THEN** cada página é inspecionada visualmente antes da entrega

### Requirement: Tamanho e roteiro
A apresentação SHALL ter entre 10 e 12 slides, seguindo o roteiro de 20 minutos com um slide por bloco e dois slides dedicados ao experimento.

#### Scenario: Contagem de slides
- **WHEN** a apresentação é contada
- **THEN** o total está entre 10 e 12 slides

#### Scenario: Cobertura do experimento
- **WHEN** o roteiro é verificado
- **THEN** o experimento ocupa dois slides, com a comparação de 50% e 75%

### Requirement: Capa com autoria
A capa SHALL exibir "Frederico Maciel de Mello e Luan Pedro de Souza Silva" como autores e a data de apresentação em 16/10.

#### Scenario: Conteúdo da capa
- **WHEN** o primeiro slide é exibido
- **THEN** os dois nomes completos aparecem e a data 16/10 está presente

### Requirement: Números medidos somente
Os números apresentados nos slides SHALL vir de `metricas.csv` ou de medições registradas pelo notebook, e SHALL NOT ser digitados à mão.

#### Scenario: Rastreio dos números
- **WHEN** um número aparece em um slide
- **THEN** ele existe em `resultados/` ou no registro de medição de orçamento

### Requirement: Idioma e pontuação
Os slides SHALL estar em português brasileiro e SHALL NOT conter o caractere travessão U+2014.

#### Scenario: Verificação de caracteres
- **WHEN** o texto dos slides é verificado
- **THEN** não há ocorrência de U+2014
