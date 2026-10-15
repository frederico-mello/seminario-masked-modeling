README

# Seminário: Masked Modeling em Deep Learning

Aprendizagem de representações pela reconstrução de conteúdo oculto: BERT, MAE e SimMIM, com um experimento didático de Masked Autoencoder no CIFAR-10.

**Grupo:** Frederico Maciel de Mello e Luan Pedro de Souza Silva
**Data de apresentação:** 16/10
**Licença do código próprio:** MIT (arquivo `LICENSE`)

## O experimento

Implementação própria de um MAE (no estilo de He et al. (2022)) em PyTorch puro:
imagem 32x32x3 em 16 patches de 8x8, encoder que vê somente os patches visíveis
(dim 128, 4 blocos, 4 heads), decoder leve (dim 64, 2 blocos, 4 heads) e perda
MSE somente nos patches ocultos, em pixels brutos em [0,1]. Duas condições de
mascaramento (50% e 75%) com mesma semente (42), máscara aninhada (permutação
fixa por imagem) e mesmo orçamento de treino (épocas, batch e lr) com AdamW.

A implementação é validada contra a classe `MAE` do `vit-pytorch` (1.24.1) como
oráculo de teste: pesos e máscara idênticos, formas, perda e reconstrução
comparados com tolerâncias explícitas. O relatório fica em
`tests/relatorio_equivalencia.txt`. O oráculo é dependência de desenvolvimento e
não entra no pacote de entrega.

Linear probing está fora do escopo deste trabalho: aparece como próximo passo.

## Estudo de retreinamento (melhorar-reconstrucoes-mae)

O registro abaixo descreve a rodada v1. A avaliação visual aberta posterior de
um único avaliador humano considerou os resultados ruins nas duas taxas; o
objetivo visual não foi atingido. Não houve avaliação cega nem notas individuais.
As [notas finais](openspec/changes/melhorar-reconstrucoes-mae/notas-finais.md)
registram também a ausência de treino completo C0 v2 e uma inconsistência
de origem dos controles no relatório v2 original, corrigida externamente na
[retificação de validação](openspec/changes/melhorar-reconstrucoes-mae/retificacao-validacao.md).
A retificação usa somente eventos com `estado=validacao` do histórico existente,
com dados individuais por seed e hashes de proveniência; o original permanece intacto.
C1 a 75% tem SSIM mediano 0,362957 contra RGB de validação 0,355630;
C2 a 50% tem 0,365044 contra RGB de validação 0,355596. Isso é descritivo,
sem superioridade universal, confirmação independente ou ganho demonstrado contra C0.

Estudo complementar, com protocolos congelados antes da execução (versão das
regras com hash em
`resultados/estudo-melhorar-reconstrucoes-mae/manifesto.json`): C0 (MAE direto
retreinado), C1 (decoder de dimensão 128 e três blocos) e C2 (perda MSE mais
0,1 L1), três seeds de treino (10, 20, 30), duas taxas (50% e 75%), máscara
determinística por identidade, época e seed, régua fixa de validação e contadores
cumulativos de orçamento (90 minutos principais mais 30 de reserva, jamais
excedidos). Candidatos extras e o residual C3 só existem quando o critério
frozen autoriza; no resultado desta execução, o piloto do C0 excedeu o limiar
de 1,2 s por época e o candidato não foi treinado: nenhum vencedor foi
declarado (ausência de melhoria demonstrada pela regra congelada), o resultado
por candidato é exploratório e o conjunto de teste só foi consultado uma vez,
depois do congelamento da seleção.

Artefatos do estudo em `resultados/estudo-melhorar-reconstrucoes-mae/`:

- `historico.csv`: registro append-only por época e evento (execução,
  candidato, seed, taxa, perdas, SSIM, tempo, hashes e versões).
- `contador.jsonl`: contador cumulativo de orçamento (teto 120 minutos,
  principal e reserva separados).
- `resumo.json`: resumo derivado do histórico (medias e medianas por seed,
  controles, decisão de C3, seleção, avaliação final).
- `figuras/`: curvas de validação, melhores de validação e avaliação final.
- `ficha-visual/`: reconstruções dos oito IDs de inspeção nas duas taxas
  (`ficha_50.png`, `ficha_75.png`), ficha preenchível sem cegamento efetivo
  (`ficha_visual.json`) e mapeamento de rótulos (`ficha-rotulos.json`); o
  registro original não contém notas; o julgamento posterior está nas notas finais.
- `checkpoints/`: cópias imutáveis do melhor e do final por execução, com
  SHA-256 e época registrados no histórico; ficam de fora do zip.

O relatório completo da fase B fica em
`openspec/changes/melhorar-reconstrucoes-mae/relatorio-fase-b.md` (dentro do
pacote no mesmo caminho, além do alias `relatorio-fase-b.md`). Os resultados anteriores do notebook
(`metricas.csv`, `curva_perda.png`, `reconstrucoes.png` e seus checkpoints)
continuam intactos e identificáveis, com protocolo próprio.

## Como executar

### Se você recebeu o zip (seminario_masked_modeling.zip)

O pacote já traz o código, o subset, os resultados, os slides e o `uv.lock`
(versões travadas). Instale sem o grupo de desenvolvimento (o oráculo
vit-pytorch só serve aos testes):

```sh
uv sync --no-dev                        # ambiente a partir do lockfile, vit-pytorch não é instalado
uv run --no-dev python codigo/preparar_dados.py --seed 42   # baixa CIFAR-10 (md5 verificado) e cria o subset
uv run --no-dev jupyter nbconvert --execute --to notebook --inplace codigo/notebook.ipynb
                                        # treina, avalia e regenera resultados/
uv run --no-dev python scripts/gerar_slides.py   # regenera pptx, pdf e png dos slides
uv run --no-dev python scripts/montar_zip.py     # remonta o zip com conferência de md5
```

A execução do notebook acima é uma reprodução científica opcional e refaz treino
e teste do experimento original; não é necessária para ler os resultados ou
montar a entrega. A correção documental foi feita sem executar células científicas.
O código atual difere dos fontes congelados: o gate v2 permanece ativo e recusa
reexecutar o estudo com esses hashes. Não recongelar os resultados existentes.
Para somente consolidar registros existentes, use
`uv run --no-dev python scripts/retificar_validacao.py`, sem treino ou inferência.

Todo comando do destinatário usa `--no-dev`: o `uv run` sem a opção
 ressincronizaria o ambiente e reinstalaria o grupo dev (vit-pytorch e pytest).

### No repositório (desenvolvimento)

```sh
uv sync                                  # ambiente completo, com grupo dev (vit-pytorch e pytest)
uv run pytest                            # testes unitários e equivalência com o oráculo (fora do zip)
uv run python scripts/construir_notebook.py  # fonte única regenera codigo/notebook.ipynb
```

O notebook é autocontido: baixa, verifica, cria o subset, mede o orçamento de
treino (previsto versus medido), treina as duas condições, avalia o teste e
grava `resultados/`. Sem GPU CUDA o notebook falha com erro explícito: não há
fallback silencioso para CPU.

## Pré-requisitos de sistema

Para regenerar os slides (pptx para pdf e png de inspeção) são necessários dois
programas fora do ambiente Python:

- **LibreOffice** (`soffice`): converte o `.pptx` gerado pelo script em `.pdf`,
  em modo headless, pelo próprio `scripts/gerar_slides.py`.
- **pdftoppm** (poppler-utils): converte o `.pdf` em um png por página para
  inspeção visual, também chamado pelo script de slides.

Forma de conferir a presença de cada um no sistema:

```sh
command -v soffice                  # caminho esperado: /usr/bin/soffice
command -v pdftoppm                 # conversão de pdf em png
```

Sem LibreOffice ou sem pdftoppm, o script de slides falha com erro explícito
(`check=True` no subprocesso): nesse caso, instale o programa ausente e rode
novamente. O pdf e os pngs são saídas derivadas e regeneráveis.

## Recuperando o pacote a partir do repositório

O zip de entrega (`seminario_masked_modeling.zip`) não é versionado no git. Se
o pacote não chegar ao destinatário ou se algum arquivo ficar desatualizado,
regenere tudo na ordem abaixo, a partir da raiz do repositório:

```sh
uv sync                                     # ambiente completo (com grupo dev)
uv run python codigo/preparar_dados.py --seed 42   # 1. dados: baixa CIFAR-10 (md5 verificado) e cria o subset
uv run jupyter nbconvert --execute --to notebook --inplace codigo/notebook.ipynb
                                            # 2. resultados: treina e grava resultados/ (exige GPU CUDA)
uv run python scripts/gerar_slides.py       # 3. slides: regenera pptx, pdf e png
uv run python scripts/montar_zip.py         # 4. empacotamento: grava o zip
```

O script de empacotamento confere a presença de cada arquivo obrigatório e
falha nomeando o que falta antes de gravar o zip; ao gravar, regenera
`scripts/md5_pacote.csv` com o md5 de cada arquivo do pacote. Conferência
posterior: `uv run pytest tests/test_montar_zip.py`.

## Arquivos

- [Guia explicativo do repositório](docs/explicacao-seminario-masked-modeling/README.md): visão simples da estrutura, dos dados, do fluxo do experimento e das entregas.
- `pyproject.toml`, `uv.lock`: ambiente reprodutível (torch cu130, dev: vit-pytorch).
- `codigo/mae.py`: implementação do MAE (patchify, máscara aninhada, encoder, decoder, perda).
- `codigo/dados.py`: download do CIFAR-10 com verificação de md5 e subset seed 42.
- `codigo/treino.py`: exigência de CUDA, treino AdamW, medição de época e avaliação.
- `codigo/notebook.ipynb`: notebook autocontido do experimento.
- `scripts/construir_notebook.py`: fonte única do notebook.
- `scripts/gerar_slides.py`: gera `slides/*.pptx` e `slides/*.pdf` (mesmo script).
- `scripts/montar_zip.py`: monta o zip conferindo presença e md5 de cada arquivo.
- `tests/`: testes de unidade, de dados e do oráculo (fora do zip).
- `dados/cifar10_raw/`: CIFAR-10 bruto (fora do git, verificado por md5).
- `dados/cifar10_subset/`: subset do experimento (`indices.csv` e `subset.npz`).
- `checkpoints/`: pesos das duas condições (fora do zip, SHA-256 em `metricas.csv`).
- `resultados/`: saídas geradas pelo notebook (abaixo).
- `slides/recursos-complementares/`: três PNGs do experimento complementar do grupo,
  extraídos da apresentação complementar do grupo (arquivo
  `Apresentação_final.pptx`) e usados no slide 8 com crédito:
  `vitmae-fluxo-experimento.png` (fluxo do experimento em 6 etapas),
  `vitmae-grade-taxas.png` (grade de mascarado e reconstruído nas taxas de
  25% a 90%) e `vitmae-grafico-mse.png` (gráfico do MSE por taxa).

## Experimento complementar (crédito)

O experimento complementar apresentado no slide 8 vem do material complementar
do grupo e não foi reproduzido por este repositório: número e visuais são
creditados à implementação pública. A implementação pública utilizada no experimento complementar
foi a ViTMAE do projeto Transformers da Hugging Face (modelo
`facebook/vit-mae-base`, Meta AI). O código do experimento complementar está no
Colab <https://colab.research.google.com/drive/11BkUg8lzF079vWErYh5plimEVcF16gXN>.
O material complementar traz o fluxo do experimento, a grade de máscaras e
reconstruções por taxa e o gráfico do MSE por taxa. Os MSEs citados
(0,0476 com 25%; 0,1403 com 75%; 0,3117 com 90%) são os documentados no
texto do material complementar; o MSE da taxa de 50% aparece apenas no gráfico em imagem,
versado em `slides/recursos-complementares/`, que cobre o quadro completo.

## Conteúdo de `resultados/`

- `metricas.csv`: uma linha por condição (`mascara_50`, `mascara_75`) com o MSE
  de teste nos patches ocultos, o orçamento (épocas, batch, lr), o tempo medido
  por época na GPU, o orçamento previsto em minutos, o SHA-256 do checkpoint e
  as versões de Python, PyTorch, CUDA e driver.
- `curva_perda.png`: perda de validação (MSE nos ocultos) por época, as duas
  condições no mesmo eixo.
- `reconstrucoes.png`: 8 imagens fixas do teste (seed 42); para cada condição,
  original, versão mascarada e reconstrução.
- `slides/*.pptx` e `slides/*.pdf` (e `slides/*.png` para inspeção visual, fora
  do git): apresentação de 13 slides; números do experimento próprio lidos de
  `metricas.csv`, números do experimento complementar creditados à implementação pública
  e números do estudo de retreinamento lidos de
  `resultados/estudo-melhorar-reconstrucoes-mae/resumo.json` (slide 9).

O zip de entrega (`seminario_masked_modeling.zip`) inclui ainda `uv.lock`, os
geradores (`scripts/gerar_slides.py`, `scripts/montar_zip.py`,
`scripts/construir_notebook.py`), o histórico, o resumo, as figuras e a ficha
visual do estudo (`resultados/estudo-melhorar-reconstrucoes-mae/`) e o
relatório da fase B, para que a sequência documentada funcione sem nada fora
do pacote; testes, o oráculo e os checkpoints ficam de fora.

## Dados e referências

- CIFAR-10: Krizhevsky (2009), download de cs.toronto.edu, md5
  `c58f30108f718f92721af3b95e74349a` verificado antes do uso.
- He et al. (2022). Masked Autoencoders Are Scalable Vision Learners. [link](https://arxiv.org/abs/2111.06377)
- Repositório oficial: [github.com/facebookresearch/mae](https://github.com/facebookresearch/mae) (licença
  CC-BY-NC 4.0, não reutilizado: referência apenas).
- Oráculo de teste: [github.com/lucidrains/vit-pytorch](https://github.com/lucidrains/vit-pytorch) (MIT), versão 1.24.1,
  dependência de desenvolvimento.