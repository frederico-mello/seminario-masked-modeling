# Registro do gate humano - melhorar-reconstrucoes-mae

Data: 15 de outubro de 2026.

## Aprovação central de direção (tarefa 1.1)

Decisão humana aprovada nesta data, com os valores a seguir (coincidem com a aprovação central de direção registrada em proposal.md e design.md):

- C0: MAE direto retreinado no protocolo novo.
- C1: decoder de dimensão 128 e três blocos, encoder atual.
- C2: perda MSE + 0,1 * L1 nos pixels ocultos, arquitetura de C0.
- C3: residual sobre a média RGB dos visíveis, opcional conforme critério do design D7.
- Seeds de treino: 10, 20 e 30; a semente 42 fica reservada à régua fixa.
- Épocas planejadas: 200.
- Ganho mínimo contra C0, em cada taxa: redução de pelo menos 5% no MSE mediano (razão de medianas de MSE <= 0,95) e mediana das diferenças pareadas de SSIM >= 0,02; tolerância secundária de SSIM 0,01 só para desempate entre elegíveis.
- Orçamento: teto de 120 minutos com 90 minutos principais (30 por candidato C0/C1/C2: 2 de piloto, 24 de treino/validação/SSIM/I-O divididos em 8 por seed, 2 de consolidação e 2 de avaliação/registros, com guard por época e salvamento persistente e retomada) até 6 minutos agregados para avaliação final e baselines, e reserva protegida de 30 minutos.
- Configuração comum: batch 64, AdamW, learning rate 1e-4, weight decay 0,05, betas (0,9; 0,999), eps 1e-8, precisão float32, sem scheduler e sem clipagem de gradiente.
- SSIM conforme especificado no design D6 (janela gaussiana 3x3, sigma 1,5, reflexão sem repetir a borda, divisor populacional, C1=(0,01)^2, C2=(0,03)^2, epsilon 1e-12).
- Critério de C3 conforme o design D7.

## Aprovação das propostas operacionais finais (tarefa 1.1)

Aprovadas verbalmente nesta data (15/10/2026):

- Definição matemática e testes de referência do SSIM conforme D6.
- Configuração comum acima, com hash SHA256 do manifesto como formalização do congelamento (a gravação do arquivo com o hash ocorre imediatamente antes do primeiro piloto, na fase de execução).
- Critério de C3: mediana de MSE de C0 estritamente menor que a de cada baseline nas duas taxas e saldo elegível de pelo menos 30 minutos fora da reserva de 30 minutos; a reserva nunca financia C3.
- Orçamento detalhado: 90 minutos principais com envelopes por seed/taxa de 4 minutos, piloto de 2 minutos por candidato, guard por época, interrupção no limite e retomada na mesma identidade, salvamento persistente; 30 minutos de reserva.
- Ficha de inspeção visual: oito IDs de validação escolhidos pela ordenação SHA-256 de visual-v1|versão_do_split|índice_original_decimal com desempate pelo índice, notas de cor, estrutura, borramento e artefatos de 1 a 5, preferência pareada e comentário; o usuário será o avaliador, e nenhuma avaliação humana foi realizada nesta fase.
- Regra de desempate da seleção conforme D6: maior SSIM mediano entre elegíveis; manter os que estejam a no máximo 0,01 abaixo; dentre eles menor MSE mediano; empate por menor tempo acumulado e depois ordem fixa C1, C2, C3.

## Autorização de Apply (tarefa 1.2)

Autorização explícita de Apply concedida nesta data para a fase A (infraestrutura e testes unitários) nesta worktree: implementação dos módulos do estudo e dos nove testes novos, sem pilotos, treino real, consulta ao conjunto de teste ou geração de resultados. O congelamento de versão Git/código, lockfile/ambiente, splits/índices, hash integral da configuração, ordem de seleção, orçamento e IDs da inspeção visual ocorre antes do primeiro piloto, imediatamente antes do treino, e não depende do conjunto de teste: nenhum campo da configuração referenciado ao conjunto de teste.

## Pendências

Nenhuma. Os congelamentos operacionais restantes pertencem à fase de execução, antes do primeiro piloto.

## Autorização complementar da retomada C0 v2

Data: 15 de outubro de 2026.

Foi autorizada nesta solicitação uma nova rodada isolada somente de C0, no diretório `resultados/estudo-melhorar-reconstrucoes-mae-c0-v2`. A rodada preserva a v1, usa limiar de 1,25 s no piloto, máximo de 200 épocas e 4 minutos por combinação de seed e taxa, e consome no máximo 30 minutos em contador v2 separado, mantendo a soma com v1 dentro do teto global de 120 minutos. São mantidos dados, máscaras, hiperparâmetros, seeds 10, 20 e 30 e taxas 0,5 e 0,75. Execuções interrompidas são incompletas; não há autorização para novos treinos C1, C2 ou C3, novos controles, consulta ao teste, atualização de slides ou pacote, commit, push ou archive. A comparação autorizada é descritiva e restrita à validação, com as referências v1 disponíveis e com as limitações de protocolo explicitadas.

Esta autorização posterior acrescenta somente o escopo acima. Não altera nem reclassifica registros v1 ou a autorização da fase anterior.
