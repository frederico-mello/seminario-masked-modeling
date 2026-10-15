# Emenda C0 v2

## Registro de autorização

Data: 15 de outubro de 2026.

Foi autorizada uma retomada isolada do candidato C0 neste diretório de trabalho. A autorização não reclassifica retroativamente a v1 e não autoriza qualquer consulta nova ao conjunto de teste.

## Protocolo autorizado

- Diretório exclusivo: `resultados/estudo-melhorar-reconstrucoes-mae-c0-v2`.
- Somente C0, com configuração, dados, máscaras, hiperparâmetros, seeds 10, 20 e 30 e taxas 0,5 e 0,75 já aprovados.
- Um piloto por taxa com seed 10, medindo uma época completa com validação, SSIM e I/O. O limiar passa a 1,25 s nesta v2. Resultado acima do limiar é registrado como inviável e não há repetição do piloto.
- Se qualquer taxa falhar no piloto ou não o completar, C0 é considerado inviável e nenhum dos seis treinos completos começa.
- Cada treino tem no máximo 200 épocas e 240 segundos por seed e taxa. Os 240 segundos incluem carga e setup do treino, época, validação, SSIM, checkpoint, cópias imutáveis e I/O. A guarda usa tempo monotônico com precisão de nanossegundo e interrompe no limite. A época parcial não entra na contagem de épocas concluídas.
- Duzentas épocas são um máximo, não uma garantia de conclusão. Qualquer execução com menos épocas recebe estado incompleto e não é tratada como equivalente a 200 épocas.
- O contador v2 é separado do contador v1 e limita a reserva v2 a 30 minutos. A soma v1 + v2 fica limitada a 120 minutos. A reserva já consumida pela v1 não é zerada nem transferida.
- O executor grava um marcador antes do primeiro piloto. Uma segunda invocação não repete piloto ou treino iniciado nem zera qualquer contador.
- O manifesto v2 congela hashes do código real, inclusive arquivos de código sem commit e os arquivos novos, configuração, lockfile, índices e dados somente de treino e validação, além dos hashes de referência v1. Divergência antes do piloto ou de um treino impede a execução.
- Checkpoints melhor e final são preservados em cópias imutáveis distintas, identificadas por época e SHA-256.
- MSE e SSIM usam a mesma régua de validação da v1. Não há novos treinos C1, C2 ou C3, inferência de controles, consulta ao teste, atualização de slides ou pacote, commit, push ou archive.
- A comparação com referências C1, C2 e controles v1 é descritiva, exclusivamente na validação. Protocolo distinto, treinos incompletos e referências ausentes são identificados; ausência de C0 v1 não significa derrota e ausência de referência não significa evidência negativa.

## Checks e evidências requeridos

Antes do primeiro piloto: `uv sync --locked`, `uv run pytest -q` e `openspec validate melhorar-reconstrucoes-mae`, todos com código de saída zero. Nenhuma falha pode ser ocultada por skip ou enfraquecimento de teste.

Antes do primeiro piloto, registrar o hash real do código, lockfile, configuração e dados de treino e validação. Se manifesto e estado executado divergirem, parar sem treinar.

Ao concluir, emitir relatório em português do Brasil com quadro por seed e taxa, estado, épocas concluídas, métricas de melhor e final, tempo, hashes de checkpoint, saldo v1 + v2 e lacunas. Nenhuma conclusão pode tratar um treino incompleto como 200 épocas.
