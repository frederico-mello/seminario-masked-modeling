# Spec Delta

## Purpose

Define o protocolo reproduzível para comparar reconstruções do MAE e controles com avaliação numérica e visual, orçamento limitado, seleção sem vazamento do teste e preservação dos resultados anteriores.

## ADDED Requirements

### Requirement: Máscaras de treino estáveis e aninhadas
O estudo SHALL gerar a máscara de cada imagem a partir de sua identidade original, época e seed, sem depender da ordem dos lotes ou do gerador aleatório global.

#### Scenario: Recomputação independente da ordem
- **WHEN** uma imagem é apresentada em outra ordem ou lote com a mesma seed e época
- **THEN** ela recebe a mesma máscara de treino

#### Scenario: Máscara varia por época e seed
- **WHEN** as máscaras são geradas para épocas ou seeds distintas
- **THEN** cada máscara é determinada por sua identidade, época e seed, sem estado aleatório global compartilhado

#### Scenario: Taxas aninhadas
- **WHEN** as taxas de 50% e 75% são geradas para a mesma identidade, época e seed
- **THEN** os 8 patches ocultos a 50% também estão entre os 12 patches ocultos a 75%

### Requirement: Régua fixa de avaliação
O estudo SHALL avaliar todos os candidatos e controles na mesma máscara fixa, sobre os patches ocultos de todo o conjunto de validação.

#### Scenario: Avaliação comparável
- **WHEN** qualquer candidato, baseline ou controle é avaliado para seleção
- **THEN** usa o mesmo split de validação, máscara e métrica nos patches ocultos

#### Scenario: Comparação por seed e taxa
- **WHEN** os resultados são comparados
- **THEN** C0 e cada controle e candidato têm resultados identificáveis por seed e taxa

### Requirement: Checkpoints de validação e final separados
Cada execução SHALL preservar separadamente o melhor modelo segundo a validação e o modelo da última época concluída.

#### Scenario: Menor perda de validação
- **WHEN** uma época termina com perda de validação menor que a melhor anterior
- **THEN** o melhor checkpoint passa a representar essa época

#### Scenario: Empate de validação
- **WHEN** uma época empata com a menor perda de validação anterior
- **THEN** a primeira época com essa perda continua sendo o melhor checkpoint

#### Scenario: Cópias imutáveis
- **WHEN** uma execução termina ou é interrompida
- **THEN** as cópias do melhor e do final são distintas, imutáveis e identificadas por hash e época

#### Scenario: Relato de checkpoints
- **WHEN** o relatório final apresenta métricas
- **THEN** reporta separadamente melhor checkpoint de validação e checkpoint da última época, com hash e época, sem reabrir a seleção pelo resultado do final

### Requirement: Baselines sem acesso a pixels ocultos
O estudo SHALL comparar os candidatos com preenchimentos determinísticos derivados somente dos pixels visíveis e com fallback baseado somente no split de treino.

#### Scenario: Média RGB dos visíveis
- **WHEN** o baseline RGB reconstrói pixels ocultos
- **THEN** usa a média por canal calculada a partir dos pixels visíveis da imagem

#### Scenario: Interpolação espacial
- **WHEN** o baseline espacial preenche um patch oculto
- **THEN** calcula o preenchimento por distância entre coordenadas dos centros dos patches visíveis, sem acessar pixels ocultos

#### Scenario: Fallback explícito
- **WHEN** não há amostra visível utilizável ou os pesos espaciais são inválidos
- **THEN** usa a média RGB visível e, se ela não puder ser calculada, a média por canal do split de treino

### Requirement: Candidatos e regras congelados antes do treino
O estudo SHALL incluir MAE direto retreinado e SHALL aplicar a todos os candidatos aprovados a mesma regra de seleção e o mesmo teto por execução.

#### Scenario: Variantes limitadas
- **WHEN** os candidatos são aprovados no gate humano
- **THEN** cada arquitetura, perda, seed, taxa e justificativa é registrada antes do treino completo

#### Scenario: Candidato residual opcional
- **WHEN** uma variante residual é considerada
- **THEN** C0 tem MSE mediano estritamente menor que cada baseline em ambas as taxas e existe saldo elegível de pelo menos 30 minutos na alocação principal de 90 minutos, após C0/C1/C2 e descontados até 6 minutos para avaliação final; a decisão precede o congelamento e o teste, e a reserva de 30 minutos não pode financiar C3

#### Scenario: Candidato residual não elegível
- **WHEN** qualquer comparação de C0 com baseline falha ou o saldo elegível é inferior a 30 minutos
- **THEN** C3 é registrado como não executado com a condição que falhou

#### Scenario: Configuração congelada
- **WHEN** começa o primeiro treino completo
- **THEN** candidatos, configurações, limiares e regra de seleção estão congelados e não são alterados em resposta ao teste

### Requirement: Melhoria numérica e visual agregada
O estudo SHALL definir antes do treino limiares de ganho no MSE e SSIM da validação, além de uma inspeção humana fixa que não determine a seleção por galeria escolhida.

#### Scenario: Limiares propostos ao gate
- **WHEN** o plano é submetido ao gate humano
- **THEN** apresenta como propostas redução de pelo menos 5% no MSE mediano e ganho de pelo menos 0,02 no SSIM mediano contra C0, em cada taxa

#### Scenario: Seleção multiobjetivo
- **WHEN** um candidato é escolhido para uma taxa
- **THEN** cumpre ambos os limiares congelados e a regra de desempate usa MSE, SSIM com tolerância, tempo e ordem predefinida

#### Scenario: Qualidade visual
- **WHEN** a qualidade visual é avaliada
- **THEN** SSIM usa janela gaussiana 3x3, sigma 1,5, padding por reflexão sem repetir a borda, covariância e variâncias populacionais, faixa dinâmica 1, C1=(0,01)^2, C2=(0,03)^2, epsilon 1e-12, média dos canais RGB e agregação patch/imagem/seed/taxa definidas no design; pixels de entrada e saída são limitados a [0,1]

#### Scenario: Patch constante
- **WHEN** um canal de um patch tem variância zero
- **THEN** a fórmula SSIM permanece definida com variâncias e covariância zero; canais constantes iguais pontuam 1 e constantes diferentes usam o termo de luminância padrão

#### Scenario: Testes de referência SSIM
- **WHEN** a implementação for criada na Apply
- **THEN** testes planejados com vetores sintéticos verificam janela, padding, canais, agregação, patches idênticos e constantes, sem adicionar dependências

#### Scenario: Seleção da ficha visual
- **WHEN** a galeria de inspeção é preparada
- **THEN** oito IDs originais de validação são escolhidos antes de inferência pela ordenação SHA-256 da versão do split e ID, e a ficha anônima pontua cor, estrutura, borramento e artefatos de 1 (problema grave) a 5 (sem problema visível relevante), registra preferência pareada e comentários, sem exigir inferência extra ou serviço

#### Scenario: Nenhum ganho
- **WHEN** nenhum candidato cumpre os limiares numéricos e visuais
- **THEN** o relatório declara que não houve melhoria demonstrada

### Requirement: Teto cumulativo com interrupção persistente
O estudo SHALL contabilizar todos os pilotos, treinos, avaliações computacionais e repetições dentro do teto total aprovado, nunca ultrapassando 120 minutos.

#### Scenario: Planejamento e guarda de tempo
- **WHEN** o estudo inicia uma época ou atividade computacional
- **THEN** verifica o saldo cumulativo persistente e não inicia atividade sem saldo previsto suficiente

#### Scenario: Interrupção no limite
- **WHEN** o limite total ou individual é atingido durante uma execução
- **THEN** a execução é interrompida, o tempo fica registrado e o último checkpoint completo é preservado

#### Scenario: Retomada
- **WHEN** uma execução interrompida é retomada
- **THEN** mantém a mesma identidade e consome o saldo remanescente, sem reiniciar o contador

#### Scenario: Reserva para repetições
- **WHEN** o gate aprova uma reserva para repetições
- **THEN** o estudo preserva 30 minutos fora da alocação principal de 90 minutos e só os gasta em repetições justificadas aprovadas; C3 nunca usa a reserva

#### Scenario: Alocação principal simétrica
- **WHEN** C0, C1 e C2 são comparados
- **THEN** cada candidato recebe o mesmo envelope máximo de 30 minutos: piloto de 2 minutos com uma época seed 10 por taxa, treino/validação/SSIM/I-O de 24 minutos divididos em 4 por execução seed/taxa, consolidação de 2 minutos e avaliação final/registros de 2 minutos

#### Scenario: Piloto inviável
- **WHEN** qualquer época piloto completa, uma por taxa com seed 10, incluindo validação, SSIM e I/O, excede 1,2 segundos, limite de 4 minutos por execução seed/taxa dividido por 200 épocas
- **THEN** o candidato é marcado inviável para 200 épocas no limite de treino; não inicia treino completo e seu saldo não é redistribuído para alterar o plano dos demais

### Requirement: Histórico auditável por execução
O estudo SHALL manter registros estruturados que relacionem cada resultado à sua execução, configuração, dados, regra e custo.

#### Scenario: Linha de época
- **WHEN** uma época ou evento computacional é concluído
- **THEN** o registro inclui execução, candidato, seed, taxa, época, perdas, SSIM de validação, tempo e unidade, configuração, split, versões, regra e estado

#### Scenario: Métrica na régua comum
- **WHEN** uma medida é registrada para seleção
- **THEN** ela identifica a validação e a máscara fixa comum, sem usar pixels visíveis na métrica dos candidatos

#### Scenario: Controles determinísticos
- **WHEN** um controle sem rede é comparado por seed
- **THEN** seu valor calculado uma única vez por taxa e imagem é referenciado nas linhas das três seeds, sem recálculo por estado de rede

### Requirement: Teste apenas depois do congelamento
O estudo SHALL acessar o conjunto de teste uma única vez, depois de congelar candidatos, configurações e regras de seleção.

#### Scenario: Teste indisponível durante seleção
- **WHEN** candidatos ou regras ainda podem ser selecionados ou alterados
- **THEN** nenhum resultado do conjunto de teste é consultado

#### Scenario: Avaliação final
- **WHEN** candidatos e regras estão congelados
- **THEN** o teste é avaliado uma vez na régua definida, sem reabrir a seleção

### Requirement: Entrega coerente e histórico preservado
O relatório, slides e pacote SHALL refletir os mesmos resultados rastreáveis e SHALL preservar os artefatos e limites do experimento anterior.

#### Scenario: Números rastreáveis
- **WHEN** um resultado do estudo aparece em documento, slide ou pacote
- **THEN** ele corresponde ao histórico ou resumo identificado, com protocolo e limitações declarados

#### Scenario: Resultados anteriores
- **WHEN** a entrega atualizada é produzida
- **THEN** os resultados anteriores permanecem identificados como experimento original e não são substituídos

#### Scenario: Resultado negativo
- **WHEN** o estudo não demonstra ganho numérico e visual
- **THEN** os documentos relatam esse resultado explicitamente

### Requirement: Retomada C0 v2 isolada
A rodada C0 v2 SHALL usar um diretório, manifesto e contador próprios, preservar sem alteração os artefatos v1 e registrar hashes que identifiquem a versão v1, o código real incluindo arquivos de código sem commit, configuração, lockfile, splits e dados de treino e validação. O contador v2 SHALL ser append-only, limitar seu próprio consumo a 30 minutos e impedir que o consumo somado de v1 e v2 ultrapasse 120 minutos.

#### Scenario: Isolamento da v1
- **WHEN** a retomada v2 é preparada ou executada
- **THEN** escreve somente em `resultados/estudo-melhorar-reconstrucoes-mae-c0-v2` e preserva o contador, histórico, resultados, checkpoints e seleções v1

#### Scenario: Manifesto correspondente
- **WHEN** piloto ou treino v2 começa
- **THEN** os hashes congelados de código, configuração, lockfile e dados correspondem aos arquivos efetivamente usados, ou a execução para antes de treinar

#### Scenario: Piloto da v2
- **WHEN** cada taxa é pilotada para C0 com seed 10
- **THEN** mede uma época completa com validação, SSIM e I/O, usa o limiar de 1,25 segundos e registra qualquer piloto acima do limiar como inviável, sem repeti-lo

#### Scenario: Reexecução da v2
- **WHEN** o executor v2 já gravou o marcador de início
- **THEN** uma nova invocação não reinicia pilotos, treinos ou contador

#### Scenario: Piloto inviável de C0
- **WHEN** ao menos uma taxa do piloto C0 excede 1,25 segundos ou fica incompleta
- **THEN** C0 é registrado como inviável e nenhum treino completo de C0 começa em qualquer taxa

#### Scenario: Teto por seed e taxa
- **WHEN** uma execução C0 v2 é iniciada
- **THEN** o limite máximo é de 200 épocas e 4 minutos, incluindo carga, setup, checkpoints, validação, SSIM e I/O; a guarda monotônica interrompe ao atingir o limite e mantém só épocas completas

#### Scenario: Treino incompleto
- **WHEN** uma execução termina antes de 200 épocas ou é interrompida no teto
- **THEN** relata estado incompleto, épocas efetivamente concluídas, checkpoint melhor e checkpoint final com hashes, sem apresentar a execução como equivalente a 200 épocas

#### Scenario: Escopo de avaliação da v2
- **WHEN** os resultados v2 são consolidados
- **THEN** calculam MSE e SSIM na mesma régua de validação v1, não iniciam C1, C2, C3 ou controles, não consultam o teste e comparam descritivamente com referências disponíveis de validação v1

#### Scenario: Relato de lacunas
- **WHEN** o relatório C0 v2 é gerado
- **THEN** identifica o protocolo, execuções incompletas, saldo conjunto v1 e v2 e lacunas, sem tratar C0 ausente em v1 como derrota ou ausência de referência como evidência negativa
