# Revisão posterior às correções

Esta revisão substitui o estado de bloqueio documental anterior somente quando os checks de `verificacao-correcao/` passam integralmente. Nenhum treino, piloto, inferência ou nova consulta ao teste foi executado. Nenhum stage, commit, push, publicação ou arquivamento foi realizado.

## Achados endereçados

1. O leitor `codigo/estudo_execucao_c0_v2.py`, função `_resumo_refs_v1`, agora exige `estado=validacao` para controles. `tests/test_estudo_orcamento_c0_v2.py` cobre ambos os estados em ambas as ordens e os dados reais por seed. O resultado primário é validação do histórico, sem usar o último controle de teste. Em eventos de época, o estado é `concluido`, e somente as colunas de validação são usadas.
2. `retificacao-validacao.md` e `.json` registram origem, hashes antigos e atuais, doze execuções por seed, controles corretos e medianas melhor/final. C1 a 75% supera descritivamente RGB em SSIM de validação: 0,362957 contra 0,355630; os valores do teste não sustentam comparações de validação. O relatório e resumo v2 originais permanecem intactos; o executor original foi preservado em `fontes-historicas/`, com hash idêntico ao registrado. O gate de fontes não foi removido nem desativado, portanto a reexecução histórica com código atual é recusada. O consolidador novo só lê registros.
3. `scripts/gerar_relatorio_fase_b.py` escreve em novo caminho, preservando relatório histórico e adendo. Relata avaliação visual aberta negativa de um único avaliador humano, objetivo visual não atingido, fichas não cegas e sem notas individuais. README, notebook e slide 9 dão a mesma interpretação: exploratório, sem confirmação independente ou superioridade universal.
4. `scripts/gerar_slides.py` distingue máximo planejado de 200 épocas, C1 seed 10 a 75% interrompido em 185 e orçamento v1 versus v2. Os controles vêm da retificação com origem explícita. Metadados variáveis dos binários são normalizados sem alterar o conteúdo visual; a evidência verifica igualdade de hashes em duas gerações consecutivas.
5. `scripts/montar_zip.py` usa inventário explícito de módulos e documentos, inclui `codigo/__init__.py`, fontes do estudo, v2 original, retificação, notas e relatório no caminho original, além do alias histórico. Os pesos, dados brutos, caches e registros com caminhos pessoais ficam fora. As cópias de apresentação do estado v1 e do mapeamento removem somente caminhos pessoais e documenta hash de origem. Fontes com nome `estudo_checkpoints.py` são incluídos; arquivos de pesos e diretórios `checkpoints` são proibidos. CSV usa LF; zip tem timestamps e permissões fixos. Teste confere entradas, hashes e bytes contra o conteúdo corrente.
6. `scripts/construir_notebook.py` preserva código, saídas científicas e IDs das células existentes; somente o stdout com caminho pessoal é convertido para caminho relativo. O texto distingue experimento original e estudo posterior. O construtor foi executado sem executar as células científicas. Resultados v1, manifesto, contadores e artefatos científicos v2 permanecem com os hashes iniciais.

## Checks e proposta de stage

Os comandos, diretório relativo real (`.` na raiz do projeto), saídas, códigos e limitações estão em `verificacao-correcao/`. A suíte completa inclui os subconjuntos previstos em `tasks.md`. O warning do oráculo permanece visível; não é falha nem foi suprimido. O relatório de equivalência preexistente é restaurado byte a byte após o pytest e comparado ao backup. A proposta de stage é uma lista explícita de caminhos em `verificacao-correcao/stage-proposto.txt`; nenhum comando de stage foi executado. Os arquivos originais com caminhos pessoais continuam preservados localmente e são excluídos dessa lista, que inclui suas cópias de apresentação quando necessárias.

Limitações: validação estrutural e testes determinísticos não certificam qualidade científica; caminhos de treino real C0 v2 não foram exercitados. Nenhum escopo científico extra foi introduzido. A ausência de C0 impede demonstrar ganho pela regra congelada e não significa derrota; o objetivo visual permanece não atingido.

## Localização das provas

| Achado | Arquivo e linha | Prova |
|---|---|---|
| Separação validação/teste | `codigo/estudo_execucao_c0_v2.py:836` | `tests/test_estudo_orcamento_c0_v2.py:142` e `:160`; pytest completo |
| Derivações por seed e hashes | `scripts/retificar_validacao.py:26` | `retificacao-validacao.json`; integridade dos originais em `verificacao-correcao/integridade.json` |
| Relatório original preservado | `scripts/gerar_relatorio_fase_b.py:23` | Saída em novo caminho; hashes do original conferidos |
| Pacote completo e LF | `scripts/montar_zip.py:63` | Teste compara lista atual e bytes; CSV sem CRLF e diff sem erros |
| Notebook e slides coerentes | `scripts/construir_notebook.py:52` e `scripts/gerar_slides.py:388` | Saídas científicas preservadas; slide 9 inspecionado; hashes iguais nas duas gerações |

Estado final: todos os checks obrigatórios passaram. Os resultados exatos e os códigos de saída estão nos arquivos de evidência correspondentes, incluindo a suíte completa com 111 testes aprovados. A inspeção visual do slide 9 confirmou tabela e nota legíveis, sem transbordamento. A proposta de stage exclui os originais com caminhos pessoais, pesos e logs locais; fontes necessárias e cópias sanitizadas estão incluídas explicitamente.

## Revisão dirigida posterior: IDs Markdown e caminho temporário

A revisão independente identificou dois itens residuais no notebook. O construtor preservava IDs e resultados apenas nas células de código; os dez IDs Markdown existentes em `HEAD` estavam ausentes. Um warning mantinha o prefixo `/tmp/ipykernel_...` no texto de saída.

`scripts/construir_notebook.py` agora associa os dez IDs da base aos títulos Markdown únicos correspondentes e falha se uma âncora estiver ausente ou duplicada. O sanitizador remove somente o prefixo de caminho temporário antes de `UserWarning`, mantendo a mensagem completa. A regeneração preservou as saídas das células científicas com código idêntico, sem executar células, treino ou inferência.

Os testes de regressão conferem os IDs contra `git show HEAD:codigo/notebook.ipynb` e verificam que a mensagem do warning permanece byte a byte após a remoção do caminho. A suíte completa passou com 113 testes e um warning de execução já esperado; `tests/relatorio_equivalencia.txt` foi restaurado do backup e seu SHA-256 permaneceu `6300b890889bd0ae20a68ca121598316503a43889b954173cbf5f23ee0be9921`.

Notebook, slides e pacote foram regenerados em execuções repetidas. Os hashes SHA-256 coincidiram entre as duas gerações de cada artefato. O pacote contém 65 arquivos e seus MD5 foram conferidos pela suíte. Hashes de arquivos de resultados v1/v2 e da fonte histórica foram comparados antes e depois sem divergências. Os comandos, diretório, saídas e estado de stage estão em `verificacao-correcao/revisao-ids-warning.md` e a lista explícita de stage em `verificacao-correcao/stage-proposto.txt`.
