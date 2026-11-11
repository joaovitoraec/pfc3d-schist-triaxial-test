#!/usr/bin/env python3
# 00_gera_lote.py  [v3.4.1]  -  prepara a rodada de VARIAS amostras em sequencia no PFC
#
# Por que existe: o 'model new' do Main apaga todos os simbolos FISH, entao o nome da amostra nao pode ser passado de
# um arquivo para o outro. Este script copia o seu 00_Main_Run.dat uma vez por amostra, trocando SO a linha
#     global amostra = '...'
# (e, no modo matriz, usa_foliacao = 0 e o call do 02 comentado). Tudo mais fica igual ao seu Main (inclusive
# edicoes que voce fizer nele). Gera tambem 00_Lote_Run.dat, que chama os Mains gerados um apos o outro.
#
# Uso (rode DENTRO de 00_Inputs, ou passe --proj com a raiz do projeto):
#     python 00_gera_lote.py                      # grupo padrao: foliacao, confianca high/medium (11 amostras)
#     python 00_gera_lote.py --amostras ITA40,ITA08
#     python 00_gera_lote.py --grupo mat          # ruptura na matriz (usa_foliacao = 0)
#     python 00_gera_lote.py --pular-existentes   # pula as que ja tem o Triaxial_Histories.txt em 03_Outputs
#     python 00_gera_lote.py --listar             # so mostra o plano e as estimativas, sem escrever nada
# Depois, no PFC: rode 01_Scripts/00_Lote_Run.dat (no lugar do 00_Main_Run.dat).
#
# Limites (hipoteses, nao testadas no PFC): se uma amostra der ERRO, o PFC para o lote inteiro; corrija e gere de
# novo com --pular-existentes. Os tempos sao estimativas grosseiras da sua propria maquina (rodadas ITA40 e ITA08).
import argparse
import glob
import os
import re
import sys


def le_params(caminho):
    t = open(caminho, encoding='ascii', errors='replace').read()
    d = {'arquivo': caminho}
    m = re.search(r'ruptura\s*=\s*(\S+)\s*\|\s*confianca\s*=\s*(\S+)\s*\|\s*em analise\s*=\s*(\S+)', t)
    d['ruptura'], d['confianca'], d['em_analise'] = (m.group(1), m.group(2), m.group(3)) if m else ('?', '?', '?')
    for k in ('pressao_conf', 'foliacao_dip', 'p_sjcoh', 'p_sjfa', 'eps_ax_max', 'lab_dev_pico', 'lab_eps_pico', 'lab_E_GPa'):
        m = re.search(r'^\s*' + k + r'\s*=\s*([-+0-9.eE]+)', t, flags=re.M)
        d[k] = float(m.group(1)) if m else None
    return d


def estima(d, ciclos_max=1500000, pos_pico_frac=0.5):
    # Regra empirica das suas rodadas: ciclos ate o pico ~ 770 mil x deformacao do pico (%); para em
    # pico + pos_pico_frac x (ciclos ate o pico); 0.20 a 0.26 min por 1000 ciclos no 04; 4 a 5 min de 01 a 03.
    eps = abs(d.get('lab_eps_pico') or 0.0)
    c_pico = 770000.0 * eps
    c_tot = min(ciclos_max, 20000.0 + (1.0 + pos_pico_frac) * c_pico)
    lo = 4.0 + c_tot / 1000.0 * 0.20
    hi = 5.0 + c_tot / 1000.0 * 0.26
    return c_tot, lo, hi


def main():
    aqui = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description='Gera o lote de amostras do PFC a partir do 00_Main_Run.dat')
    ap.add_argument('--proj', default=None, help='raiz do projeto (padrao: pasta acima deste script)')
    ap.add_argument('--inputs', default=None, help='pasta dos *_params.dat (padrao: pasta deste script)')
    ap.add_argument('--scripts', default=None, help='pasta dos .dat (padrao: <proj>/01_Scripts)')
    ap.add_argument('--saidas', default=None, help='pasta de saidas (padrao: <proj>/03_Outputs)')
    ap.add_argument('--main', default='00_Main_Run.dat', help='nome do Main dentro da pasta de scripts')
    ap.add_argument('--grupo', default='fol', choices=['fol', 'mat', 'todas'],
                    help='fol = ruptura na foliacao, confianca high/medium; mat = ruptura na matriz; todas = todos os params')
    ap.add_argument('--amostras', default=None, help='lista separada por virgula (ex.: ITA40,ITA08); ignora --grupo')
    ap.add_argument('--excluir', default='', help='amostras a tirar do grupo (separadas por virgula)')
    ap.add_argument('--modo', default='auto', choices=['auto', 'fol', 'mat'],
                    help='auto = matriz se a ruptura do lab foi na matriz; senao com foliacao')
    ap.add_argument('--ordem', default='tempo', choices=['tempo', 'nome'],
                    help='tempo = mais rapidas primeiro (padrao); nome = ordem alfabetica')
    ap.add_argument('--pular-existentes', action='store_true', help='pula amostra que ja tem o Triaxial_Histories.txt')
    ap.add_argument('--listar', action='store_true', help='so mostra o plano; nao escreve arquivos')
    a = ap.parse_args()

    proj = os.path.abspath(a.proj) if a.proj else os.path.dirname(aqui)
    inputs = os.path.abspath(a.inputs) if a.inputs else aqui
    scripts = os.path.abspath(a.scripts) if a.scripts else os.path.join(proj, '01_Scripts')
    saidas = os.path.abspath(a.saidas) if a.saidas else os.path.join(proj, '03_Outputs')

    caminho_main = os.path.join(scripts, a.main)
    if not os.path.isfile(caminho_main):
        print('ERRO: nao achei o Main em', caminho_main, '(use --proj ou --scripts)')
        return 2
    bruto = open(caminho_main, 'rb').read()
    try:
        main_txt = bruto.decode('ascii')
    except UnicodeDecodeError:
        print('ERRO: o Main tem caractere nao-ASCII; o PFC pode estranhar. Corrija antes.')
        return 2
    nl = '\r\n' if '\r\n' in main_txt else '\n'
    main_txt = main_txt.replace('\r\n', '\n')

    # confere que os scripts instalados sao a v3.4 (servo do carregamento)
    p04 = os.path.join(scripts, '04_Axial_Loading.dat')
    if os.path.isfile(p04):
        if 'servo_ganho_carga' not in open(p04, encoding='ascii', errors='replace').read():
            print('AVISO: o 04_Axial_Loading.dat instalado NAO e o da v3.4 (sem servo_ganho_carga). O lote rodaria com o servo antigo.')
    else:
        print('AVISO: 04_Axial_Loading.dat nao encontrado em', scripts)

    # o Main precisa ter exatamente uma linha de amostra
    padrao_am = re.compile(r"^(\s*global\s+amostra\s*=\s*)'[^']*'(.*)$", flags=re.M)
    if len(padrao_am.findall(main_txt)) != 1:
        print("ERRO: esperava exatamente uma linha  global amostra = '...'  no Main; achei",
              len(padrao_am.findall(main_txt)))
        return 2

    arqs = sorted(glob.glob(os.path.join(inputs, '*_params.dat')))
    todos = {}
    for f in arqs:
        nome = os.path.basename(f).replace('_params.dat', '')
        todos[nome] = le_params(f)
    if not todos:
        print('ERRO: nenhum *_params.dat em', inputs)
        return 2

    if a.amostras:
        sel = [s.strip() for s in a.amostras.split(',') if s.strip()]
        faltam = [s for s in sel if s not in todos]
        if faltam:
            print('ERRO: sem params para:', ', '.join(faltam))
            return 2
    else:
        sel = []
        for n, d in todos.items():
            if a.grupo == 'fol':
                ok = d['ruptura'] == 'foliation' and d['confianca'] in ('high', 'medium') and d['em_analise'] == 'yes'
            elif a.grupo == 'mat':
                ok = d['ruptura'] == 'matrix' and d['em_analise'] == 'yes'
            else:
                ok = True
            if ok:
                sel.append(n)
    excl = [s.strip() for s in a.excluir.split(',') if s.strip()]
    sel = [s for s in sel if s not in excl]

    linhas = []
    for n in sel:
        d = todos[n]
        mat = (a.modo == 'mat') or (a.modo == 'auto' and d['ruptura'] == 'matrix')
        modo = 'Mat' if mat else 'Fol'
        sg = abs(d['pressao_conf']) / 1.0e6 if d['pressao_conf'] is not None else 0.0
        sg_txt = ('%g' % sg)
        hist = os.path.join(saidas, '%s_%s_%sMPa_Triaxial_Histories.txt' % (n, modo, sg_txt))
        existe = os.path.isfile(hist)
        c_tot, lo, hi = estima(d)
        linhas.append(dict(n=n, d=d, mat=mat, modo=modo, sg=sg, existe=existe, c_tot=c_tot, lo=lo, hi=hi, hist=hist))
    if a.pular_existentes:
        pulados = [l['n'] for l in linhas if l['existe']]
        linhas = [l for l in linhas if not l['existe']]
    else:
        pulados = []
    if a.ordem == 'tempo':
        linhas.sort(key=lambda l: (l['c_tot'], l['n']))
    if not linhas:
        print('Nada a rodar (grupo vazio ou todas ja existem).')
        return 0

    plano = []
    plano.append('PLANO DO LOTE  (estimativas grosseiras; ver comentario no topo do 00_gera_lote.py)')
    plano.append('%-7s %-4s %7s %8s %7s %7s %9s %8s %12s  %s' % ('amostra', 'modo', 's3 MPa', 'dip', 'c MPa', 'phi', 'eps_pico%', 'ciclos', 'tempo (h)', 'observacao'))
    t_lo = t_hi = 0.0
    for l in linhas:
        d = l['d']
        obs = []
        if l['mat']:
            obs.append('matriz: FJ NAO calibrado para esta rocha')
        if d['ruptura'] not in ('foliation',) and not l['mat']:
            obs.append('ruptura no lab = %s' % d['ruptura'])
        if d['confianca'] not in ('high', 'medium'):
            obs.append('confianca lab = %s' % d['confianca'])
        if l['existe']:
            obs.append('JA EXISTE saida (sera sobrescrita)')
        plano.append('%-7s %-4s %7.1f %8.2f %7.2f %7.2f %9.4f %8d %5.1f a %4.1f  %s' % (
            l['n'], l['modo'], l['sg'], d['foliacao_dip'] or 0.0, (d['p_sjcoh'] or 0.0) / 1.0e6, d['p_sjfa'] or 0.0,
            d['lab_eps_pico'] or 0.0, int(l['c_tot']),
            l['lo'] / 60.0, l['hi'] / 60.0, '; '.join(obs)))
        t_lo += l['lo']
        t_hi += l['hi']
    plano.append('TOTAL: %d amostras, %.1f a %.1f h (um computador, em sequencia)' % (len(linhas), t_lo / 60.0, t_hi / 60.0))
    if pulados:
        plano.append('Puladas (ja tem saida): ' + ', '.join(pulados))
    plano.append('Espaco em disco: cada amostra grava 4 .sav em 02_Saves (01, 02, 03, 04); confira o espaco livre antes.')
    print('\n'.join(plano))

    if a.listar:
        return 0

    os.makedirs(scripts, exist_ok=True)
    gerados = []
    for l in linhas:
        n = l['n']
        t = main_txt
        cab = ('; [LOTE] Gerado por 00_Inputs/00_gera_lote.py a partir de %s. Amostra = %s, modo = %s.\n'
               '; Nao edite este arquivo: gere de novo (ele e sobrescrito).\n' % (a.main, n, l['modo']))
        t = padrao_am.sub(lambda m: m.group(1) + "'" + n + "'" + m.group(2), t, count=1)
        if l['mat']:
            p_us = re.compile(r'^(\s*global\s+usa_foliacao\s*=\s*)\d+(.*)$', flags=re.M)
            if len(p_us.findall(t)) != 1:
                print('ERRO: esperava uma linha global usa_foliacao no Main')
                return 2
            t = p_us.sub(lambda m: m.group(1) + '0' + m.group(2), t, count=1)
            p_c2 = re.compile(r"^(\s*)call\s+'01_Scripts/02_Foliation_SJM\.dat'", flags=re.M)
            if len(p_c2.findall(t)) != 1:
                print('ERRO: esperava uma linha call do 02 no Main (modo matriz)')
                return 2
            t = p_c2.sub(lambda m: ";" + m.group(0), t, count=1)
        t = cab + t
        assert all(ord(c) < 128 for c in t)
        destino = os.path.join(scripts, 'Lote_Main_%s.dat' % n)
        with open(destino, 'w', newline='') as f:
            f.write(t.replace('\n', nl))
        gerados.append(n)

    run = []
    run.append('; =========================================================')
    run.append(';   LOTE DE AMOSTRAS  [v3.4]  - gerado por 00_Inputs/00_gera_lote.py (sobrescrito a cada geracao)')
    run.append('; =========================================================')
    run.append('; Rode ESTE arquivo no PFC no lugar do 00_Main_Run.dat. Cada linha abaixo roda uma amostra inteira (01 a 04).')
    run.append('; Se uma amostra der erro, o PFC para aqui: veja o *_Log.txt dela em 03_Outputs, corrija e gere de novo com')
    run.append(';     python 00_gera_lote.py --pular-existentes')
    run.append('; Para pular uma amostra sem gerar de novo, ponha ; no inicio da linha dela.')
    for l in linhas:
        run.append(';  %s  modo %s  sigma3 = %g MPa  dip = %.2f  tempo estimado %.1f a %.1f h' % (
            l['n'], l['modo'], l['sg'], l['d']['foliacao_dip'] or 0.0, l['lo'] / 60.0, l['hi'] / 60.0))
    run.append('')
    for l in linhas:
        run.append("call '01_Scripts/Lote_Main_%s.dat'" % l['n'])
    txt = nl.join(run) + nl
    assert all(ord(c) < 128 for c in txt)
    with open(os.path.join(scripts, '00_Lote_Run.dat'), 'w', newline='') as f:
        f.write(txt)
    with open(os.path.join(scripts, '00_Lote_Plano.txt'), 'w', newline='') as f:
        f.write(nl.join(plano) + nl)
    print('\nGerados %d Mains (Lote_Main_<amostra>.dat), 00_Lote_Run.dat e 00_Lote_Plano.txt em %s' % (len(gerados), scripts))
    print('No PFC: rode 01_Scripts/00_Lote_Run.dat. Ao fim, mande os *_Log.txt e *_Triaxial_Histories.txt de 03_Outputs.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
