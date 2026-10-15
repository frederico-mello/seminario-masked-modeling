# Design

## Context

A entrega do seminário já tem o experimento executado e os resultados gravados em `resultados/` (métricas de duas razões de máscara com semente 42, curva de perda e reconstruções), além de slides e pacote gerados por scripts versionados. O planejamento em `docs/Planejamento_Masked_Modeling_em_Deep_Learning.md` define o roteiro de 20 minutos e o conteúdo didático esperado, que os slides atuais cobrem apenas parcialmente. Os deltas de comportamento estão em `specs/` deste change; este design decide como implementá-los. Este ambiente não tem o CIFAR-10 bruto nem GPU, portanto o design não assume reexecução de treino nem download dos dados.

## Goals / Non-Goals

**Goals:**
- Fechar o conteúdo didático dos slides conforme o planejamento: diagrama do fluxo do MAE, equação da perda explicada termo a termo e pseudocódigo do treinamento.
- Estruturar a comparação BERT x MAE x SimMIM em tabela (modalidade, alvo previsto, perda, arquitetura), com o contraste MSE x L1 explicado, e encerrar com aplicações e as quatro referências completas.
- Delimitar a interpretação dos resultados ao experimento (máscara aninhada, semente única 42, teste fixo), sem generalizar.
- Fechar a lacuna de cobertura dos testes de dados sem enfraquecer a suíte.
- Documentar pré-requisitos de sistema no README e tornar o zip regenerável com instrução de recuperação.

**Non-Goals:**
- Reexecutar o experimento, retreinar ou alterar qualquer número de `resultados/`.
- Adicionar linear probing ou múltiplas sementes (mantidos como próximo passo).
- Renomear colunas de `metricas.csv` (os nomes de coluna são identificadores de dados, não texto de apresentação; a correção de acentuação se aplica ao texto visível, como o título "Protocolo e orçamento de treino").
- Alterar o método didático de desenho de slides ou trocar de biblioteca de geração.

## Decisions

**D1: Diagrama do MAE como slide de texto em blocos com setas.**
O diagrama segue a linha de blocos do planejamento (imagem → patches → máscara → codificador → tokens de máscara → decodificador → reconstrução → perda), renderizado com as caixas de texto e formas do python-pptx que o script já usa, em vez de imagem raster externa. Alternativa descartada: PNG gerado por Matplotlib, que adicionaria dependência de estilo e impediria edição futura dos textos. O `verificar_limites` do script continua garantindo que o diagrama não sai da área do slide.

**D2: Equação e pseudocódigo como texto monoespaçado.**
A equação `L_MAE = (1/|M|) Σ_{i∈M} (1/d) ||x_i − x̂_i||²` e o pseudocódigo entram como texto em fonte monoespaçada, com um quadro lateral (ou parágrafos numerados) explicando `x_i`, `M`, `x̂_i`, `d` e a média. Alternativa descartada: imagem com a fórmula renderizada por editor externo, que romperia a regra de geração por um único script e a revisão por texto.

**D3: Comparação por tabela em dois eixos.**
A comparação usa tabela de três colunas (BERT, MAE, SimMIM) por quatro linhas (modalidade, alvo previsto, perda, arquitetura), mais o contraste MSE x L1 como linha ou nota explicativa (MSE nos pixels normalizados e média por patch contra L1 com regressão direta e cabeça linear leve). A tabela cabe no slide 16:9 com fonte reduzida já usada nos outros slides.

**D4: Cobertura dos testes de dados por verificação sintética, não por remoção de skips.**
`test_dados_md5.py` já demonstra o padrão: quando o arquivo bruto ausenta, um arquivo sintético com conteúdo qualquer é rejeitado contra o md5 esperado. O change estende esse padrão: (a) o teste que hoje imprime mensagem e retorna quando o bruto ausenta passa a rodar a verificação `verificar_md5` sobre o arquivo sintético e a validar a mensagem de erro completa (md5 obtido e esperado); (b) os skips de `test_dados.py` ganham um ramo alternativo que verifica o subconjunto gerado quando ele existe (contagens, disjunção, dtype, determinismo), limitando a ausência de verificação apenas às asserções que comparam contra o arquivo oficial bruto, com motivo explicado em comentário; (c) nenhum teste que roda hoje com dados presentes muda de comportamento. Alternativa descartada: download do CIFAR-10 no setup da suíte, que dependeria de rede e deixaria o CI mais lento e frágil.

**D5: Pré-requisitos de sistema e recuperação no README existente.**
O README ganha seção de pré-requisitos de sistema (LibreOffice `soffice` headless e `pdftoppm`, com papel de cada um) e seção de recuperação do pacote: ordem de regeneração (dados pelo script de preparação, resultados pelo notebook, slides pelo script dedicado e zip pelo script de empacotamento) e comando final. A instrução menciona que o zip não é versionado (requisito existente de dados-cifar10-subset), por isso a recuperação parte sempre dos geradores, nunca de um arquivo armazenado.

**D6: Sem mudança em `montar_zip.py` além da lista, se necessária.**
Os arquivos obrigatórios do zip não mudam (slides, código, subset, resultados e README); se o texto do slide alterar apenas conteúdo, `scripts/md5_pacote.csv` é regenerado pelo próprio script de empacotamento. Nenhum teste do empacotamento precisa de mudança.

## Risks / Trade-offs

- [Slides podem passar do máximo de 12 com o conteúdo didático novo] → o change comprime blocos existentes (por exemplo, fundir leitura dos números com limitações) e o requisito mantém o intervalo 10 a 12; `verificar_limites` continua como travessão de segurança visual; a contagem será conferida após a geração.
- [Verificações sintéticas dos testes podem dar falsa segurança se divergirem do fluxo real] → os testes sintéticos verificam a mesma função `verificar_md5` e a mesma mensagem de erro que o fluxo real usa, e o ramo com arquivo real permanece intacto para execução em ambiente completo.
- [Acentuação corrigida em texto, mas não em colunas de `metricas.csv`] → colunas são identificadores lidos pelo notebook e pelo script; renomear implicaria reexecutar o notebook, fora de escopo; o requisito de acentuação se aplica ao texto visível.
- [Diagrama em caixas pode estourar limites em resolução menor] → `verificar_limites` falha a geração antes de gravar o pptx, que é o comportamento desejado.

## Migration Plan

A ordem de aplicação é: primeiro os testes de dados (para que a suíte valide regressão antes das mudanças de conteúdo), depois `scripts/gerar_slides.py` com o conteúdo didático e a acentuação, depois o README, e por fim a regeneração dos artefatos derivados (pptx, pdf, png e zip) com reverificação visual. Não há rollback especial: os artefatos derivados são regeneráveis e os scripts ficam versionados.

## Open Questions

- O limite superior de 12 slides deve comodar diagrama, equação, pseudocódigo, aplicações e referências em slides separados ou agrupados (por exemplo, equação e pseudocódigo no mesmo slide)? Decide-se na aplicação, respeitando o requisito de contagem e a legibilidade em 20 minutos.