# Integridade do historico e verificacao final

Data: 2026-10-15. Diretorio: raiz do repositorio.

## Diagnostico do whitespace

O `git diff --cached --check` inicial apontou somente os retornos CR antes das quebras de linha de `resultados/estudo-melhorar-reconstrucoes-mae/historico.csv`. O arquivo segue CRLF em todos os registros e pode ser lido pelo parser CSV RFC 4180. Nao ha LF ou CR isolado, nem espacos ou tabs no fim das linhas.

`.gitattributes` declara `whitespace=cr-at-eol` somente para esse CSV. Os demais checks de whitespace continuam ativos. Os bytes nao foram normalizados.

## Integridade do CSV

- Tamanho: 430149 bytes; 2445 registros, 18 campos por registro.
- SHA-256 antes e depois: `6d54737fa3e977d906f56a3e4d5fedb2f3b12b94825cfbdf7985512bda6ebdf7`.
- Teste `test_historico_v1_preserva_bytes_e_crlf_rfc4180`: confere hash, CRLF, ausencia de whitespace final e leitura dos registros.
- Snapshot de 17 arquivos de resultados e fonte historica comparado antes e depois: nenhuma divergencia.
- `tests/relatorio_equivalencia.txt` restaurado byte a byte; SHA-256: `6300b890889bd0ae20a68ca121598316503a43889b954173cbf5f23ee0be9921`.

## Validacoes finais

| Comando | Resultado |
|---|---|
| `uv sync --locked` | exit 0; 140 pacotes conferidos |
| `uv run pytest -q` | exit 0; 114 testes passaram; 1 warning de execucao preservado |
| `openspec validate melhorar-reconstrucoes-mae` | change valida |
| `git diff --cached --check` | exit 0 com regra de CRLF restrita ao CSV historico |
| `git diff --check` | exit 0 |
| construcao do notebook, duas vezes | exit 0; SHA-256 estavel: `dc734fc6a1a57ade748cd1f0475c78bf0cff67d4c118acda0d118a1550ef3604` |
| geracao dos slides, duas vezes | exit 0; 13 paginas; PPTX e PDF com hashes estaveis |
| montagem do pacote, duas vezes | exit 0; 65 arquivos; ZIP com hash estavel |

Hashes finais: PPTX `761ac72ebef7448a0fbd9017d35f93a224d89bd8e7b369e025584db78da9b620`; PDF `9d95b3be24fbb91cc7b9046b64821d9890304331d2f7c7c531d664be2f23dbc7`; ZIP `91cb2700d5e3d146923aa55afb7cae90ed851e55f75f27179d4a17e11ab5618a`; lista MD5 `1f0fdf52aded64c6dc9d5ef4197feb6e4267eb054f5e65847d02f8ee8fa35436`.

## Limites do estudo

O objetivo de melhoria visual nao foi atingido. A avaliacao visual aberta tem um avaliador humano; o estudo e exploratorio, sem confirmacao independente e sem alegacao de superioridade visual. C0 nao foi treinado e C3 nao foi executado. A retificacao separa controles de validacao e teste. Nenhuma celula do notebook, treino ou inferencia foi executada nesta verificacao.
