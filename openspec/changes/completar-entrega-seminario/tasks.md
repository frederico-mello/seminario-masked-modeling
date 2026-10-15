# Tasks

## 1. Cobertura dos testes de dados

- [x] 1.1 Estender `test_dados_md5.py` para o ramo sem arquivo bruto rodar `verificar_md5` sobre arquivo sintético com md5 divergente e validar a mensagem de erro completa (md5 obtido e esperado); verificação: `uv run pytest tests/test_dados_md5.py` passa sem download e sem pulo silencioso
- [x] 1.2 Alterar `test_dados.py`: quando o arquivo bruto ausentar e o subconjunto existir, verificar contagens por classe, disjunção treino e validação, dtype uint8, formato 32x32x3 e reprodutibilidade da seleção; registrar em comentário o motivo de omitir apenas as asserções que comparar contra o split oficial bruto; verificação: suíte roda sem CIFAR-10 bruto e passa com asserções avaliadas em todos os ramos
- [x] 1.3 Conferir que nenhum ramo de teste de dados retorna sem asserção e que os ramos com arquivo real continuam íntegros; verificação: `uv run pytest -q` verde e revisão dos ramos no código

## 2. Conteúdo didático dos slides

- [x] 2.1 Adicionar em `scripts/gerar_slides.py` a função do diagrama do fluxo do MAE (oito blocos: imagem, patches, máscara, codificador dos visíveis, tokens de máscara, decodificador, reconstrução, perda oculta) com caixas e setas do python-pptx; verificação: slide gerado dentro da área, conferido por `verificar_limites`
- [x] 2.2 Adicionar slide da equação da perda com os termos `x_i`, `M`, `x̂_i`, `d` e a média sobre `M` explicados termo a termo, e slide do pseudocódigo do laço de treinamento com os seis passos do planejamento; verificação: leitura do slide confirmada no png gerado
- [x] 2.3 Converter o panorama em tabela estruturada BERT x MAE x SimMIM (modalidade, alvo previsto, perda, arquitetura) com nota do contraste MSE x L1; verificação: quatro dimensões presentes para os três métodos
- [x] 2.4 Adicionar slides de aplicações das representações e de referências completas (Devlin et al. 2019, He et al. 2022, Xie et al. 2022, Krizhevsky: CIFAR-10) e comprimir blocos existentes para manter o total entre 10 e 12 slides; verificação: contagem final de slides no log do script
- [x] 2.5 Corrigir acentuação no texto visível ("Protocolo e orçamento de treino" e demais ocorrências) e reforçar a delimitação da interpretação: máscara aninhada, semente única 42, teste fixo, sem generalização e sem tratar reconstrução visual como prova; verificação: varredura de texto sem palavra acentuável sem acento e sem U+2014

## 3. README, pré-requisitos e recuperação do pacote

- [x] 3.1 Adicionar no README a seção de pré-requisitos de sistema com LibreOffice headless (conversão pptx para pdf) e pdftoppm (png de inspeção), papel de cada um e forma de conferir a presença; verificação: leitura do README confirma comando conferido
- [x] 3.2 Adicionar no README a instrução de recuperação do pacote: ordem de regeneração (dados, resultados, slides, empacotamento) e comando `uv run python scripts/montar_zip.py` com a conferência de presença e md5; verificação: leitura do README confirma a sequência completa a partir do repositório

## 4. Regeneração dos artefatos derivados e reverificação

- [x] 4.1 Regenerar `slides/seminario_masked_modeling.pptx` e `.pdf` com `uv run python scripts/gerar_slides.py`; verificação: script termina sem erro, contagem de slides e pngs conferidas no log
- [x] 4.2 Reverificar visualmente o png de cada slide alterado (diagrama, equação, pseudocódigo, tabela, referências); verificação: inspeção registrada no encerramento da tarefa
- [x] 4.3 Regenerar `seminario_masked_modeling.zip` com `uv run python scripts/montar_zip.py`; verificação: zip gravado com a lista completa de arquivos obrigatórios e `scripts/md5_pacote.csv` atualizado
- [x] 4.4 Rodar `uv run pytest -q` completo após todas as mudanças; verificação: suíte verde, incluindo o teste do empacotamento contra o zip recém-gravado

## 5. Checks determinísticos antecipados (inventário da fase de proposal; nenhum check foi executado nesta fase)

Inventário dos checks determinísticos existentes no repositório, com comando, diretório de execução, pré-requisitos, resultado esperado e classificação obrigatório ou condicional. Registrados sem execução nesta fase; executam durante a implementação (`apply`), nos grupos indicados acima, e na entrega.

| Check | Comando | Diretório | Pré-requisitos | Resultado esperado | Classificação |
|---|---|---|---|---|---|
| Suíte pytest | `uv run pytest -q` | raiz do repositório | `uv sync --locked` completo (grupo dev: pytest e oráculo) | todos os testes verdes; cobertura dos testes de dados nos dois ramos após 1.1 e 1.2 | obrigatório (local) |
| CI pytest | `uv run pytest -q` em push ou pull_request | máquina do CI (ubuntu-latest) | workflow `.github/workflows/tests.yml`: `uv sync --locked` antes de rodar | todos os testes verdes no ambiente do lockfile | obrigatório (CI) |
| Sincronização travada | `uv sync --locked` | raiz do repositório | `pyproject.toml` e `uv.lock` consistentes | ambiente criado sem resolver versões novas | obrigatório (condição dos demais) |
| Geração de slides | `uv run python scripts/gerar_slides.py` | raiz do repositório | `resultados/metricas.csv` existente; LibreOffice (`/usr/bin/soffice`) e `pdftoppm` no sistema | pptx e pdf gravados, contagem de png igual à de slides, limites verificados | obrigatório (local, depende dos pré-requisitos de sistema; no CI e nos ambientes sem LibreOffice ou pdftoppm é lacuna: o workflow não roda este check, e sem os binários ele falha com erro explícito) |
| Empacotamento | `uv run python scripts/montar_zip.py` | raiz do repositório | todos os arquivos obrigatórios de `OBRIGATORIOS` presentes | zip gravado e `scripts/md5_pacote.csv` regenerado; falha nomeada se faltar arquivo | obrigatório na entrega |
| Testes do empacotamento | `uv run pytest tests/test_montar_zip.py` | raiz do repositório | zip previamente gravado ou montado no próprio teste | conteúdo e md5 conferidos, sem arquivo proibido | condicional (exige zip presente, que o teste monta se necessário) |
| Testes de dados | `uv run pytest tests/test_dados.py tests/test_dados_md5.py` | raiz do repositório | sem CIFAR-10 bruto: cobertura parcial via subconjunto gerado e arquivo sintético; com bruto: cobertura completa | contagens, disjunção, dtype, determinismo e md5 verificados nos ramos possíveis | condicional (cobertura completa exige o arquivo bruto; lacuna de ambiente registrada) |
| Treino e avaliação | `uv run --no-dev jupyter nbconvert --execute --to notebook --inplace codigo/notebook.ipynb` | raiz do repositório | GPU CUDA disponível; CIFAR-10 baixado e verificado | `resultados/` regenerado | condicional: fora da aplicação deste change (nenhum experimento é reexecutado); lacuna aqui: este ambiente não tem GPU nem dados brutos, portanto `resultados/` permanece intocado |

Artefatos gerados que exigem reverificação após a implementação: `slides/seminario_masked_modeling.pptx`, `slides/seminario_masked_modeling.pdf` (regenerados em 4.1 e inspecionados em 4.2) e `seminario_masked_modeling.zip` (regenerado em 4.3 e conferido em 4.4). Lacunas registradas para aprovação: ausência de LibreOffice e pdftoppm fora do ambiente local de slides, ausência de CIFAR-10 bruto no ambiente atual e ausência de GPU; nenhuma é resolvida por este change (o experimento não é reexecutado).