# Design

## Context

O estudo parte do MAE existente, com imagens CIFAR-10 de 32x32, 16 patches de 8x8 e taxas de máscara de 50% e 75%. O registro antigo informa 0,58 s por época e MSE de teste de 0,0608 e 0,0717 nos patches ocultos; esses números descrevem o experimento anterior, e 0,58 s é somente referência, não uma medição atual. Ver proposal.md para a motivação. A execução depende de gate humano e ocorre somente na Apply.

## Goals / Non-Goals

**Goals:** produzir comparações reproduzíveis de candidatos e controles, decidir por regras congeladas usando validação, cumprir um teto cumulativo efetivo e manter rastreabilidade desde configuração até os documentos de entrega.

**Non-Goals:** classificar imagens, fazer linear probing, alterar dados, resolução, taxas ou número de patches, instalar dependências, nem reescrever os resultados anteriores.

## Decisions

### Aprovação central já registrada

O usuário aprovou a direção experimental: C0 direto, C1 com decoder de dimensão 128 e três blocos, C2 com MSE + 0,1 L1, C3 residual sobre a média RGB visível como opção; seeds 10, 20 e 30; 200 épocas planejadas; ganho de 5% em MSE e 0,02 em SSIM contra C0; tolerância secundária de SSIM 0,01; teto total de 120 minutos e reserva de 30 minutos. Esta aprovação define a direção, não autoriza Apply, implementação, treino ou teste. Os detalhes operacionais abaixo são as propostas finais para o gate humano e continuam pendentes de registro explícito antes de qualquer execução.

### D1. Máscaras de treino estáveis por identidade

Para cada imagem, época e semente, gerar uma permutação local dos 16 patches a partir da tupla `(semente, época, índice original da imagem no CIFAR-10)`. Usar algoritmo de permutação e codificação dessa tupla explicitamente versionados, sem RNG global ou compartilhado. Assim, a máscara independe da ordem ou composição dos lotes e pode ser reproduzida em retomadas. Ocultar os primeiros 8 índices para 50% e os primeiros 12 para 75%, garantindo aninhamento. Validar o mapa de índices originais contra o arquivo de índices do split. Alternativas rejeitadas: uma máscara fixa para todas as épocas e identidade pela posição corrente no lote ou vetor, ambas sensíveis ao protocolo de apresentação.

### D2. Régua comum e avaliação sem vazamento

Usar em todas as seeds e candidatos uma única máscara fixa por posição, aninhada e idêntica à avaliação original, sobre o conjunto completo de validação. Registrar MSE exclusivamente nos patches ocultos. Baselines, candidatos e controles são avaliados na mesma régua, incluindo comparações de C0 com cada controle em cada seed e taxa. O teste só pode ser avaliado uma vez depois de congelados candidatos, configurações e regras; seus resultados não podem reabrir seleção. A comparação com o estudo antigo é apenas indicativa, pois as máscaras de treino diferem.

### D3. Checkpoints de melhor validação e final

Manter dois artefatos distintos por execução: o checkpoint de menor perda de validação na régua e o checkpoint da última época concluída. Persistir uma cópia imutável de cada um, com hash e época registrados. Atualizar o melhor somente quando a perda for estritamente menor; empate mantém a primeira época. Usar a mesma regra de seleção, épocas planejadas e teto por execução para todos os candidatos. O relatório final apresenta ambos, identifica épocas e hashes, e mantém a seleção baseada somente no melhor checkpoint de validação; as métricas do checkpoint final são relatadas sem reabrir a seleção.

### D4. Controles sem rede e sem pixels ocultos

Implementar e documentar dois controles determinísticos, calculados por imagem e taxa sem consultar pixels ou valores dos patches ocultos:

- **Média RGB visível:** preencher cada pixel oculto com a média de cada canal sobre todos os pixels visíveis da imagem.
- **Interpolação espacial visível:** tratar cada patch visível como uma amostra em seu centro na grade 4x4; para cada patch oculto, preencher com a média ponderada dos patches visíveis, usando pesos inversamente proporcionais à distância euclidiana quadrática entre centros e normalizados para somar um. Coordenadas, unidade de distância, regra de normalização e pesos ficam registrados.

Se nenhum vizinho visível ou peso finito estiver disponível, o controle espacial usa a média RGB dos pixels visíveis; se também não houver pixel visível, usa a média por canal calculada somente no split de treino. A média RGB usa o mesmo último fallback quando sua amostra for vazia. As taxas atuais sempre deixam patches visíveis, mas o fallback é explícito. Registrar o MSE por taxa; repetir a linha comparativa por seed para que cada comparação com C0 e variantes fique identificável.

### D5. Candidatos limitados e hipóteses verificáveis

- **C0, MAE direto retreinado:** arquitetura e MSE atuais no protocolo novo; referência para isolar o efeito do protocolo.
- **C1, decoder reforçado:** proposta de dimensão 128 e três blocos no decoder, com encoder atual. Hipótese a testar: maior capacidade de decodificação pode ajudar quando poucos patches são visíveis, especialmente a 75%; custo e benefício permanecem incertos.
- **C2, perda mista:** proposta de MSE mais 0,1 vezes L1 nos pixels ocultos, com arquitetura de C0. Hipótese a testar: L1 pode reduzir borramento; MSE nos ocultos continua sendo a métrica numérica comparável.
- **C3, residual opcional:** predizer uma correção sobre o preenchimento pela média RGB visível. Só pode ser executado se C0 tiver MSE mediano menor que cada baseline nas duas taxas e houver pelo menos 30 minutos elegíveis da alocação principal, sem usar a reserva. Hipótese a testar: o preenchimento inicial pode acelerar a convergência; não é resultado garantido.

Fixar para todos os candidatos batch 64, AdamW com learning rate 1e-4, weight decay 0,05, betas (0,9; 0,999), epsilon 1e-8, precisão float32, sem scheduler e sem clipping de gradiente. O restante da configuração C0 existente é capturado literalmente no manifesto congelado, incluindo embaralhamento e inicialização aleatória, sem edição manual posterior. Somente C1 pode alterar o decoder para dimensão 128 e três blocos; encoder e demais parâmetros seguem C0. C2 mantém a arquitetura C0 e usa `MSE + 0,1 * L1`, ambas calculadas nos pixels ocultos em escala [0,1]. C3 usa arquitetura C0 e a mesma perda MSE. Congelar versão do código por hash Git, versão dos dados/splits e índices, ambiente/lockfile e hash integral da configuração imediatamente antes do primeiro piloto; não alterar esses valores durante a comparação. O piloto mede apenas duração e não consulta validação para escolha nem teste.

Cada candidato comparável usa exatamente o mesmo plano, seeds, taxas, limite de épocas e orçamento individual. Baselines determinísticos são calculados uma vez por taxa e imagem; suas linhas são associadas às três seeds nas comparações, sem inferência de rede ou recálculo por estado da rede. Não ampliar a lista em resposta a resultados do teste.

### D6. Seeds, ganho e decisão multiobjetivo

Usar três seeds de treino (10, 20 e 30), 200 épocas planejadas e comparação pareada por seed e taxa. C0 e cada controle/variante devem constar em cada comparação. Controles determinísticos são calculados uma vez por taxa e imagem e referenciados nas linhas correspondentes às seeds, pois não dependem do estado da rede. A semente 42 fica reservada à régua fixa.

Um candidato só é melhoria se, em cada taxa, a razão entre a mediana por seed do MSE de validação do candidato e a mediana de C0 for no máximo 0,95, e a mediana por seed das diferenças pareadas de SSIM (candidato menos C0) for pelo menos 0,02. Comparar C0 com cada baseline e candidato separadamente em cada taxa; reportar também os valores por seed, sem substituir a regra agregada. Entre candidatos elegíveis, identificar o maior SSIM mediano; manter os que estejam a no máximo 0,01 abaixo dele e, desse conjunto, escolher o menor MSE mediano. Empates exatos são resolvidos por menor tempo cumulativo e depois ordem fixa C1, C2, C3. Se nenhum cumprir ambos os limiares contra C0 em uma taxa, declarar ausência de melhoria demonstrada nessa taxa, sem vencedor. A tolerância de 0,01 só desempata candidatos elegíveis e não relaxa o ganho mínimo de 0,02 contra C0.

Calcular SSIM em cada patch oculto RGB de 8x8, com pixels e predições limitados a [0,1]. Para cada canal, usar janela gaussiana separável 3x3, sigma 1,5, pesos discretos normalizados para soma 1, centrada em cada pixel; padding por reflexão sem repetir o pixel de borda. Calcular médias, variâncias e covariância locais com os pesos e divisor populacional (sem correção de Bessel); limitar variâncias negativas por arredondamento a zero. Usar C1=(0,01)^2 e C2=(0,03)^2 para faixa dinâmica 1 e dividir pela expressão SSIM padrão, protegendo cada denominador com epsilon 1e-12. Para patch constante, aplicar a mesma fórmula: variâncias e covariância zero, SSIM 1 para canais constantes iguais e luminância conforme a fórmula para valores diferentes. Fazer média dos 3 canais por pixel, depois média dos pixels do patch, média dos patches ocultos por imagem, média das imagens por seed e taxa, e mediana das três seeds. Não consultar imagem inteira nem pixels visíveis na métrica. Implementação sem dependências novas; testes de referência planejados com patches idênticos, constantes iguais/diferentes, padrão simples e verificação independente da janela, padding, canais e agregação.

Fixar antes do treino oito IDs originais de validação: ordenar os IDs disponíveis pelo par `(SHA-256(UTF-8("visual-v1|" + versão_do_split + "|" + índice_original_decimal)), índice_original)` e escolher os oito primeiros; a mesma lista vale para ambas as taxas. A lista e hash ficam no manifesto antes de qualquer inferência. Capturar as reconstruções desses IDs na mesma passagem de validação por época já prevista e gerar a ficha visual sem inferência adicional nem serviço externo. Em ordem aleatória e rótulos anonimizados quando possível, a ficha registra por imagem/candidato notas de 1 a 5 para cor, estrutura, borramento e artefatos: 1 indica problema grave, 3 qualidade mista/aceitável e 5 reconstrução consistente sem problema visível relevante; inclui preferência geral pareada e campo de comentário. Dois avaliadores preenchem a ficha, sem alegar que a avaliação humana ocorreu nesta fase. É evidência qualitativa e não altera a seleção numérica.

### D7. Teto cumulativo, persistência e interrupção

O orçamento é um teto de tempo monotônico de parede, incluindo inicialização, carregamento e salvamento de dados, piloto, treino, validação por época, SSIM, teste final, controles, checkpoint e escrita dos registros. Dos 120 minutos, 90 são alocação principal e 30 ficam protegidos exclusivamente para repetições justificadas aprovadas. A alocação principal é exatamente 30 minutos para cada um de C0, C1 e C2: 2 minutos de piloto de uma época; 24 minutos de treino, validação por época, SSIM e I/O, divididos igualmente em 8 minutos por seed; 2 minutos de consolidação e verificação de checkpoints; e 2 minutos para a parte proporcional da avaliação final e registros. O teste final e o cálculo único dos baselines usam até 6 minutos agregados dentro dos 90 minutos, rateados igualmente como parte dos 2 minutos de avaliação de cada candidato; atividade compartilhada é contabilizada uma única vez no contador global, sem duplicar trabalho.

O piloto não avalia teste e não escolhe hiperparâmetros. Para cada candidato, medir uma época completa com seed 10 em cada uma das duas taxas, incluindo validação, SSIM e I/O; ambas cabem no envelope de piloto de 2 minutos. Como os 24 minutos de treino se dividem por três seeds e duas taxas, cada execução seed/taxa recebe 4 minutos. Se qualquer época piloto exceder 1,2 segundos, o candidato é marcado inviável para 200 épocas dentro do limite de sua execução; seus treinos completos não começam e o saldo fica não gasto. O critério resulta de 4 minutos divididos por 200 épocas e aplica-se igualmente a todos. Durante treino, não iniciar época se o tempo medido da última época não couber no saldo de 4 minutos da execução seed/taxa ou no saldo global. O candidato fica com épocas completas já registradas; não encurtar épocas nem reduzir validações. Se custo real ultrapassar a estimativa do piloto, interromper no limite e registrar incompletude; não redistribuir sua alocação para alterar o plano de outro candidato.

C3 só pode ser executado depois da avaliação de C0 contra cada baseline: em ambas as taxas, a mediana por seed do MSE de C0 deve ser estritamente menor que a de cada um dos dois baselines. A decisão ocorre depois dos pilotos e execuções principais de C0, C1 e C2, mas antes do congelamento final e da única avaliação do teste. Deve restar pelo menos 30 minutos dos 90 principais, já descontados até 6 minutos para avaliação final de validação/teste e controles. C3 recebe no máximo 30 minutos desse saldo, sem tocar nos 30 minutos protegidos, e usa o mesmo envelope e critérios por candidato. Se o critério de C0 falhar ou o saldo elegível for menor que 30 minutos, registrar C3 como não executado e a razão. A reserva de 30 minutos nunca financia C3.

Manter contador cumulativo persistente, registrar duração monotônica real, e verificar o saldo antes de iniciar cada época e durante a execução. Não iniciar época se o saldo ou o limite individual não comportar o tempo estimado; ao atingir limite, interromper imediatamente, marcar a execução e conservar o checkpoint da última época completa. Salvar estado de modelo, otimizador, época e contador ao completar época e antes de encerrar. Retomada continua a mesma identidade de execução e consome o mesmo saldo, sem reiniciar contadores. Nenhuma repetição, falha ou reinício zera o total. A barreira de tempo também inclui pilotos e avaliação, para impedir que atividades omitidas do orçamento ultrapassem o teto.

### D8. Histórico estruturado e versões

Gravar uma linha por época e por execução em um CSV append-only, com identificador de execução, candidato, seed, taxa, época, perda de treino, perda de validação, SSIM de validação, tempo da época e acumulado, unidade, configuração e hash, split e versão de índices, versão do código, versão das regras, estado e motivo de interrupção. Registros de piloto e avaliação recebem tipo de evento explícito. Um resumo derivado mantém época e hashes dos checkpoints melhor e final, médias/medianas por seed, métricas dos controles, decisões e tempo total. Todas as medidas de seleção apontam para validação na mesma régua; eventos de teste são posteriores ao congelamento e marcados como avaliação final.

### D9. Documentos e pacote coerentes

Gerar relatório, figuras, slides e pacote a partir do histórico e do resumo versionados; números não serão digitados manualmente. Distinguir graficamente e no texto o estudo anterior e o novo, com protocolo, seeds, limitações e fontes de cada valor. Preservar métricas, curvas, reconstruções e documentos anteriores identificados no repositório. Atualizar README e especificação do pacote para incluir os novos artefatos e conservar as exclusões vigentes de dados brutos, checkpoints e oráculo.

## Emenda C0 v2: retomada isolada autorizada

A autorização posterior cobre somente uma nova rodada C0 em `resultados/estudo-melhorar-reconstrucoes-mae-c0-v2`. A rodada anterior permanece v1, com seus manifestos, contador, histórico, resultados, checkpoints e seleções intactos. Nenhuma métrica de v1 é reclassificada retroativamente.

O protocolo conserva os mesmos dados CIFAR-10, configuração C0, máscaras por identidade, época e seed, régua fixa de validação, seeds 10, 20 e 30 e taxas 0,5 e 0,75. A única mudança científica autorizada é o limiar do piloto, de 1,2 s em v1 para 1,25 s em v2. O piloto de cada taxa usa seed 10 e mede uma época completa de treino, validação, SSIM e checkpoints; carga de dados e montagem do modelo são contabilizadas no orçamento, embora não componham o tempo da época usado no limiar.

Se qualquer piloto exceder 1,25 s ou ficar incompleto, C0 é considerado inviável para treino completo nas duas taxas, e nenhum dos seis treinos começa. O piloto não é repetido.

Cada execução seed/taxa tem limite de 240 segundos, incluindo carga, configuração, validação, SSIM, salvamentos, cópias imutáveis e I/O. Duzentas épocas são o máximo planejado, não uma garantia. Uma execução interrompida relata apenas épocas completas e permanece marcada como incompleta; checkpoint final parcial não equivale a 200 épocas. O guarda monotônico usa nanossegundos inteiros, consulta o saldo antes de uma execução e durante cada lote e interrompe o processo no limite sem arredondar a duração para baixo. Um piloto acima de 1,25 s é registrado como inviável e não é repetido.

O contador v2 é independente e append-only em `contador.jsonl`. Seu consumo acumulado não pode ultrapassar 30 minutos; a soma do contador v1, incluindo eventual reserva já consumida, com o v2 não pode ultrapassar 120 minutos. O manifesto v2 registra hashes de referência dos artefatos v1, o hash real dos fontes Python presentes, inclusive arquivos de código sem commit, o lockfile, a configuração, os índices de treino e validação e os dados de treino e validação. O manifesto precisa corresponder ao código e às entradas no instante da execução ou a rodada para sem treinar.

O executor grava um marcador antes de iniciar a sequência. Uma segunda invocação não repete pilotos ou treinos iniciados e não zera contadores ou checkpoints.

O escopo executável limita-se ao piloto C0 e aos treinos C0 para as seis combinações de seed e taxa. Não são feitos novos treinos C1, C2 ou C3, nem inferências de controle, avaliação do conjunto de teste ou consulta a novas métricas de teste. SSIM e MSE por época são calculados na mesma régua de validação v1. A comparação posterior com C1, C2 e controles v1 é descritiva e não constitui uma comparação causal equivalente, pois o protocolo e o nível de conclusão das execuções podem diferir. Ausência de C0 em v1 não é derrota, e ausência de uma referência não é evidência negativa.

Os checkpoints melhor e final são cópias imutáveis separadas, com época e SHA-256. O relatório v2 traz o estado e o número efetivo de épocas de cada taxa e seed, a diferença de protocolo, o total v1 e v2 e as lacunas remanescentes. A rodada não altera slides, pacote, README, histórico ou artefatos de v1.

## Risks / Trade-offs

- [A máscara depende do mapeamento dos índices originais] → validar o mapa de cada split antes do estudo e falhar explicitamente em caso de divergência.
- [A interpolação espacial pode borrar detalhes e depender da geometria escolhida] → congelar coordenadas e pesos antes da comparação e tratar o controle como referência, não como reconstrução semântica.
- [SSIM e julgamento visual são aproximações de qualidade perceptual] → definir limiares e parâmetros antes do treino, combinar métrica agregada e inspeção cega, e declarar que não medem reconhecimento.
- [Múltiplas variantes e seeds podem consumir o teto ou ajustar-se à validação] → limitar candidatos, usar regra congelada, alocação igual e teto persistente; o teste não participa da escolha.
- [Uma época pode cruzar o limite de tempo] → conferir saldo antes e durante a época, interromper ao atingir limite e conservar somente o último checkpoint completo.
- [Nenhum candidato atingir ambos os limiares] → relatar o resultado negativo e preservar a referência anterior sem alegar melhoria.

## Migration Plan

1. No gate humano, registrar a aprovação da direção já acordada e aprovar, editar ou rejeitar os detalhes operacionais propostos, incluindo SSIM, C3, configuração comum, inspeção visual e alocação detalhada. Sem esse registro e sem autorização separada para Apply, nenhuma implementação, piloto ou treino começa.
2. Na Apply, implementar e cobrir com testes a máscara, régua, controles, checkpoints e contador; medir pilotos; então executar somente o plano aprovado dentro do saldo persistente.
3. Selecionar apenas por validação; congelar candidatos e regras; consultar teste uma vez ao fim; derivar relatório, figuras, slides, README e pacote do histórico.
4. Reversão consiste em retirar módulos e artefatos novos do estudo. Os arquivos e resultados originais permanecem preservados e identificados.

## Open Questions

- Nenhuma decisão científica ou operacional foi deixada para a Apply. O layout das figuras pode ser definido durante a produção, desde que derive do histórico e identifique taxas, seeds, controles e candidatos.

## Propostas para o gate humano

Propostas finais pendentes do gate humano: definição matemática e testes de referência do SSIM; configuração comum completa e hashes de congelamento; critério C3 de superioridade estrita de C0 sobre cada baseline nas duas taxas e saldo elegível mínimo de 30 minutos fora da reserva; distribuição exata dos 90 minutos principais e política de inviabilidade do piloto; seleção determinística dos oito IDs visuais e ficha; regra de desempate especificada em D6. A aprovação central da direção e a autorização futura de Apply são registros distintos. Nenhum resultado histórico é substituído.
