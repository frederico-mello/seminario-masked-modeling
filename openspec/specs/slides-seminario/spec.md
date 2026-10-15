# slides-seminario Specification

## Purpose
Define os slides do seminário sobre masked modeling: formato de entrega, tamanho, roteiro de 20 minutos, capa com o grupo e regra de que os números apresentados vêm somente de medições reais do experimento.

## Requirements

### Requirement: Formato e geração dos slides
O sistema SHALL gerar a apresentação em formato pptx e em pdf a partir de um mesmo script, usando python-pptx para o pptx e LibreOffice headless para o pdf.

#### Scenario: Dois formatos do mesmo script
- **WHEN** o script de geração é executado
- **THEN** são produzidos um arquivo pptx e um arquivo pdf com o mesmo conteúdo

#### Scenario: Inspeção visual
- **WHEN** o pdf é convertido em imagens PNG
- **THEN** cada página é inspecionada visualmente antes da entrega

### Requirement: Tamanho e roteiro
A apresentação SHALL ter entre 10 e 12 slides, seguindo o roteiro de 20 minutos com um slide por bloco e dois slides dedicados ao experimento, e SHALL acomodar os slides didáticos novos, o slide de aplicações e o slide de referências dentro desse intervalo.

#### Scenario: Contagem de slides
- **WHEN** a apresentação é contada
- **THEN** o total está entre 10 e 12 slides
- **AND** os slides de diagrama, equação, pseudocódigo, aplicações e referências estão presentes

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
- **THEN** ele existe em `resultados/` ou no registro de medição de treinamento

### Requirement: Idioma e pontuação
Os slides SHALL estar em português brasileiro com acentuação correta, SHALL NOT conter o caractere travessão U+2014 e SHALL NOT conter palavra que exija acento escrita sem acento.

#### Scenario: Verificação de caracteres
- **WHEN** o texto dos slides é verificado
- **THEN** não há ocorrência de U+2014
- **AND** palavras de título e corpo usam acentuação correta, incluindo "orçamento", "máscara" e "métrica".

### Requirement: Diagrama do fluxo do MAE
A apresentação SHALL incluir o diagrama do fluxo do MAE cobrindo, em ordem, a imagem sem rótulo, a divisão em patches, a máscara aleatória, o codificador sobre os patches visíveis, a inserção dos tokens de máscara com posições, o decodificador leve, a reconstrução dos pixels e a perda calculada nos patches ocultos.

#### Scenario: Blocos do diagrama
- **WHEN** o slide do diagrama é lido
- **THEN** os oito elementos do fluxo (imagem, patches, máscara, codificador, tokens de máscara, decodificador, reconstrução e perda nos ocultos) aparecem na ordem do planejamento
- **AND** está explícito que o codificador processa apenas os patches visíveis

#### Scenario: Coerência com a implementação
- **WHEN** o diagrama é comparado com o experimento descrito
- **THEN** ele refere a arquitetura assimétrica (codificador maior, decodificador leve) e o descarte do decodificador para tarefas posteriores

### Requirement: Equação da perda explicada termo a termo
A apresentação SHALL apresentar a equação da perda do MAE como erro quadrático médio nos patches ocultos e SHALL explicar cada termo: o vetor de pixels `x_i` do patch `i`, o conjunto mascarado `M`, a reconstrução `x̂_i` e a dimensão de normalização `d`, com a média sobre `i` em `M`.

#### Scenario: Significado de cada termo
- **WHEN** o slide da equação é lido
- **THEN** cada símbolo da equação está acompanhado do seu significado em português
- **AND** está indicado que a perda ignora os patches visíveis e normaliza pela dimensão `d`

### Requirement: Pseudocódigo do treinamento
A apresentação SHALL incluir o pseudocódigo do laço de treinamento com a sequência: dividir em patches, amostrar a máscara na razão `r`, codificar os visíveis, decodificar com tokens de máscara, calcular a perda nos ocultos e atualizar os parâmetros por retropropagação.

#### Scenario: Passos do laço
- **WHEN** o slide do pseudocódigo é lido
- **THEN** os seis passos do laço aparecem na ordem do planejamento

### Requirement: Comparação estruturada BERT x MAE x SimMIM
A apresentação SHALL comparar BERT, MAE e SimMIM em quatro dimensões: modalidade, alvo previsto, função de perda e arquitetura; SHALL contrastar o erro quadrático médio do MAE com a perda L1 do SimMIM, que faz regressão direta de pixels com cabeça de predição linear leve; SHALL usar estrutura de tabela ou equivalente visual.

#### Scenario: Dimensões da comparação
- **WHEN** o slide da comparação é lido
- **THEN** modalidade, alvo previsto, perda e arquitetura são indicados para os três métodos
- **AND** o contraste entre MSE e L1 está explicado com a consequência arquitetural (codificador assimétrico e decoder separado contra cabeça leve sobre um codificador único)

### Requirement: Aplicações e referências no encerramento
A apresentação SHALL encerrar com um slide de aplicações das representações aprendidas e, em seguida, referências bibliográficas completas, incluindo Devlin et al. (2019), He et al. (2022), Xie et al. (2022) e a fonte do CIFAR-10 (Krizhevsky, Nair e Hinton).

#### Scenario: Referências completas
- **WHEN** o slide de encerramento é lido
- **THEN** as quatro referências básicas do planejamento estão citadas com autor, título e ano
- **AND** para cada método aparece a aplicação estudada no trabalho correspondente (compreensão de linguagem para BERT; classificação, detecção e segmentação para MAE e SimMIM)

### Requirement: Evidência local e delimitada
Os slides de resultados SHALL apresentar os números como evidência desta configuração experimental: duas razões de máscara com conjuntos de patches aninhados, semente única 42 e conjunto de teste fixo de 1.000 imagens; SHALL NOT generalizar para outras razões, sementes, modalidades ou tarefas downstream, e SHALL NOT tratar a qualidade visual da reconstrução como prova de representações melhores.

#### Scenario: Delimitação explícita
- **WHEN** o slide de leitura dos números é lido
- **THEN** a semente única 42 e a máscara aninhada estão citadas como delimitação da comparação
- **AND** está indicado que repetição com mais sementes permanece necessária antes de generalizar
- **AND** nenhum resultado é apresentado como tendência geral de masked modeling
