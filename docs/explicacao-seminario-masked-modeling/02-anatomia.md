# 02. Anatomia do repositório

O fluxo lembra uma oficina. Primeiro, os dados passam por seleção. Depois, o notebook conduz o teste e os scripts preparam os materiais finais. Cada etapa tem arquivos próprios.

## Mapa do fluxo

O diagrama mostra o caminho principal, desde o conjunto de imagens até o pacote de entrega. A parte de treino usa o notebook e o modelo descritos nos capítulos seguintes.

```mermaid
flowchart LR
    DATA["CIFAR-10 original"] --> SUB["Subset balanceado"]
    SUB --> NB["Notebook do experimento"]
    NB --> TRAIN["Treino, ocultar 8 ou 12 patches"]
    TRAIN --> OUT["Métricas e figuras"]
    OUT --> SLIDES["Slides PDF e PPTX"]
    SLIDES --> ZIP["Pacote ZIP"]
```

## Mapa de pastas

| Caminho | Papel em linguagem simples |
|---|---|
| `README.md` | Manual principal: explica o experimento, a instalação e os comandos. |
| `pyproject.toml` e `uv.lock` | Receita do ambiente Python e versões de programas usados. |
| `codigo/notebook.ipynb` | Roteiro executável do experimento, do preparo dos dados até as figuras. |
| `codigo/mae.py` | Modelo que separa a imagem em partes e prevê as partes escondidas. |
| `codigo/dados.py` | Baixa e verifica o CIFAR-10, escolhe as imagens e salva o subconjunto. |
| `codigo/treino.py` | Confere a GPU, treina o modelo e calcula a medida no teste. |
| `scripts/construir_notebook.py` | Fonte única usada para gerar o notebook executável. |
| `scripts/gerar_slides.py` | Produz os arquivos editáveis e de leitura da apresentação. |
| `scripts/montar_zip.py` | Confere os arquivos obrigatórios e monta o pacote compactado. |
| `dados/cifar10_subset/` | Índices das imagens escolhidas e imagens salvas em formato compacto. |
| `resultados/` | Medidas e figuras do experimento registrado no repositório. |
| `slides/` | Apresentação e imagens complementares usadas nos slides. |
| `docs/` | Planejamento do seminário em formato DOCX e Markdown. |
| `tests/` | Verificações automáticas do modelo, dos dados, do pacote e da comparação com a referência. |
| `openspec/` | Regras detalhadas sobre o comportamento esperado do experimento e dos materiais. |
| `.github/workflows/` | Configuração para executar testes automaticamente no GitHub. |

## Peças com analogia

- **A prancheta:** `codigo/notebook.ipynb`, reúne as etapas em ordem e mostra os resultados.
- **A recepção e a balança:** `codigo/dados.py`, obtém as imagens e confere o arquivo antes de usá-lo.
- **O reconstrutor:** `codigo/mae.py`, lê as partes visíveis e prevê os pixels faltantes.
- **O treinador:** `codigo/treino.py`, ajusta o modelo e mede o erro ao longo do processo.
- **A pasta de evidências:** `resultados/`, guarda os números e as figuras produzidas.
- **A equipe de apresentação:** `scripts/gerar_slides.py` prepara os slides; `scripts/montar_zip.py` confere e reúne os arquivos.

## Ambiente e dependências

O projeto usa Python 3.12 ou superior, PyTorch, Torchvision, NumPy, pandas, Matplotlib e Jupyter. O arquivo `uv.lock` registra as versões resolvidas para tornar a instalação mais consistente.

O índice configurado para PyTorch usa a família CUDA 13.0. A GPU é requisito do treino, não uma opção aceleradora: sem ela, a execução para.

`vit-pytorch` e `pytest` ficam no grupo de desenvolvimento. O primeiro serve como referência automatizada para comparar o modelo próprio. Ele não é importado durante o treino normal e não entra no ZIP de entrega.

## Atenção ao planejamento

O arquivo em `docs/` se apresenta como planejamento e diz que não é a apresentação pronta. Como o repositório também contém o notebook, os resultados e os slides gerados, tratar esse planejamento como manual de execução atual seria arriscado. *(inferência)* Para comandos e comportamento, o README e o código oferecem evidência mais direta.
