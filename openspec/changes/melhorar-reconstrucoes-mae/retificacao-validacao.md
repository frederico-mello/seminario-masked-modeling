# Retificação documental: validação v1 e interpretação v2

Consolidação posterior de registros já existentes, sem treino, piloto, inferência ou nova consulta ao teste. O relatório v2 e seu resumo originais permanecem íntegros como evidência histórica; suas linhas de controles rotuladas como validação estavam contaminadas por eventos de teste e devem ser substituídas pelas tabelas abaixo.

O resultado primário usa os controles com `evento=controle` e `estado=validacao` explicitamente. Nos candidatos, os eventos de época têm `estado=concluido`; as métricas vêm exclusivamente das colunas `perda_validacao` e `ssim_validacao`. Melhor é a primeira época de menor MSE; final é a última época registrada.

## Proveniência e revisão posterior

O código corrigido não é o executado na rodada histórica. O manifesto, os contadores, os resultados e os hashes originais não foram recongelados. O gate original continua ativo e recusa fontes atuais divergentes; este consolidador apenas lê registros e escreve novos documentos.

| Origem | SHA-256 |
|---|---|
| `resultados/estudo-melhorar-reconstrucoes-mae/historico.csv` | `6d54737fa3e977d906f56a3e4d5fedb2f3b12b94825cfbdf7985512bda6ebdf7` |
| `resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/manifesto.json` | `26c3e2c9960e65941bd6d40100cf491f4b9a50997f1b548cb1ed418613c76d28` |
| `resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/historico.jsonl` | `07cb33ba52097d30c5a1f02419ccde7282eedc1242cbd8579b340c8cece2d242` |
| `resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/contador.jsonl` | `bf57749b308a5b4cd72ad3b2836456ca77645fbb6907212c2f9dce3ff32cb9af` |
| `resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/resumo.json` | `16769afc5ba49baa0133c9e601e1352c1a83a687ddb5f6d8362c70e2c360ee6c` |
| `resultados/estudo-melhorar-reconstrucoes-mae-c0-v2/relatorio-c0-v2.md` | `2d3c80ae9bafdb44dc2a0574768940044402dd994c9b334b077e8c0fbf3850c9` |
| Fonte atual `codigo/estudo_execucao_c0_v2.py` | `5b10f4491bccc20696cc1ab621c35e352e0eac8b5ce872203416883a0a5b5d0b` |
| Fonte atual `scripts/retificar_validacao.py` | `71c0be6b3e510522338f62b65775f6af953c0043571cfe5432096e2e7a38ec26` |
| Executor antigo executado | `07f8496dd86744fcb3094bdf70537c148d5696cac55853bb769b38e4b003adef` |
| Inventário de fontes original | `9eba0cb402003f739abfe18ade2b06d6160c57642a4342c7ba8a417934de7cf9` |

## Controles corretos de validação

| Taxa | Controle | MSE | SSIM |
|---|---|---:|---:|
| 0.5 | controle_interpolacao | 0.044741 | 0.269084 |
| 0.5 | controle_media_rgb | 0.049111 | 0.355596 |
| 0.75 | controle_interpolacao | 0.054458 | 0.237844 |
| 0.75 | controle_media_rgb | 0.051706 | 0.355630 |

## Dados individuais por seed

| Candidato | Taxa | Seed | Estado | Épocas | Melhor: época / MSE / SSIM | Final: época / MSE / SSIM |
|---|---|---|---|---:|---|---|
| C1 | 0.5 | 10 | completo | 200 | 181 / 0.033555 / 0.397872 | 200 / 0.033933 / 0.400218 |
| C1 | 0.5 | 20 | completo | 200 | 198 / 0.033764 / 0.398724 | 200 / 0.034440 / 0.396323 |
| C1 | 0.5 | 30 | completo | 200 | 183 / 0.033520 / 0.400543 | 200 / 0.033765 / 0.402818 |
| C1 | 0.75 | 10 | incompleto | 185 | 163 / 0.041888 / 0.358202 | 185 / 0.042473 / 0.360543 |
| C1 | 0.75 | 20 | completo | 200 | 200 / 0.041816 / 0.362957 | 200 / 0.041816 / 0.362957 |
| C1 | 0.75 | 30 | completo | 200 | 197 / 0.041316 / 0.364348 | 200 / 0.041547 / 0.365102 |
| C2 | 0.5 | 10 | completo | 200 | 200 / 0.036938 / 0.366839 | 200 / 0.036938 / 0.366839 |
| C2 | 0.5 | 20 | completo | 200 | 198 / 0.037122 / 0.365044 | 200 / 0.037487 / 0.363728 |
| C2 | 0.5 | 30 | completo | 200 | 184 / 0.038078 / 0.357809 | 200 / 0.038146 / 0.361678 |
| C2 | 0.75 | 10 | completo | 200 | 191 / 0.044569 / 0.343256 | 200 / 0.045754 / 0.343916 |
| C2 | 0.75 | 20 | completo | 200 | 200 / 0.044032 / 0.343815 | 200 / 0.044032 / 0.343815 |
| C2 | 0.75 | 30 | completo | 200 | 193 / 0.043516 / 0.346509 | 200 / 0.043682 / 0.347883 |

## Medianas de validação e diferenças descritivas

| Candidato | Taxa | n | MSE melhor | SSIM melhor | MSE final | SSIM final | SSIM melhor menos RGB de validação |
|---|---|---:|---:|---:|---:|---:|---:|
| C1 | 0.5 | 3 | 0.033555 | 0.398724 | 0.033933 | 0.400218 | +0.043128 |
| C1 | 0.75 | 3 | 0.041816 | 0.362957 | 0.041816 | 0.362957 | +0.007327 |
| C2 | 0.5 | 3 | 0.037122 | 0.365044 | 0.037487 | 0.363728 | +0.009448 |
| C2 | 0.75 | 3 | 0.044032 | 0.343815 | 0.044032 | 0.343916 | -0.011815 |

C1 a 75%: 0,362957 > RGB de validação 0,355630 (diferença +0,007327). C2 a 50%: 0,365044 > RGB de validação 0,355596 (+0,009448). RGB 0,363144 e 0,365483 são do teste e não entram nesta comparação. As medianas agregam três seeds; os controles determinísticos não constituem três réplicas independentes.

## Conclusão e limites

Avaliação visual aberta negativa de um único avaliador humano nas duas taxas; objetivo visual não atingido. As fichas não são cegas: o cabeçalho revela os métodos. Sem notas individuais ou preferências preenchidas. O resultado é exploratório, sem confirmação independente ou superioridade universal. C0 não teve treino completo em v1 ou v2; não se pode aplicar a regra de ganho contra C0. Os dois pilotos v2 excederam 1,25 s; os seis treinos não começaram. As 200 épocas são máximo planejado: C1, seed 10, taxa 75%, terminou em 185. A reserva v2 consumiu 0,209334139 minuto, com total v1 + v2 de 41,270848124 minutos. Nenhum julgamento visual altera a seleção numérica ou demonstra qualidade de representações.
