# Shortlist: tecnologias candidatas do seminário Masked Modeling

Rascunho do agente RESEARCH (OpenSpec, change `seminario-masked-modeling`). Fora do git: não versionar. Nenhum código, `openspec/` ou `openspec/changes` foi alterado. Fontes consultadas em 2026-10-12. Marcação `[INFERENCE]` = não observado em fonte nem no host.

## Escopo e fatos do repositório

- Planejamento (`docs/Planejamento_Masked_Modeling_em_Deep_Learning.md`): seminário de 20 min; MAE como foco técnico; SimMIM como contraste; BERT como exemplo em texto.
- Experimento pedido: CIFAR-10, subset de 5.000 treino e 1.000 teste, patches 8x8, máscaras de 50% e 75%, MSE nos patches ocultos, curva de perda. Entrega: zip com slides, notebook, dados, resultados e README.
- Aritmética: 32/8 = 4 patches por lado, 16 patches no total. Com 50% de máscara restam 8 visíveis; com 75%, restam 4.
- Host (observado, não é fonte web): Python 3.12.3; uv 0.12.19; torch 2.14.1+cpu com `cuda None` (sem treino em GPU); python-pptx 1.0.2; LibreOffice 24.2.7 (libreoffice-core 4:24.2.7-0ubuntu0.24.04.7) em `/usr/bin/soffice`; GPU NVIDIA GeForce RTX 3050 6GB Laptop, driver 595.99.02; sem `.venv` no repo. `.gitignore` cobre `.venv/` e `.ipynb_checkpoints/`, mas não `.openspec-research/`; esta pasta fica fora do git por `.git/info/exclude` (observado com `git check-ignore`).

## Shortlist recomendada

| Ponto | Escolha |
|---|---|
| MAE no notebook | MAE próprio em PyTorch puro, validado contra vit-pytorch |
| CIFAR-10 | `torchvision.datasets.CIFAR10` com md5 publicado na página oficial [1]; índices do subset salvos |
| Slides | python-pptx (pptx editável) + LibreOffice headless (PDF) |
| Ambiente | uv com `pyproject.toml` e `uv.lock`; torch 2.14.1 do índice cu130 |

## 1. Implementação do MAE

| Opção | Versão, licença, maturidade | Encaixe | Tradeoffs | Riscos |
|---|---|---|---|---|
| A. MAE próprio, PyTorch puro, desenho de He et al. (2022) [6] | PyTorch 2.14 [14]; host com torch 2.14.1+cpu (observado). Código próprio; licença a definir pelo grupo. | Alto. Controle de patchify, masking, decoder e loss. Cabe em 6 GB com 5k imagens 32x32 `[INFERENCE]`. | Mais código para escrever e explicar. | Erro de índices no masking e no alvo normalizado. Mitigar com teste de patchify/unpatchify e comparação com a opção C. |
| B. Adaptar facebookresearch/mae [5] | Licença CC-BY-NC 4.0 (README) [5]. 8.361 stars. `archived: true` na API do GitHub, consultada em 2026-10-12 [5]. | Baixo. Pipeline de pré-treino (`main_pretrain.py`, `PRETRAIN.md`) [5]; adaptar para 32x32 exige mudanças grandes. | Referência canônica do paper [6]. | NC restringe uso e redistribuição do código derivado no zip. README indica base em `timm==0.3.2` [5]: pin antigo, sem prova de compatibilidade com torch 2.14. |
| C. vit-pytorch, classe `MAE` (`from vit_pytorch import ViT, MAE`) [7] | MIT [7]. PyPI 1.24.1 (22 jun 2026) [7]; conda-forge 1.25.0 [7]. 25.498 stars no GitHub [7]. | Médio. Oráculo para validar A, ou dependência direta. `MAE(nn.Module)` em `vit_pytorch/mae.py` usa `encoder.to_patch_embedding` e `encoder.pos_embedding` do `ViT` [7]. | Pronto e testado pela comunidade; esconde a lógica de masking. | API pode mudar entre as versões 1.24.1 e 1.25.0; dependência extra só para o notebook. |
| D. Exemplo Keras "Masked image modeling with Autoencoders" [8] | Keras (Apache-2.0, 64.364 stars) [21]. Repo keras-io sob Apache-2.0 [19]. Backend TensorFlow, CIFAR-10, ViT reduzido, batch 32, lr 5e-3, weight decay 1e-4 [8]. | Médio. Bom para hiperparâmetros e linear probing. | Boa referência pedagógica. | Introduz TensorFlow/Keras num ambiente PyTorch. |

Recomendação: A. Masking aleatório por permutação, encoder ViT pequeno (ViT-Tiny como ponto de partida [10]; dimensões a fixar no notebook), decoder leve e MSE só nos patches ocultos. Citar B e He et al. (2022) sem copiar código CC-BY-NC. Usar C apenas como teste local.

SimMIM [9] entra como contraste conceitual no slide, sem implementação. Repositório oficial `microsoft/SimMIM`: licença MIT e 1.048 stars (GitHub, consultado em 2026-10-12) [20]; código de pré-treino documentado para ImageNet-1K [20].

## 2. Obtenção do CIFAR-10

| Opção | Versão, licença, maturidade | Encaixe | Tradeoffs | Riscos |
|---|---|---|---|---|
| A. `torchvision.datasets.CIFAR10(download=True)` [2] | torchvision 0.29.1, BSD-3-Clause [25]. Mesma origem oficial; torchvision verifica md5 ao baixar [2]. | Alto. Uma chamada; verificação automática. | Depende do torchvision, que já vem no stack PyTorch. | Depende de cs.toronto.edu estar no ar. Mitigar com cache local e md5. |
| B. Download manual do site oficial [1] | `https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz`, md5 `c58f30108f718f92721af3b95e74349a` [2]. | Alto, se o md5 bater. | Passos manuais. | A página [1] não declara licença; pede citar Krizhevsky (2009). |
| C. Espelhos UCI [3] ou TFDS [4] | UCI: 60.000 instâncias; licença não declarada na página, remete ao site original [3]. TFDS: biblioteca Apache-2.0 e 4.599 stars no GitHub [22]; licença do dataset não verificada no catálogo; 50k treino, 10k teste, 32x32 [4]. | Médio. Só como contingência. | TFDS puxa TensorFlow `[INFERENCE]`; splits e formato podem diferir. | Divergência entre espelhos. |

Recomendação: A, conferir o md5 publicado na página oficial [1] após o download, e salvar os índices do subset (5.000 de treino, 1.000 de teste) com seed fixa, para o zip ser reproduzível.

## 3. Slides em pptx editável e PDF final

| Opção | Versão, licença, maturidade | Encaixe | Tradeoffs | Riscos |
|---|---|---|---|---|
| A. python-pptx gera o pptx; LibreOffice headless converte para PDF | python-pptx 1.0.2, MIT [11]; 3.555 stars [23]. LibreOffice 24.2.7 instalado no host (observado). | Alto. Ambos já instalados; slides versionáveis como código. | Layout por código, sem editor visual. | Render do LibreOffice pode diferir do PowerPoint (fontes, quebras de linha). Mitigar validando páginas do PDF em PNG. O comando `soffice --headless --convert-to pdf` é o padrão `[INFERENCE]`, não lido em fonte. |
| B. Marp CLI: Markdown para pptx e PDF [12] | MIT [12]. 3.863 stars no GitHub [12]. Versão 4.5.1 no `package.json` da `main` [12]; a página npm consultada mostrava 4.4.0, possivelmente desatualizada [12]. | Médio. Slides em Markdown; `--pptx` e `--pptx-editable` [12]. | Precisa de Node/npx; pptx editável é EXPERIMENTAL e exige navegador e LibreOffice Impress [12]. | Editabilidade não garantida; falha ou sai incompleto com temas complexos [12]; toolchain extra. |
| C. Pandoc: Markdown para pptx com `reference.pptx` [13] | GPL-2.0 ou posterior [13]. Versão 3.12, publicada no GitHub em 29 set 2026 [13]. 46.462 stars [13]. | Médio. Layout herdado de `reference.pptx`. | Controle de layout limitado; ajustar o modelo exige PowerPoint [13]. | PDF continua dependendo de LibreOffice. |

Recomendação: A. Não exige instalação nova, e pptx e PDF saem do mesmo script.

## 4. Ambiente do experimento

O driver 595.99.02 atende o mínimo de 580 para CUDA 13.x [17]. O torch atual é CPU, então treino na GPU exige wheel CUDA. cu128 não é opção: CUDA 12.8 foi deprecado e removido dos binários prebuilt a partir do release 2.12 [15].

| Opção | Versão, licença, maturidade | Encaixe | Tradeoffs | Riscos |
|---|---|---|---|---|
| A. uv com `pyproject.toml` + `uv.lock`; torch via `[[tool.uv.index]]` e `tool.uv.sources` [18] | uv 0.12.19 instalado; Apache-2.0 e 90.645 stars [24]. Wheels cu130 em download.pytorch.org [16]; CUDA 13.0 é a variante estável no PyPI, segundo anúncio de abril de 2026 [15]. | Alto. Lockfile reprodutível; CPU e GPU na mesma config. | Mais arquivos no repo. | `torch 2.14.1+cu130-cp312-cp312-manylinux_2_28_x86_64.whl` consta no índice [16] (sha256 `5359b255...`); wheel não baixado, `uv lock` não executado. |
| B. `python -m venv .venv` + pip com `--index-url https://download.pytorch.org/whl/cu130` | pip padrão; `.venv/` já no `.gitignore`. | Médio. Simples. | Sem lock; versões podem divergir entre máquinas. | Mesmo risco de wheel. |
| C. torch 2.14.1+cpu já instalado no host | Observado no host. | Só desenvolvimento e teste de forma. | Sem treino na GPU. | Tempo em CPU não medido. |

Recomendação: A com cu130. Tempo de treino e pico de VRAM do MAE no RTX 3050 não foram medidos; medir no notebook antes de fechar 5k/1k e o número de épocas.

## Riscos transversais

- Licença do MAE oficial (CC-BY-NC 4.0) e repo arquivado: usar só como referência.
- Pin `timm==0.3.2` do MAE oficial: evitar dependência.
- Versões de Marp e vit-pytorch divergem entre fontes (npm vs `package.json`; PyPI vs conda-forge). Confirmar ao fixar dependências.
- Página do CIFAR-10 não declara licença: citar Krizhevsky (2009).

## Passos de verificação (pendentes, exceto item 1)

1. Wheel: confirmado por leitura de `https://download.pytorch.org/whl/cu130/torch/` (linha 143: `torch-2.14.1+cu130-cp312-cp312-manylinux_2_28_x86_64.whl`). Download e `uv lock` não executados.
2. CIFAR-10: após o download, `md5sum cifar-10-python.tar.gz` deve dar `c58f30108f718f92721af3b95e74349a`.
3. Slides: gerar pptx de teste com python-pptx, converter com `soffice --headless --convert-to pdf` e inspecionar uma página em PNG.

Pendências de fonte: conferir a versão exata de vit-pytorch (PyPI 1.24.1 vs conda-forge 1.25.0) e de Marp (4.5.1 na `main` vs 4.4.0 no npm) ao fixar; a página do CIFAR-10 não declara licença, então citar Krizhevsky (2009).

## Fontes

[1] Krizhevsky, A. CIFAR-10 and CIFAR-100 datasets (página sem licença declarada; pede citação do relatório técnico de 2009). https://cave.cs.toronto.edu/kriz/cifar.html
[2] torchvision, módulo `datasets.cifar` (URL e md5 do tar.gz). https://docs.pytorch.org/docs/1.5.0/_modules/torchvision/datasets/cifar.html ; https://docs.pytorch.org/vision/main/_modules/torchvision/datasets/cifar.html
[3] UCI ML Repository, CIFAR-10. https://archive.ics.uci.edu/dataset/691/cifar
[4] TensorFlow Datasets, catálogo cifar10. https://www.tensorflow.org/datasets/catalog/cifar10
[5] facebookresearch/mae (README: CC-BY-NC 4.0; `archived: true` na API do GitHub, consultada em 2026-10-12; 8.361 stars; README indica base em `timm==0.3.2`). https://github.com/facebookresearch/mae ; https://github.com/facebookresearch/mae/blob/main/main_pretrain.py
[6] He, K. et al. Masked Autoencoders Are Scalable Vision Learners. CVPR 2022. DOI 10.1109/CVPR52688.2022.01553. https://doi.org/10.1109/CVPR52688.2022.01553
[7] lucidrains/vit-pytorch (MIT; 25.498 stars; `from vit_pytorch import ViT, MAE` no README). https://github.com/lucidrains/vit-pytorch ; PyPI: https://pypi.org/project/vit-pytorch/ ; conda-forge: https://anaconda.org/conda-forge/vit-pytorch
[8] Keras, exemplo "Masked image modeling with Autoencoders" (última modificação em 2026-02-15; backend TensorFlow; batch 32, lr 5e-3, weight decay 1e-4). https://keras.io/examples/vision/masked_image_modeling/
[9] Xie, Z. et al. SimMIM: A Simple Framework for Masked Image Modeling. CVPR 2022, p. 9653-9663. https://openaccess.thecvf.com/content/CVPR2022/html/Xie_SimMIM_A_Simple_Framework_for_Masked_Image_Modeling_CVPR_2022_paper.html
[10] A Closer Look at Self-supervised Lightweight Vision Transformers (MAE-Tiny, 400 épocas). https://arxiv.org/pdf/2205.14443
[11] python-pptx 1.0.2 (licença MIT). https://pypi.org/project/python-pptx/
[12] marp-team/marp-cli (MIT; README: `--pptx`, `--pptx-editable` EXPERIMENTAL; `package.json` com 4.5.1). https://github.com/marp-team/marp-cli ; https://github.com/marp-team/marp-cli/blob/main/package.json ; npm: https://www.npmjs.com/package/@marp-team/marp-cli
[13] Pandoc User's Guide (saída pptx e `reference.pptx`). https://pandoc.org/MANUAL.html ; licença GPL-2.0: https://github.com/jgm/pandoc ; release 3.12: https://github.com/jgm/pandoc/releases/tag/3.12
[14] PyTorch 2.14 Release Blog (2026-09-17). https://pytorch.org/blog/pytorch-2-14-release-blog/
[15] PyTorch dev-discuss: CUDA 13.2 introduzido e CUDA 12.8 deprecado (release 2.12, abr 2026). https://dev-discuss.pytorch.org/t/introducing-cuda-13-2-and-deprecating-cuda-12-8-release-2-12/3337
[16] Índice de wheels cu130. https://download.pytorch.org/whl/cu130
[17] NVIDIA CUDA Toolkit 13.0 Update 3, release notes (13.x requer driver >= 580). https://docs.nvidia.com/cuda/archive/13.0.3/cuda-toolkit-release-notes/index.html
[18] uv, docs de índices (`[[tool.uv.index]]`, `tool.uv.sources`). https://github.com/astral-sh/uv/blob/main/docs/concepts/indexes.md
[19] keras-team/keras-io, arquivo LICENSE (Apache-2.0). https://github.com/keras-team/keras-io/blob/master/LICENSE
[20] microsoft/SimMIM (MIT; 1.048 stars; README com pré-treino ImageNet-1K). https://github.com/microsoft/SimMIM
[21] keras-team/keras (Apache-2.0; 64.364 stars; GitHub API consultada em 2026-10-12). https://github.com/keras-team/keras
[22] tensorflow/datasets (Apache-2.0; 4.599 stars; GitHub API consultada em 2026-10-12). https://github.com/tensorflow/datasets
[23] scanny/python-pptx (MIT; 3.555 stars; GitHub API consultada em 2026-10-12). https://github.com/scanny/python-pptx
[24] astral-sh/uv (Apache-2.0; 90.645 stars; GitHub API consultada em 2026-10-12). https://github.com/astral-sh/uv
[25] pytorch/vision (BSD-3-Clause; 17.954 stars; torchvision 0.29.1 no PyPI). https://github.com/pytorch/vision ; https://pypi.org/project/torchvision/
