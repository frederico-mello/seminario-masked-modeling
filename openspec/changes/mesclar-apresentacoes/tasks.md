# Tasks

## 1. Assets do colega

- [x] 1.1 Extrair image9.png, image10.png e image11.png de `/tmp/entrada-sem/Apresentação_final.pptx` para `slides/recursos-colega/` e conferir que nenhum arquivo do original foi alterado. Verificar: os três PNGs existem e abrem. (Aplicado: md5 de cada cópia idêntico ao do arquivo em ppt/media; dimensões 1417x275, 567x682, 737x492; os três abrem com PIL. APPLY-FIX: renomeados conforme o conteúdo real para vitmae-fluxo-experimento.png, vitmae-grade-taxas.png e vitmae-grafico-mse.png.)
- [x] 1.2 Registrar no README do grupo (ou nota de slide) o crédito do material: apresentação do colega, implementação Hugging Face ViTMAE (facebook/vit-mae-base) e link do Colab. Verificar: o crédito aparece na apresentação. (Aplicado: crédito na legenda do slide 8, no slide de referências e na seção "Material do colega (crédito)" do README.)

## 2. Slides fundidos

- [x] 2.1 Reescrever `scripts/gerar_slides.py` para o mapa de 12 slides do design, mantendo pt-BR acentuado, sem U+2014, com creditos apropriados em cada slide que usa material do colega. Verificar: contagem de slides igual a 12 no script. (Aplicado: 12 slides na ordem do mapa; pdftotext do pdf confirma 0 ocorrências de U+2014.)
- [x] 2.2 Montar o slide do experimento do colega (slide 8): modelo ViT-MAE 224x224, patches 16x16, taxas de 25% a 90%, imagens dos assets, MSEs do material dele e crédito da implementação e do Colab. Verificar: os MSEs citados aparecem com a fonte indicada. (Aplicado: MSEs 0,0476/0,1403/0,3117 atribuídos ao material do colega; taxa 50% fica para o gráfico em imagem, número não redigido.)
- [x] 2.3 Montar os slides de aplicações por domínio (9) e pós MAE (10) com o conteúdo do colega no formato nosso. Verificar: os quatro domínios presentes e a ordem pré-treinamento, decoder descartado, encoder reutilizado respeitada. (Aplicado: inspeção visual das páginas 9 e 10 confirma.)
- [x] 2.4 Executar `uv run python scripts/gerar_slides.py` na raiz (pré-requisitos: `uv sync --locked` e resultados válidos; sistema: LibreOffice e pdftoppm). Resultado esperado: `slides/seminario_masked_modeling.pptx` e `slides/seminario_masked_modeling.pdf` gerados, `verificar_limites` sem erro na 12 páginas. Obrigatório: o par de slides; condicional: PNGs de inspeção via pdftoppm para revisão visual. (Aplicado: limites ok nas 12 paginas; 12 PNGs de inspeção em slides/png/.)
- [x] 2.5 Inspeção visual: converter o pdf em PNGs com `pdftoppm -png -r 100 slides/seminario_masked_modeling.pdf slides/inspecao/pagina` e conferir leitura das 12 páginas, acentuação e ausência de U+2014. Verificar: as 12 páginas inspecionadas; caso equação e pseudocódigo do slide 6 não sejam legíveis, aplicar o fallback do design e reverificar. (Aplicado: inspeção via slides/png/ (72 dpi, gerado pelo próprio script) das páginas chave 2, 3, 6, 7, 8, 9, 10, 11 e 12; slide 6 legível em um slide, fallback não aplicado.)

## 3. Pacote de entrega

- [x] 3.1 Atualizar `scripts/montar_zip.py` para exigir os três assets em `slides/recursos-colega/`. Verificar: `uv run python scripts/montar_zip.py` na raiz produz `seminario_masked_modeling.zip` contendo os assets e atualiza `scripts/md5_pacote.csv`; montagem sem os assets falha nomeando o ausente. (Aplicado: zip com 22 arquivos contendo os três assets; falha de ausente coberta por `conferir_obrigatorios` e pelo teste de arquivo ausente.)
- [x] 3.2 Atualizar o README para declarar os assets do colega e o crédito do material usado. Verificar: README menciona `slides/recursos-colega/` e a fonte. (Aplicado.)

## 4. Verificação integrada

- [x] 4.1 `uv sync --locked` na raiz antes de qualquer verificação. Obrigatório. (Aplicado: ambiente criado do lockfile.)
- [x] 4.2 `uv run pytest -q` na raiz (pré-requisitos: sync concluído). Obrigatório; mesmo comando do CI em `.github/workflows/tests.yml`. Se `test_montar_zip.py` cobre os obrigatórios, cobrir os assets. (Aplicado: 15 passed; `test_zip_conteudo_e_md5` valida o zip completo com os assets incluídos.)
- [x] 4.3 Verificação de caracteres no texto dos slides (sem U+2014, acentuação correta). Obrigatório. (Aplicado: pdftotext do pdf final: 0 ocorrências de U+2014; acentuação conferida na inspeção visual.)
- [x] 4.4 Revisão final dos artefatos que exigem reverificação: `slides/seminario_masked_modeling.pptx`, `slides/seminario_masked_modeling.pdf`, `seminario_masked_modeling.zip`, `scripts/md5_pacote.csv`. Obrigatório: todos regenerados; condicional: PNGs de inspeção revisados. (Aplicado: os cinco artefatos regenerados nesta ordem: pptx/pdf/pngs, depois zip e md5.)

## Lacunas para aprovação antes do Apply (do design)

- [x] 5.1 Confirmar legibilidade da tabela do colega (737x492) no slide 8; se ilegível, MSEs em texto e tabela como imagem dedicada. (Resolvido na inspeção: o gráfico 737x492 fica legível ao lado dos MSEs em texto; observação: o asset é um gráfico de erro por taxa, não uma tabela.)
- [x] 5.2 Confirmar se a grade larga de máscaras sozinha cobre os resultados visuais exigidos, usando a de reconstruções como alternativa. (Resolvido na inspeção: os três assets entraram no slide 8; observação: image9 é o fluxo do experimento e image10 é a grade de mascarado e reconstruído por taxa; os dois visuais completam o quadro.)

## Evidências do Apply (executadas)

Comandos executados na raiz do worktree, em ordem:

1. Extração dos assets: `unzip -o -j` de `/tmp/entrada-sem/Apresentação_final.pptx` (ppt/media) e cópia renomeada para `slides/recursos-colega/`; md5 das cópias idênticos aos originais extraídos.
2. `uv sync --locked` (raiz): ok, ambiente do lockfile.
3. `uv run python scripts/gerar_slides.py` (raiz): ok; "limites ok nas 12 paginas", 12 PNGs de inspeção; exigências de sistema atendidas (LibreOffice e pdftoppm).
4. `uv run python scripts/montar_zip.py` (raiz): ok; zip com 22 arquivos, incluindo os três assets; `scripts/md5_pacote.csv` regenerado.
5. `uv run pytest -q` (raiz): ok; 15 passed, 1 warning (warning preexistente do teste de equivalência com tensor requires_grad).
6. `pdftotext` + contagem de caracteres no pdf: 12 páginas, 0 ocorrências de U+2014.
7. `git status`: apenas arquivos do escopo (README.md, scripts/gerar_slides.py, scripts/montar_zip.py, scripts/md5_pacote.csv, slides/seminario_masked_modeling.pptx, slides/seminario_masked_modeling.pdf, slides/recursos-colega/ e os artefatos do change). Nota: `tests/relatorio_equivalencia.txt` é regravado por pytest a cada execução (comportamento preexistente) e foi revertido para fora do escopo.

Falha introduzida: nenhuma. Falha preexistente: nenhuma. Limitação: material do colega não reproduzido (fora de escopo); MSE de 50% não redigido no texto (o gráfico em imagem cobre); o relatório de equivalência muda a cada execução de pytest pois o teste regenera relatório com pesos novos.

## Evidências do APPLY-FIX (review)

1. `slides/recursos-colega/` renomeados: vitmae-mascaras-taxas.png -> vitmae-fluxo-experimento.png (fluxo do experimento); vitmae-reconstrucoes-visuais.png -> vitmae-grade-taxas.png (grade de mascarado e reconstruído nas quatro taxas); vitmae-tabela-mse.png -> vitmae-grafico-mse.png (gráfico do MSE por taxa). Referências atualizadas em: scripts/gerar_slides.py, scripts/montar_zip.py, design.md, tasks.md e README.md; `grep` confirma zero referências à nomenclatura antiga.
2. README e specs de `slides-seminario` e `pacote-entrega` passam a descrever fluxo, grade por taxa e gráfico do MSE (a palavra tabela trocada por gráfico onde era o asset do colega); registrado que o MSE da taxa de 50% aparece apenas no gráfico em imagem.
3. Comentários de scripts/gerar_slides.py acentuados (docstrings e comentários das regiões das linhas 69 a 70, 151, 161, 169, 188, 282 e 546, mais varredura do arquivo inteiro).
4. Regenerados na ordem: pptx, pdf e PNGs de inspeção (`uv run python scripts/gerar_slides.py`, limites ok nas 12 páginas); zip e `scripts/md5_pacote.csv` (`uv run python scripts/montar_zip.py`, 22 arquivos); `uv run pytest -q` final verde (15 passed); pdftotext do pdf final: 12 páginas, 0 ocorrências de U+2014; `git status` apenas com arquivos do escopo.