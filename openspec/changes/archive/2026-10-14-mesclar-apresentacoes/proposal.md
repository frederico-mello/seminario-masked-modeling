# Proposal

## Why

Os itens obrigatórios das instruções da disciplina (aplicações por domínio, fluxo pós MAE, segundo experimento com resultados visuais adicionais) precisam de conteúdo que está presente na apresentação entregue pelo colega e ausente na nossa. O tema e o grupo são os mesmos; a entrega final exige uma apresentação única, fundida, que preserva a nossa espinha dorsal experimental e incorpora o material didático e o experimento complementar do colega, dentro do limite de 10 a 12 slides.

## What Changes

- Fusão da apresentação em exatamente 12 slides: mantém a nossa estrutura (capa com título e grupo, o que é a ideia-chave, motivações, tabela BERT x MAE x SimMIM, diagrama de 8 etapas, equação da perda, pseudocódigo, experimento próprio CIFAR-10 do zero com 50% e 75%, aplicações, conclusões, referências) e incorpora do colega:
  - abertura didática com a frase "O próprio dado fornece a supervisão";
  - fluxo pós MAE: pré-treinamento, decoder descartado, tarefas downstream;
  - aplicações por domínio: visão computacional, imagens médicas, sensoriamento remoto e outras modalidades;
  - segundo experimento com MAE pré-treinado (ViT-MAE, entrada 224x224, patches 16x16) nas taxas 25%, 50%, 75% e 90%, com as imagens visuais e os MSEs 0,0476/0,1403/0,3117 do material do colega, creditando a implementação pública (Hugging Face ViTMAE, modelo facebook/vit-mae-base) e o link do Colab;
  - referências extras: Dosovitskiy et al. (2021), ViT, e Bao et al. (2022), BEiT.
- SimMIM permanece apenas na nossa tabela comparativa.
- Inventário dos assets do colega (imagens de resultados visuais e figura de arquitetura) determina quais entram na apresentação; a extração ocorre no Apply, para o diretório de assets decidido no design.
- Delimitação da interpretação mantida: semente única 42 no experimento próprio; no experimento do colega, os números são citados como vindos do material do colega com MAE pré-treinado público, sem generalizar.
- O zip de entrega passa a incluir os assets do colega usados nos slides.

## Capabilities

### New Capabilities

- (nenhuma)

### Modified Capabilities

- `slides-seminario`: novo total de 12 slides com slide adicional de experimento do colega, aplicação por domínio expandida e referências extras; números do experimento do colega com rastreio ao material dele (MSEs documentados e imagens versadas como assets) em vez de digitação à mão a partir de resultados locais.
- `pacote-entrega`: o zip inclui o diretório de assets do colega referenciado pela geração de slides, com verificação de presença e md5 como os demais arquivos obrigatórios.

## Impact

- `slides/gerar_slides.py`: novos slides 8 a 10 (experimento do colega, aplicações por domínio, pós MAE) e ajuste dos demais para caber em 12; `verificar_limites` atualizado.
- `slides/recursos-colega/` (diretório a confirmar no design): assets PNG extraídos do pptx do colega, versionados no repositório no Apply.
- `scripts/montar_zip.py`: inclui os assets no pacote, com md5.
- `openspec/specs/slides-seminario/spec.md` e `openspec/specs/pacote-entrega/spec.md`: deltas nos requisitos alterados.