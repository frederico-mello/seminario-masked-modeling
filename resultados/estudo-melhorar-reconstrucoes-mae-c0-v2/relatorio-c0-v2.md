# Retomada C0 v2

## Protocolo e alcance

Esta retomada executa somente C0 no diretório v2 isolado. Mantém dados, máscaras, hiperparâmetros, seeds 10, 20 e 30 e taxas 0,5 e 0,75. O limiar do piloto é 1,25 s. Cada treino tem no máximo 200 épocas e 240 segundos, incluindo setup, validação, SSIM, checkpoints e I/O. Duzentas épocas são um máximo, não uma garantia.

Uma execução interrompida é relatada como incompleta e contabiliza somente épocas concluídas. Os checkpoints melhor e final são cópias imutáveis distintas com época e SHA-256. MSE e SSIM vêm da mesma régua de validação da v1.

Não foram iniciados novos treinos C1, C2 ou C3, novos controles ou inferências nos modelos v1. Não houve consulta ao conjunto de teste.

## Pilotos C0 v2

| Seed | Taxa | Estado | Época completa | Tempo da época | Limiar | SHA-256 do checkpoint de piloto |
|---:|---:|---|---:|---:|---:|---|
| 10 | 0.5 | inviável, acima do limiar | 1 | 1.430503879 s | 1.25 s | bc755bb6448105d7ef6aeeef7afb6db196d0c3cc352d03168f5cd0fdac968959 |
| 10 | 0.75 | inviável, acima do limiar | 1 | 1.358304787 s | 1.25 s | 3292e74ed7bc3de1ba1775003c0d21b8f6960b967bab57845e7c9075dba4e2ec |

A regra pré-fixada exige que ambas as taxas passem no piloto para iniciar qualquer treino completo C0. As duas épocas completas excederam 1,25 s; C0 v2 foi registrado como inviável e nenhum dos seis treinos foi iniciado. Não houve repetição. Os checkpoints e métricas de validação dos pilotos permanecem no estado e no histórico para auditoria, mas não são resultados de treino nem entram na comparação de desempenho.

## Treinos completos C0 v2
| Seed | Taxa | Estado | Épocas concluídas | Melhor | Final | Tempo de treino completo | Checkpoint melhor | Checkpoint final |
|---:|---:|---|---:|---|---|---:|---|---|
| 10 | 0.5 | inviável pelo piloto | 0 | sem treino | sem treino | 0.000000 s | não gerado | não gerado |
| 10 | 0.75 | inviável pelo piloto | 0 | sem treino | sem treino | 0.000000 s | não gerado | não gerado |
| 20 | 0.5 | inviável pelo piloto | 0 | sem treino | sem treino | 0.000000 s | não gerado | não gerado |
| 20 | 0.75 | inviável pelo piloto | 0 | sem treino | sem treino | 0.000000 s | não gerado | não gerado |
| 30 | 0.5 | inviável pelo piloto | 0 | sem treino | sem treino | 0.000000 s | não gerado | não gerado |
| 30 | 0.75 | inviável pelo piloto | 0 | sem treino | sem treino | 0.000000 s | não gerado | não gerado |

## Referências de validação v1

Valores de C1, C2 e controles são lidos do histórico v1, sem nova inferência. A tabela resume os melhores e finais por seed, quando existem; execução interrompida continua identificada pelo número efetivo de épocas.

| Taxa | Referência | Seeds disponíveis | MSE mediano melhor | SSIM mediano no melhor | MSE mediano final | SSIM mediano final |
|---:|---|---:|---:|---:|---:|---:|
| 0.5 | C0_v2 | 0 | sem treino | sem treino | sem treino | sem treino |
| 0.5 | C1_v1 | 3 | 0.033555 | 0.398724 | 0.033933 | 0.400218 |
| 0.5 | C2_v1 | 3 | 0.037122 | 0.365044 | 0.037487 | 0.363728 |
| 0.5 | controle_interpolacao v1 | 1 | 0.045078 | 0.272857 | não aplicável | não aplicável |
| 0.5 | controle_media_rgb v1 | 1 | 0.048649 | 0.365483 | não aplicável | não aplicável |
| 0.75 | C0_v2 | 0 | sem treino | sem treino | sem treino | sem treino |
| 0.75 | C1_v1 | 3 | 0.041816 | 0.362957 | 0.041816 | 0.362957 |
| 0.75 | C2_v1 | 3 | 0.044032 | 0.343815 | 0.044032 | 0.343916 |
| 0.75 | controle_interpolacao v1 | 1 | 0.054904 | 0.241592 | não aplicável | não aplicável |
| 0.75 | controle_media_rgb v1 | 1 | 0.051779 | 0.363144 | não aplicável | não aplicável |


Leitura descritiva da validação v1: em 0,5, as medianas de MSE melhor/final foram 0.033555/0.033933 para C1 e 0.037122/0.037487 para C2; em 0,75 foram 0.041816/0.041816 para C1 e 0.044032/0.044032 para C2. Os controles v1 tiveram MSE 0.045078 e 0.048649 em 0,5, e 0.054904 e 0.051779 em 0,75. C0 v2 não tem métricas de treino completo para comparar; os tempos e checkpoints de piloto não são usados como desempenho. Esses valores descrevem referências de validação v1 e não estimam efeito causal de C0 v2.

## Estado das referências C1 e C2 v1 por seed

| Taxa | Candidato | Seed | Estado observado | Épocas registradas | Melhor: época / MSE / SSIM | Final: época / MSE / SSIM |
|---:|---|---:|---|---:|---|---|
| 0.5 | C1 v1 | 10 | completo | 200 | 181 / 0.033555 / 0.397872 | 200 / 0.033933 / 0.400218 |
| 0.5 | C1 v1 | 20 | completo | 200 | 198 / 0.033764 / 0.398724 | 200 / 0.03444 / 0.396323 |
| 0.5 | C1 v1 | 30 | completo | 200 | 183 / 0.03352 / 0.400543 | 200 / 0.033765 / 0.402818 |
| 0.5 | C2 v1 | 10 | completo | 200 | 200 / 0.036938 / 0.366839 | 200 / 0.036938 / 0.366839 |
| 0.5 | C2 v1 | 20 | completo | 200 | 198 / 0.037122 / 0.365044 | 200 / 0.037487 / 0.363728 |
| 0.5 | C2 v1 | 30 | completo | 200 | 184 / 0.038078 / 0.357809 | 200 / 0.038146 / 0.361678 |
| 0.75 | C1 v1 | 10 | incompleto | 185 | 163 / 0.041888 / 0.358202 | 185 / 0.042473 / 0.360543 |
| 0.75 | C1 v1 | 20 | completo | 200 | 200 / 0.041816 / 0.362957 | 200 / 0.041816 / 0.362957 |
| 0.75 | C1 v1 | 30 | completo | 200 | 197 / 0.041316 / 0.364348 | 200 / 0.041547 / 0.365102 |
| 0.75 | C2 v1 | 10 | completo | 200 | 191 / 0.044569 / 0.343256 | 200 / 0.045754 / 0.343916 |
| 0.75 | C2 v1 | 20 | completo | 200 | 200 / 0.044032 / 0.343815 | 200 / 0.044032 / 0.343815 |
| 0.75 | C2 v1 | 30 | completo | 200 | 193 / 0.043516 / 0.346509 | 200 / 0.043682 / 0.347883 |

## Limitações e lacunas

A v1 não contém uma referência C0 treinada, portanto não há comparação de C0 v2 com C0 v1. A v1 usou limiar de piloto de 1,2 s; esta retomada usa 1,25 s. Como os pilotos v2 reprovaram, não existe desempenho de treino completo C0 v2 para comparar com C1, C2 ou controles. A comparação disponível é descritiva e limitada às métricas de validação v1; diferenças de protocolo e execuções incompletas impedem atribuição causal. Em C1 v1 na taxa 0,75, seed 10 terminou incompleto na época 185. A ausência de C0 v1 não é derrota, e a falta de referência não é evidência negativa. Não há reclassificação retroativa da v1 nem seleção de vencedor nesta retomada.

## Congelamento anterior aos pilotos

O manifesto foi congelado antes do primeiro piloto, após os checks obrigatórios. Hashes verificados:

- Manifesto v2: `fda2ab28a44b9a74d6b02d5b19dc621687e1d5d98035fa2419716b0794ed4e16`.
- Código-fonte real, incluindo arquivos não commitados: `9eba0cb402003f739abfe18ade2b06d6160c57642a4342c7ba8a417934de7cf9`.
- Configuração: `0818e65052c935c8748a2475b99160e8b606256dc22614b64ecc8ecf27c324d8`.
- Splits treino/validação: `8ab3c26222c8349e9b0260d7a5ca1e5ce6f96764e7e654958f9088e54e56e5fe`.
- Lockfile: `5ed81eed1698af6c9d19c2ff813ffd033b3e44e6b74b88a5a23c8267de1f0ced`.

O inventário inclui os fontes Python sem commit; a execução e o relatório preservam os mesmos hashes congelados.
## Contabilização

- Consumo principal v1: 41.061513985 min.
- Reserva consumida v1: 0.000000000 min.
- Consumo v2: 0.209334139 min de no máximo 30 min.
- Total v1 + v2: 41.270848124 min de no máximo 120 min.
- Saldo da reserva v2: 29.790665861 min.
- Saldo global: 78.729151876 min.

Referências v1: SHA-256 da árvore `4e0e50213113c937dbe2dc3bbc91771a865b487c4a3f960f77a6d3a1ebd48e54`; manifesto `b87f36261eeabd348c8e4cd32f9002f4aecb112be75c1fdad794efba45743cad`; contador `6152650eecee6554c27ab22ca8fc39aea9ef8065f9f61737f2275027841f79a0`. O manifesto C0 v2 é `fda2ab28a44b9a74d6b02d5b19dc621687e1d5d98035fa2419716b0794ed4e16`.

## Rastreabilidade

Os números desta página são derivados do histórico JSONL v2 e dos eventos de época e controle de validação presentes no histórico v1. O resumo legível por máquina está em `resumo.json`; as durações monotônicas completas estão em `contador.jsonl`.
