# Relatório da fase B: estudo melhorar-reconstrucoes-mae

Documento interno derivado integralmente dos artefatos registrados do estudo (manifesto.json, historico.csv, contador.jsonl, resumo.json e estado.json em resultados/estudo-melhorar-reconstrucoes-mae/). Tabelas e números são calculados pelo gerador a partir dos arquivos; as provas de execução são transcrições resumidas dos logs.

## 1. Congelamentos

- Versão das regras: `regras-estudo-v1`. Hash SHA-256 do manifesto completo: `f6fd9a10d3d1532e6a94b8be9882c187a30050434889d65efcda8a28881c332d`; congelado antes do primeiro piloto.
- Versão do split de índices: `02cdb84acfac19d6`. Hash do código do estudo (SHA-256 dos módulos): `e13ef0653e119b00`.
- Teto de orçamento: 120 minutos, 90 principais mais 30 de reserva, com contador cumulativo persistido em `contador.jsonl`.
- Oito IDs visuais fixados no congelamento: 20736, 12985, 33580, 25306, 6418, 34029, 31327, 45589.
- Barreira de avaliação: congelamento final com hash `72bb04bd3a502dbf4caac81f3b096800f03e2f0b120c849e7352ec4c865eb24e`; o conjunto de teste só foi consultado uma vez, depois dela.

## 2. Pilotos (uma época por taxa, seed 10, com validação, SSIM e I/O)

| candidato | taxa | tempo do ciclo (s) | viável |
|---|---|---|---|
| C0 | 50,0000% | 1,22 | não |
| C0 | 75,0000% | 0,89 | não |
| C1 | 50,0000% | 1,03 | sim |
| C1 | 75,0000% | 1,16 | sim |
| C2 | 50,0000% | 1,03 | sim |
| C2 | 75,0000% | 0,99 | sim |

Limiar congelado: 1,2 s por época completa (treino, validação, SSIM e I/O), que é 4 min divididos por 200 épocas por execução. C0 excedeu o limiar na taxa 50% (1,22 s) e ficou inviável: seus treinos completos não começaram e nenhuma parte do saldo dele foi gasta. O primeiro ciclo do processo inclui o aquecimento da GPU, e o critério congelado foi aplicado literalmente, sem reavaliação nem redistribuição de saldo. C1 e C2 foram viáveis e treinaram.

## 3. Execuções de treino (melhor e final por execução)

| execução | estado | épocas concluídas | melhor: mse, ssim, época |
|---|---|---|---|
| `C0|10|0.5` | inviavel | 0 | não executada |
| `C0|10|0.75` | inviavel | 0 | não executada |
| `C0|20|0.5` | inviavel | 0 | não executada |
| `C0|20|0.75` | inviavel | 0 | não executada |
| `C0|30|0.5` | inviavel | 0 | não executada |
| `C0|30|0.75` | inviavel | 0 | não executada |
| `C1|10|0.5` | completo | 200 | 0,0336, 0,3979, época 181 |
| `C1|10|0.75` | interrompido | 185 | 0,0419, 0,3582, época 163 |
| `C1|20|0.5` | completo | 200 | 0,0338, 0,3987, época 198 |
| `C1|20|0.75` | completo | 200 | 0,0418, 0,3630, época 200 |
| `C1|30|0.5` | completo | 200 | 0,0335, 0,4005, época 183 |
| `C1|30|0.75` | completo | 200 | 0,0413, 0,3643, época 197 |
| `C2|10|0.5` | completo | 200 | 0,0369, 0,3668, época 200 |
| `C2|10|0.75` | completo | 200 | 0,0446, 0,3433, época 191 |
| `C2|20|0.5` | completo | 200 | 0,0371, 0,3650, época 198 |
| `C2|20|0.75` | completo | 200 | 0,0440, 0,3438, época 200 |
| `C2|30|0.5` | completo | 200 | 0,0381, 0,3578, época 184 |
| `C2|30|0.75` | completo | 200 | 0,0435, 0,3465, época 193 |

A época do checkpoint final coincide com a última época concluída de cada execução (coluna anterior); cópias imutáveis e hashes de melhor e final estão no histórico (evento checkpoint) e em checkpoints/ com modo de somente leitura. A seleção usa apenas o melhor de validação e não foi reaberta depois.

Interrupção registrada: a execução `C1|10|0.75` parou na época 185 de 200 porque a época real (cerca de 1,5 s) ficou acima da estimativa do piloto e o saldo do envelope de 4 minutos dessa execução terminou. O melhor checkpoint (época 163) e o final (época 185) foram consolidados; nada mais ocorreu nessa execução.

## 4. Auditoria por seed e taxa (melhor de validação na régua)

Por seed, com a mediana das seeds em negrito; os controles determinísticos foram medidos uma vez por taxa e imagem (D4) e repetidos por seed apenas como linhas comparativas no histórico, sem recálculo por rede.

### Taxa 50,0000%

| medição | mse por seed | ssim por seed | mse mediana | ssim mediana |
|---|---|---|---|---|
| C1 | 10: 0,0336; 20: 0,0338; 30: 0,0335 | 10: 0,3979; 20: 0,3987; 30: 0,4005 | **0,0336** | **0,3987** |
| C2 | 10: 0,0369; 20: 0,0371; 30: 0,0381 | 10: 0,3668; 20: 0,3650; 30: 0,3578 | **0,0371** | **0,3650** |
| controle média RGB | igual por seed (medida única por imagem) | igual por seed | **0,0491** | **0,3556** |
| controle interpolação | igual por seed (medida única por imagem) | igual por seed | **0,0447** | **0,2691** |
| C0 | sem treinos completos (inviável pelo piloto) | não aplicável | não aplicável | não aplicável |

### Taxa 75,0000%

| medição | mse por seed | ssim por seed | mse mediana | ssim mediana |
|---|---|---|---|---|
| C1 | 10: 0,0419; 20: 0,0418; 30: 0,0413 | 10: 0,3582; 20: 0,3630; 30: 0,3643 | **0,0418** | **0,3630** |
| C2 | 10: 0,0446; 20: 0,0440; 30: 0,0435 | 10: 0,3433; 20: 0,3438; 30: 0,3465 | **0,0440** | **0,3438** |
| controle média RGB | igual por seed (medida única por imagem) | igual por seed | **0,0517** | **0,3556** |
| controle interpolação | igual por seed (medida única por imagem) | igual por seed | **0,0545** | **0,2378** |
| C0 | sem treinos completos (inviável pelo piloto) | não aplicável | não aplicável | não aplicável |

Comparação descritiva com os controles: na taxa 50%, C1 (0,0336) e C2 (0,0371) ficaram abaixo dos dois controles (0,0491 e 0,0447); na taxa 75%, C1 (0,0418) e C2 (0,0440) também ficaram abaixo dos dois controles (0,0517 e 0,0545). Essa observação não equivale a melhoria demonstrada: a regra congelada exige comparação contra C0, e sem treinos completos de C0 nenhum candidato pode ser declarado elegível.

## 5. Seleção e decisão de C3

- Taxa 50,0000%: vencedor nenhum. Motivo registrado: referência C0 sem treinos completos (inviável pelo limiar de 1,2 s do piloto): regra de elegibilidade contra C0 não pôde ser aplicada; ausência de melhoria demonstrada
- Taxa 75,0000%: vencedor nenhum. Motivo registrado: referência C0 sem treinos completos (inviável pelo limiar de 1,2 s do piloto): regra de elegibilidade contra C0 não pôde ser aplicada; ausência de melhoria demonstrada
- C3: elegível não. Motivo registrado: C0 sem treinos completos (inviável pelo limiar de 1,2 s do piloto): o critério de média de MSE de C0 contra cada baseline não é verificável; C3 registrado como NÃO EXECUTADO

## 6. Única avaliação de teste (depois do congelamento)

| medição no teste | taxa 50% mse | taxa 50% ssim | taxa 75% mse | taxa 75% ssim |
|---|---|---|---|---|
| controle média RGB | 0,0486 | 0,3655 | 0,0518 | 0,3631 |
| controle interpolação | 0,0451 | 0,2729 | 0,0549 | 0,2416 |

Sem vencedor por taxa, não há candidato vencedor a registrar na avaliação final: somente os controles foram medidos no teste, na mesma régua fixa e uma única vez. O conjunto de teste nunca entrou na escolha. O resultado é exploratório: o teste é conhecido uma vez e não há alegação de confirmação independente nem de repetição aprovada.

## 7. Orçamento real do contador (teto de 120 minutos)

- Alocação principal consumida: **41,1 minutos de 90** (limiares por categoria e por candidato respeitados os guards).
- Reserva de repetições justificadas: **0,0 minutos de 30 (intocada)**.
- Por categoria (minutos): avaliacao 0,0, avaliacao_final 0,0, consolidacao 0,0, piloto 0,1, treino_por_seed_taxa 40,9.
- Por candidato (minutos): C0 0,0, C1 22,7, C2 18,2, C3 0,0.
- O saldo não gasto por C0 (inviável) e por C3 (não executado) permaneceu no orçamento; nada foi redistribuído entre candidatos.

## 8. Ficha visual (evidência qualitativa)

- Arquivos: `ficha-visual/ficha_50.png`, `ficha-visual/ficha_75.png` (reconstruções dos oito IDs em ambas as taxas, com rótulos anônimos), `ficha-visual/ficha_visual.json` (ficha preenchível, campos não preenchidos) e `ficha-visual/ficha-rotulos.json` (mapeamento das letras).
- A avaliação humana não foi realizada nesta fase: a ficha fica pronta para os avaliadores (usuário e, se disponível, Luan), e nenhum artefato alega preenchimento humano. A ficha não altera a seleção numérica e não mede reconhecimento.

## 9. Checagens da fase (provas de execução, resumidas dos logs)

```text
$ openspec validate melhorar-reconstrucoes-mae
Change 'melhorar-reconstrucoes-mae' is valid

$ uv sync --locked
ambiente sincronizado a partir do uv.lock (sem alterações de dependências)

$ uv run pytest -q
99 passed, 1 warning in ~4 s

$ uv run python -m codigo.estudo_execucao congelar
congelado: hash=f6fd9a10d3d1532e split=02cdb84acfac19d6 codigo=e13ef0653e119b00 torch=2.14.1+cu130 ids=[20736, 12985, 33580, 25306, 6418, 34029, 31327, 45589]

$ uv run python -m codigo.estudo_execucao piloto
C0: piloto viavel=False [0.5=1.22s 0.75=0.89s]
C1: piloto viavel=True [0.5=1.03s 0.75=1.16s]
C2: piloto viavel=True [0.5=1.03s 0.75=0.99s]

$ uv run python -m codigo.estudo_execucao controles
controle controle_media_rgb@0.5: mse=0.0491 ssim=0.3556
controle controle_interpolacao@0.5: mse=0.0447 ssim=0.2691
controle controle_media_rgb@0.75: mse=0.0517 ssim=0.3556
controle controle_interpolacao@0.75: mse=0.0545 ssim=0.2378
controles validação: 1.5s

$ uv run python -m codigo.estudo_execucao treino --candidato C1 --seed 10 --taxa 0.5
C1|10|0.5: estado=completo epocas=200 melhor=0.033555@181
(o mesmo comando foi repetido para os 6 pares seed/taxa de C1 e de C2; a linha final de cada execução está registrada em estado.json e a auditoria por época, com tempos, no historico.csv)

$ uv run python -m codigo.estudo_execucao consolidar --candidato C1
consolidação C1: 0.8s em cópias
$ uv run python -m codigo.estudo_execucao consolidar --candidato C2
consolidação C2: 0.6s em cópias

$ uv run python -m codigo.estudo_execucao decidir-c3
C3 elegivel=False: C0 sem treinos completos (inviável pelo limiar de 1,2 s do piloto): o critério de mediana de MSE de C0 contra cada baseline não é verificável; C3 registrado como NÃO EXECUTADO

$ uv run python -m codigo.estudo_execucao selecao
taxa 0.5: vencedor=None (referência C0 sem treinos completos (inviável pelo limiar de 1,2 s do piloto): regra de elegibilidade contra C0 não pôde ser aplicada; ausência de melhoria demonstrada)
taxa 0.75: vencedor=None (referência C0 sem treinos completos (inviável pelo limiar de 1,2 s do piloto): regra de elegibilidade contra C0 não pôde ser aplicada; ausência de melhoria demonstrada)

$ uv run python -m codigo.estudo_execucao congelar-final
congelamento final: hash=72bb04bd3a502dbf

$ uv run python -m codigo.estudo_execucao avaliacao-final
avaliação final: 1.6s

$ uv run python -m codigo.estudo_execucao resumo
resumo em resultados/estudo-melhorar-reconstrucoes-mae/resumo.json

$ uv run python -m codigo.estudo_execucao figuras
figuras em resultados/estudo-melhorar-reconstrucoes-mae/figuras

$ uv run python -m codigo.estudo_execucao ficha
ficha em resultados/estudo-melhorar-reconstrucoes-mae/ficha-visual: ['ficha-rotulos.json', 'ficha_50.png', 'ficha_75.png', 'ficha_visual.json']

$ uv run python scripts/gerar_slides.py
limites ok nas 13 paginas
png: 13 paginas em slides/png

$ uv run python scripts/montar_zip.py
zip gravado em seminario_masked_modeling.zip (34 arquivos)
lista de md5 em scripts/md5_pacote.csv
```

Logs completos da fase, com um arquivo por etapa, estão na pasta `logs/` da worktree (01-congelar.log a 10-checks.log).

## 10. Entrega documental (slides, zip e README)

- `scripts/gerar_slides.py`: novo slide 9 com o quadro do estudo (pilotos, medianas de validação de C1 e C2, controles) e nota de resultado; números lidos de `resumo.json`. Verificação do próprio script: limites ok nas 13 páginas; pptx, pdf e 13 pngs regenerados.
- `scripts/montar_zip.py`: o pacote exige e inclui manifesto, historico.csv, contador.jsonl, resumo.json, três figuras, a ficha visual (duas imagens e dois JSON) e este relatório; conteúdos e exclusões anteriores preservados (dados brutos, checkpoints, oráculo e testes continuam de fora). Execução: zip com 34 arquivos e lista de md5 regenerada.
- README atualizado com a seção `Estudo de retreinamento`, apontando os artefatos novos; os resultados anteriores (metricas.csv, curva_perda.png, reconstrucoes.png e os checkpoints antigos) continuam intactos e identificáveis com o protocolo próprio deles.

## 11. Delimitações honestas

- C0 (referência do protocolo) não pôde ser treinado pelo limiar congelado do piloto; a regra de elegibilidade contra C0 não pôde ser aplicada e, portanto, nenhuma melhoria ficou demonstrada. A ausência de vencedor é consequência da regra congelada, não de escolha pós-hoc.
- A observação de que C1 e C2 tiveram MSE mediano abaixo dos controles é descritiva e exploratória; não equivale a melhoria demonstrada contra a referência C0 do protocolo.
- A comparação com o experimento anterior do notebook (MSE de teste de 0,0608 e 0,0717) é apenas indicativa: as máscaras de treino e a régua diferem do protocolo antigo.
- O conjunto de teste foi consultado uma única vez, depois do congelamento; não há alegação de confirmação independente.
- A inspeção visual fica como ficha pendente dos avaliadores humanos (usuário e, se disponível, Luan); nenhum resultado aqui depende dela.


## 12. Nota posterior de revisão, 15 de outubro de 2026

Foi registrada uma avaliação visual aberta por um único avaliador humano: os resultados foram considerados ruins nas duas taxas de máscara, 50% e 75%, e o objetivo de melhoria visual não foi atingido. Não houve avaliação cega: o cabeçalho das duas imagens revela o mapeamento entre letras e métodos. Não foram atribuídas notas individuais por imagem, dimensão ou candidato, nem preferências pareadas; os campos originais permanecem vazios. Esse julgamento qualitativo não altera a seleção numérica e não mede reconhecimento ou qualidade das representações.

C0 não tem treino completo em nenhuma das rodadas. Na v2, os pilotos duraram 1,430503879 s e 1,358304787 s, ambos acima de 1,25 s; nenhum dos seis treinos foi iniciado. O consumo v2 registrado é 0,209334139 minuto e o total v1 + v2 é 41,270848124 minutos. As 200 épocas são o máximo planejado; C1 v1, seed 10, taxa 75%, terminou com 185 épocas.

Os resultados são exploratórios, sem confirmação independente de melhoria. A falta de C0 impede aplicar a regra de ganho contra essa referência; ausência de referência não é derrota. MSE menor não demonstra superioridade geral em SSIM ou qualidade visual.

A revisão identificou uma inconsistência de origem nas tabelas do relatório e resumo v2: o leitor do histórico aceita eventos `controle` de validação e de teste e mantém a última ocorrência por método e taxa. Assim, os controles rotulados como validação no relatório v2 são, na realidade, os controles do teste v1. Os valores SSIM 0,362957 de C1 a 75% e 0,365044 de C2 a 50% são de validação; RGB 0,363144 e 0,365483 são de teste. Embora as desigualdades numéricas 0,362957 < 0,363144 e 0,365044 < 0,365483 sejam verdadeiras, elas comparam conjuntos distintos e não sustentam uma conclusão de desempenho. Nenhuma inferência foi refeita nesta revisão.

Os controles corretos de validação, já disponíveis no histórico v1 com `estado=validacao`, são:

| Taxa | Controle | MSE | SSIM |
|---|---|---:|---:|
| 50% | Média RGB | 0,049111 | 0,355596 |
| 50% | Interpolação | 0,044741 | 0,269084 |
| 75% | Média RGB | 0,051706 | 0,355630 |
| 75% | Interpolação | 0,054458 | 0,237844 |

Esses valores são uma transcrição dos registros existentes, sem nova avaliação científica. A correção do leitor e a emissão de um relatório retificado separado permanecem pendentes, preservando a versão executada e seus hashes. O relatório histórico registra a situação anterior à avaliação humana; suas menções a ficha cega e avaliação pendente não descrevem o estado atual.
