# Proposal

## Why

O seminário "Masked Modeling em Deep Learning" será apresentado em 16/10 e o repositório hoje contém apenas o planejamento, o README em preparação e a configuração do OpenSpec. Sem um notebook reproduzível com o experimento de MAE, resultados gerados por execução real e slides, o grupo não consegue demonstrar a comparação entre máscaras de 50% e 75% nem entregar o pacote final exigido pelo planejamento.

## What Changes

- Criar um ambiente reprodutível com uv: `pyproject.toml` e `uv.lock`, com torch 2.14.1 do índice cu130. Se o wheel cu130 ou a GPU falharem, a execução MUST falhar explicitamente, sem fallback silencioso para CPU.
- Obter o CIFAR-10 via `torchvision.datasets.CIFAR10`, verificando o md5 `c58f30108f718f92721af3b95e74349a`.
- Gerar um subset balanceado por classe com seed 42: 500 imagens de treino, 100 de validação (disjuntas das 5.000 de treino) e 100 de teste por classe. Os índices são salvos em CSV e o subset em `.npz` com `uint8`.
- Implementar um MAE próprio em PyTorch puro, com patches de 8x8 (16 por imagem), encoder ViT de dimensão 128 com 4 blocos e 4 heads, e decoder de dimensão 64 com 2 blocos e 4 heads. A perda é MSE em pixels brutos em [0,1], calculada somente nos patches ocultos.
- Validar a implementação contra a classe `MAE` do vit-pytorch como oráculo de teste, em dependência de desenvolvimento, sem entrar no zip.
- Executar o experimento com máscaras de 50% e 75% usando máscara aninhada (permutação fixa por imagem e semente), mesmo número de épocas, AdamW, e registrar o orçamento de tempo medido em uma época na RTX 3050. A métrica é o MSE nos patches ocultos do teste, com curva de perda de validação e figura de 8 imagens fixas do teste por condição.
- Entregar um notebook autocontido `codigo/notebook.ipynb` que executa do zero com `nbconvert --execute` e gera `resultados/` (`reconstrucoes.png`, `curva_perda.png`, `metricas.csv`). Os checkpoints ficam fora do zip, com hash registrado.
- Produzir de 10 a 12 slides com python-pptx, convertidos para PDF com LibreOffice headless a partir do mesmo script. A capa traz os nomes do grupo e os números só entram após medição.
- Criar um script Python que monta `seminario_masked_modeling.zip` com slides, código, subset, resultados e README, conferindo presença e md5.
- Documentar em `README.md` o ambiente, a execução, a semente, as fontes, a licença MIT do código próprio e as citações.
- Atualizar `.gitignore` para excluir dados brutos do CIFAR, o zip e os checkpoints.

Non-goals:

- Linear probing: fica fora do escopo e aparece como próximo passo nos slides.
- Reutilizar código do repositório `facebookresearch/mae`, que é CC-BY-NC 4.0, está arquivado e fixa `timm==0.3.2`. Ele é citado como referência.
- Implementar BERT ou SimMIM: aparecem apenas como conceito nos slides.
- Fallback de treino em CPU.

## Capabilities

### New Capabilities

- `ambiente-reprodutivel`: ambiente uv com torch cu130, lockfile, falha explícita sem GPU e dependência de desenvolvimento do oráculo.
- `dados-cifar10-subset`: download do CIFAR-10 com verificação de md5, seleção balanceada com seed 42, índices em CSV e subset em `.npz`.
- `mae-modelo`: MAE em PyTorch puro com patchify, máscara aninhada, encoder, decoder leve e perda somente nos ocultos.
- `experimento-mascaras`: treino com máscaras de 50% e 75% por mesmo número de épocas, métricas, curva de perda, figuras e geração dos resultados pelo notebook.
- `validacao-oraculo`: comparação do MAE próprio com a classe `MAE` do vit-pytorch, fora do pacote entregue.
- `slides-seminario`: slides pptx editáveis e PDF gerados por script, seguindo o roteiro de 20 minutos.
- `pacote-entrega`: script de empacotamento, conferência de md5, README, licença, citações e exclusões do repositório.

### Modified Capabilities

Nenhuma. O inventário de specs (`openspec list --specs`) está vazio.

## Impact

- **Arquivos novos:** `pyproject.toml`, `uv.lock`, `codigo/notebook.ipynb`, `dados/cifar10_subset/`, `resultados/`, `slides/`, `scripts/` (empacotamento e validação do oráculo) e o conteúdo do `README.md`.
- **Arquivos alterados:** `.gitignore` e `README.md` (hoje placeholder).
- **Dependências de runtime:** torch 2.14.1 (cu130), torchvision, numpy, matplotlib, nbconvert e python-pptx.
- **Dependências de desenvolvimento:** vit-pytorch 1.24.1 (PyPI, versão a confirmar no lock) e einops, que o vit-pytorch exige.
- **Sistemas externos:** cs.toronto.edu para o download do CIFAR-10, download.pytorch.org para o índice cu130, LibreOffice 24.2.7 em `/usr/bin/soffice` e GPU RTX 3050 6 GB.
- **Riscos:** indisponibilidade do wheel cu130 ou do servidor do CIFAR-10; tempo de treino na RTX 3050 ainda não medido, o que fixa o número de épocas; divergência de renderização do LibreOffice em relação ao PowerPoint.
- **Código de terceiros:** nenhum código do `facebookresearch/mae` é copiado. O código próprio é MIT.
