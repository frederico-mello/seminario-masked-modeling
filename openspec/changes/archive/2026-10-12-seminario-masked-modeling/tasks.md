# Tasks

## 1. Ambiente e dados

- [x] 1.1 Criar `pyproject.toml` gerenciado por uv, com índice cu130 para torch e grupo `dev` contendo `vit-pytorch==1.24.1`; verificar com `uv sync` e `uv run python -c "import torch; print(torch.version.cuda)"` mostrando 13.0
- [x] 1.2 Implementar download do CIFAR-10 via torchvision com verificação de md5 `c58f30108f718f92721af3b95e74349a`; verificar que um arquivo com md5 errado faz o script terminar com erro e não gera subset
- [x] 1.3 Gerar subset balanceado com seed 42 (500 treino, 100 validação, 100 teste por classe) em CSV de índices e `.npz` uint8; verificar contagens por classe, validação disjunta do treino e teste vindo do split oficial de teste
- [x] 1.4 Atualizar `.gitignore` para dados brutos, zip e checkpoints; verificar com `git status` que esses arquivos não aparecem como novos

## 2. Modelo MAE próprio

- [x] 2.1 Implementar patchify e máscara aninhada por permutação fixa com seed 42; verificar que os 8 índices ocultos a 50% estão contidos nos 12 ocultos a 75% e que duas gerações com seed 42 são idênticas
- [x] 2.2 Implementar encoder (dim 128, 4 blocos, 4 heads, só patches visíveis) e decoder (dim 64, 2 blocos, 4 heads, 192 valores por patch); verificar formas de saída com 8 e 4 tokens visíveis
- [x] 2.3 Implementar perda MSE somente nos patches ocultos, em pixels [0,1] sem normalização; verificar com tensor de exemplo que patches visíveis não alteram o valor
- [x] 2.4 Implementar teste de equivalência com vit-pytorch em `tests/` (fora do zip), com pesos e máscara iguais e tolerância declarada; verificar com `uv run pytest` passando e relatório de diferenças salvo

## 3. Medição e treino

- [x] 3.1 Medir o tempo de uma época real na RTX 3050 e registrar orçamento previsto versus medido no notebook; verificar que o registro contém os dois valores
- [x] 3.2 Definir épocas, batch size e learning rate a partir da medição, com AdamW; verificar que os mesmos valores são usados para 50% e 75%
- [x] 3.3 Garantir falha explícita sem GPU CUDA ou sem wheel cu130, sem fallback para CPU; verificar com `CUDA_VISIBLE_DEVICES=""` que o treino termina com erro antes de iniciar
- [x] 3.4 Treinar as condições de 50% e 75% com o mesmo orçamento e salvar checkpoints fora do zip com SHA-256; verificar que os hashes conferem com os arquivos gerados

## 4. Notebook e resultados

- [x] 4.1 Montar notebook autocontido que baixa, verifica, cria o subset, treina, avalia e gera figuras; verificar com `jupyter nbconvert --execute` rodando do zero sem erro
- [x] 4.2 Gerar `resultados/metricas.csv` (MSE de teste nos ocultos por condição, hashes e versões de Python, PyTorch, CUDA e driver), `curva_perda.png` e `reconstrucoes.png`; verificar que os arquivos existem e que a figura tem 8 imagens fixas com original, mascarada e reconstrução por condição
- [x] 4.3 Documentar no README o comando de execução do notebook e o significado de cada arquivo em `resultados/`; verificar que o comando documentado roda como escrito

## 5. Slides

- [x] 5.1 Escrever script python-pptx com 10 a 12 slides, capa com "Frederico Maciel de Mello e Luan Pedro de Souza Silva" e data 16/10, e números lidos de `metricas.csv`; verificar contagem de slides e ausência de U+2014
- [x] 5.2 Converter o pptx para pdf com LibreOffice headless pelo mesmo script e gerar PNG de cada página; verificar visualmente que nenhum texto sai da área do slide

## 6. Pacote de entrega

- [x] 6.1 Adicionar arquivo LICENSE MIT ao código próprio e identificar autoria e escopo (linear probing fora do escopo, referências a He et al. (2022) e ao repositório oficial) no README; verificar leitura do README contra a spec pacote-entrega
- [x] 6.2 Implementar script Python que monta `seminario_masked_modeling.zip` com slides, código, dados do subset, resultados e README, conferindo presença e md5 de cada arquivo obrigatório; verificar que um arquivo removido faz a montagem falhar sem gravar zip
- [x] 6.3 Verificar o conteúdo do zip gerado: sem dados brutos, sem checkpoints, sem arquivos que importem vit-pytorch; verificar listando o zip e conferindo a lista de md5 registrada

## 7. Integração final

- [x] 7.1 Executar o pipeline completo do zero (ambiente, dados, notebook, slides, zip) em uma cópia limpa do repositório; verificar que todos os artefatos são gerados sem intervenção manual
- [x] 7.2 Verificar que todos os arquivos do change e do repositório são pt-BR e não contêm U+2014; verificar com busca do caractere sem ocorrências
