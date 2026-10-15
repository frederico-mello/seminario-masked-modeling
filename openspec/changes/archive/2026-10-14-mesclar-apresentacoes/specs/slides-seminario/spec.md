# slides-seminario (delta)

## MODIFIED Requirements

### Requirement: Tamanho e roteiro
A apresentação SHALL ter 12 slides, seguindo o roteiro de 20 minutos nesta ordem: capa com título e grupo; o que é masked modeling com a ideia-chave "O próprio dado fornece a supervisão"; por que usar e motivações; panorama BERT x MAE x SimMIM; diagrama de blocos do MAE em 8 etapas; equação da perda termo a termo e pseudocódigo; experimento próprio no CIFAR-10 do zero com máscaras de 50% e 75% e resultados visuais e tabela; experimento com MAE pré-treinado em taxas de 25% a 90% com resultados visuais e MSEs do material complementar; aplicações por domínio; fluxo pós MAE e tarefas downstream; conclusões; referências completas.

#### Scenario: Contagem de slides
- **WHEN** a apresentação é contada
- **THEN** o total é de exatamente 12 slides
- **AND** os slides de diagrama, equação, pseudocódigo, aplicações pos MAE, pós MAE, conclusões e referências estão presentes

#### Scenario: Cobertura do experimento
- **WHEN** o roteiro é verificado
- **THEN** o experimento próprio ocupa um slide com máscaras de 50% e 75%, resultados visuais e tabela
- **AND** o experimento complementar ocupa um slide com taxas de 25% a 90%, resultados visuais e MSEs com crédito

#### Scenario: Legibilidade da equação e do pseudocódigo
- **WHEN** a inspeção visual do pdf indica que equação e pseudocódigo não cabem legíveis em um slide
- **THEN** o slide 6 é dividido em dois e o conteúdo dos slides de aplicações pos MAE e pós MAE é fundido em um, mantendo o total em 12

### Requirement: Números medidos somente
Os números do experimento próprio apresentados nos slides SHALL vir de `metricas.csv` ou de medições registradas pelo notebook, e SHALL NOT ser digitados à mão. Os números do experimento complementar SHALL vir unicamente do material complementar (MSEs do texto de conclusões do material complementar e gráfico do MSE por taxa em imagem versada no repositório), creditando o material na apresentação, e SHALL NOT ser apresentados como medição nossa.

#### Scenario: Rastreio dos números
- **WHEN** um número aparece em um slide
- **THEN** para o experimento próprio ele existe em `resultados/` ou no registro de medição de treinamento
- **AND** para o experimento complementar ele corresponde ao material complementar (0,0476 com 25%; 0,1403 com 75%; 0,3117 com 90%), com o gráfico do MSE por taxa em imagem versada no repositório e a fonte citada no slide
- **AND** nenhum valor do experimento complementar é apresentado com delimitação de semente ou protocolo nossa

### Requirement: Aplicações e referências no encerramento
A apresentação SHALL incluir aplicações por domínio (visão computacional, imagens médicas, sensoriamento remoto e outras modalidades como linguagem natural, vídeos e áudio), SHALL incluir o fluxo pós MAE (pré-treinamento, descarte do decoder, reutilização do encoder como extrator de características ou por fine-tuning em classificação, detecção e segmentação) e SHALL encerrar com conclusões e referências bibliográficas completas, incluindo Devlin et al. (2019), Dosovitskiy et al. (2021), He et al. (2022), Bao et al. (2022), Xie et al. (2022), a fonte do CIFAR-10 (Krizhevsky, Nair e Hinton) e o crédito da implementação pública do experimento complementar (Hugging Face Transformers, ViTMAE, modelo facebook/vit-mae-base) com o link do seu Colab.

#### Scenario: Aplicações por domínio
- **WHEN** o slide de aplicações é lido
- **THEN** visão computacional, imagens médicas, sensoriamento remoto e outras modalidades aparecem com exemplos de tarefa em cada domínio

#### Scenario: Fluxo pós MAE
- **WHEN** o slide pós MAE é lido
- **THEN** o pré-treinamento, o descarte do decoder e a reutilização do encoder aparecem na ordem correta
- **AND** as tarefas downstream citadas são classificação, detecção e segmentação

#### Scenario: Referências completas
- **WHEN** o slide de encerramento é lido
- **THEN** as referências básicas (Devlin et al., 2019; He et al., 2022; Xie et al., 2022; Krizhevsky, Nair e Hinton) e as extras (Dosovitskiy et al., 2021; Bao et al., 2022) estão citadas com autor, título e ano
- **AND** o crédito da implementação ViTMAE e o link do Colab do experimento complementar aparecem nas referências

### Requirement: Evidência local e delimitada
Os slides de resultados SHALL apresentar os números do experimento próprio como evidência desta configuração experimental: duas razões de máscara com conjuntos de patches aninhados, semente única 42 e conjunto de teste fixo de 1.000 imagens; os números do experimento complementar SHALL ser apresentados com o delimitador de fonte, indicando que vêm do material complementar com MAE pré-treinado público; o conjunto SHALL NOT generalizar as observações para outras razões, sementes, modalidades ou níveis de desempenho downstream, e SHALL NOT tratar a qualidade visual da reconstrução como prova de representações melhores.

#### Scenario: Delimitação explícita
- **WHEN** os slides de resultados são lidos
- **THEN** a semente única 42 e a máscara aninhada estão citadas como delimitação da comparação do experimento próprio
- **AND** está indicado que repetição com mais sementes permanece necessária antes de generalizar
- **AND** está explícito que os números e os visuais do experimento complementar vêm do material complementar com MAE pré-treinado público
- **AND** nenhum resultado é apresentado como tendência geral de masked modeling

## ADDED Requirements

### Requirement: Experimento complementar com MAE pré-treinado
A apresentação SHALL incluir o experimento complementar com MAE pré-treinado: arquitetura baseada em Vision Transformer (ViT), entrada de 224x224 pixels, patches de 16x16 e taxas de mascaramento de 25%, 50%, 75% e 90%; SHALL apresentar os resultados visuais do experimento complementar como imagens versadas no repositório e os MSEs documentados no texto do material complementar; SHALL creditar a implementação pública utilizada (Hugging Face Transformers, ViTMAE, modelo facebook/vit-mae-base) e o link do Colab do experimento.

#### Scenario: Elementos do slide do experimento complementar
- **WHEN** o slide do experimento complementar é lido
- **THEN** aparecem o modelo ViT-MAE com entrada de 224x224 e patches de 16x16 e as quatro taxas avaliadas
- **THEN** as imagens de resultados visuais estão versionadas no repositório e a legenda cita o material complementar
- **AND** o crédito da implementação pública e o link do Colab estão presentes

### Requirement: Abertura com a ideia do próprio dado fornece a supervisão
O slide conceitual SHALL incluir a frase do material complementar "O próprio dado fornece a supervisão" com a sequência didática: ocultar uma parte da entrada, usar o visível como contexto, prever ou reconstruir o conteúdo mascarado e aprender representações úteis no processo.

#### Scenario: Frase e sequência didática
- **WHEN** o slide conceitual é lido
- **THEN** a frase de ideia-chave está presente e as quatro etapas didáticas aparecem na ordem do material complementar