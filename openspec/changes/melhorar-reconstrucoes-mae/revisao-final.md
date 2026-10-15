# Revisão final antes de commit

Data: 15 de outubro de 2026. Estado: bloqueado para commit e PR. Nenhum commit, push, PR, merge ou arquivamento foi executado. A revisão registrou notas finais, executou checks locais e identificou correções que exigem trabalho direcionado.

Diretório de todos os comandos: raiz desta cópia de trabalho, `openspec-melhorar-reconstrucoes-mae-coord`. Base local: `origin/main`, commit comum `2797e1fcb6e7906abc32666698710ad400e2689f`. As referências remotas não foram atualizadas por fetch nesta revisão.

## Evidências e alterações desta revisão

Lidos os artefatos proposal, design, tasks, aprovação, emenda, quatro deltas de especificação, configuração do projeto e workflows. Não foram encontrados arquivos AGENTS.md aplicáveis nesta árvore e seus diretórios ancestrais. Revisados o diff rastreado, o inventário não rastreado, módulos novos, geradores, testes e resultados textuais. A leitura de código e dados registrados identificou falhas que a suíte atual não cobre; o sucesso dos testes não certifica o protocolo científico.

Criadas `notas-finais.md`, esta revisão e evidências textuais; README esclarece v1, julgamento visual e ausência de cegamento. O relatório histórico recebeu somente um adendo datado, preservando suas seções anteriores. Não houve nova execução científica. Fontes Python e resultados congelados v1 não foram alterados. Slides e pacote foram regenerados pelos geradores existentes para cumprir os checks previstos; a implementação dos geradores não foi modificada nesta revisão.

Uma avaliação humana aberta, por um avaliador, considerou as reconstruções ruins nas duas taxas e o objetivo visual não atingido. Não há notas individuais ou avaliação cega. As duas imagens existentes revelam os métodos no cabeçalho; o JSON original permanece vazio. Sem C0 treinado, não se demonstra ganho pela regra congelada. Resultado exploratório, sem confirmação independente.

## Achados

1. **Alta, bloqueante: controle do teste rotulado como validação.** `codigo/estudo_execucao_c0_v2.py:836` aceita eventos `controle` sem filtrar `estado=validacao` e sobrescreve por método e taxa na linha 840. `codigo/estudo_execucao.py:1037` grava também os controles do teste com esse evento. Evidência independente: histórico contém RGB SSIM de validação 0,355596/0,355630 e de teste 0,365483/0,363144, mas o relatório v2 usa os últimos sob título de validação. C1 a 75% tem 0,362957 e C2 a 50% tem 0,365044 de validação: as desigualdades contra 0,363144 e 0,365483 não são uma comparação válida entre métodos no mesmo conjunto. Sugestão: filtrar explicitamente o conjunto, acrescentar regressão sintética com ambos os estados e emitir retificação separada; preservar fontes executados e manifesto v2 originais. Não treinar nem avaliar novamente.

2. **Média: geração posterior pode apagar a avaliação humana.** `scripts/gerar_relatorio_fase_b.py:293` e `scripts/gerar_relatorio_fase_b.py:418` continuam emitindo avaliação humana pendente; o gerador reescreve o relatório e apagaria o adendo desta revisão. `codigo/estudo_execucao.py:1340` insere o mapeamento de métodos no cabeçalho apesar de descrever a ficha como cega. Sugestão: tratar as notas posteriores como entrada documental separada, manter o histórico e retirar alegações atuais de cegamento; não refazer inferência ou inventar preenchimentos.

3. **Média: slide 9 generaliza a conclusão das épocas.** `scripts/gerar_slides.py:385` imprime “200 épocas por seed e taxa” sem indicar máximo planejado nem C1 seed 10 a 75% interrompido em 185. O PDF regenerado contém a mesma frase. A reserva intocada e o consumo 41,1 descrevem apenas v1, sem rótulo explícito de rodada; v2 consumiu 0,209334139 minuto da reserva e o total é 41,270848124 minutos. Sugestão: rotular v1 e épocas planejadas/efetivas e acrescentar o resultado visual aberto; regenerar somente os documentos afetados.

4. **Média: pacote incompleto para a reprodução do estudo e notas separadas.** `scripts/montar_zip.py:25` lista os fontes antigos, mas não os módulos novos do estudo; a inspeção real do zip confirmou zero `codigo/estudo*.py`. O pacote também não leva a nota separada que o README referencia, os artefatos v2 e o caminho original OpenSpec do relatório. O adendo completo está no `relatorio-fase-b.md` da raiz do zip, portanto o julgamento está disponível no pacote. Sugestão: definir mapa explícito de fontes e documentos exigidos e caminhos válidos dentro do pacote, sem incluir pesos, logs locais, dados brutos ou caches; cobrir a lista completa com um teste do conteúdo corrente.

5. **Baixa: verificação de whitespace falha no CSV gerado.** `scripts/md5_pacote.csv:3` e outras linhas novas usam CRLF; `git diff --check` retorna 2 por trailing whitespace. O gerador usa o terminador padrão de `csv.writer` em `scripts/montar_zip.py:119`. O padrão já existia no CSV, mas a falha continua real. Sugestão: corrigir o terminador do gerador em tarefa direcionada e regenerar a lista; não editar hashes científicos.

6. **Média, segurança da entrega: stage amplo publicaria pesos de trabalho.** Há 32 arquivos `.pt` não rastreados, totalizando 363.475.300 bytes, incluindo checkpoints de trabalho e pilotos. Parte dos pesos imutáveis v1 fica ignorada pela regra `checkpoints/`, portanto o inventário de Git não representa toda a árvore física. Sugestão: usar a lista explícita proposta abaixo, revisar os hashes e manter todos os pesos, dados brutos e caches fora do stage. A varredura por nomes e padrões de credenciais no texto novo não encontrou segredos, mas não constitui prova de ausência de segredos em todos os formatos binários.

Riscos adicionais de reprodução observados em v1: `codigo/estudo_execucao.py:561` verifica somente estimativa antes da época; não há guarda dentro dos lotes e o salvamento/registro posterior não cabe nessa estimativa. `codigo/estudo_execucao.py:224` valida a integridade interna do manifesto, sem comparar o hash atual dos fontes ao congelado, enquanto `codigo/estudo_execucao.py:371` pode regravar o congelamento. Esses limites históricos não foram corrigidos nem usados para reclassificar v1; a v2 adiciona verificações de fontes e guarda monotônica. A v2 não executou nenhum dos seis treinos completos, logo seus caminhos de treino real não foram validados por esta revisão.

## Checks reais no estado final

| Comando | Resultado | Estado verificado e limites |
|---|---|---|
| `uv sync --locked` | saída 0, 144 resolvidos, 140 verificados | repetido após notas e regenerações; lockfile intacto |
| `uv run pytest -q` | saída 0, 107 passed, 1 warning, 3,63 s | após README, adendo e pacote finais; warning preexistente de conversão de tensor em escalar no oráculo |
| `openspec validate melhorar-reconstrucoes-mae` | saída 0, change válida | após notas finais; valida estrutura, não certifica conclusões |
| `uv run python scripts/gerar_slides.py` | saída 0, 13 páginas, limites ok | fonte Python e resumo congelado intactos; pptx/pdf/png gerados, limitações semânticas acima |
| `uv run python scripts/montar_zip.py` | saída 0, 34 arquivos | após README e adendo; csv de hashes regenerado; zip excluído do stage |
| `git diff --check` | saída 2 | falha real por CRLF no CSV gerado; nenhuma exceção aplicada |
| leitura `_verificar_congelamento()` | saída 0 | conferiu manifesto, configuração, 42 fontes, lockfile, índices e dados somente de treino/validação e 66 arquivos v1; não iniciou execução |
| SHA-256 do relatório de equivalência | igual ao início | backup antes do pytest e restauração byte a byte após cada execução; alteração preexistente não pertence ao stage |

Os testes específicos planejados são subconjuntos da suíte completa, que os coletou. O notebook não foi alterado nem executado; continua sendo resultado do protocolo histórico, não evidência de C0 retreinado. `construir_notebook.py` é condicional à alteração do notebook e não foi executado. Os workflows de revisão externa não definem outro check determinístico local e não foram acionados. Nenhum check obrigatório foi pulado ou enfraquecido. Os comandos de treino, piloto, inferência e avaliação científica não foram executados.

As saídas textuais estão em `verificacao-final/`. A cópia principal fora desta raiz não foi acessada para escrita. O backup do relatório preexistente permaneceu fora da entrega. A geração de slides altera metadados dos binários, portanto seus hashes atuais diferem do pacote anterior; o md5 foi recalculado para os binários atuais.

## Integridade científica

Manifesto v2 íntegro: `fda2ab28a44b9a74d6b02d5b19dc621687e1d5d98035fa2419716b0794ed4e16`. Inventário de fontes: `9eba0cb402003f739abfe18ade2b06d6160c57642a4342c7ba8a417934de7cf9`. Árvore v1: `4e0e50213113c937dbe2dc3bbc91771a865b487c4a3f960f77a6d3a1ebd48e54`. Todas as referências v1 e fontes congelados conferiram no estado final. Pilotos v2: 1,430503879 s e 1,358304787 s, acima de 1,25 s; seis treinos não iniciados; reserva v2 0,209334139 minuto; total 41,270848124 minutos. Nenhum desses fatos valida a tabela contaminada de controles v2.

## Stage proposto, sem execução

Stage autorizado para realizar agora: nenhum, pois a revisão encontrou bloqueios. A lista exata de arquivos candidatos após as correções está em `verificacao-final/stage-proposto.txt`, um caminho relativo por linha; não usar `git add .`, `git add -A` ou glob de diretório. A lista é uma proposta de seleção, não uma aprovação do conteúdo com achados pendentes. Reavaliar hashes dos arquivos gerados depois das correções. O inventário completo de modificados e não rastreados, com tamanhos e exclusões, está em `verificacao-final/inventario.tsv`.

Excluir do stage: `tests/relatorio_equivalencia.txt`, `logs/` histórico local, todos os `.pt` (inclusive ignorados), `dados/cifar10_raw/`, caches, `.venv/`, `slides/png/`, `seminario_masked_modeling.zip` e `.zip_conteudo/`. Os dados do subconjunto e índices já versionados não mudaram; o pacote mantém o subconjunto existente de 19.807.280 bytes e índices de 143.805 bytes. O zip final tem 34 entradas e 23.415.860 bytes; não contém pesos, dados brutos ou caches. Os binários novos da entrega são figuras PNG e slides pptx/pdf, com tamanhos no inventário. Há caminhos absolutos locais em estado e mapeamento de ficha congelados e em logs históricos; evitar publicar os logs locais e definir cópias de apresentação sem esses caminhos se necessário, sem alterar os congelados.

Pendente: corrigir separação validação/teste em relatório retificado, coerência de geradores e slides, conteúdo do pacote e falha de whitespace; repetir checks afetados e revisão antes de commit e PR. Não há autorização nesta etapa para merge ou arquivamento.
