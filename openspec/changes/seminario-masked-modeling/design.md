# Design

## Context

- Motivação e escopo: ver proposal.md (Why e What).
- Imagens CIFAR-10 de 32x32x3 divididas em patches de 8x8: 16 tokens por imagem.
- Hardware de medição: GPU NVIDIA RTX 3050. Ambiente gerenciado por uv, com PyTorch via wheel cu130.
- Oráculo de teste: classe MAE do pacote vit-pytorch 1.24.1 (PyPI), usado apenas como dependência de desenvolvimento.
- Referências citadas: He et al. (2022), "Masked Autoencoders Are Scalable Vision Learners", e o repositório oficial facebookresearch/mae. Este último NÃO é reutilizado: licença CC-BY-NC, arquivado, depende de timm antigo.

## Goals / Non-Goals

**Goals:**
- Implementar um MAE mínimo em PyTorch puro, reproduzível do zero por um notebook.
- Comparar mascaramento de 50% e 75% com o mesmo número de épocas e máscara aninhada.
- Validar a implementação própria contra o oráculo vit-pytorch em testes de equivalência.
- Entregar slides de 10 a 12 páginas (pptx e pdf) e um zip verificado por md5.

**Non-Goals:**
- Linear probing e classificação downstream: citados como próximo passo nos slides, fora do escopo.
- Pré-treino em ImageNet ou em escala maior que o subset e a GPU permitem.
- Reutilizar código do repositório facebookresearch/mae.
- Busca de hiperparâmetros além da medição de orçamento descrita em D6.
- Incluir checkpoints de pesos ou o validador do oráculo no zip.

## Decisions

### D1. MAE próprio em PyTorch puro; vit-pytorch apenas como oráculo
- Escolha: implementação própria com patchify, máscara, encoder ViT, decoder leve e perda.
- Alternativas rejeitadas:
  - facebookresearch/mae: licença CC-BY-NC incompatível com código MIT, repo arquivado, timm antigo.
  - vit-pytorch como implementação de runtime: esconde a lógica que o seminário precisa explicar.
  - timm ou transformers prontos: mesma objeção, e acoplamento a APIs externas.
- vit-pytorch==1.24.1 entra no grupo `dev` do uv e só é usado pelos testes de equivalência. Não é distribuído no zip.

### D2. Arquitetura
- Encoder: dim 128, 4 blocos Transformer, 4 heads. Recebe somente os patches visíveis, com embedding posicional. Detalhes de tokens especiais seguem o oráculo (ver Open Questions).
- Decoder: dim 64, 2 blocos Transformer, 4 heads. Recebe os tokens visíveis projetados para 64 mais tokens de máscara, e prevê 8x8x3 = 192 valores por patch.
- Os hiperparâmetros são os mesmos passados ao oráculo (dim, depth e heads), para que a comparação de equivalência seja possível.
- Alternativa rejeitada: decoder de 512 dims e 8 blocos, do paper original. Custo incompatível com a RTX 3050 e sem ganho para o objetivo didático.

### D3. Dados: CIFAR-10 com md5 e subset balanceado
- Download via torchvision do arquivo cifar-10-python.tar.gz, com md5 verificado (c58f30108f718f92721af3b95e74349a). Se o md5 diferir, o script falha.
- Subset balanceado por classe, seed 42: 500 treino, 100 validação e 100 teste por classe, totalizando 5.000, 1.000 e 1.000 imagens.
- Origem: treino e validação saem do split de treino oficial (50.000). A validação é disjunta das 5.000 imagens de treino. O teste sai do split de teste oficial (10.000) e é usado somente no fim.
- Saídas: índices em CSV (split, classe, índice original) e imagens em .npz uint8. Dados brutos e o zip ficam fora do git, via .gitignore.

### D4. Escala de pixels e perda
- Pixels em float32 no intervalo [0,1], sem normalização por canal e sem normalização por patch (norm_pix_loss desligado).
- Motivo: segue o planejamento aprovado e a configuração do oráculo, que usa pixels brutos. Essa igualdade é verificada no teste de equivalência.
- Perda: MSE calculado somente nos patches ocultos. Patches visíveis não entram na perda.

### D5. Máscara aninhada
- Para cada imagem, uma permutação fixa dos 16 índices de patch, gerada com seed 42.
- 50% oculta os 8 primeiros índices da permutação; 75% oculta os 12 primeiros. Logo, os ocultos a 50% são um subconjunto dos ocultos a 75%.
- Motivo: a diferença entre condições vem só da quantidade de informação removida, e não de quais patches foram removidos.
- Alternativa rejeitada: máscara aleatória independente por condição. Adiciona variância que confunde a comparação com um único seed.

### D6. Otimização e orçamento medido
- Otimizador AdamW. Épocas, batch size e learning rate NÃO são fixados aqui: são decididos após medir uma época real na RTX 3050, e o resultado é registrado no notebook (orçamento previsto versus medido).
- Ambas as condições (50% e 75%) usam exatamente o mesmo número de épocas, batch e learning rate.
- Sem fallback silencioso para CPU: se o wheel cu130 não carregar ou a GPU não estiver disponível, o script falha com erro explícito.

### D7. Teste de equivalência com o oráculo
- Mesmos pesos inicializados passados para a implementação própria e para vit-pytorch, com mesma config (dim, depth, heads, patch size, máscara).
- Verificações: formas dos tensores, perda igual dentro de tolerância numérica, e reconstrução igual para a mesma máscara.
- O teste roda fora do zip. O zip contém apenas o código do MAE próprio.

### D8. Notebook autocontido e resultados gerados
- Um notebook executa do zero com `jupyter nbconvert --execute`: download, verificação de md5, criação do subset, treino das duas condições, avaliação e figuras.
- Saídas geradas em `resultados/`: `reconstrucoes.png`, `curva_perda.png` e `metricas.csv`. Nada é digitado à mão; os números dos slides vêm desses arquivos.
- Métrica final: MSE nos patches ocultos do conjunto de teste, uma por condição.
- Figura de reconstruções: 8 imagens fixas do teste, em três colunas por condição (original, mascarada, reconstrução).
- Curva de perda de validação por época, para as duas condições no mesmo gráfico.

### D9. Checkpoints fora do zip, com hash
- Cada checkpoint tem SHA-256 registrado na coluna `sha256` de `resultados/metricas.csv`, para rastreio.
- Motivo: tamanho e reprodutibilidade. Quem quiser reavaliar roda o notebook; o zip não depende dos pesos.

## Risks / Trade-offs

- [Subset pequeno (500 imagens por classe) reduz a qualidade absoluta da reconstrução] → Comparação é relativa entre 50% e 75%, com mesmo orçamento. Números absolutos são apresentados como medidos, sem extrapolação.
- [Diferença entre condições pode ser ruído de um único seed] → Seed fixo 42 para subset e máscara; limitação declarada nos slides. Repetição com mais seeds fica como próximo passo.
- [Wheel cu130 pode não existir ou não casar com o driver da máquina] → Falha explícita, sem fallback de CPU. Verificação de disponibilidade no primeiro passo do notebook.
- [Divergência numérica entre implementação própria e vit-pytorch] → Teste de equivalência com tolerância explícita; diferenças acima dela bloqueiam a entrega.
- [Downloads do CIFAR-10 mudam ou falham] → md5 verificado; falha se diferir. Arquivo baixado fica fora do git.
- [Orçamento medido pode exigir reduzir épocas] → Decisão tomada com medição real antes do treino final; o valor escolhido e o medido são registrados.
- [Licença do código: dependência dev vit-pytorch é MIT, mas não entra no zip] → Código próprio sob MIT; oráculo apenas como dependência de desenvolvimento.

## Migration Plan

- Projeto novo: não há sistema existente a migrar.
- Ordem: dados (D3), modelo (D1, D2, D4, D5), teste de equivalência (D7), medição de orçamento e escolha de épocas, batch e lr (D6), treino final e notebook (D8, D9), slides e zip.
- Rollback: reverter os commits no git e apagar `resultados/` e os checkpoints locais. Rodar o notebook de novo regenera tudo.

## Open Questions

- Tokens especiais (CLS) e tipo exato do embedding posicional, para casar com a configuração do vit-pytorch no teste D7. Resolver ao ler o oráculo na implementação. Não muda os requisitos, só detalhes internos do encoder.
- Valores finais de épocas, batch size e learning rate: definidos pela medição de D6. Não alteram o desenho nem as specs.
