# Tasks

## 1. Gate humano e congelamento

- [ ] 1.1 Registrar separadamente a aprovação central de direção já dada pelo usuário e a aprovação/edição/rejeição das propostas operacionais finais: SSIM, configuração comum, critério e saldo de C3, orçamento detalhado, ficha visual e desempates. Verificar registro datado; aprovação central não autoriza Apply, piloto, treino ou teste.
- [ ] 1.2 Após gate humano e autorização explícita de Apply, congelar antes do piloto versão Git/código, lockfile/ambiente, splits/índices, configuração completa/hash, ordem de seleção, orçamento e IDs da inspeção visual. Os pilotos medem somente duração, não consultam teste nem selecionam parâmetros. Verificar que nenhum campo depende do teste.

## 2. Máscaras e controles de reconstrução

- [ ] 2.1 Implementar máscaras determinísticas por identidade original, época e seed, independentes de lote, ordem e RNG global, aninhadas em 8 e 12 dos 16 patches; verificar com `uv run pytest tests/test_estudo_mascaras.py -q` na raiz que recomputação, mudança de época, aninhamento e independência de ordem são cobertos. Execução apenas na Apply, após 1.1. Artefato: testes da máscara.
- [ ] 2.2 Implementar e documentar a média RGB dos visíveis e a interpolação espacial ponderada por distância entre coordenadas dos centros; cobrir fallback explícito e garantir ausência de acesso a pixels ocultos. Verificar com `uv run pytest tests/test_estudo_baselines.py -q` na raiz e casos sintéticos. Artefatos: documentação dos algoritmos e testes dos controles.
- [ ] 2.3 Implementar a régua fixa comum na validação para candidatos e controles, nos pixels ocultos e com comparação identificável por seed e taxa; verificar com `uv run pytest tests/test_estudo_avaliacao.py -q` na raiz a igualdade da máscara e o cálculo sem contribuição de pixels visíveis. Artefato: teste da régua.

## 3. Candidatos e seleção de checkpoints

- [ ] 3.1 Implementar C0 como MAE direto retreinado e permitir que cada variante aprovada declare arquitetura e perda antes do treino, preservando entrada, resolução, patches e codificação dos visíveis; verificar com `uv run pytest tests/test_mae.py tests/test_estudo_candidatos.py -q` na raiz a configuração de referência e as variantes declaradas. Artefatos: implementação e testes de candidatos.
- [ ] 3.2 Implementar checkpoints separados de melhor validação e final, cópias imutáveis com hashes e desempate pela primeira época; verificar com `uv run pytest tests/test_estudo_checkpoints.py -q` na raiz os empates, as épocas e a imutabilidade. Artefatos: testes e documentação dos checkpoints.
- [ ] 3.3 Implementar C3 residual apenas se, nas duas taxas, a mediana de MSE de C0 for estritamente menor que a de cada baseline e houver ao menos 30 minutos livres nos 90 minutos principais após C0/C1/C2 e desconto de até 6 minutos para avaliação final. Decidir antes de congelar e consultar teste; C3 nunca usa a reserva de 30 minutos. Se qualquer condição falhar, registrar não execução e motivo. Verificar com `uv run pytest tests/test_estudo_candidatos.py -q` na raiz. Artefato: teste de elegibilidade.

## 4. Orçamento e histórico

- [ ] 4.1 Implementar contador cumulativo persistente para piloto, treino, validação por época, SSIM, checkpoint/I-O, avaliação final e repetição: 90 minutos principais, em envelopes iguais de 30 para C0/C1/C2 (2 piloto com uma época seed 10 por taxa + 24 treino/validação/SSIM/I-O, 4 por seed/taxa + 2 consolidação + 2 avaliação/registros), e 30 minutos protegidos para repetição justificada. Se qualquer época piloto exceder 1,2 segundos, marcar inviável para 200 épocas e não iniciar treino completo; saldo não é redistribuído para alterar os outros planos. Verificar com `uv run pytest tests/test_estudo_orcamento.py -q` na raiz. Artefatos: testes e registro de tempo.
- [ ] 4.2 Registrar por época e evento execução, candidato, seed, taxa, perdas, SSIM, tempo e unidade, configuração, splits, versões, regra, estado e motivo de interrupção; verificar com `uv run pytest tests/test_estudo_historico.py -q` na raiz que cada campo e a sequência append-only são auditáveis. Artefatos: esquema, histórico de exemplo sintético e testes.

## 5. Qualidade visual, decisão e teste final

- [ ] 5.1 Implementar SSIM conforme design: patch 8x8 RGB, entrada [0,1], gaussiana 3x3 sigma 1,5, reflexão sem repetir borda, população, constantes/epsilon explícitos e agregação definida. Não adicionar dependências; planejar testes sintéticos de referência para iguais, constantes, padrão, janela/padding, canais e agregação. Fixar oito IDs de validação pela ordenação SHA-256 descrita e uma ficha cega de cor, estrutura, borramento, artefatos e preferência, sem inferência extra. Verificar com `uv run pytest tests/test_estudo_visual.py -q` na raiz. Artefatos: protocolo e testes planejados.
- [ ] 5.2 Comparar por taxa e seed C0 com cada controle e candidato. Melhoria exige razão das medianas de MSE <=0,95 e mediana da diferença pareada de SSIM >=0,02 contra C0 em cada taxa. Entre elegíveis, reter SSIM até 0,01 da maior mediana e escolher menor MSE; empate exato por tempo, depois ordem C1/C2/C3. Controles determinísticos são calculados uma vez por taxa/imagem e referenciados por seed. Verificar com `uv run pytest tests/test_estudo_selecao.py -q`, sem acesso ao teste. Artefato: resumo reproduzível da seleção.
- [ ] 5.3 Congelar candidatos e regras e somente então avaliar uma vez o conjunto de teste na régua; verificar que o histórico contém eventos finais posteriores ao congelamento e nenhuma consulta anterior. Artefatos: resultados finais identificados e registro da barreira de avaliação.

## 6. Relatório, documentos, slides e pacote

- [ ] 6.1 Gerar relatório e figuras a partir do histórico e resumo, declarando protocolos, fontes, limitações, trade-offs e resultado negativo sem atenuação; verificar que todo número pode ser rastreado e que a inspeção visual não é apresentada como prova de reconhecimento. Artefatos: relatório e figuras do estudo.
- [ ] 6.2 Atualizar README e slides com números derivados dos resultados registrados, mantendo identificáveis os resultados anteriores e a delimitação de cada protocolo; verificar na raiz com `uv run python scripts/gerar_slides.py` que pptx, pdf e imagens de inspeção são produzidos e que os limites de página declarados pelo script passam. Pré-requisitos: ambiente sincronizado, resultados e resumo disponíveis, LibreOffice e pdftoppm. Artefatos: slides, pdf e imagens de inspeção.
- [ ] 6.3 Atualizar o empacotamento para incluir histórico, resumo, figuras e relatório, manter os conteúdos e exclusões atuais e falhar nomeando arquivo obrigatório ausente; verificar com `uv run pytest tests/test_montar_zip.py -q` e `uv run python scripts/montar_zip.py` na raiz. Pré-requisitos: entrega completa. Artefatos: zip e `scripts/md5_pacote.csv` atualizado.

## 7. Checks integrados na Apply

- [ ] 7.1 Executar o inventário determinístico aplicável na ordem e diretório descritos abaixo, registrando saídas e artefatos derivados; verificar que as tarefas condicionais só rodam se suas condições forem atendidas e que nenhum treino excede o teto aprovado.
- [ ] 7.2 Executar `openspec validate melhorar-reconstrucoes-mae` na raiz após completar os artefatos e novamente antes da revisão; verificar saída sem erros. Na fase PROPOSE, esta é a única validação autorizada.

## Inventário de checks e comandos existentes

Este inventário foi feito por leitura de configurações, scripts, README e workflows. Nenhum comando abaixo foi executado nesta fase, exceto `openspec validate melhorar-reconstrucoes-mae` ao final. Todos os comandos de implementação pertencem à Apply, depois do gate humano. Diretório para cada comando: raiz do repositório `.`; nunca executar no projeto principal.

As linhas abaixo distinguem comandos obrigatórios dos condicionais, anotam pré-requisitos e resultado esperado, e registram lacunas: os testes específicos do estudo ainda não existem; slides/pacote dependem de implementação e arquivos de resultado; teste do conjunto de teste só ocorre na avaliação final congelada. Esta fase PROPOSE não executa testes, builds, pilotos ou treinos.

1. **Suíte determinística do CI, obrigatória na Apply.** Comandos reais em `.github/workflows/tests.yml`: `uv sync --locked`, depois `uv run pytest -q`. Pré-requisitos: uv disponível e ambiente definido pelo lockfile; o teste de equivalência também requer dependências de desenvolvimento. Resultado esperado: código de saída zero para toda a suíte. Artefato derivado conhecido: `tests/relatorio_equivalencia.txt`, escrito pelo teste de equivalência; preservar qualquer cópia local preexistente e não executar no projeto principal. Cobertura existente: `tests/test_mae.py`, `tests/test_dados.py`, `tests/test_dados_md5.py`, `tests/test_equivalencia_oraculo.py` e `tests/test_montar_zip.py`. Na Apply, testes novos do estudo também entram nesta suíte.
2. **Geração de slides, condicional à mudança dos slides e prevista nesta change.** Comando real: `uv run python scripts/gerar_slides.py`. Pré-requisitos: ambiente sincronizado, arquivos de resultados, LibreOffice (`soffice`) e `pdftoppm`. Resultado esperado: pptx e pdf gerados, limites verificados pelo próprio script e imagens PNG para inspeção. Artefatos derivados: `slides/seminario_masked_modeling.pptx`, `slides/seminario_masked_modeling.pdf` e imagens em `slides/png/`. Obrigatória na Apply se os slides forem atualizados.
3. **Montagem do pacote, condicional à mudança do pacote e prevista nesta change.** Comando real: `uv run python scripts/montar_zip.py`. Pré-requisito: todos os arquivos requeridos presentes. Resultado esperado: zip gravado somente após verificação de presença e md5. Artefatos derivados: `seminario_masked_modeling.zip` e `scripts/md5_pacote.csv`. Obrigatória na Apply se o pacote for atualizado.
4. **Regeneração do notebook, condicional.** Comando real: `uv run python scripts/construir_notebook.py`. Pré-requisito: ambiente Python sincronizado. Resultado esperado: `codigo/notebook.ipynb` regenerado a partir da fonte única. Artefato derivado: `codigo/notebook.ipynb`. Não é requisito desta change; executar somente se o notebook for alterado.
5. **Validação OpenSpec, obrigatória para este change.** Comando real: `openspec validate melhorar-reconstrucoes-mae`. Pré-requisito: CLI OpenSpec disponível. Resultado esperado: saída sem erros; nenhum arquivo derivado. Na PROPOSE, é a única validação executada e ocorre após a escrita de todos os artefatos.
6. **Outros workflows.** Os workflows de revisão automatizada dependem de serviço externo e não definem check determinístico local; ficam fora deste inventário. A geração de dados e os treinos são comandos de produção de artefatos, não checks, e não serão executados nesta fase.

## Checks novos planejados para a Apply

Os seguintes comandos não existem hoje e serão adicionados junto dos testes correspondentes; são distintos do inventário de checks existentes e não foram executados na PROPOSE: `uv run pytest tests/test_estudo_mascaras.py -q`, `uv run pytest tests/test_estudo_baselines.py -q`, `uv run pytest tests/test_estudo_avaliacao.py -q`, `uv run pytest tests/test_estudo_candidatos.py -q`, `uv run pytest tests/test_estudo_checkpoints.py -q`, `uv run pytest tests/test_estudo_orcamento.py -q`, `uv run pytest tests/test_estudo_historico.py -q`, `uv run pytest tests/test_estudo_visual.py -q` e `uv run pytest tests/test_estudo_selecao.py -q`. Diretório para todos: raiz; pré-requisitos: gate aprovado, ambiente sincronizado e implementação correspondente; resultado esperado: testes passam, sem consultar o teste para seleção. Artefatos derivados: relatórios de teste conforme configuração existente, sem alterar os artefatos de resultados anteriores.

## Workflow follow-up

- O layout das figuras pode ser definido na Apply, desde que elas sejam derivadas do histórico e mantenham candidatos, seeds, taxas e controles identificáveis.
- Após revisão da implementação, sincronizar e arquivar a change conforme o fluxo OpenSpec do repositório.

## Tarefas da emenda C0 v2

- [x] 8.1 Registrar a autorização posterior e a separação explícita entre a rodada v2 e os registros v1, sem reclassificação retroativa.
- [x] 8.2 Criar configuração, manifesto e contador v2 independentes, com limite individual de 4 minutos, reserva máxima de 30 minutos e guarda conjunta v1 + v2 de 120 minutos; corrigir o executor com interrupção monotônica e preservar checkpoints melhor e final.
- [x] 8.3 Adicionar testes determinísticos de limiar, precisão do teto, interrupção e isolamento do contador, sem treinos científicos extras.
- [x] 8.4 Executar `uv sync --locked`, a suíte completa `uv run pytest -q` e `openspec validate melhorar-reconstrucoes-mae` antes dos pilotos; preservar falhas sem skip ou enfraquecimento.
- [x] 8.5 Congelar o hash real dos fontes e entradas v2 após os checks e antes do piloto; parar sem treinar se o manifesto não corresponder ao estado executado.
- [x] 8.6 Executar somente os pilotos C0 seed 10 nas duas taxas; ambas excederam 1,25 s, portanto C0 foi registrado inviável e os seis treinos completos foram corretamente omitidos, sem repetição.
- [x] 8.7 Gerar relatório v2 com quadro por seed e taxa, épocas, estados, métricas/checkpoints indisponíveis quando não houve treino, durações dos pilotos, saldos v1 + v2, comparação descritiva em validação e lacunas.
- [x] 8.8 Verificar os hashes congelados e a preservação v1; executar os checks obrigatórios antes dos pilotos e validar OpenSpec após as edições finais. Não alterar slides, pacote, commit, push ou archive.
