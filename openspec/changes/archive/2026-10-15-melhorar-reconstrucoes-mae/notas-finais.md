# Notas finais de interpretação

Data: 15 de outubro de 2026. Este registro posterior complementa o relatório histórico da fase B e o relatório C0 v2, sem alterar resultados, fichas originais, contadores ou manifestos congelados.

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

Esses valores são uma transcrição dos registros existentes, sem nova avaliação científica. O leitor foi corrigido e a [retificação externa](retificacao-validacao.md), com dados individuais e hashes, foi emitida em caminho separado, preservando a versão executada e seus hashes. O relatório histórico registra a situação anterior à avaliação humana; suas menções a ficha cega e avaliação pendente não descrevem o estado atual.
