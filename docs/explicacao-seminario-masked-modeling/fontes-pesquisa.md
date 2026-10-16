# Fontes e limites da leitura

## Fontes do repositório

Para afirmar como o projeto funciona, foram consultados os arquivos que descrevem e implementam o comportamento:

- `README.md`: objetivo, instruções, dependências, limites e saídas.
- `pyproject.toml` e `uv.lock`: requisitos e versões do ambiente.
- `codigo/dados.py`, `codigo/mae.py` e `codigo/treino.py`: seleção de imagens, modelo, treino e avaliação.
- `codigo/configuracao_estudo.py` e `codigo/configuracao_estudo_c0_v2.py`: regras congeladas do estudo, das rodadas v1 e v2.
- `codigo/estudo_execucao.py`, `codigo/estudo_execucao_c0_v2.py` e os demais módulos `codigo/estudo_*.py`: orquestração, máscaras, candidatos, orçamento, histórico, seleção, SSIM, avaliação, controles e ficha visual.
- `codigo/notebook.ipynb` e `scripts/construir_notebook.py`: ordem executável do experimento e geração do notebook.
- `scripts/gerar_slides.py`, `scripts/montar_zip.py` e `scripts/gerar_relatorio_fase_b.py`: apresentação, empacotamento e relatórios.
- `resultados/metricas.csv`: números registrados para as duas condições.
- `resultados/estudo-melhorar-reconstrucoes-mae/resumo.json` e `resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/resumo.json`: resumos derivados dos históricos das duas rodadas.
- `openspec/specs/`: requisitos de dados, modelo, experimento, testes, materiais e do estudo de retreinamento.
- `openspec/changes/archive/2026-10-15-melhorar-reconstrucoes-mae/`: especificação e materiais do estudo concluído.
- `tests/`: 17 arquivos de teste, incluindo a comparação com o oráculo.
- `.github/workflows/`: testes automáticos e revisão automática configurados no GitHub.

O arquivo de mapa `graphify-out/graph.json` não estava presente. Por isso, a explicação foi verificada diretamente nas fontes acima. Nenhum grafo foi criado no repositório.

## Pesquisa externa

A pesquisa foi usada para explicar por que certas escolhas são comuns e para conferir os dados de referência. As fontes externas não substituem o README ou o código na descrição do comportamento deste projeto.

1. **He et al., MAE, CVPR 2022.** O artigo descreve um encoder que recebe somente os patches visíveis e um decoder mais leve que reconstrói as partes faltantes. Isso confirma que a assimetria descrita em `codigo/mae.py` segue a ideia central do método. [Artigo no repositório oficial do CVPR](https://openaccess.thecvf.com/content/CVPR2022/html/He_Masked_Autoencoders_Are_Scalable_Vision_Learners_CVPR_2022_paper.html).
2. **CIFAR-10, Universidade de Toronto.** A fonte oficial informa 60.000 imagens coloridas de 32 por 32 pixels, 10 classes, 50.000 imagens de treino, 10.000 de teste e o MD5 usado no código. Isso confirma os tamanhos e a conferência de integridade do projeto. [Página oficial do CIFAR-10](https://cave.cs.toronto.edu/kriz/cifar.html).
3. **Torchvision, conjunto CIFAR10.** A documentação explica os parâmetros de pasta, partição de treino ou teste e download. Isso esclarece o papel de `torchvision.datasets.CIFAR10` em `codigo/dados.py`. [Documentação do conjunto CIFAR10](https://docs.pytorch.org/vision/main/generated/torchvision.datasets.CIFAR10.html).
4. **uv, travamento e sincronização.** A documentação explica que o arquivo de trava registra as dependências resolvidas e que a sincronização instala as versões a partir dele. Isso contextualiza `uv.lock` e os comandos `uv sync`. [Documentação oficial do uv](https://docs.astral.sh/uv/concepts/projects/sync/).
5. **PyTorch, instalação local.** O guia oficial trata a plataforma de cálculo como parte da escolha de instalação e mostra como verificar o acesso à GPU. O índice `cu130` e a exigência exata de CUDA deste projeto vêm do próprio `pyproject.toml`, `uv.lock` e código, não de uma afirmação genérica do guia. [Guia oficial do PyTorch](https://docs.pytorch.org/get-started/locally/).
6. **PyTorch, aleatoriedade e reprodução.** A documentação explica que sementes ajudam a controlar sorteios, mas não garantem resultados idênticos entre versões ou plataformas. Isso contextualiza as três sementes do estudo sem prometer reprodução exata. [Nota oficial sobre aleatoriedade](https://docs.pytorch.org/docs/main/notes/randomness.html).

## O que a pesquisa confirmou

- O encoder do MAE processar somente partes visíveis é uma decisão de arquitetura do método, não apenas um detalhe do código local.
- O arquivo CIFAR-10 conferido pelo projeto corresponde à versão oficial em formato Python e ao MD5 publicado pela Universidade de Toronto.
- `uv.lock` tem a função de fixar a resolução das dependências; não é apenas uma lista informativa.
- A pesquisa confirma que as sementes organizam a aleatoriedade, mas não asseguram resultados idênticos entre versões e plataformas do PyTorch.
- A pesquisa não confirma que o conjunto exato de versões deste projeto funcionará em qualquer computador. A compatibilidade com GPU e CUDA deve seguir as restrições declaradas pelo próprio projeto.

## Leitura marcada como inferência

- *(inferência)* `docs/Planejamento_Masked_Modeling_em_Deep_Learning.md` parece registrar um plano anterior, não a instrução operacional atual: o próprio arquivo diz que é planejamento, enquanto o README, o notebook, os resultados e os slides descrevem uma execução já materializada.
- *(inferência)* O estudo de retreinamento parece ter sido planejado para comparar mudanças de arquitetura ou de perda antes de aplicá-las ao material de entrega, porque exige regras congeladas, orçamento e avaliação separada.

## Limites

O guia descreve o código e os resultados do commit `c063dfd`. Os comandos de treino, geração de slides e montagem do ZIP foram conferidos, mas não foram executados. Os testes do projeto também não foram executados.

Os comandos do estudo de retreinamento não foram executados. Os registros das rodadas v1 e v2 foram lidos como saídas já existentes no commit consultado.

A ausência do grafo significa que não havia um mapa automático das ligações entre funções, classes e arquivos. A arquitetura foi reconstruída pela leitura direta dos módulos e conferida contra o notebook, o README, os testes e as especificações.
