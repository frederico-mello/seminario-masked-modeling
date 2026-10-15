# Evidência da correção dirigida do notebook

Data: 2026-10-15. Diretório de execução: raiz do repositório (`.`).

## Achados corrigidos

- Os dez IDs Markdown de `HEAD` são transferidos por título estrutural único. A geração falha se faltar uma âncora ou se ela estiver duplicada.
- O prefixo `/tmp/ipykernel_.../arquivo.py:linha:` foi removido da saída histórica. O tipo e a mensagem de `UserWarning` foram mantidos integralmente.
- As saídas científicas das células de código com fonte idêntica foram mantidas. Nenhuma célula do notebook, treino, inferência ou avaliação científica foi executada.

## Verificações

| Comando | Resultado |
|---|---|
| `uv sync --locked` | exit 0; 140 pacotes conferidos |
| `uv run pytest tests/test_construir_notebook.py -q` | exit 0; 2 testes passaram |
| `uv run pytest -q` | exit 0; 113 testes passaram, 1 warning de execução; 4,05 s |
| `uv run python scripts/construir_notebook.py` duas vezes | exit 0 nas duas; SHA-256 idêntico: `dc734fc6a1a57ade748cd1f0475c78bf0cff67d4c118acda0d118a1550ef3604` |
| `uv run python scripts/gerar_slides.py` duas vezes | exit 0 nas duas; 13 páginas; hashes idênticos |
| `uv run python scripts/montar_zip.py` duas vezes | exit 0 nas duas; 65 arquivos; hashes idênticos |
| `openspec validate melhorar-reconstrucoes-mae` | change válida |
| `git diff --check` | exit 0 |

Hashes finais SHA-256:

- `slides/seminario_masked_modeling.pptx`: `761ac72ebef7448a0fbd9017d35f93a224d89bd8e7b369e025584db78da9b620`
- `slides/seminario_masked_modeling.pdf`: `9d95b3be24fbb91cc7b9046b64821d9890304331d2f7c7c531d664be2f23dbc7`
- `seminario_masked_modeling.zip`: `91cb2700d5e3d146923aa55afb7cae90ed851e55f75f27179d4a17e11ab5618a`
- `scripts/md5_pacote.csv`: `1f0fdf52aded64c6dc9d5ef4197feb6e4267eb054f5e65847d02f8ee8fa35436`

O teste do pacote validou a lista e os MD5 dos 65 arquivos. A suíte confirmou os bytes empacotados contra as origens.

O backup de `tests/relatorio_equivalencia.txt` foi restaurado após o pytest e comparado byte a byte. SHA-256 antes e depois: `6300b890889bd0ae20a68ca121598316503a43889b954173cbf5f23ee0be9921`.

Snapshots SHA-256 anteriores e posteriores foram comparados sem divergências para `resultados/estudo-melhorar-reconstrucoes-mae/`, `resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/` e `openspec/changes/melhorar-reconstrucoes-mae/fontes-historicas/`.

## Stage

A lista de stage está em `verificacao-correcao/stage-proposto.txt`. Ela inclui a regressão nova e esta evidência, além dos caminhos explicitamente propostos para a change. `tests/relatorio_equivalencia.txt` e `logs/` ficam fora. Nenhum commit, push, PR ou publicação foi realizado.

O stage final contém exatamente os 100 caminhos da lista, comparados após ordenação. O relatório de equivalência continua fora do stage e seu backup foi comparado byte a byte. O check adicional `git diff --cached --check` sinalizou finais de linha CRLF no CSV histórico v1. Os bytes e o hash do CSV foram preservados conforme o requisito; o comando solicitado `git diff --check` passou.
