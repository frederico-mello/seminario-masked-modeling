"""Consolida somente registros existentes; não chama execução científica nem gates.

O gate original de execução permanece intacto. Os artefatos originais não são
reescritos; a retificação tem caminho próprio e hashes de origem explícitos.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from codigo.estudo_execucao_c0_v2 import _mediana_metricas, _resumo_refs_v1

DESTINO = RAIZ / 'openspec/changes/melhorar-reconstrucoes-mae'
V1 = RAIZ / 'resultados/estudo-melhorar-reconstrucoes-mae'
V2 = RAIZ / 'resultados/estudo-melhorar-reconstrucoes-mae-c0-v2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def consolidar():
    refs = _resumo_refs_v1()
    manifesto = json.loads((V2 / 'manifesto.json').read_text())
    fontes = ['codigo/estudo_execucao_c0_v2.py', 'scripts/retificar_validacao.py']
    origens = [V1 / 'historico.csv', V2 / 'manifesto.json', V2 / 'historico.jsonl',
               V2 / 'contador.jsonl', V2 / 'resumo.json', V2 / 'relatorio-c0-v2.md']
    dados = {
        'tipo': 'retificação documental posterior, somente registros existentes',
        'origens_sha256': {str(p.relative_to(RAIZ)): sha(p) for p in origens},
        'fontes_atuais_sha256': {p: sha(RAIZ / p) for p in fontes},
        'fonte_executor_original_sha256': manifesto['fontes_python']['arquivos']['codigo/estudo_execucao_c0_v2.py'],
        'inventario_fontes_original_sha256': manifesto['fontes_python']['sha256'],
        'hash_manifesto_v2_original': manifesto['hash_manifesto_v2'],
        'selecao_controles': 'evento=controle e estado=validacao explicitamente; nunca teste',
        'selecao_candidatos': 'evento=epoca; colunas perda_validacao e ssim_validacao; estado=concluido indica época completa',
        'referencias_validacao': refs,
    }
    linhas = ['# Retificação documental: validação v1 e interpretação v2', '',
        'Consolidação posterior de registros já existentes, sem treino, piloto, inferência ou nova consulta ao teste. '
        'O relatório v2 e seu resumo originais permanecem íntegros como evidência histórica; suas linhas de controles '
        'rotuladas como validação estavam contaminadas por eventos de teste e devem ser substituídas pelas tabelas abaixo.', '',
        'O resultado primário usa os controles com `evento=controle` e `estado=validacao` explicitamente. '
        'Nos candidatos, os eventos de época têm `estado=concluido`; as métricas vêm exclusivamente das colunas '
        '`perda_validacao` e `ssim_validacao`. Melhor é a primeira época de menor MSE; final é a última época registrada.', '',
        '## Proveniência e revisão posterior', '',
        'O código corrigido não é o executado na rodada histórica. O manifesto, os contadores, os resultados e '
        'os hashes originais não foram recongelados. O gate original continua ativo e recusa fontes atuais divergentes; '
        'este consolidador apenas lê registros e escreve novos documentos.', '',
        '| Origem | SHA-256 |', '|---|---|']
    for p,h in dados['origens_sha256'].items(): linhas.append(f'| `{p}` | `{h}` |')
    for p,h in dados['fontes_atuais_sha256'].items(): linhas.append(f'| Fonte atual `{p}` | `{h}` |')
    linhas += [f"| Executor antigo executado | `{dados['fonte_executor_original_sha256']}` |",
        f"| Inventário de fontes original | `{dados['inventario_fontes_original_sha256']}` |", '',
        '## Controles corretos de validação', '', '| Taxa | Controle | MSE | SSIM |', '|---|---|---:|---:|']
    for taxa,controles in refs['controles'].items():
        for nome,m in controles.items(): linhas.append(f"| {taxa} | {nome} | {m['mse']:.6f} | {m['ssim']:.6f} |")
    linhas += ['', '## Dados individuais por seed', '',
        '| Candidato | Taxa | Seed | Estado | Épocas | Melhor: época / MSE / SSIM | Final: época / MSE / SSIM |',
        '|---|---|---|---|---:|---|---|']
    for nome,taxas in refs['candidatos'].items():
        for taxa,seeds in taxas.items():
            for seed,item in seeds.items():
                a,b=item['melhor'],item['final']
                linhas.append(f"| {nome} | {taxa} | {seed} | {item['estado']} | {item['epocas']} | {a['epoca']} / {a['mse']:.6f} / {a['ssim']:.6f} | {b['epoca']} / {b['mse']:.6f} / {b['ssim']:.6f} |")
    linhas += ['', '## Medianas de validação e diferenças descritivas', '',
        '| Candidato | Taxa | n | MSE melhor | SSIM melhor | MSE final | SSIM final | SSIM melhor menos RGB de validação |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for nome,taxas in refs['candidatos'].items():
        for taxa,seeds in taxas.items():
            a,b=_mediana_metricas(seeds,'melhor'),_mediana_metricas(seeds,'final')
            rgb=refs['controles'][taxa]['controle_media_rgb']['ssim']
            linhas.append(f"| {nome} | {taxa} | {a['n']} | {a['mse_mediano']:.6f} | {a['ssim_mediano']:.6f} | {b['mse_mediano']:.6f} | {b['ssim_mediano']:.6f} | {a['ssim_mediano']-rgb:+.6f} |")
    linhas += ['', 'C1 a 75%: 0,362957 > RGB de validação 0,355630 (diferença +0,007327). '
        'C2 a 50%: 0,365044 > RGB de validação 0,355596 (+0,009448). '
        'RGB 0,363144 e 0,365483 são do teste e não entram nesta comparação. '
        'As medianas agregam três seeds; os controles determinísticos não constituem três réplicas independentes.', '',
        '## Conclusão e limites', '',
        'Avaliação visual aberta negativa de um único avaliador humano nas duas taxas; objetivo visual não atingido. '
        'As fichas não são cegas: o cabeçalho revela os métodos. Sem notas individuais ou preferências preenchidas. '
        'O resultado é exploratório, sem confirmação independente ou superioridade universal. '
        'C0 não teve treino completo em v1 ou v2; não se pode aplicar a regra de ganho contra C0. '
        'Os dois pilotos v2 excederam 1,25 s; os seis treinos não começaram. '
        'As 200 épocas são máximo planejado: C1, seed 10, taxa 75%, terminou em 185. '
        'A reserva v2 consumiu 0,209334139 minuto, com total v1 + v2 de 41,270848124 minutos. '
        'Nenhum julgamento visual altera a seleção numérica ou demonstra qualidade de representações.', '']
    DESTINO.mkdir(parents=True,exist_ok=True)
    (DESTINO/'retificacao-validacao.json').write_text(json.dumps(dados,ensure_ascii=False,indent=2)+'\n')
    (DESTINO/'retificacao-validacao.md').write_text('\n'.join(linhas))
    print('Retificação gerada somente de registros existentes.')


if __name__ == '__main__':
    consolidar()
