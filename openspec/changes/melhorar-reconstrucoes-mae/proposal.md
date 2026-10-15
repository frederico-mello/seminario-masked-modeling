# Proposal

## Why

As reconstruções já registradas têm uma única semente e não comparam qualidade visual de modo agregado; por isso, ainda não sabemos se mudanças de treino, arquitetura ou perda melhoram as reconstruções de forma reproduzível. Um estudo exploratório com avaliação nos pixels ocultos, critério visual e orçamento controlado permitirá medir ganhos reais e também relatar claramente quando eles não ocorrerem.

## Registro de aprovação e escopo desta proposta

A direção central aprovada pelo usuário é: C0 direto; C1 decoder de dimensão 128 e três blocos; C2 MSE + 0,1 L1; C3 residual sobre a média RGB visível opcional; seeds 10, 20 e 30; 200 épocas; ganho de 5% no MSE e 0,02 no SSIM contra C0; tolerância secundária SSIM 0,01; teto de 120 minutos com reserva de 30 minutos. Esta aprovação não autoriza Apply ou treinamento. Os parâmetros operacionais finais detalhados em `design.md` são propostas pendentes de gate humano, a registrar separadamente da aprovação central; não há alegação de resultados ou avaliação humana realizados.

## What Changes

- Introduzir um protocolo reprodutível para comparar poucos candidatos, incluindo o MAE direto retreinado, baselines sem rede e uma variante residual apenas se validação e orçamento permitirem.
- Fixar configuração comum, SSIM reproduzível, condição objetiva de C3, seleção visual e alocação exata de tempo para aprovação humana antes da Apply, preservando CIFAR-10, imagens 32x32, 16 patches e taxas de máscara de 50% e 75%.
- Registrar máscaras por época e semente, avaliação comum nos patches ocultos, seleção por validação, checkpoints distintos de melhor e final, histórico por execução e tempo cumulativo limitado a duas horas.
- Definir comparação numérica e visual sem seleção de imagens a dedo nem métrica de imagem inteira dominada por pixels visíveis copiados; consultar o teste uma única vez após congelar candidatos e regras.
- Atualizar, na Apply, os documentos, slides e pacote para refletir os resultados do estudo sem apagar ou reclassificar resultados anteriores; não incluir classificação nem linear probing.
- Nesta fase, especificar e planejar apenas: nenhum treino, teste ou geração de resultados será executado.

## Capabilities

### New Capabilities

- `melhorias-reconstrucao`: comportamento do protocolo exploratório, baselines, comparação de candidatos, avaliação, orçamento, histórico e relato dos resultados.

### Modified Capabilities

- `mae-modelo`: configuração explícita das variantes de arquitetura e perda permitidas entre candidatos, mantendo entradas, resolução, quantidade de patches e codificação dos visíveis.
- `slides-seminario`: apresentação de resultados novos rastreáveis, delimitados e coerentes com o histórico, sem substituir os resultados anteriores.
- `pacote-entrega`: inclusão dos artefatos do estudo com conteúdo coerente com documentos e slides, preservando resultados anteriores e exclusões vigentes.

## Impact

Na Apply, poderão ser afetados `codigo/mae.py`, `codigo/treino.py`, novos módulos de estudo, `README.md`, scripts de slides e empacotamento, além de artefatos em `resultados/`. As regras definitivas dependem do gate humano; dados, CIFAR-10, resolução 32x32, 16 patches e taxas de 50% e 75% permanecem fixos. Nenhuma implementação ou medição faz parte desta proposta.

## Emenda autorizada: retomada C0 v2

Uma autorização posterior permite uma rodada isolada somente de C0, sem reclassificar ou sobrescrever a rodada v1. A emenda mantém dados, máscaras, hiperparâmetros, seeds 10, 20 e 30 e taxas de 50% e 75%; altera somente o limiar do piloto para 1,25 s, dentro do limite máximo de 200 épocas e 4 minutos por seed e taxa. A rodada v2 usa `resultados/estudo-melhorar-reconstrucoes-mae-c0-v2`, um manifesto próprio e um contador de reserva separado, limitado a 30 minutos e sujeito ao teto global de 120 minutos somados ao consumo v1. O escopo, a contabilização, as interrupções, a comparação limitada à validação e as evidências estão registrados em `design.md` e em `emenda-c0-v2.md`.
