# Proposal

## Why

O material do seminário está funcional, mas incompleto frente ao planejamento em `docs/Planejamento_Masked_Modeling_em_Deep_Learning.md`: os slides atuais não trazem o diagrama do fluxo do MAE, a derivação da perda explicada termo a termo nem o pseudocódigo de treinamento exigidos para os blocos de 08:00 a 15:00 do roteiro; a comparação BERT x MAE x SimMIM não está estruturada por modalidade, alvo previsto, perda e arquitetura; e a apresentação termina sem aplicações e referências completas. Além disso, os testes de dados pulam ou retornam sem verificar nada quando o CIFAR-10 bruto não está disponível, o README não declara os pré-requisitos de sistema (LibreOffice e pdftoppm) e o zip de entrega não é recompilável pelo destinatário nem tem instrução de recuperação no repositório. A entrega é em 16/10, por isso essa lacuna precisa ser fechada agora.

## What Changes

- Slides ganham conteúdo didático completo conforme o planejamento: diagrama do fluxo do MAE (imagem, divisão em patches, máscara, codificador sobre patches visíveis, tokens de máscara, decodificador, reconstrução, perda), equação da perda MSE nos patches ocultos explicada termo a termo (x_i, M, x̂_i, d) e pseudocódigo do laço de treinamento.
- Comparação estruturada de BERT, MAE e SimMIM em modalidade, alvo previsto, perda e arquitetura, com o contraste entre erro quadrático médio e perda L1; aplicação das representações e referências completas (Devlin et al. 2019, He et al. 2022, Xie et al. 2022, Krizhevsky) no encerramento.
- Interpretação dos resultados restrita ao experimento: evidência de duas razões de máscara com conjuntos de patches aninhados e semente única 42, sem generalização; revisão de acentuação no texto do pacote (por exemplo, "orçamento" sem acento na apresentação).
- Testes de dados deixam de pular ou retornar sem verificar nada quando o CIFAR-10 bruto está ausente: ganham cobertura via verificações que não dependem do arquivo bruto ou condicional explicitamente justificada, sem enfraquecer a suíte.
- README recebe a seção de pré-requisitos de sistema (LibreOffice para a conversão pdf e pdftoppm para a inspeção png) e a instrução de recuperação do zip: regeneração a partir do repositório pelo script de empacotamento quando o arquivo não chegar ao destinatário.

## Capabilities

### New Capabilities

(nenhuma; todas as capacidades afetadas já existem no projeto)

### Modified Capabilities

- `slides-seminario`: conteúdo didático passa a ser exigido (diagrama do fluxo do MAE, equação da perda termo a termo, pseudocódigo de treinamento, comparação estruturada BERT x MAE x SimMIM com MSE x L1, aplicações e referências completas no encerramento), a interpretação dos resultados passa a ser delimitada ao experimento (semente única, máscara aninhada, sem generalização) e a acentuação correta se torna requisito de texto.
- `dados-cifar10-subset`: os testes de verificação de md5, contagens e integridade do subconjunto passam a exigir cobertura efetiva mesmo sem o CIFAR-10 bruto presente (verificação sintética ou equivalente), e qualquer teste condicional SHALL declarar explicitamente o que verifica quando o arquivo existe; retorno silencioso sem verificação deixa de ser aceito.
- `pacote-entrega`: o README do pacote passa a declarar os pré-requisitos de sistema da geração de slides (LibreOffice, pdftoppm) e SHALL documentar a recuperação do pacote: regeneração do zip a partir do repositório pelo script de empacotamento, com a ordem de produção dos artefatos que o zip exige.

## Impact

- `scripts/gerar_slides.py`: novos slides, diagrama do MAE, bloco de comparação e encerramento com referências; correção de acentuação.
- `slides/seminario_masked_modeling.pptx` e `.pdf`: regenerados e exigem reverificação visual.
- `tests/test_dados.py` e `tests/test_dados_md5.py`: alterados para eliminar pulo silencioso e retorno sem verificação; `dados/` sem CIFAR-10 bruto neste ambiente, por isso coberturas sintéticas precisam existir.
- `README.md`: novas seções de pré-requisitos de sistema e de recuperação do pacote.
- `seminario_masked_modeling.zip`: regenerado via `scripts/montar_zip.py` após a nova geração dos slides; registro em `scripts/md5_pacote.csv` atualizado.
- `resultados/`: sem alteração; nenhum experimento é reexecutado.