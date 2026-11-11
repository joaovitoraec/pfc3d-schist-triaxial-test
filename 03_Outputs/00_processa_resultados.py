#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_processa_resultados.py - pos-processamento dos ensaios do PFC (pasta 03_Outputs)

O que faz, para cada rodada encontrada:
  1) le o arquivo de historicos gravado pelo 04_Axial_Loading.dat (<amostra>_<modo>_<sigma3>MPa_Triaxial_Histories.txt;
     o PFC grava TEXTO ALINHADO POR ESPACOS, nao CSV: por isso o Excel abria tudo em uma coluna);
  2) grava CSV de verdade:  <base>_Historico.csv            (virgula, ponto decimal: Python, R, Excel em ingles)
                            <base>_Historico_excel_ptbr.csv (ponto e virgula, virgula decimal: abre em colunas no Excel em portugues)
  3) compara com o laboratorio (curves_lab.csv ou curves.csv, se achar) e grava <base>_painel.png (2 graficos: A desviador x deformacao e B sn x tau, mais 3 tabelas) e <base>_resumo.txt;
     [24/10] <base>_diagnostico.png so tem 2 graficos: 1 desviador x deformacao axial e 2 contatos colados;
  4) [v3.4] com 2 ou mais rodadas, grava tambem resumo_geral.csv / _excel_ptbr.csv / .txt e resumo_geral_painel.png
     (uma linha por amostra: pico, E, desvio do sigma3, contatos colados restantes ... modelo x laboratorio).

Uso (na pasta 03_Outputs):
    python 00_processa_resultados.py                          # processa todos os *_Triaxial_Histories.txt da pasta
    python 00_processa_resultados.py ITA40_Fol_3MPa_Triaxial_Histories.txt
    python 00_processa_resultados.py --dados ../00_Inputs     # onde esta o curves_lab.csv (ou curves.csv) do laboratorio
    python 00_processa_resultados.py --janela rodada          # [v3.4.1] janelas pos-pico diferentes (lab 1o terco, modelo ate o fim)
              --sem-diagnostico (nao grava o _diagnostico.png);
Opcoes uteis: --inputs (pasta dos <amostra>_params.dat), --saida (padrao: ./analise), --c e --phi (plano, MPa e graus; so reserva para
              rodadas SEM a linha de parametros no log), --mu (atrito residual do plano), --raio (m), --altura (mm),
              --pos-pico-lab (fracao do tempo pos-pico do laboratorio que e usada; padrao 1/3, 1 = usa tudo).

Regra do laboratorio: depois do pico so vale o 1o terco do tempo (o resto tem muito erro de dado: descarregamento, reversao de
deformacao). Por isso a curva do lab e cortada em  t_pico + 1/3 (t_fim - t_pico)  antes de qualquer comparacao.

Precisa de: python 3, numpy, pandas, matplotlib.
v3.3.1: a curva do laboratorio passa a ser cortada no 1o terco do tempo apos o pico (--pos-pico-lab).
v3.3.2: avisa no console e no painel quando o curves.csv do laboratorio nao e encontrado (ele fica em 00_Inputs).
v3.4: o arquivo do laboratorio pode se chamar curves_lab.csv (nome usado no projeto) ou curves.csv; procura os dois.
v3.4: resumo geral entre amostras; o pos-pico do lab e do modelo passa a ser comparado pela deformacao axial dos EXTENSOMETROS
      (o deslizamento pelo atuador do lab nao e confiavel: atuador e extensometro discordam depois do pico); lab: minimo e nivel
      no fim do 1o terco pos-pico; sigma3 fora de +-5 % (dois lados); coesao implicita no fim; perfil do plano por anel (log da v3.4);
      amostras em modo matriz ou sem mergulho valido nao quebram as formulas do plano.
v3.4.1: JANELA COMUM de pos-pico. Lab e modelo sao comparados no mesmo intervalo depois do pico, medido como a fracao f do tempo ate o pico
        (lab: segundos; modelo: ciclos; a taxa de carregamento e constante nos dois, entao f vale a mesma deformacao imposta). f = o menor entre
        o que o lab permite (regra do 1o terco do tempo pos-pico) e o que a rodada do modelo cobre. --janela rodada volta ao comportamento da v3.4.
        O log passa a ser lido so a partir da ULTIMA rodada (o log acumula tentativas); le tambem as linhas 'cruzam o plano / mesmo lado' do 04 v3.4.1.
v3.4.2: [so Python] painel principal passa a ter 3 graficos no formato do Excel do usuario: (A) desviador x deformacao radial (esq.) e axial (dir.);
        (B) E instantaneo x desviador; (C) Poisson instantaneo x desviador (modelo x lab, ate o pico em B e C). Os 6 graficos antigos vao para
        <base>_diagnostico.png (nada foi apagado). Rotulo corrigido: o plano tem 'mergulho de X graus' (angulo com a horizontal), nao 'X graus do eixo'.
        Pico = 1o pico travado, pela mesma regra do 04 (queda de 10 % do maximo); antes era o maximo global, que difere se o pos-pico endurece de novo
        acima do 1o pico (ex.: ITA42). Para as rodadas em que o 1o pico e o maximo global nada muda.
pacote v3.4.1 (sobre o Python v3.4.2): (a) c, phi e mu do plano vem da RODADA (linha 'Parametros do plano aplicados' do log, escrita pelo 02;
        senao do params.dat; senao --c/--phi/--mu): a envoltoria e a coesao implicita usam o que o modelo realmente usou;
        (b) o painel traz os dados do laboratorio, o calculo de c e phi do plano (sn, tau, ajuste comum, usado no modelo) e o diagrama sn x tau com o
        ponto do lab e o do modelo; (c) SAIU o Poisson (grafico, textos, colunas): o modelo e elastico ate o pico e o lab e inelastico, as curvas nao
        sao comparaveis. E instantaneo e curvas desviador x deformacao continuam.
        [ajuste de 24/10, so layout] legenda do grafico C no canto superior esquerdo (nao cobre mais os pontos), marca 'c' no eixo, rodape quebrado
        em linhas; o texto sobre o 04 passou a dizer que o 04 atual nao separa contatos que cruzam o plano dos de mesmo bloco.
        [ajuste de 24/10 (2), so graficos] PAINEL: saiu o grafico de E instantaneo e o rodape cinza; o grafico do plano virou B (legenda fora do
        grafico); lab, calculo de c e phi e modelo x lab agora sao TABELAS (os avisos de origem de c e phi e de curves_lab ausente estao nelas).
        DIAGNOSTICO: so ficaram o antigo 1 (desviador x deformacao axial) e o antigo 6 (contatos colados, agora numerado 2); os outros 4 graficos
        (deformacao radial, pos-pico em f, servo lateral, prato x esfera) foram tirados; os numeros continuam no _resumo.txt e no _Historico.csv.
v4: [so Python] (a) leque: para as amostras cujo .dat traz 'LEQUE a = ...' o resumo, o painel e o resumo_geral mostram o a da amostra, a reta
        usada (tau = c + tan(phi) sn) e as equacoes do leque (c(a), tan(phi(a)) e a em funcao de tau e sn; as ancoras sao lidas dos .dat); o grafico B
        mostra o leque (a = 0 e a = 1) no lugar da reta comum. (b) SAIU o aviso 'c e/ou phi diferem do ajuste comum' para as amostras do leque.
        (c) SAIU o E tangente 40-60 % (so o E secante fica): resumo, painel, resumo_geral (colunas E_tang_*). O resto e igual a v3.4.2.
Le tambem as 12 colunas da v3.1/v3.2; as colunas de contatos colados (sj_colados, fj_colados) existem a partir da v3.3.
"""
import argparse
import copy
import glob
import io
import math
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd

# ---------------------------------------------------------------- colunas (mesma ordem do 'history export' do 04)
COLUNAS_12 = ["ciclo", "eps_ax_pct", "eps_rad_pct", "eps_vol_pct", "dev_MPa", "sigma1_MPa", "conf_MPa",
              "eps_ax_A_pct", "eps_ax_B_pct", "eps_ax_plat_pct", "sigma1_prato_MPa", "mu_mob_prato"]
COLUNAS_14 = COLUNAS_12 + ["sj_colados", "fj_colados"]

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e3e1da"
AZUL, LARANJA, VERDE, ROXO = "#2a78d6", "#eb6834", "#2f9e6b", "#7b5cc4"


def v(x, n=1, sinal=False):
    """numero com virgula decimal (texto dos graficos e do resumo); sinal=True escreve + nos positivos"""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/d"
    if round(x, n) == 0:
        x = 0.0                                   # sem "-0,0"
    return f"{x:+.{n}f}".replace(".", ",") if sinal else f"{x:.{n}f}".replace(".", ",")


# ---------------------------------------------------------------- leitura
def le_pfc(caminho):
    """Le o texto do PFC: 2 linhas de cabecalho (nomes truncados + tracejado) e uma linha por amostragem."""
    with open(caminho, encoding="ascii", errors="ignore") as f:
        linhas = f.read().splitlines()
    ini = None
    for i, ln in enumerate(linhas[:10]):
        if re.fullmatch(r"[\s\-]+", ln) and "-" in ln:
            ini = i + 1
            break
    if ini is None:
        raise ValueError("nao achei a linha tracejada do cabecalho do PFC em " + caminho)
    corpo = "\n".join(l for l in linhas[ini:] if l.strip())
    df = pd.read_csv(io.StringIO(corpo), sep=r"\s+", header=None)
    if df.shape[1] == 14:
        df.columns = COLUNAS_14
    elif df.shape[1] == 12:
        df.columns = COLUNAS_12
    else:
        raise ValueError(f"{caminho}: {df.shape[1]} colunas (esperado 12 ou 14). A lista do 'history export' no 04 mudou?")
    return df


def meta_do_nome(caminho):
    m = re.match(r"^(ITA\d+)_(Fol|Mat)_([\d.]+)MPa_Triaxial_Histories", os.path.basename(caminho))
    if not m:
        return None, None, None
    return m.group(1), m.group(2), float(m.group(3))


def le_dat(arq):
    """um <amostra>_params.dat: numeros (pressao_conf, foliacao_dip, p_sjcoh, p_sjfa, lab_dev_pico, lab_eps_pico, lab_E_GPa ...) e,
    do comentario do cabecalho, _ruptura, _confianca, _em_analise e _ajuste ('ajuste do plano' = yes/no/check; None nos .dat antigos)"""
    d = {}
    txt = open(arq, encoding="ascii", errors="ignore").read()
    for ln in txt.splitlines():
        m = re.match(r"^\s*(\w+)\s*=\s*([-+0-9.eE]+)\s*$", ln.split(";")[0])
        if m:
            d[m.group(1)] = float(m.group(2))
    m = re.search(r"ruptura\s*=\s*(\S+)\s*\|\s*confianca\s*=\s*(\S+)\s*\|\s*em analise\s*=\s*(\S+)", txt)
    d["_ruptura"], d["_confianca"], d["_em_analise"] = m.groups() if m else ("?", "?", "?")
    m = re.search(r"ajuste do plano\s*=\s*(\S+)", txt)
    d["_ajuste"] = m.group(1) if m else None
    m = re.search(r"LEQUE a\s*=\s*([-+0-9.]+)", txt)                  # [v4] so nos .dat que receberam o leque
    d["_a_leque"] = float(m.group(1)) if m else None
    d["_arquivo"] = arq
    return d


def le_params(amostra, pastas):
    """<amostra>_params.dat do 00_Inputs"""
    for p in pastas:
        arq = os.path.join(p, f"{amostra}_params.dat")
        if os.path.isfile(arq):
            return le_dat(arq)
    return {}


# ---------------------------------------------------------------- plano: tensoes, ajuste comum e o que a rodada usou [v3.4.1]
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179,
        13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086}      # t de Student, 97,5 %, por grau de liberdade


def tensoes_plano(s3, D, dip_deg):
    """equilibrio no plano de mergulho dip (sigma1 vertical): sn = s3 + D cos^2(th); tau = D sin(th) cos(th)"""
    th = math.radians(dip_deg)
    return s3 + D * math.cos(th) ** 2, D * math.sin(th) * math.cos(th)


def ajusta_reta(sn, tau):
    """minimos quadrados de tau = c + sn tan(phi) (mesma conta do 01_fit_plano_foliacao.py)"""
    sn, tau = np.asarray(sn, dtype=float), np.asarray(tau, dtype=float)
    n = len(sn)
    tp, c = np.polyfit(sn, tau, 1)
    res = tau - (c + tp * sn)
    s = math.sqrt((res ** 2).sum() / (n - 2))
    sxx = float(((sn - sn.mean()) ** 2).sum())
    se_tp, se_c = s / math.sqrt(sxx), s * math.sqrt(1.0 / n + sn.mean() ** 2 / sxx)
    t = T975.get(n - 2, 1.96)
    return {"n": n, "c": float(c), "tanphi": float(tp), "phi": math.degrees(math.atan(tp)), "s": s, "se_c": se_c, "t": t,
            "r2": 1.0 - float((res ** 2).sum()) / float(((tau - tau.mean()) ** 2).sum()), "xbar": float(sn.mean()), "sxx": sxx,
            "ci_c": (float(c) - t * se_c, float(c) + t * se_c),
            "ci_phi": (math.degrees(math.atan(tp - t * se_tp)), math.degrees(math.atan(tp + t * se_tp)))}


def le_ajuste_plano(pastas):
    """ajuste comum do plano com os .dat que dizem 'ajuste do plano = yes' (use_plane_fit do banco). None se nao houver (.dat antigos)"""
    for p in pastas:
        arqs = sorted(glob.glob(os.path.join(p, "ITA*_params.dat")))
        if not arqs:
            continue
        pts = []
        for arq in arqs:
            d = le_dat(arq)
            if d.get("_ajuste") == "yes" and d.get("lab_dev_pico", 0) > 0 and d.get("foliacao_dip", 0) > 0 and "pressao_conf" in d:
                sn, tau = tensoes_plano(abs(d["pressao_conf"]) / 1e6, d["lab_dev_pico"], d["foliacao_dip"])
                pts.append((re.search(r"ITA\d+", os.path.basename(arq)).group(0), sn, tau))
        if len(pts) >= 4:
            return {"pts": pts, "fit": ajusta_reta([x[1] for x in pts], [x[2] for x in pts]), "pasta": os.path.normpath(p)}
        return None
    return None


# ---------------------------------------------------------------- leque [v4]
ANC_CIMA = ("ITA901", "ITA906")        # a = 1  (DEVEM ser iguais as do 00_gera_params.py)
ANC_BAIXO = ("ITA902", "ITA905")       # a = 0


def reta_2pts(p1, p2):
    """(c, m) de tau = c + m sn pela reta que passa nos pontos p1 e p2 (sn, tau)"""
    m = (p2[1] - p1[1]) / (p2[0] - p1[0])
    return p1[1] - m * p1[0], m


def le_leque(pastas):
    """[v4] leque (as duas retas extremas) recalculado das amostras ancora (.dat da pasta de inputs): mesma conta do 00_gera_params.py.
    Devolve dict(cl, ml, cu, mu, dc, dm) ou None se faltar alguma ancora."""
    for p in pastas:
        pts = {}
        for k in ANC_CIMA + ANC_BAIXO:
            arq = os.path.join(p, f"{k}_params.dat")
            if not os.path.isfile(arq):
                break
            d = le_dat(arq)
            if not (d.get("lab_dev_pico", 0) > 0 and d.get("foliacao_dip", 0) > 0 and "pressao_conf" in d):
                break
            pts[k] = tensoes_plano(abs(d["pressao_conf"]) / 1e6, d["lab_dev_pico"], d["foliacao_dip"])
        else:
            cu, mu = reta_2pts(pts[ANC_CIMA[0]], pts[ANC_CIMA[1]])
            cl, ml = reta_2pts(pts[ANC_BAIXO[0]], pts[ANC_BAIXO[1]])
            return {"cl": cl, "ml": ml, "cu": cu, "mu": mu, "dc": cu - cl, "dm": mu - ml}
    return None


def a_do_ponto(L, sn, tau):
    """a da reta do leque que passa em (sn, tau): a = (tau - cl - ml sn) / (dc + dm sn)"""
    return (tau - L["cl"] - L["ml"] * sn) / (L["dc"] + L["dm"] * sn)


RE_PLANO_AP = re.compile(r"Parametros do plano aplicados:\s*c\s*=\s*([-+0-9.eE]+)\s*MPa\s+phi\s*=\s*([-+0-9.eE]+)\s*graus\s+"
                         r"atrito residual \(sj_fric\)\s*=\s*([-+0-9.eE]+)")


def plano_aplicado(base, pasta, params, a):
    """c (MPa), phi (graus) e mu do plano que a RODADA usou. 1) linha do log (02 da v3.4.1); 2) log sem a linha = rodada de antes da v3.4.1:
    valores padrao do Main antigo (--c, --phi, --mu); 3) sem log: params.dat; 4) --c, --phi, --mu. Devolve (c, phi, mu, origem, aviso)."""
    arq, linhas, _ = acha_log(base, pasta)
    c_dat, f_dat = params.get("p_sjcoh", float("nan")) / 1e6, params.get("p_sjfa", float("nan"))
    ms = [m for m in (RE_PLANO_AP.search(l) for l in linhas) if m]
    aviso = None
    if ms:
        c, f, mu = (float(x) for x in ms[-1].groups())
        origem = "log da rodada"
        if np.isfinite(c_dat) and (abs(c - c_dat) > 0.01 or abs(f - f_dat) > 0.01):
            aviso = (f"o params.dat de agora (c = {v(c_dat, 2)} MPa, phi = {v(f_dat, 2)} graus) difere do que a rodada usou: o .dat foi gerado de novo depois dela; "
                     "valem os numeros do log")
    elif arq is not None:
        c, f, mu = a.c, a.phi, a.mu
        origem = "rodada anterior a v3.4.1 (sem a linha no log): valores padrao do Main antigo (--c, --phi, --mu)"
    elif np.isfinite(c_dat) and np.isfinite(f_dat):
        c, f, mu = c_dat, f_dat, a.mu
        origem = "params.dat (sem log para conferir)"
    else:
        c, f, mu = a.c, a.phi, a.mu
        origem = "valores de reserva (--c, --phi, --mu)"
    return c, f, mu, origem, aviso


def le_lab(amostra, pastas):
    for p in pastas:
        arq = next((os.path.join(p, n) for n in ("curves_lab.csv", "curves.csv") if os.path.isfile(os.path.join(p, n))), None)
        if arq:
            cols = ["id_ita", "t_rel_s", "ax_disp_mm", "eps_ax_pct", "eps_rad_pct", "dev_MPa", "conf_MPa"]
            cols += [c for c in ("E_inst_GPa", "nu_inst") if c in pd.read_csv(arq, nrows=0).columns]     # [v3.4.2] opcionais (painel B e C)
            lab = pd.read_csv(arq, usecols=cols)
            lab = lab[(lab.id_ita == amostra) & lab.eps_ax_pct.notna()].sort_values("t_rel_s").reset_index(drop=True)
            if len(lab):
                return lab, arq
    return None, None


def primeiro_pico(dev, ref_lab=0.0, queda=0.90, pico_min=5.0, pico_min_lab=0.5):
    """[v3.4.2] indice do 1o PICO pela MESMA regra do 04 (halt_axial): acompanha o maximo e, quando o desviador cai abaixo de
    queda x maximo (com o maximo acima de pico_min, ou de pico_min_lab x pico do lab se for maior), o pico fica travado.
    Sem queda: maximo ate o fim. Antes (v3.4.1) era o maximo global, que difere se o pos-pico endurece de novo acima do 1o pico."""
    dev = np.asarray(dev, dtype=float)
    pm = max(pico_min, pico_min_lab * ref_lab) if ref_lab and ref_lab > 0 else pico_min
    km = 0
    for k in range(len(dev)):
        if dev[k] > dev[km]:
            km = k
        if dev[km] > pm and dev[k] < queda * dev[km]:
            return km
    return km


def corta_lab_f(lab, f):
    """[v3.4.1] mantem do lab so o que vem ate t_pico + f*(t_pico - t_inicio): f = fracao do tempo ATE o pico (None = nao corta)"""
    if lab is None or f is None or not np.isfinite(f):
        return lab
    kl = int(lab.dev_MPa.idxmax())
    t_i, t_pk = lab.t_rel_s.iloc[0], lab.t_rel_s[kl]
    return lab[lab.t_rel_s <= t_pk + f * (t_pk - t_i)].reset_index(drop=True)


def janela_comum(df, lab, a, c0_log):
    """[v3.4.1] janela pos-pico: f = (tempo depois do pico) / (tempo ate o pico). No lab o tempo e em segundos (t_rel_s, desde o inicio do
    carregamento); no modelo e em ciclos desde o inicio do carregamento (c0, lido do log; sem log, a 1a amostragem). A taxa de carregamento
    e constante nos dois, entao f corresponde a mesma deformacao imposta depois do pico.
    --janela comum : f = menor entre o que o lab permite (1o terco do tempo pos-pico) e o que a rodada do modelo cobre; os dois usam o mesmo f.
    --janela rodada: comportamento da v3.4 (lab ate o 1o terco; modelo ate o fim da rodada; as janelas podem ser diferentes)."""
    j = {"modo": a.janela}
    ref_lab = float(lab.dev_MPa.max()) if lab is not None else 0.0
    ip = primeiro_pico(df.dev_MPa.values, ref_lab)      # [v3.4.2] 1o pico travado (regra do 04), nao o maximo global
    j["ip"] = ip
    cp, cf = float(df.ciclo[ip]), float(df.ciclo.iloc[-1])
    if c0_log is not None and 0 <= c0_log < cp:
        c0, j["origem_c0"] = float(c0_log), "log"
    else:
        c0, j["origem_c0"] = float(df.ciclo.iloc[0]), "1a amostragem"
    j["c0"], j["cp"], j["cf"], j["n_ate"] = c0, cp, cf, cp - c0
    j["f_mod"] = (cf - cp) / j["n_ate"]
    nan = float("nan")
    j["f_lab"] = j["lab_t_pk"] = j["lab_t_i"] = j["lab_t_fim"] = j["lab_t_ate_pico"] = nan
    j["frac_lab"] = a.pos_pico_lab if 0.0 < a.pos_pico_lab < 1.0 else 1.0
    if lab is not None:
        kl = int(lab.dev_MPa.idxmax())
        j["lab_t_i"], j["lab_t_pk"], j["lab_t_fim"] = float(lab.t_rel_s.iloc[0]), float(lab.t_rel_s[kl]), float(lab.t_rel_s.iloc[-1])
        j["lab_t_ate_pico"] = j["lab_t_pk"] - j["lab_t_i"]
        j["f_lab"] = j["frac_lab"] * (j["lab_t_fim"] - j["lab_t_pk"]) / j["lab_t_ate_pico"]
    if j["modo"] == "comum" and lab is not None:
        j["f"] = min(j["f_lab"], j["f_mod"])
        j["limita"] = "laboratorio" if j["f_lab"] <= j["f_mod"] else "modelo"
        j["f_lab_jan"] = j["f_mod_jan"] = j["f"]
    elif j["modo"] == "comum":                 # sem lab: janela = rodada inteira do modelo
        j["f"], j["limita"], j["f_lab_jan"], j["f_mod_jan"] = j["f_mod"], "modelo", nan, j["f_mod"]
    else:
        j["f"], j["limita"], j["f_lab_jan"], j["f_mod_jan"] = nan, "", j["f_lab"], j["f_mod"]
    j["ciclo_lim"] = cp + j["f_mod_jan"] * j["n_ate"]
    return j


# ---------------------------------------------------------------- mecanica (formulas idealizadas: blocos rigidos, tensao uniforme)
def dev_envoltoria(c_mpa, phi_deg, sigma3, dip_deg):
    """desviador de pico de um plano de fraqueza (Jaeger): tau = c + sn tan(phi), plano com normal a 'dip' do eixo"""
    th, mu = math.radians(dip_deg), math.tan(math.radians(phi_deg))
    return (c_mpa + mu * sigma3) / (math.cos(th) * (math.sin(th) - mu * math.cos(th)))


def dev_atrito(mu, sigma3, dip_deg):
    """desviador de deslizamento so por atrito (sem coesao)"""
    th = math.radians(dip_deg)
    den = 1.0 - mu / math.tan(th)
    return float("inf") if den <= 0 else sigma3 * ((1.0 + mu * math.tan(th)) / den - 1.0)


def mu_equivalente(dev, sigma3, dip_deg):
    """atrito que explicaria 'dev' se o plano deslizasse so por atrito, sem coesao"""
    th = math.radians(dip_deg)
    r = (dev + sigma3) / sigma3
    return (r - 1.0) / (math.tan(th) + r / math.tan(th))


def coesao_implicita(dev, sigma3, dip_deg, mu):
    """[v3.4] coesao (MPa) que, com atrito mu, explicaria 'dev' no plano: c = D cos(th)(sin(th) - mu cos(th)) - mu sigma3.
    No fim do ensaio, c/c_plano ~ fracao do plano que ainda resiste como se estivesse colada (inferencia, formula idealizada)."""
    th = math.radians(dip_deg)
    return dev * math.cos(th) * (math.sin(th) - mu * math.cos(th)) - mu * sigma3


# ---------------------------------------------------------------- analise
def analisa(df, lab, params, a, modo="Fol", jan=None):
    r = {"jan": jan}
    h = float(np.median(np.diff(df.ciclo))) if len(df) > 1 else 500.0
    dip = params.get("foliacao_dip", a.dip)
    s3 = abs(params.get("pressao_conf", -a.s3 * 1e6)) / 1e6 if "pressao_conf" in params else a.s3
    r["dip"], r["s3"], r["intervalo"] = dip, s3, h
    # [v3.4] formulas do plano so valem com foliacao e mergulho entre 5 e 85 graus (modo Mat ou dip 0 nao tem plano)
    plano = (modo == "Fol") and 5.0 < dip < 85.0
    r["plano"] = plano
    ip = jan["ip"]                                        # [v3.4.2] 1o pico travado (regra do 04), calculado em janela_comum
    r["ip"] = ip
    r["max_global"], r["ciclo_max_global"] = float(df.dev_MPa.max()), int(df.ciclo[df.dev_MPa.idxmax()])
    r["pico"], r["eps_pico"], r["ciclo_pico"] = df.dev_MPa[ip], df.eps_ax_pct[ip], df.ciclo[ip]
    r["conf_pico"], r["eps_plat_pico"] = df.conf_MPa[ip], df.eps_ax_plat_pct[ip]
    r["ciclo_ini"] = df.ciclo.iloc[0]
    ref = params.get("lab_dev_pico", 0.0)
    if lab is not None:
        kl = int(lab.dev_MPa.idxmax())
        r["kl"] = kl
        r["lab_pico"], r["lab_eps_pico"] = lab.dev_MPa[kl], lab.eps_ax_pct[kl]
        ref = ref if ref > 0 else r["lab_pico"]
    else:
        ref = ref if ref > 0 else r["pico"]
        r["lab_pico"] = params.get("lab_dev_pico", float("nan"))
        r["lab_eps_pico"] = params.get("lab_eps_pico", float("nan"))
    r["ref"] = ref
    r["Esec"] = r["pico"] / (r["eps_pico"] / 100.0) / 1000.0
    if lab is not None:
        r["lab_Esec"] = r["lab_pico"] / (r["lab_eps_pico"] / 100.0) / 1000.0
    else:
        r["lab_Esec"] = float("nan")
    # envoltoria do plano
    r["env"] = dev_envoltoria(a.c, a.phi, s3, dip) if plano else float("nan")
    # pos-pico
    pos = df.iloc[ip:]
    jm = int(pos.dev_MPa.idxmin())
    r["min_pos"], r["ciclo_min_pos"] = df.dev_MPa[jm], df.ciclo[jm]
    r["fim"], r["eps_fim"], r["eps_plat_fim"] = df.dev_MPa.iloc[-1], df.eps_ax_pct.iloc[-1], df.eps_ax_plat_pct.iloc[-1]
    r["conf_fim"], r["ciclo_fim"] = df.conf_MPa.iloc[-1], df.ciclo.iloc[-1]
    r["ciclos_pos"] = r["ciclo_fim"] - r["ciclo_pico"]
    sn = math.sin(math.radians(dip)) if plano else float("nan")
    df["deslizamento_mm"] = (df.eps_ax_plat_pct - r["eps_plat_pico"]) / 100.0 * a.altura / sn
    r["slip_fim"] = df.deslizamento_mm.iloc[-1]
    df.loc[df.ciclo < r["ciclo_pico"], "deslizamento_mm"] = np.nan   # so faz sentido depois do pico
    # [v3.4] deformacao axial dos extensometros contada a partir do pico (comparavel com o lab; nao usa o atuador)
    df["d_eps_ax_pos_pct"] = df.eps_ax_pct - r["eps_pico"]
    df.loc[df.ciclo < r["ciclo_pico"], "d_eps_ax_pos_pct"] = np.nan
    r["mu_eq_fim"] = mu_equivalente(r["fim"], r["conf_fim"], dip) if plano else float("nan")
    r["mu_eq_fim_nominal"] = mu_equivalente(r["fim"], s3, dip) if plano else float("nan")
    r["D_atrito"] = dev_atrito(a.mu, s3, dip) if plano else float("nan")
    # [v3.4] coesao implicita no fim e no minimo pos-pico (c do plano = a.c)
    r["c_impl_fim"] = coesao_implicita(r["fim"], r["conf_fim"], dip, a.mu) if plano else float("nan")
    r["c_impl_min"] = coesao_implicita(r["min_pos"], s3, dip, a.mu) if plano else float("nan")
    # servo lateral
    r["conf_max"] = df.conf_MPa.max()
    r["conf_min"] = df.conf_MPa.min()
    r["n5"] = int((df.conf_MPa > 1.05 * s3).sum() * h)
    r["n10"] = int((df.conf_MPa > 1.10 * s3).sum() * h)
    r["n100"] = int((df.conf_MPa > 2.0 * s3).sum() * h)
    # [v3.4] criterio do projeto: sigma3 dentro de +-5 % do alvo (o lab varia no maximo 5 %)
    dv3 = (df.conf_MPa / s3 - 1.0) * 100.0
    fora = dv3.abs() > 5.0
    antes = df.ciclo <= r["ciclo_pico"]
    r["conf_dev_max_pct"] = float(dv3.abs().max())
    r["conf_dev_max_sinal_pct"] = float(dv3.loc[dv3.abs().idxmax()])
    r["conf_fora5_pct"] = float(100.0 * fora.mean())
    r["conf_fora5_pre_pct"] = float(100.0 * fora[antes].mean()) if antes.any() else float("nan")
    r["conf_fora5_pos_pct"] = float(100.0 * fora[~antes].mean()) if (~antes).any() else float("nan")
    r["conf_dev_pre_max_pct"] = float(dv3[antes].abs().max()) if antes.any() else float("nan")
    # prato x esfera (so pre-pico, depois do transiente inicial)
    m = (df.ciclo > df.ciclo.iloc[0] + 20000) & (df.ciclo < r["ciclo_pico"] - 5000)
    rat = (df.sigma1_prato_MPa / df.sigma1_MPa)[m]
    r["razao_prato"] = float(rat.median()) if len(rat) else float("nan")
    r["raio_ef_mm"] = a.raio * 1000.0 * math.sqrt(r["razao_prato"]) if len(rat) else float("nan")
    r["mu_prato_max"] = df.mu_mob_prato.max()
    df["dev_prato_MPa"] = df.sigma1_prato_MPa - df.conf_MPa
    r["pico_prato"] = df.dev_prato_MPa.max()
    # contatos colados
    r["tem_colados"] = "sj_colados" in df.columns
    if r["tem_colados"]:
        r["sj0"], r["sj_pico"], r["sj_fim"] = df.sj_colados.iloc[0], df.sj_colados[ip], df.sj_colados.iloc[-1]
        r["fj0"], r["fj_pico"], r["fj_fim"] = df.fj_colados.iloc[0], df.fj_colados[ip], df.fj_colados.iloc[-1]
        df["sj_colados_frac"] = df.sj_colados / max(r["sj0"], 1)
        df["fj_colados_frac"] = df.fj_colados / max(r["fj0"], 1)
    # [v3.4] laboratorio no pos-pico (ja cortado no 1o terco do tempo): minimo, nivel no fim da janela e curva contra a deformacao
    # axial dos EXTENSOMETROS depois do pico. O deslizamento pelo atuador nao e usado: atuador e extensometro discordam no pos-pico.
    nan = float("nan")
    r["lab_min_pos"] = r["lab_fim_janela"] = r["lab_med_pos"] = r["lab_mu_eq"] = r["lab_mu_eq_fim"] = nan
    r["lab_c_impl_min"] = r["lab_c_impl_fim"] = r["lab_s3"] = r["lab_deps_fim"] = nan
    r["lab_conf_dev_max_pct"] = nan
    r["lab_n_jan"] = 0
    if lab is not None:
        lab = lab.copy()
        lab["d_eps_ax_pos_pct"] = lab.eps_ax_pct - lab.eps_ax_pct[kl]
        seg = lab.iloc[kl:]
        r["lab_s3"] = float(lab.conf_MPa.iloc[: kl + 1].median()) if "conf_MPa" in lab.columns and lab.conf_MPa.notna().any() else nan
        s3l = r["lab_s3"] if np.isfinite(r["lab_s3"]) and r["lab_s3"] > 0 else s3
        if len(seg) > 1:
            r["lab_n_jan"] = len(seg) - 1
            r["lab_min_pos"] = float(seg.dev_MPa.min())
            r["lab_med_pos"] = float(seg.dev_MPa.iloc[1:].median())
            nfim = max(3, int(0.1 * len(seg)))
            r["lab_fim_janela"] = float(seg.dev_MPa.iloc[-nfim:].median())      # mediana dos ultimos 10 % da janela
            r["lab_deps_fim"] = float(seg.d_eps_ax_pos_pct.iloc[-1])
            if plano:
                r["lab_mu_eq"] = mu_equivalente(r["lab_min_pos"], s3l, dip)
                r["lab_mu_eq_fim"] = mu_equivalente(r["lab_fim_janela"], s3l, dip)
                r["lab_c_impl_min"] = coesao_implicita(r["lab_min_pos"], s3l, dip, a.mu)
                r["lab_c_impl_fim"] = coesao_implicita(r["lab_fim_janela"], s3l, dip, a.mu)
        if "conf_MPa" in lab.columns and lab.conf_MPa.notna().any() and s3l > 0:
            r["lab_conf_dev_max_pct"] = float(((lab.conf_MPa / s3l - 1.0) * 100.0).abs().max())
    # [v3.4.1] modelo dentro da janela pos-pico (a mesma do lab): minimo, nivel no fim (mediana dos ultimos 10 %), deformacao, atrito e coesao
    jn = r["jan"]
    pj = df[(df.ciclo >= r["ciclo_pico"]) & (df.ciclo <= jn["ciclo_lim"] + 0.5)]
    jm2 = int(pj.dev_MPa.idxmin())
    r["jan_min"], r["jan_ciclo_min"], r["jan_conf_min"] = df.dev_MPa[jm2], df.ciclo[jm2], df.conf_MPa[jm2]
    nfj = max(3, int(0.1 * len(pj)))
    r["jan_fim"] = float(pj.dev_MPa.iloc[-nfj:].median())
    r["jan_conf_fim"] = float(pj.conf_MPa.iloc[-nfj:].median())
    r["jan_ciclo_fim"] = int(pj.ciclo.iloc[-1])
    r["jan_n"] = len(pj) - 1
    r["jan_deps_fim"] = float(pj.d_eps_ax_pos_pct.iloc[-1])
    dvj = (pj.conf_MPa / s3 - 1.0) * 100.0
    r["jan_conf_dev_max_pct"] = float(dvj.abs().max())
    r["jan_conf_fora5_pct"] = float(100.0 * (dvj.abs() > 5.0).mean())
    r["jan_mu_eq_min"] = r["jan_mu_eq_fim"] = r["jan_c_impl_min"] = r["jan_c_impl_fim"] = float("nan")
    if plano:
        r["jan_mu_eq_min"] = mu_equivalente(r["jan_min"], r["jan_conf_min"], dip)
        r["jan_mu_eq_fim"] = mu_equivalente(r["jan_fim"], r["jan_conf_fim"], dip)
        r["jan_c_impl_min"] = coesao_implicita(r["jan_min"], r["jan_conf_min"], dip, a.mu)
        r["jan_c_impl_fim"] = coesao_implicita(r["jan_fim"], r["jan_conf_fim"], dip, a.mu)
    return r, df, lab


def texto_janela(r, lab_ok):
    """[v3.4.1] bloco do resumo que descreve a janela pos-pico e compara modelo x lab dentro dela"""
    j = r["jan"]
    L = ["JANELA POS-PICO (o mesmo intervalo de tempo no modelo e no laboratorio)", "-" * 78,
         "f = tempo depois do pico / tempo ate o pico (lab em segundos, modelo em ciclos). Ate o pico os dois carregam em taxa constante (modelo: velocidade",
         "do prato; lab: 0,0005 %/s nos extensometros), entao ciclos do modelo <-> segundos do lab se correspondem (inferencia)."]
    if lab_ok:
        L.append(f"laboratorio: pico em {v(j['lab_t_pk'], 0)} s, ultimo dado em {v(j['lab_t_fim'], 0)} s; so vale o 1o terco do tempo pos-pico -> "
                 f"f ate {v(j['f_lab'], 3)} ({v(j['f_lab'] * j['lab_t_ate_pico'], 0)} s depois do pico)")
    else:
        L.append("laboratorio: curves_lab.csv nao encontrado (sem comparacao; janela = rodada inteira do modelo)")
    if lab_ok:
        L.append("ATENCAO (inferencia): o lab e controlado pelo extensometro (la, deformacao do extensometro = taxa x tempo, tambem depois do pico); o modelo e controlado")
        L.append("pelo prato, e depois do pico o extensometro anda mais rapido que o prato (o plano desliza dentro da base de medida). Por isso, no mesmo f, a")
        L.append("'def. axial apos o pico' do modelo sai maior que a do lab (linha da tabela abaixo): no mesmo tempo o modelo desliza mais que o lab.")
    L.append(f"modelo     : pico no ciclo {int(j['cp'])} ({int(j['n_ate'])} ciclos de carregamento, inicio lido de: {j['origem_c0']}); a rodada vai ate o ciclo {int(j['cf'])} "
             f"-> f ate {v(j['f_mod'], 3)} ({int(j['cf'] - j['cp'])} ciclos)")
    if j["modo"] == "comum":
        extra = f"; lab: {v(j['f'] * j['lab_t_ate_pico'], 0)} s depois do pico ({r['lab_n_jan']} amostras)" if lab_ok else ""
        L.append(f"janela adotada: f = {v(j['f'], 3)} (limitada pelo {j['limita']}) -> modelo: ate o ciclo {r['jan_ciclo_fim']} ({r['jan_n']} amostragens depois do pico){extra}")
        if lab_ok and j["limita"] == "modelo":
            L.append(f"   o MODELO limita: a rodada cobre so parte da janela valida do lab (f = {v(j['f_lab'], 2)}). Para cobrir toda ela, rodar com pos_pico_frac ~ {v(j['f_lab'], 1)} no 04.")
        elif lab_ok:
            L.append(f"   o LAB limita: o modelo foi {int(j['cf'] - r['jan_ciclo_fim'])} ciclos alem da janela; esse trecho fica tracejado nos paineis e fora das comparacoes abaixo.")
    else:
        L.append(f"AVISO (--janela rodada): janelas DIFERENTES: lab ate f = {v(j['f_lab'], 3)}, modelo ate f = {v(j['f_mod'], 3)}. Use --janela comum para o mesmo intervalo.")
    return L


def texto_plano(r, lab_ok):
    """[v3.4.1] dados do laboratorio e calculo de c e phi do plano (as mesmas contas do painel)"""
    p = r["params"]
    L = ["DADOS DO LABORATORIO E CALCULO DE c E phi DO PLANO", "-" * 78]
    L.append(f"laboratorio: ruptura = {p.get('_ruptura', '?')} | confianca = {p.get('_confianca', '?')} | em analise = {p.get('_em_analise', '?')} | "
             f"entra no ajuste do plano = {p.get('_ajuste') or 'n/d (.dat antigo)'}")
    L.append(f"             sigma3 = {v(r['s3'], 1)} MPa | mergulho theta = {v(r['dip'], 2)} graus (banco) | pico D = {v(r['lab_pico'], 2)} MPa "
             f"em eps_ax = {v(r['lab_eps_pico'], 4)} % | E secante = {v(r['lab_Esec'], 1)} GPa" + ("" if lab_ok else " (valores do params.dat)"))
    if not r["plano"]:
        L.append("(modo matriz ou mergulho fora de 5-85 graus: nao ha calculo de c e phi do plano)")
        return L
    L.append(f"ponto do ensaio no plano (equilibrio): sn = s3 + D cos^2(theta) = {v(r['sn_lab'], 2)} MPa;  tau = D sen(theta) cos(theta) = {v(r['tau_lab'], 2)} MPa")
    aj, lq, a_lq = r.get("ajuste"), r.get("leque"), r.get("a_leque")
    if a_lq is not None and np.isfinite(a_lq):                    # [v4] amostra com leque
        m_u = math.tan(math.radians(r["phi_plano"]))
        if lq:
            L.append(f"LEQUE (ancoras: a = 1 = {' + '.join(ANC_CIMA)}; a = 0 = {' + '.join(ANC_BAIXO)}):")
            L.append(f"   reta a = 0 (baixo): tau = {v(lq['cl'], 2)} + {v(lq['ml'], 4)} sn      reta a = 1 (cima): tau = {v(lq['cu'], 2)} + {v(lq['mu'], 4)} sn")
            L.append(f"   reta de qualquer a:  c(a) = {v(lq['cl'], 2)} + {v(lq['dc'], 2)} a [MPa]    tan(phi(a)) = {v(lq['ml'], 4)} + {v(lq['dm'], 4)} a    (tau = c(a) + tan(phi(a)) sn)")
            L.append(f"   a do ensaio (reta que passa no ponto dele):  a = (tau - {v(lq['cl'], 2)} - {v(lq['ml'], 4)} sn) / ({v(lq['dc'], 2)} + {v(lq['dm'], 4)} sn)"
                     f" = ({v(r['tau_lab'], 2)} - {v(lq['cl'], 2)} - {v(lq['ml'], 4)} x {v(r['sn_lab'], 2)}) / ({v(lq['dc'], 2)} + {v(lq['dm'], 4)} x {v(r['sn_lab'], 2)})"
                     f" = {v(a_do_ponto(lq, r['sn_lab'], r['tau_lab']), 3)}")
        L.append(f"USADO nesta rodada: a = {v(a_lq, 3)}  ->  c = {v(r['c_plano'], 2)} MPa, phi = {v(r['phi_plano'], 2)} graus, atrito residual sj_fric = tan(phi) = {v(r['mu_ref'], 4)}"
                 f"   [origem: {r['plano_origem']}]")
        L.append(f"   reta usada: tau = {v(r['c_plano'], 2)} + {v(m_u, 4)} sn")
    else:
        if aj:
            f = aj["fit"]
            L.append(f"ajuste COMUM tau = c + sn tan(phi) (minimos quadrados, n = {f['n']}: {', '.join(x[0] for x in aj['pts'])}): "
                     f"c = {v(f['c'], 2)} +- {v(f['se_c'], 2)} MPa (IC95 {v(f['ci_c'][0], 1)} a {v(f['ci_c'][1], 1)}); phi = {v(f['phi'], 1)} graus "
                     f"(IC95 {v(f['ci_phi'][0], 1)} a {v(f['ci_phi'][1], 1)}); R2 = {v(f['r2'], 2)}")
        else:
            L.append("ajuste comum: nao calculado (os .dat desta pasta nao trazem 'ajuste do plano'; gere de novo com 00_gera_params.py)")
        L.append(f"USADO nesta rodada: c = {v(r['c_plano'], 2)} MPa, phi = {v(r['phi_plano'], 2)} graus, atrito residual mu = {v(r['mu_ref'], 2)}   [origem: {r['plano_origem']}]")
    if r.get("plano_aviso"):
        L.append(f"   AVISO: {r['plano_aviso']}")
    if not (a_lq is not None and np.isfinite(a_lq)) and aj and (abs(r["c_plano"] - aj["fit"]["c"]) > 0.02 or abs(r["phi_plano"] - aj["fit"]["phi"]) > 0.02):
        L.append("   ATENCAO: c e/ou phi desta rodada diferem do ajuste comum (valor calibrado ao pico do lab desta amostra, ou rodada antiga).")
    L.append(f"distancia do ensaio a reta usada: tau - (c + sn tan phi) = {v(r['resid_lab'], 2, True)} MPa (lab)  |  {v(r['resid_mod'], 2, True)} MPa (modelo no pico)")
    L.append(f"envoltoria (Jaeger) com c e phi usados: D = {v(r['env'])} MPa -> lab = {v(100 * r['D_lab_plano'] / r['env'], 1)} %, modelo = {v(100 * r['pico'] / r['env'], 1)} % da envoltoria")
    return L


def texto_resumo(base, am, modo, r, lab_ok, aviso_log, aneis=None):
    j = r["jan"]
    L = []
    L.append(f"RESUMO DA RODADA  {base}")
    L.append("=" * 78)
    L.append(f"amostra {am} | modo {modo} | sigma3 = {v(r['s3'])} MPa | plano com mergulho de {v(r['dip'], 2)} graus | "
             f"{len(r['_n'])} amostragens (a cada {int(r['intervalo'])} ciclos)")
    L.append(f"carregamento: ciclo {int(r['ciclo_ini'])} a {int(r['ciclo_fim'])}; pico no ciclo {int(r['ciclo_pico'])}; "
             f"ciclos apos o pico = {int(r['ciclos_pos'])}")
    if r["max_global"] > 1.005 * r["pico"]:
        L.append(f"ATENCAO: o desviador sobe de novo depois do 1o pico (maximo da rodada {v(r['max_global'])} MPa no ciclo {r['ciclo_max_global']}); "
                 f"o pico usado e o 1o, travado pela mesma regra do 04 (queda de 10 %): {v(r['pico'])} MPa no ciclo {int(r['ciclo_pico'])}.")
    if not lab_ok:
        L.append("(curves_lab.csv do laboratorio NAO encontrado: so as referencias do params.dat; use --dados <pasta do curves_lab.csv>)")
    L.append("")
    L.append("PRE-PICO E PICO (tensao do modelo = esfera de medida central, sigma_a - sigma_r)")
    L.append("-" * 78)
    L.append(f"{'':34s}{'modelo':>12s}{'laboratorio':>14s}{'erro':>10s}")

    def lin(nome, m, lb, n=2, pct=True):
        e = (m / lb - 1.0) * 100.0 if (lb and np.isfinite(lb) and np.isfinite(m) and lb != 0 and pct) else float("nan")
        L.append(f"{nome:34s}{v(m, n):>12s}{v(lb, n):>14s}{(('%+.1f%%' % e).replace('.', ',') if np.isfinite(e) else ''):>10s}")

    lin("pico do desviador (MPa)", r["pico"], r["lab_pico"])
    lin("deformacao axial no pico (%)", r["eps_pico"], r["lab_eps_pico"], 4)
    lin("E secante ate o pico (GPa)", r["Esec"], r["lab_Esec"])
    L.append(f"{'envoltoria do plano (c, phi) (MPa)':34s}{v(r['env']):>12s}   -> pico do modelo = {v(100 * r['pico'] / r['env'], 1)} % da envoltoria")
    L.append("   (Poisson nao e comparado: o modelo e elastico ate o pico e o laboratorio e inelastico.)")
    L.append("")
    L.extend(texto_plano(r, lab_ok))
    L.append("")
    L.extend(texto_janela(r, lab_ok))
    L.append("")
    L.append(f"{'POS-PICO NA JANELA':34s}{'modelo':>12s}{'laboratorio':>14s}{'erro':>10s}")
    L.append("-" * 78)
    lin("minimo na janela (MPa)", r["jan_min"], r["lab_min_pos"])
    lin("nivel no fim da janela (MPa)", r["jan_fim"], r["lab_fim_janela"])
    lin("def. axial (extens.) apos o pico, fim (%)", r["jan_deps_fim"], r["lab_deps_fim"], 3)
    if r["plano"]:
        lin("atrito equivalente no minimo", r["jan_mu_eq_min"], r["lab_mu_eq"], 2)
        lin("atrito equivalente no fim", r["jan_mu_eq_fim"], r["lab_mu_eq_fim"], 2)
        lin("coesao implicita no minimo (MPa)", r["jan_c_impl_min"], r["lab_c_impl_min"], 1)
        lin("coesao implicita no fim (MPa)", r["jan_c_impl_fim"], r["lab_c_impl_fim"], 1)
        L.append(f"   'nivel no fim da janela' = mediana dos ultimos 10 % da janela (minimo 3 amostras), igual no modelo e no lab. Atrito equivalente = so atrito, sem coesao.")
        L.append(f"   coesao implicita: c = D cos(th)(sin(th) - mu cos(th)) - mu sigma3, mu = {v(r['mu_ref'], 2)}; modelo no fim = {v(100 * r['jan_c_impl_fim'] / r['c_plano'], 0)} % da coesao do plano ({v(r['c_plano'], 1)} MPa)")
        L.append(f"   referencia: com mu = {v(r['mu_ref'], 2)} no plano e sem coesao o desviador seria {v(r['D_atrito'])} MPa; o excedente do modelo indica contatos ainda colados / travamento")
    else:
        L.append("(modo matriz ou mergulho fora de 5-85 graus: as formulas do plano de foliacao nao se aplicam)")
    L.append(f"sigma3 dentro da janela pos-pico: desvio maximo = {v(r['jan_conf_dev_max_pct'], 1)} % do alvo; fora de +-5 % em {v(r['jan_conf_fora5_pct'], 1)} % das amostragens"
             + (f" | lab (curva toda): desvio maximo da mediana = {v(r['lab_conf_dev_max_pct'], 1)} %" if lab_ok and np.isfinite(r['lab_conf_dev_max_pct']) else ""))
    L.append("")
    L.append("RODADA INTEIRA DO MODELO (inclui o trecho alem da janela; sem comparacao com o lab)")
    L.append("-" * 78)
    L.append(f"minimo apos o pico (MPa) / ciclo        : {v(r['min_pos'])} / {int(r['ciclo_min_pos'])}")
    L.append(f"no fim da rodada (MPa)                  : {v(r['fim'])}   (deformacao axial {v(r['eps_fim'], 3)} %, pratos {v(r['eps_plat_fim'], 3)} %)")
    L.append(f"deformacao axial dos extensometros apos o pico, no fim: {v(r['eps_fim'] - r['eps_pico'], 3)} %   (deslizamento estimado pelo curso dos pratos: {v(r['slip_fim'], 2)} mm)")
    if r["plano"]:
        L.append(f"atrito equivalente no fim da rodada: {v(r['mu_eq_fim'], 2)} (sigma3 instantaneo) / {v(r['mu_eq_fim_nominal'], 2)} (sigma3 nominal); "
                 f"coesao implicita no fim da rodada = {v(r['c_impl_fim'])} MPa ({v(100 * r['c_impl_fim'] / r['c_plano'], 0)} % da coesao do plano)")
    if r["tem_colados"]:
        L.append(f"plano colado (smooth joint): {int(r['sj0'])} no inicio -> {int(r['sj_pico'])} no pico -> {int(r['sj_fim'])} no fim "
                 f"({v(100 * r['sj_fim'] / max(r['sj0'], 1), 0)} % do inicial)")
        L.append(f"matriz colada (flat joint)  : {int(r['fj0'])} -> {int(r['fj_pico'])} -> {int(r['fj_fim'])}")
    else:
        L.append("contatos colados: sem historico (rodada anterior a v3.3); veja o log do console")
    L.append("")
    L.append("CONTROLE E FRONTEIRA (rodada inteira)")
    L.append("-" * 78)
    L.append(f"sigma3 no pico = {v(r['conf_pico'], 2)} MPa; maximo = {v(r['conf_max'], 2)} MPa; minimo = {v(r['conf_min'], 2)} MPa; ciclos acima de +5 % / +10 % / +100 % do alvo = "
             f"{r['n5']} / {r['n10']} / {r['n100']}")
    L.append(f"CRITERIO sigma3 = alvo +-5 %: desvio maximo = {v(r['conf_dev_max_sinal_pct'], 1)} % (pre-pico: {v(r['conf_dev_pre_max_pct'], 1)} % em modulo); "
             f"fora da faixa em {v(r['conf_fora5_pct'], 1)} % das amostragens (pre-pico {v(r['conf_fora5_pre_pct'], 1)} %, pos-pico {v(r['conf_fora5_pos_pct'], 1)} %)"
             + (f" | lab: desvio maximo da mediana = {v(r['lab_conf_dev_max_pct'], 1)} %" if lab_ok and np.isfinite(r['lab_conf_dev_max_pct']) else ""))
    pre_ok, pos = r['conf_dev_pre_max_pct'] <= 5.0, r['conf_fora5_pos_pct']
    if pre_ok and pos <= 1.0:
        L.append("   OK: pre-pico e pos-pico dentro de +-5 %")
    elif pre_ok and pos <= 10.0:
        L.append(f"   OK no regime (pre-pico dentro de +-5 %); no pos-pico ha um TRANSIENTE no colapso do plano: sigma3 chega a {v(r['conf_max'], 2)} MPa "
                 f"({r['n5']} ciclos acima de +5 %). O lab nao mostra esse pico; se incomodar, ver o ganho do servo (servo_ganho_carga no 04).")
    elif pre_ok:
        L.append("   pre-pico OK, mas o pos-pico fica muito tempo fora de +-5 %: veja o painel 4 do _diagnostico.png (ganho do servo no 04)")
    else:
        L.append("   FORA do criterio ja no pre-pico: veja o painel 4 do _diagnostico.png (ganho do servo no inicio do 04)")
    L.append(f"sigma1 pelo prato / pela esfera (pre-pico, mediana) = {v(r['razao_prato'], 3)}  -> raio efetivo = {v(r['raio_ef_mm'], 2)} mm (nominal {v(r['raio_nom'], 1)} mm)")
    L.append(f"   pico do desviador pelo prato (area nominal) = {v(r['pico_prato'])} MPa; com a area do raio efetivo ficaria {v(r['pico_prato'] / r['razao_prato'])} MPa")
    L.append(f"atrito mobilizado no prato: maximo = {v(r['mu_prato_max'], 3)}")
    if aneis:
        L.append("")
        L.append("PERFIL DO PLANO (log da v3.4/v3.4.1; so medicao; deslizamento = movimento relativo das duas bolas do contato, inclui poucos um elasticos)")
        L.append("-" * 78)
        L.extend(texto_aneis(aneis, r["ciclo_pico"], r["ciclo_fim"]))
        L.extend(leitura_aneis(aneis, r["ciclo_fim"]))
    elif r.get("servo_v34") is False:
        L.append("")
        L.append("(o log desta rodada nao tem as linhas da v3.4: foi rodada com o 04 antigo, servo do carregamento com o ganho da v3.3)")
    if aviso_log:
        L.append("")
        L.append("DO LOG DO CONSOLE (ultima rodada)")
        L.append("-" * 78)
        L.extend(aviso_log)
    L.append("")
    L.append("LIMITES: formulas idealizadas (blocos rigidos, tensao uniforme); janela comum = mesmo f (tempo normalizado), vale com taxa de carregamento constante;")
    L.append("o pos-pico do lab so vale no 1o terco do tempo; sigma1 pelo prato usa a area nominal. Leituras sao inferencias, nao medidas.")
    return "\n".join(L) + "\n"


def acha_log(base_sem_ext, pasta):
    """devolve (caminho, linhas da ULTIMA rodada, linhas do 04 dessa rodada). O log do PFC acumula (modo append) e pode ter tentativas
    interrompidas: a ultima rodada comeca na ultima linha 'Geometria (m):' (01) e o 04 na ultima 'Servo no carregamento'."""
    cand = [os.path.join(pasta, base_sem_ext.replace("_Triaxial_Histories", "") + "_Log.txt")]
    cand += glob.glob(os.path.join(pasta, base_sem_ext.split("_Triaxial")[0] + "*Log*.txt"))
    for arq in cand:
        if os.path.isfile(arq):
            linhas = open(arq, encoding="ascii", errors="ignore").read().splitlines()
            marc = [i for i, l in enumerate(linhas) if l.strip().startswith("Geometria (m):")]
            if not marc:
                marc = [i for i, l in enumerate(linhas) if l.startswith("Amostra ") and "modo =" in l]
            seg = linhas[marc[-1]:] if marc else linhas
            serv = [i for i, l in enumerate(seg) if l.strip().startswith("Servo no carregamento")]
            seg04 = seg[serv[-1]:] if serv else seg
            if len(serv) > 1:            # 04 rodado de novo dentro da mesma rodada: descarta as linhas da tentativa anterior
                seg = seg[:serv[0]] + seg04
            return arq, seg, seg04
    return None, [], []


def le_log(base_sem_ext, pasta):
    """pega do log do console (se existir) as linhas de conferencia da ULTIMA rodada"""
    arq, linhas, _ = acha_log(base_sem_ext, pasta)
    if arq is None:
        return None
    pad = ("Bolas apos", "Geometria", "Contatos no plano", "dos quais", "Flat joint fora", "Extensometros virtuais",
           "Servo no carregamento", "1o PICO TRAVADO", "plano SJ colados", "Plano de foliacao no ciclo", "anel ",
           "cruzam o plano", "mesmo lado do plano", "Motivo da parada", "Paredes no modelo", "Pico do desviador",
           "E do modelo", "nu do modelo", "Desviador apos", "1o pico:")
    out = [l.strip() for l in linhas if any(l.strip().startswith(p) for p in pad)]
    return ["(" + os.path.basename(arq) + ")"] + out[-60:] if out else None


def inicio_carga_log(base_sem_ext, pasta):
    """ciclo em que o carregamento axial comecou = ciclo do 1o pico - 'ciclos ate o pico' (linha '1o pico:' do 04); None se nao achar"""
    arq, _, seg04 = acha_log(base_sem_ext, pasta)
    ms = [re.search(r"1o pico:\s*ciclo\s*=\s*(\d+)\s+ciclos ate o pico\s*=\s*(\d+)", l) for l in seg04]
    ms = [m for m in ms if m]
    return int(ms[-1].group(1)) - int(ms[-1].group(2)) if ms else None


RE_ANEL = re.compile(r"anel\s+(\d)\s+\(r ate\s+([-+0-9.eE]+)\s*mm\):\s*colados / total =\s*(\d+)\s*/\s*(\d+)\s+"
                     r"deslizamento medio \(um\):\s*colados =\s*([-+0-9.eE]+)\s+nao colados =\s*([-+0-9.eE]+)")
RE_LADO = re.compile(r"(cruzam o plano|mesmo lado do plano)\s*\([^)]*\):\s*colados / total =\s*(\d+)\s*/\s*(\d+)\s+"
                     r"deslizamento medio \(um\):\s*colados =\s*([-+0-9.eE]+)\s+nao colados =\s*([-+0-9.eE]+)")
RE_PLANO = re.compile(r"Plano de foliacao no ciclo\s+(\d+)")


def le_aneis(base_sem_ext, pasta):
    """perfil do plano gravado pelo 04 no 1o pico e no fim: 4 aneis de raio (v3.4) e, na v3.4.1, as duas classes de contato
    (cruzam o plano x mesmo lado). Devolve blocos {'ciclo', 'aneis': [{'i','r_mm','colados','total','slip_col_um','slip_nao_um'}],
    'lados': {'cruzam'|'mesmo': {'colados','total','slip_col_um','slip_nao_um'}}} na ordem do log; [] se nao houver."""
    arq, linhas, _ = acha_log(base_sem_ext, pasta)
    blocos, atual = [], None
    for l in linhas:
        m = RE_PLANO.search(l)
        if m:
            atual = {"ciclo": int(m.group(1)), "aneis": [], "lados": {}}
            blocos.append(atual)
            continue
        if atual is None:
            continue
        m = RE_ANEL.search(l)
        if m:
            atual["aneis"].append({"i": int(m.group(1)), "r_mm": float(m.group(2)), "colados": int(m.group(3)), "total": int(m.group(4)),
                                   "slip_col_um": float(m.group(5)), "slip_nao_um": float(m.group(6))})
            continue
        m = RE_LADO.search(l)
        if m:
            atual["lados"]["cruzam" if m.group(1).startswith("cruzam") else "mesmo"] = {
                "colados": int(m.group(2)), "total": int(m.group(3)), "slip_col_um": float(m.group(4)), "slip_nao_um": float(m.group(5))}
    return [b for b in blocos if len(b["aneis"]) == 4]


def servo_v34(base_sem_ext, pasta):
    """True/False se o log da ultima rodada tem a linha 'Servo no carregamento' (v3.4); None se nao ha log"""
    arq, linhas, seg04 = acha_log(base_sem_ext, pasta)
    if arq is None:
        return None
    return any(l.strip().startswith("Servo no carregamento") for l in seg04)


def texto_aneis(blocos, ciclo_pico, ciclo_fim):
    """linhas de texto do perfil do plano (resumo)"""
    L = []
    for b in blocos:
        rot = "no fim da rodada" if b["ciclo"] >= ciclo_fim else ("logo apos o 1o pico (queda a 90 %)" if b["ciclo"] >= ciclo_pico else "antes do pico")
        L.append(f"ciclo {b['ciclo']} ({rot}):")
        for g in b["aneis"]:
            pc = 100.0 * g["colados"] / g["total"] if g["total"] else float("nan")
            L.append(f"   anel {g['i']} (r ate {v(g['r_mm'], 0)} mm): colados {g['colados']} de {g['total']} ({v(pc, 0)} %) | deslizamento medio: colados {v(g['slip_col_um'], 1)} um, "
                     f"nao colados {v(g['slip_nao_um'], 1)} um")
        for k, nome in (("cruzam", "cruzam o plano (bolas em lados opostos)"), ("mesmo", "mesmo lado (as duas bolas no mesmo bloco)")):
            g = b["lados"].get(k)
            if g:
                pc = 100.0 * g["colados"] / g["total"] if g["total"] else float("nan")
                L.append(f"   {nome}: colados {g['colados']} de {g['total']} ({v(pc, 0)} %) | deslizamento medio: colados {v(g['slip_col_um'], 1)} um, nao colados {v(g['slip_nao_um'], 1)} um")
    return L


def fracao_mesmo_lado(blocos, ciclo_fim):
    """no ultimo bloco com as classes (v3.4.1): (colados cruzam / total cruzam, colados mesmo / total mesmo, parte dos colados que e 'mesmo lado'); None se nao ha"""
    b = next((x for x in reversed(blocos) if x["ciclo"] >= ciclo_fim and len(x["lados"]) == 2), None)
    if b is None:
        return None
    cx, ms = b["lados"]["cruzam"], b["lados"]["mesmo"]
    fc = cx["colados"] / cx["total"] if cx["total"] else float("nan")
    fm = ms["colados"] / ms["total"] if ms["total"] else float("nan")
    tot = cx["colados"] + ms["colados"]
    return fc, fm, (ms["colados"] / tot if tot else float("nan"))


def leitura_aneis(blocos, ciclo_fim):
    """texto de leitura do perfil (inferencia). Limiares sao regra de bolso, nao criterio calibrado."""
    L = []
    fr = fracao_mesmo_lado(blocos, ciclo_fim)
    if fr is None:
        L.append("Leitura: colados que quase nao deslizaram, ou concentrados num anel, mostram o trecho do plano que nao rompe (hipotese de 'borda': nao verificada).")
        L.append("(o 04 atual nao separa os contatos que cruzam o plano dos de mesmo bloco)")
        return L
    fc, fm, sh = fr
    L.append(f"Leitura (inferencia): no fim, {v(100 * fc, 0)} % dos contatos que cruzam o plano e {v(100 * fm, 0)} % dos de mesmo lado ainda estao colados; "
             f"{v(100 * sh, 0)} % dos colados que restam sao de mesmo lado.")
    if np.isfinite(sh) and np.isfinite(fc) and sh >= 0.8 and fc <= 0.10:
        L.append("   Consistente com a hipotese de que o que nao rompe sao contatos DENTRO de um bloco (dentro da faixa sj_band), e nao a interface: o plano de fato rompeu.")
        L.append("   Se for isso, a coesao implicita alta no pos-pico vem de outro mecanismo (travamento/atrito) e nao de 'plano colado'. Nao verificado alem deste numero.")
    elif np.isfinite(fc) and fc >= 0.25:
        L.append("   NAO consistente com a hipotese: uma parte relevante dos contatos que cruzam o plano continua colada (plano nao rompe por inteiro).")
    else:
        L.append("   Resultado misto: nem confirma nem descarta a hipotese dos contatos dentro do bloco.")
    return L


# ---------------------------------------------------------------- graficos
def estilo(ax):
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=10.5)


def inst_local(x, dev, w=3):
    """[v3.4.2] E instantaneo (GPa) por derivada local: reta ajustada em janela de 2w+1 amostras
    (desviador x eps_ax, em MPa por %, vira GPa dividindo por 10). Tem ruido (derivada). [v3.4.1] sem Poisson."""
    x, dev = (np.asarray(t, dtype=float) for t in (x, dev))
    E = np.full(len(x), np.nan)
    for i in range(len(x)):
        a0, b0 = max(0, i - w), min(len(x), i + w + 1)
        if b0 - a0 < 3 or np.ptp(x[a0:b0]) <= 1e-9:
            continue
        E[i] = np.polyfit(x[a0:b0], dev[a0:b0], 1)[0] / 10.0
    return E


def calcula_plano(r, params):
    """[v3.4.1] ponto (sn, tau) do ensaio de laboratorio e do pico do modelo no plano, e a distancia de cada um a reta (c, phi) usada"""
    nan = float("nan")
    r["D_lab_plano"] = params.get("lab_dev_pico") or r["lab_pico"]
    for k in ("sn_lab", "tau_lab", "sn_mod", "tau_mod", "resid_lab", "resid_mod"):
        r[k] = nan
    if not r["plano"]:
        return
    tp = math.tan(math.radians(r["phi_plano"]))
    r["sn_lab"], r["tau_lab"] = tensoes_plano(r["s3"], r["D_lab_plano"], r["dip"])
    r["sn_mod"], r["tau_mod"] = tensoes_plano(r["conf_pico"], r["pico"], r["dip"])        # sigma3 do modelo no pico (medido)
    r["resid_lab"] = r["tau_lab"] - (r["c_plano"] + r["sn_lab"] * tp)
    r["resid_mod"] = r["tau_mod"] - (r["c_plano"] + r["sn_mod"] * tp)


def tabela(fig, x0, y_topo, largura, cabecalho, linhas, larguras, alinha, passo=0.0225):
    """[v3.4.1] tabela desenhada na figura (x0, y_topo, largura, passo em fracao da figura): cabecalho em negrito sobre faixa clara, uma linha
    por item, fios finos entre as linhas. linhas = lista de celulas (lista de textos) ou (celulas, True) para negrito; larguras = fracao
    da largura de cada coluna; alinha = 'l' ou 'r' por coluna."""
    n = len(linhas) + 1
    ax = fig.add_axes([x0, y_topo - n * passo, largura, n * passo])
    ax.set_xlim(0, 1)
    ax.set_ylim(n, 0)
    ax.axis("off")
    xs = np.concatenate([[0.0], np.cumsum(larguras)])
    pad = 0.014

    def escreve(k, y, t, **kw):
        ax.text(xs[k] + pad if alinha[k] == "l" else xs[k + 1] - pad, y, t, ha="left" if alinha[k] == "l" else "right", va="center", **kw)

    ax.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor=GRID, edgecolor="none", alpha=0.6))
    for k, t in enumerate(cabecalho):
        escreve(k, 0.5, t, fontsize=9.6, fontweight="bold", color=INK)
    ax.plot([0, 1], [1, 1], color=MUTED, lw=1.0, clip_on=False)
    for i, lin in enumerate(linhas):
        cel, neg = lin if isinstance(lin, tuple) else (lin, False)
        for k, t in enumerate(cel):
            escreve(k, i + 1.5, t, fontsize=9.2, fontweight="bold" if neg else "normal", color=INK)
        ult = i == len(linhas) - 1
        ax.plot([0, 1], [i + 2, i + 2], color=MUTED if ult else GRID, lw=0.9 if ult else 0.7, clip_on=False)
    return ax


def origem_curta(txt):
    """texto curto para a tabela (o texto completo continua no resumo)"""
    t = str(txt)
    if t.startswith("log da rodada"):
        return "log da rodada"
    if t.startswith("rodada anterior"):
        return "Main antigo (--c, --phi)"
    if t.startswith("params.dat"):
        return "params.dat"
    return "valores de reserva"


def painel(df, lab, lab_val, r, am, modo, params, caminho_png):
    """[v3.4.1] painel principal: (A) desviador x deformacao radial (esq.) e axial (dir.), (B) plano: sn x tau com o ponto do lab, o do modelo e a
    reta de c e phi usada (legenda fora do grafico); embaixo, tres TABELAS: dados do laboratorio, calculo de c e phi, modelo x lab.
    A: ate o fim da janela pos-pico comum. Sem Poisson (modelo elastico x lab inelastico), sem E instantaneo e sem notas de rodape."""
    j = r["jan"]
    ip, cfj = r["ip"], r["jan_ciclo_fim"]
    dm = df[df.ciclo <= cfj]                          # modelo dentro da janela pos-pico
    tem_lab = lab is not None
    pico_max = max(r["pico"], r["lab_pico"] if np.isfinite(r["lab_pico"]) else 0.0)
    fig = plt.figure(figsize=(13.6, 10.4), dpi=130, facecolor="white")
    a1 = fig.add_axes([0.065, 0.455, 0.53, 0.395])
    a3 = fig.add_axes([0.675, 0.455, 0.31, 0.395])
    for ax in (a1, a3):
        ax.grid(color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_color(MUTED)
        ax.tick_params(colors=MUTED, labelsize=10)
    # A: classico (radial a esquerda, axial a direita; as duas curvas de cada ensaio na mesma cor)
    if tem_lab:
        a1.plot(lab.eps_ax_pct, lab.dev_MPa, color=AZUL, lw=2.1, label="laboratório")
        a1.plot(lab.eps_rad_pct, lab.dev_MPa, color=AZUL, lw=2.1)
        a1.plot([lab.eps_ax_pct.iloc[r["kl"]], lab.eps_rad_pct.iloc[r["kl"]]], [r["lab_pico"]] * 2, "o", color=AZUL, ms=6.5, mec="white", mew=1.1, ls="none")
    a1.plot(dm.eps_ax_pct, dm.dev_MPa, color=LARANJA, lw=2.1, label="modelo")
    a1.plot(dm.eps_rad_pct, dm.dev_MPa, color=LARANJA, lw=2.1)
    a1.plot([df.eps_ax_pct[ip], df.eps_rad_pct[ip]], [r["pico"]] * 2, "o", color=LARANJA, ms=6.5, mec="white", mew=1.1, ls="none")
    a1.axvline(0, color=MUTED, lw=0.9)
    x_ax, x_rad = [dm.eps_ax_pct.max()], [dm.eps_rad_pct.min()]               # modelo: nunca cortado
    if tem_lab:
        k = r["kl"]
        x_ax.append(min(lab.eps_ax_pct.max(), 3.0 * max(lab.eps_ax_pct.iloc[k], 0.1)))
        x_rad.append(max(lab.eps_rad_pct.min(), -3.0 * max(abs(lab.eps_rad_pct.iloc[k]), 0.05)))
    # limites do eixo x: dados da janela; o lab pos-pico pode ir longe (reversao, deslizamento): teto de 3x a deformacao no pico, o resto sai do quadro
    x_lo, x_hi = min(-0.05, 1.08 * min(x_rad)), max(0.2, 1.08 * max(x_ax))
    a1.set_xlim(x_lo, x_hi)
    y_jan = max(dm.dev_MPa.max(), lab.dev_MPa.max() if tem_lab else 0.0)       # o pos-pico dentro da janela pode passar do pico
    a1.set_ylim(0, 1.18 * max(pico_max, y_jan))
    a1.set_xlabel("deformação (%)", fontsize=11, color=INK)
    a1.set_ylabel("desviador σa − σr (MPa)", fontsize=11, color=INK)
    a1.text(0.02, 0.97, "← radial", transform=a1.transAxes, fontsize=10.5, color=MUTED, va="top")
    a1.text(0.98, 0.97, "axial →", transform=a1.transAxes, fontsize=10.5, color=MUTED, va="top", ha="right")
    a1.legend(frameon=False, fontsize=10.5, loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=2, borderaxespad=0.2)
    a1.set_title("A  Desviador × deformação", fontsize=11.5, color=INK, loc="left", pad=22)
    # B: plano, sn x tau (legenda fora do grafico, embaixo)
    a3.set_title("B  Plano de foliação no pico: σn × τ", fontsize=11.5, color=INK, loc="left", pad=22)
    if r["plano"]:
        aj = r.get("ajuste")
        tp = math.tan(math.radians(r["phi_plano"]))
        xs_all = [r["sn_lab"], r["sn_mod"]] + ([x[1] for x in aj["pts"]] if aj else [])
        ys_all = [r["tau_lab"], r["tau_mod"], r["c_plano"]] + ([x[2] for x in aj["pts"]] if aj else [])
        xmax, ymax = 1.12 * max(xs_all), 1.2 * max(ys_all)
        xs = np.linspace(0, xmax, 100)
        a_lq, lq = r.get("a_leque"), r.get("leque")
        com_a = a_lq is not None and np.isfinite(a_lq)
        dif = (not aj) or abs(r["c_plano"] - aj["fit"]["c"]) > 0.02 or abs(r["phi_plano"] - aj["fit"]["phi"]) > 0.02
        if com_a and lq:                                   # [v4] leque no lugar da reta comum
            a3.fill_between(xs, lq["cl"] + lq["ml"] * xs, lq["cu"] + lq["mu"] * xs, color=GRID, alpha=0.8, lw=0, label="leque (entre a = 0 e a = 1)")
            for nome_a, c_, m_ in (("a = 0", lq["cl"], lq["ml"]), ("a = 1", lq["cu"], lq["mu"])):
                a3.plot(xs, c_ + m_ * xs, color=MUTED, lw=1.1)
                a3.annotate(nome_a, (xmax, c_ + m_ * xmax), textcoords="offset points", xytext=(-3, 4), fontsize=8.5, color=MUTED, ha="right")
        if aj and not (com_a and lq):
            f = aj["fit"]
            se = f["s"] * np.sqrt(1.0 / f["n"] + (xs - f["xbar"]) ** 2 / f["sxx"])
            a3.fill_between(xs, f["c"] + f["tanphi"] * xs - f["t"] * se, f["c"] + f["tanphi"] * xs + f["t"] * se, color=GRID, alpha=0.8, lw=0,
                            label="IC 95 % da reta comum")
            a3.plot(xs, f["c"] + f["tanphi"] * xs, color=MUTED, lw=1.2, label="reta do ajuste comum" if dif else "reta do ajuste comum = usada no modelo")
        if aj:
            for ita, sn_, tau_ in aj["pts"]:
                if ita != am:
                    a3.plot([sn_], [tau_], "o", color="white", mec=MUTED, ms=5.5, mew=1.0, zorder=3)
                    a3.annotate(ita.replace("ITA", ""), (sn_, tau_), textcoords="offset points", xytext=(4, 3), fontsize=7.5, color=MUTED)
            a3.plot([], [], "o", color="white", mec=MUTED, ms=5.5, mew=1.0, label="demais amostras do ajuste (nº = ITA)")
        if com_a:
            a3.plot(xs, r["c_plano"] + tp * xs, color=LARANJA, lw=1.7, label="reta usada no modelo")
            a3.text(0.03, 0.97, f"a = {v(a_lq, 3)}\nτ = {v(r['c_plano'], 2)} + {v(tp, 4)} σn", transform=a3.transAxes, fontsize=9.2,
                    color=LARANJA, va="top", fontweight="bold")
        elif dif:
            a3.plot(xs, r["c_plano"] + tp * xs, color=LARANJA, lw=1.5, ls="--", label="reta usada no modelo")
        a3.plot([0], [r["c_plano"]], "o", color=LARANJA, ms=5, zorder=4)
        a3.annotate("c", (0, r["c_plano"]), textcoords="offset points", xytext=(7, 4), fontsize=8.5, color=LARANJA)
        a3.plot([r["sn_lab"]], [r["tau_lab"]], "o", color=AZUL, ms=8, mec="white", mew=1.1, zorder=5, label=f"{am} laboratório")
        a3.plot([r["sn_mod"]], [r["tau_mod"]], "o", color=LARANJA, ms=8, mec="white", mew=1.1, zorder=5, label=f"{am} modelo")
        a3.set_xlim(0, xmax)
        a3.set_ylim(0, ymax)
        a3.set_xlabel("σn = σ3 + D cos²θ (MPa)", fontsize=10.5, color=INK)
        a3.set_ylabel("τ = D senθ cosθ (MPa)", fontsize=10.5, color=INK)
        a3.legend(frameon=False, fontsize=8.8, loc="upper center", bbox_to_anchor=(0.44, -0.17), ncol=2, columnspacing=1.2, handlelength=1.8, borderaxespad=0)
    else:
        a3.axis("off")
        a3.text(0.0, 0.8, "Sem plano de foliação nesta rodada\n(modo matriz, ou mergulho fora de 5–85°):\nnão há cálculo de c e φ.", fontsize=11, color=MUTED, va="top")
    # titulo e subtitulo
    plano_txt = f"  ·  plano com mergulho de {v(r['dip'], 2)}°" if r["plano"] else "  ·  sem plano de foliação (matriz)"
    fig.text(0.065, 0.958, f"{am}  ·  σ3 = {v(r['s3'], 0)} MPa{plano_txt}  —  " + ("modelo × laboratório" if tem_lab else "modelo (sem laboratório)"), fontsize=18, color=INK, va="center")
    jtxt = (f"janela pós-pico comum f = {v(j['f'], 2)}" if j["modo"] == "comum"
            else f"janelas pós-pico diferentes: lab f = {v(j['f_lab'], 2)}, modelo f = {v(j['f_mod'], 2)}")
    fig.text(0.065, 0.926, f"Pico {v(r['pico'])} MPa (lab {v(r['lab_pico'])})   ·   E secante {v(r['Esec'])} GPa (lab {v(r['lab_Esec'])}) até o pico   ·   {jtxt}",
             fontsize=11.5, color=MUTED, va="center")
    # tabelas: dados do laboratorio | calculo de c e phi | modelo x laboratorio
    p = r["params"]
    T1 = [["ruptura · confiança", f"{p.get('_ruptura', '?')} · {p.get('_confianca', '?')}"],
          ["em análise · ajuste do plano", f"{p.get('_em_analise', '?')} · {p.get('_ajuste') or 'n/d'}"],
          ["σ3 (MPa)", v(r["s3"], 1)],
          ["mergulho θ (°), Campanha", v(r["dip"], 2)],
          ["pico D (MPa)", v(r["lab_pico"], 2)],
          ["ε no pico (%)", v(r["lab_eps_pico"], 3)],
          ["E secante (GPa)", v(r["lab_Esec"], 1)],
          ["janela pós-pico f", v(j["f_lab_jan"] if np.isfinite(j["f_lab_jan"]) else j["f_lab"], 2)],
          ["pós-pico: mín. · fim (MPa)", f"{v(r['lab_min_pos'], 1)} · {v(r['lab_fim_janela'], 1)}"]]
    if not tem_lab:
        T1.append(["curvas", "curves_lab.csv NÃO achado"])
    if r["plano"]:
        aj = r.get("ajuste")
        a_lq, lq = r.get("a_leque"), r.get("leque")
        com_a = a_lq is not None and np.isfinite(a_lq)
        T2 = [["σn = σ3 + D·cos²θ (MPa)", v(r["sn_lab"], 2)],
              ["τ = D·senθ·cosθ (MPa)", v(r["tau_lab"], 2)]]
        if com_a:                                          # [v4] leque: a, c(a), tan(phi(a)) e a formula do a
            m_u = math.tan(math.radians(r["phi_plano"]))
            if lq:
                T2 += [(["a (0 = reta de baixo, 1 = de cima)", v(a_lq, 3)], True),
                       [f"c(a) = {v(lq['cl'], 2)} + {v(lq['dc'], 2)}·a (MPa)", v(r["c_plano"], 2)],
                       [f"tanφ(a) = {v(lq['ml'], 4)} + {v(lq['dm'], 4)}·a", f"{v(m_u, 4)}  (φ = {v(r['phi_plano'], 2)}°)"],
                       [f"a = (τ − {v(lq['cl'], 2)} − {v(lq['ml'], 4)}σn)/({v(lq['dc'], 2)} + {v(lq['dm'], 4)}σn)", ""]]
            else:
                T2 += [(["a do leque", v(a_lq, 3)], True), ["tanφ", v(m_u, 4)]]
        elif aj:
            f = aj["fit"]
            T2 += [["ajuste comum: n · R²", f"{f['n']} · {v(f['r2'], 2)}"],
                   ["c do ajuste (MPa)", f"{v(f['c'], 2)} ± {v(f['se_c'], 2)}"],
                   ["φ do ajuste (°)", f"{v(f['phi'], 1)}  (IC95 {v(f['ci_phi'][0], 0)}–{v(f['ci_phi'][1], 0)})"]]
        else:
            T2 += [["ajuste comum", "sem 'ajuste do plano' nos .dat"]]
        T2 += [(["USADO: c (MPa) · φ (°)", f"{v(r['c_plano'], 2)} · {v(r['phi_plano'], 2)}"], True),
               ["μ residual" + (" (= tanφ)" if com_a else ""), v(r["mu_ref"], 4 if com_a else 2)],
               ["resíduo do lab (MPa)", v(r["resid_lab"], 1, True)],
               ["D da envoltória (MPa)", v(r["env"], 1)],
               ["origem de c e φ", origem_curta(r["plano_origem"])]]
        if r.get("plano_aviso"):
            T2.append(["atenção", "params.dat ≠ log"])
    else:
        T2 = [["sem plano de foliação"], ["não há cálculo de c e φ"]]

    def erro(m, lb):
        e = pct(m, lb)
        return ("%+.1f%%" % e).replace(".", ",") if np.isfinite(e) else ""

    def lt(nome, m, lb, n=1):
        return [nome, v(m, n), v(lb, n), erro(m, lb)]

    T3 = [lt("pico (MPa)", r["pico"], r["lab_pico"]),
          lt("ε no pico (%)", r["eps_pico"], r["lab_eps_pico"], 3),
          lt("E secante (GPa)", r["Esec"], r["lab_Esec"]),
          lt("mín. pós-pico (MPa)", r["jan_min"], r["lab_min_pos"]),
          lt("fim da janela (MPa)", r["jan_fim"], r["lab_fim_janela"])]
    if np.isfinite(r["env"]):
        T3.append(["pico / envoltória (%)", v(100 * r["pico"] / r["env"], 0), v(100 * r["D_lab_plano"] / r["env"], 0), ""])
    T3.append(["σ3 fora de ±5 % (%)", v(r["conf_fora5_pct"], 1), "–", ""])
    y0 = 0.305
    tabela(fig, 0.065, y0, 0.285, ["DADOS DO LABORATÓRIO", ""], T1, [0.60, 0.40], ["l", "r"])
    tabela(fig, 0.375, y0, 0.295, ["CÁLCULO DE c E φ DO PLANO", ""], T2, [0.60, 0.40], ["l", "r"])
    tabela(fig, 0.695, y0, 0.29, ["MODELO × LAB.", "modelo", "lab", "erro"], T3, [0.45, 0.20, 0.16, 0.19], ["l", "r", "r", "r"])
    fig.savefig(caminho_png, facecolor="white")
    plt.close(fig)


def painel_diagnostico(df, lab, lab_val, r, am, modo, params, caminho_png):
    """[v3.4.1] diagnostico: so dois graficos, (1) desviador x deformacao axial e (2) contatos colados. (Os outros quatro da v3.4.2 - deformacao radial,
    pos-pico em f, servo lateral, prato x esfera - foram tirados; os numeros continuam no _resumo.txt e no _Historico.csv.)"""
    j = r["jan"]
    fig, axs = plt.subplots(1, 2, figsize=(15.5, 7.4), dpi=130, facecolor="white")
    fig.subplots_adjust(left=0.065, right=0.975, top=0.755, bottom=0.2, wspace=0.17)
    fig.text(0.02, 0.945, f"{am}  ·  {modo}  ·  σ3 = {v(r['s3'], 0)} MPa  ·  plano com mergulho de {v(r['dip'], 2)}°  —  diagnóstico (modelo × laboratório)",
             fontsize=17, color=INK)
    jtxt = (f"janela pós-pico comum f = {v(j['f'], 2)} (limitada pelo {j['limita']})" if j["modo"] == "comum"
            else f"janelas diferentes: lab f = {v(j['f_lab'], 2)}, modelo f = {v(j['f_mod'], 2)}")
    fig.text(0.02, 0.893, f"Pico {v(r['pico'])} MPa (lab {v(r['lab_pico'])}) · E secante {v(r['Esec'])} GPa (lab {v(r['lab_Esec'])}) · "
             f"σ3 fora de ±5 %: {v(r['conf_fora5_pct'], 1)} % das amostragens (máx. {v(r['conf_dev_max_sinal_pct'], 1)} %)", fontsize=11.5, color=MUTED)
    fig.text(0.02, 0.852, f"{jtxt}: mínimo {v(r['jan_min'])} MPa (lab {v(r.get('lab_min_pos'))}), fim {v(r['jan_fim'])} MPa (lab {v(r.get('lab_fim_janela'))})",
             fontsize=11.5, color=MUTED)
    cfj = r["jan_ciclo_fim"]
    dentro = df.ciclo <= cfj                      # modelo dentro da janela
    fora = df.ciclo >= cfj                        # (inclui a amostragem de fronteira, para a linha tracejada continuar a cheia)
    tem_fora = bool((df.ciclo > cfj).any())
    n_lab_jan = len(lab) if lab is not None else 0
    lab_alem = lab_val is not None and len(lab_val) > n_lab_jan
    # 1. tensao-deformacao
    ax = axs[0]
    xmax = max(0.45, 1.15 * df.eps_ax_pct.iloc[-1])
    if lab is not None:
        ax.plot(lab.eps_ax_pct, lab.dev_MPa, color=AZUL, lw=1.7, label="laboratório (janela comum)", zorder=2)
        if lab_alem:
            ax.plot(lab_val.eps_ax_pct.iloc[n_lab_jan - 1:], lab_val.dev_MPa.iloc[n_lab_jan - 1:], color=AZUL, lw=1.1, ls="--", alpha=0.6,
                    label="laboratório válido, depois da janela", zorder=2)
        ax.plot([r["lab_eps_pico"]], [r["lab_pico"]], "o", color=AZUL, ms=7, mec="white", zorder=4)
        ax.plot([0, r["lab_eps_pico"]], [0, r["lab_pico"]], ls=":", color=AZUL, lw=1.1)
    ax.plot(df.eps_ax_pct[dentro], df.dev_MPa[dentro], color=LARANJA, lw=1.9, label="modelo (esfera de medida)", zorder=3)
    if tem_fora:
        ax.plot(df.eps_ax_pct[fora], df.dev_MPa[fora], color=LARANJA, lw=1.2, ls="--", alpha=0.6, label="modelo depois da janela", zorder=3)
    ax.plot(df.eps_ax_pct, df.dev_prato_MPa, color=LARANJA, lw=1.0, ls=":", alpha=0.6, label="modelo, F/A do prato (área nominal)", zorder=2)
    ax.plot([r["eps_pico"]], [r["pico"]], "o", color=LARANJA, ms=7, mec="white", zorder=5)
    ax.plot([0, r["eps_pico"]], [0, r["pico"]], ls=":", color=LARANJA, lw=1.1)
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, 1.18 * max(r["pico"], r["lab_pico"] if np.isfinite(r["lab_pico"]) else 0))
    ax.set_xlabel("deformação axial dos extensômetros (%)", fontsize=11, color=INK)
    ax.set_ylabel("desviador σa − σr (MPa)", fontsize=11, color=INK)
    ax.set_title("1  Desviador × deformação axial (pontilhado = secante até o pico)", fontsize=11.5, color=INK, loc="left", pad=8)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    estilo(ax)
    # 2. colados (era o 6)
    ax = axs[1]
    if r["tem_colados"]:
        ax.plot(df.ciclo / 1000.0, 100 * df.sj_colados_frac, color=ROXO, lw=2.0, label=f"plano (smooth joint): {int(r['sj0'])} no início")
        ax.plot(df.ciclo / 1000.0, 100 * df.fj_colados_frac, color=AZUL, lw=1.6, label=f"matriz (flat joint): {int(r['fj0'])} no início")
        ax.axvline(r["ciclo_pico"] / 1000.0, color=LARANJA, lw=0.9, ls="--")
        ax.axvline(cfj / 1000.0, color=MUTED, lw=0.9, ls=":")
        ax.set_ylim(0, 105)
        ax.set_xlabel("ciclos (mil)", fontsize=11, color=INK)
        ax.legend(frameon=False, fontsize=9.5, loc="lower left")
        ax.set_title("2  Contatos colados (% do início): o plano rompe por inteiro?", fontsize=11.5, color=INK, loc="left", pad=8)
        estilo(ax)
    else:
        ax.axis("off")
        ax.text(0.0, 0.7, "2  Contatos colados\n\nEsta rodada é anterior à v3.3: o arquivo não tem o histórico\n"
                "de contatos colados. A partir da v3.3 o 04 grava sj_colados e fj_colados\na cada 500 ciclos e este painel mostra se o plano rompe por inteiro.",
                fontsize=11, color=MUTED, va="top")
    fig.text(0.02, 0.055, "Modelo: PFC3D, flat joint na matriz e smooth joint no plano de foliação. Tensões do modelo pela esfera de medida central (σa − σr). "
             "Pós-pico: lab e modelo no mesmo f (tempo normalizado); do lab só vale o 1º terço do tempo.\n" + ("Laboratório: curves_lab.csv." if lab is not None else "ATENÇÃO: curves_lab.csv do laboratório NÃO encontrado (o pico vem do params.dat): copie-o para 00_Inputs ou use --dados <pasta>.")
             + " Fórmulas idealizadas (blocos rígidos, tensão uniforme) são inferências.",
             fontsize=9.5, color=MUTED, va="center", linespacing=1.4)
    fig.savefig(caminho_png)
    plt.close(fig)


# ---------------------------------------------------------------- resumo entre amostras [v3.4]
def pct(m, lb):
    return (m / lb - 1.0) * 100.0 if (lb and np.isfinite(lb) and np.isfinite(m) and lb != 0) else float("nan")


def linha_geral(am, modo, r, aneis):
    """uma linha (dict) com as metricas da amostra para o resumo_geral"""
    j = r["jan"]
    d = {"amostra": am, "modo": modo, "sigma3_MPa": r["s3"], "mergulho_graus": r["dip"],
         "pico_modelo_MPa": r["pico"], "pico_lab_MPa": r["lab_pico"], "erro_pico_pct": pct(r["pico"], r["lab_pico"]),
         "envoltoria_MPa": r["env"], "pico_modelo_sobre_envoltoria_pct": 100.0 * r["pico"] / r["env"] if np.isfinite(r["env"]) else float("nan"),
         "pico_lab_sobre_envoltoria_pct": 100.0 * r["lab_pico"] / r["env"] if np.isfinite(r["env"]) and np.isfinite(r["lab_pico"]) else float("nan"),
         "eps_pico_modelo_pct": r["eps_pico"], "eps_pico_lab_pct": r["lab_eps_pico"], "erro_eps_pico_pct": pct(r["eps_pico"], r["lab_eps_pico"]),
         "E_secante_modelo_GPa": r["Esec"], "E_secante_lab_GPa": r["lab_Esec"], "erro_E_secante_pct": pct(r["Esec"], r["lab_Esec"]),
         "a_leque": r.get("a_leque", float("nan")), "c_plano_MPa": r["c_plano"], "phi_plano_graus": r["phi_plano"], "sn_lab_MPa": r.get("sn_lab", float("nan")),
         "tau_lab_MPa": r.get("tau_lab", float("nan")), "residuo_lab_na_reta_MPa": r.get("resid_lab", float("nan")),
         "ciclo_pico": r["ciclo_pico"], "ciclos_ate_pico": j["n_ate"], "ciclos_pos_pico": r["ciclos_pos"],
         # janela pos-pico comum (v3.4.1): f = tempo depois do pico / tempo ate o pico
         "janela_modo": j["modo"], "janela_f": j["f_mod_jan"], "janela_f_lab_permite": j["f_lab"], "janela_f_modelo_cobre": j["f_mod"],
         "janela_limitada_por": j["limita"], "janela_ciclos_modelo": r["jan_ciclo_fim"] - j["cp"],
         "janela_s_lab": (j["f_lab_jan"] * j["lab_t_ate_pico"]) if np.isfinite(j["f_lab_jan"]) else float("nan"),
         "jan_min_modelo_MPa": r["jan_min"], "jan_min_lab_MPa": r["lab_min_pos"], "erro_jan_min_pct": pct(r["jan_min"], r["lab_min_pos"]),
         "jan_fim_modelo_MPa": r["jan_fim"], "jan_fim_lab_MPa": r["lab_fim_janela"], "erro_jan_fim_pct": pct(r["jan_fim"], r["lab_fim_janela"]),
         "jan_deps_modelo_pct": r["jan_deps_fim"], "jan_deps_lab_pct": r["lab_deps_fim"],
         "jan_mu_eq_fim_modelo": r["jan_mu_eq_fim"], "jan_mu_eq_fim_lab": r["lab_mu_eq_fim"],
         "jan_c_impl_fim_modelo_MPa": r["jan_c_impl_fim"], "jan_c_impl_fim_lab_MPa": r["lab_c_impl_fim"],
         "jan_sigma3_desvio_max_pct": r["jan_conf_dev_max_pct"], "jan_sigma3_fora_5pct_pct": r["jan_conf_fora5_pct"],
         "rodada_min_modelo_MPa": r["min_pos"], "rodada_fim_modelo_MPa": r["fim"],
         "sj_ini": r.get("sj0", float("nan")), "sj_pico": r.get("sj_pico", float("nan")), "sj_fim": r.get("sj_fim", float("nan")),
         "sj_restante_fim_pct": 100.0 * r["sj_fim"] / max(r["sj0"], 1) if r["tem_colados"] else float("nan"),
         "sj_restante_pico_pct": 100.0 * r["sj_pico"] / max(r["sj0"], 1) if r["tem_colados"] else float("nan"),
         "sigma3_max_MPa": r["conf_max"], "sigma3_min_MPa": r["conf_min"], "sigma3_desvio_max_pct": r["conf_dev_max_sinal_pct"],
         "sigma3_desvio_pre_pico_max_pct": r["conf_dev_pre_max_pct"], "sigma3_fora_5pct_amostragens_pct": r["conf_fora5_pct"],
         "sigma3_fora_5pct_pre_pico_pct": r["conf_fora5_pre_pct"], "sigma3_fora_5pct_pos_pico_pct": r["conf_fora5_pos_pct"],
         "sigma3_lab_desvio_max_pct": r["lab_conf_dev_max_pct"],
         "razao_prato_esfera": r["razao_prato"], "servo_v34": {True: 1, False: 0, None: ""}[r.get("servo_v34")]}
    fim = next((b for b in reversed(aneis) if b["ciclo"] >= r["ciclo_fim"]), None) if aneis else None
    for i in range(1, 5):
        if fim:
            g = fim["aneis"][i - 1]
            d[f"anel{i}_colados_fim_pct"] = 100.0 * g["colados"] / g["total"] if g["total"] else float("nan")
        else:
            d[f"anel{i}_colados_fim_pct"] = float("nan")
    fr = fracao_mesmo_lado(aneis, r["ciclo_fim"]) if aneis else None       # v3.4.1: contatos que cruzam o plano x mesmo lado
    d["cruzam_colados_fim_pct"] = 100.0 * fr[0] if fr else float("nan")
    d["mesmo_lado_colados_fim_pct"] = 100.0 * fr[1] if fr else float("nan")
    d["colados_fim_que_sao_mesmo_lado_pct"] = 100.0 * fr[2] if fr else float("nan")
    return d


def resumo_geral(linhas, pasta_saida):
    df = pd.DataFrame(linhas).sort_values(["modo", "amostra"]).reset_index(drop=True)
    base = os.path.join(pasta_saida, "resumo_geral")
    df.to_csv(base + ".csv", index=False, float_format="%.6g")
    df.to_csv(base + "_excel_ptbr.csv", index=False, float_format="%.6g", sep=";", decimal=",", encoding="utf-8-sig")
    # tabela de texto (colunas principais)
    L = ["RESUMO GERAL  (modelo x laboratorio; uma linha por amostra)", "=" * 130]
    cab = (f"{'amostra':8s}{'modo':5s}{'s3':>5s}{'dip':>7s}{'a':>6s}{'pico_mod':>9s}{'pico_lab':>9s}{'erro%':>7s}{'mod/env%':>9s}{'lab/env%':>9s}"
           f"{'Esec_m':>7s}{'Esec_l':>7s}{'f':>6s}{'min_m':>7s}{'min_l':>7s}{'fim_m':>7s}{'fim_l':>7s}{'SJ_fim%':>8s}{'s3dev%':>7s}{'fora5%':>7s}")
    L.append(cab)
    L.append("-" * len(cab))
    for _, x in df.iterrows():
        L.append(f"{x.amostra:8s}{x.modo:5s}{v(x.sigma3_MPa, 0):>5s}{v(x.mergulho_graus, 1):>7s}{v(x.a_leque, 2):>6s}{v(x.pico_modelo_MPa):>9s}{v(x.pico_lab_MPa):>9s}"
                 f"{v(x.erro_pico_pct, 1):>7s}{v(x.pico_modelo_sobre_envoltoria_pct, 0):>9s}{v(x.pico_lab_sobre_envoltoria_pct, 0):>9s}"
                 f"{v(x.E_secante_modelo_GPa):>7s}{v(x.E_secante_lab_GPa):>7s}{v(x.janela_f, 2):>6s}{v(x.jan_min_modelo_MPa):>7s}{v(x.jan_min_lab_MPa):>7s}"
                 f"{v(x.jan_fim_modelo_MPa):>7s}{v(x.jan_fim_lab_MPa):>7s}"
                 f"{v(x.sj_restante_fim_pct, 0):>8s}{v(x.sigma3_desvio_max_pct, 1):>7s}{v(x.sigma3_fora_5pct_amostragens_pct, 1):>7s}")
    L.append("")
    L.append("a = posicao da amostra no leque de c e phi do plano (0 = reta de baixo, 1 = reta de cima; n/d = amostra sem leque, usa c e phi comuns).")
    L.append("f = janela pos-pico comum (tempo depois do pico / tempo ate o pico); min_ e fim_ = minimo e nivel no fim DENTRO dessa janela (modelo e lab, mesma janela).")
    L.append("pico/min em MPa; Esec em GPa; erro% = (modelo/lab - 1); mod/env% e lab/env% = pico sobre a envoltoria idealizada (c, phi do plano);")
    L.append("SJ_fim% = contatos colados do plano no fim / no inicio; s3dev% = maior desvio do sigma3 em relacao ao alvo; fora5% = amostragens fora de +-5 %.")
    ok = df[df.modo == "Fol"]
    if len(ok) >= 2:
        L.append("")
        L.append(f"MEDIAS (modo Fol, {len(ok)} amostras): erro do pico = {v(ok.erro_pico_pct.mean(), 1)} % (desvio {v(ok.erro_pico_pct.std(), 1)}), "
                 f"erro do E secante = {v(ok.erro_E_secante_pct.mean(), 1)} %, SJ restante = {v(ok.sj_restante_fim_pct.mean(), 0)} %, "
                 f"sigma3 fora de +-5 % = {v(ok.sigma3_fora_5pct_amostragens_pct.mean(), 1)} % das amostragens")
    open(base + ".txt", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))
    print("gravado em", pasta_saida, "->", "resumo_geral.csv | resumo_geral_excel_ptbr.csv | resumo_geral.txt" + (" | resumo_geral_painel.png" if len(df) >= 2 else ""))
    if len(df) >= 2:
        painel_geral(df, base + "_painel.png")


def painel_geral(df, caminho_png):
    fig, axs = plt.subplots(2, 3, figsize=(17.0, 10.5), dpi=130, facecolor="white")
    fig.subplots_adjust(left=0.055, right=0.985, top=0.87, bottom=0.10, hspace=0.36, wspace=0.26)
    fig.text(0.02, 0.955, f"Resumo geral  ·  {len(df)} amostras  —  modelo × laboratório", fontsize=17, color=INK)
    fig.text(0.02, 0.925, "Cada ponto é uma amostra (rótulo = ITA). Pico, E e mínimo pós-pico: laboratório = curves_lab.csv; pós-pico na janela comum modelo × lab.",
             fontsize=11, color=MUTED)
    cor = {"Fol": LARANJA, "Mat": VERDE}

    def rotulos(ax, x, y, nomes):
        for xi, yi, n in zip(x, y, nomes):
            if np.isfinite(xi) and np.isfinite(yi):
                ax.annotate(n.replace("ITA", ""), (xi, yi), textcoords="offset points", xytext=(5, 4), fontsize=9, color=MUTED)

    def um_a_um(ax, col_m, col_l, titulo, un):
        for modo, g in df.groupby("modo"):
            ax.scatter(g[col_l], g[col_m], s=46, color=cor.get(modo, AZUL), edgecolor="white", zorder=3, label=f"modo {modo}")
            rotulos(ax, g[col_l], g[col_m], g.amostra)
        vals = pd.concat([df[col_m], df[col_l]]).dropna()
        if len(vals):
            lo, hi = 0.0, 1.1 * vals.max()
            ax.plot([lo, hi], [lo, hi], color=MUTED, lw=1.0)
            ax.plot([lo, hi], [0.9 * lo, 0.9 * hi], color=GRID, lw=1.0, ls="--")
            ax.plot([lo, hi], [1.1 * lo, 1.1 * hi], color=GRID, lw=1.0, ls="--")
            ax.set_xlim(lo, hi)
            ax.set_ylim(lo, hi)
        ax.set_xlabel(f"laboratório ({un})", fontsize=10.5, color=INK)
        ax.set_ylabel(f"modelo ({un})", fontsize=10.5, color=INK)
        ax.set_title(titulo, fontsize=11.5, color=INK, loc="left", pad=8)
        ax.legend(frameon=False, fontsize=9, loc="upper left")
        estilo(ax)
        ax.grid(axis="x", color=GRID, lw=0.8)

    um_a_um(axs[0, 0], "pico_modelo_MPa", "pico_lab_MPa", "1  Pico do desviador", "MPa")
    um_a_um(axs[0, 1], "E_secante_modelo_GPa", "E_secante_lab_GPa", "2  E secante até o pico", "GPa")
    # 3. pico sobre a envoltoria x mergulho
    ax = axs[0, 2]
    f = df[df.modo == "Fol"]
    ax.scatter(f.mergulho_graus, f.pico_modelo_sobre_envoltoria_pct, s=46, color=LARANJA, edgecolor="white", zorder=3, label="modelo")
    ax.scatter(f.mergulho_graus, f.pico_lab_sobre_envoltoria_pct, s=46, color=AZUL, edgecolor="white", zorder=3, label="laboratório")
    rotulos(ax, f.mergulho_graus, f.pico_modelo_sobre_envoltoria_pct, f.amostra)
    ax.axhline(100, color=MUTED, lw=1.0)
    ax.set_xlabel("mergulho da foliação (graus com a horizontal)", fontsize=10.5, color=INK)
    ax.set_ylabel("pico ÷ envoltoria idealizada (%)", fontsize=10.5, color=INK)
    ax.set_title("3  Pico sobre a envoltoria (c, φ do plano) × mergulho", fontsize=11.5, color=INK, loc="left", pad=8)
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    estilo(ax)
    ax.grid(axis="x", color=GRID, lw=0.8)
    # 4. sigma3: fora de +-5 %
    ax = axs[1, 0]
    x = np.arange(len(df))
    ax.bar(x - 0.2, df.sigma3_fora_5pct_pre_pico_pct, width=0.4, color=LARANJA, label="pré-pico")
    ax.bar(x + 0.2, df.sigma3_fora_5pct_pos_pico_pct, width=0.4, color=ROXO, label="pós-pico")
    ax.set_xticks(x)
    ax.set_xticklabels(df.amostra.str.replace("ITA", ""), fontsize=9.5, color=MUTED)
    ax.set_ylabel("amostragens com σ3 fora de ±5 % (%)", fontsize=10.5, color=INK)
    ax.set_xlabel("amostra", fontsize=10.5, color=INK)
    ax.set_title("4  Servo lateral: tempo fora de ±5 % do alvo", fontsize=11.5, color=INK, loc="left", pad=8)
    ax.legend(frameon=False, fontsize=9)
    estilo(ax)
    # 5. SJ restante x mergulho
    ax = axs[1, 1]
    ax.scatter(f.mergulho_graus, f.sj_restante_fim_pct, s=46, color=ROXO, edgecolor="white", zorder=3, label="no fim")
    ax.scatter(f.mergulho_graus, f.sj_restante_pico_pct, s=36, color=GRID, edgecolor=MUTED, zorder=2, label="no 1º pico")
    rotulos(ax, f.mergulho_graus, f.sj_restante_fim_pct, f.amostra)
    ax.set_ylim(0, 105)
    ax.set_xlabel("mergulho da foliação (graus)", fontsize=10.5, color=INK)
    ax.set_ylabel("contatos colados do plano (% do início)", fontsize=10.5, color=INK)
    ax.set_title("5  Plano que não rompe: colados restantes × mergulho", fontsize=11.5, color=INK, loc="left", pad=8)
    ax.legend(frameon=False, fontsize=9)
    estilo(ax)
    ax.grid(axis="x", color=GRID, lw=0.8)
    # 6. minimo pos-pico
    um_a_um(axs[1, 2], "jan_min_modelo_MPa", "jan_min_lab_MPa", "6  Mínimo pós-pico (janela comum)", "MPa")
    fig.text(0.02, 0.025, "Gráficos 1, 2 e 6: linha cheia = 1:1, tracejado = ±10 %. Envoltória idealizada: blocos rígidos, tensão uniforme (inferência). "
             "Modelo: esfera de medida central.\nAmostras em modo matriz não têm envoltória do plano (não entram nos gráficos 3 e 5).", fontsize=9.5, color=MUTED, va="center", linespacing=1.4)
    fig.savefig(caminho_png)
    plt.close(fig)


# ---------------------------------------------------------------- principal
def processa(caminho, a):
    am, modo, s3 = meta_do_nome(caminho)
    if am is None:
        print(f"[pulei] nome fora do padrao <ITAxx>_<Fol|Mat>_<s3>MPa_Triaxial_Histories: {caminho}")
        return
    pasta = os.path.dirname(os.path.abspath(caminho))
    base = os.path.basename(caminho).rsplit(".", 1)[0]
    pastas_in = [a.inputs] if a.inputs else []
    pastas_in += [os.path.join(pasta, "..", "00_Inputs"), os.path.join(pasta, "00_Inputs"), pasta, "."]
    pastas_lab = [a.dados] if a.dados else []
    pastas_lab += [pasta, os.path.join(pasta, "..", "00_Inputs"), os.path.join(pasta, ".."), "."]
    params = le_params(am, pastas_in)
    lab_total, arq_lab = le_lab(am, pastas_lab)
    if lab_total is None:
        print(f"[AVISO] curves_lab.csv (ou curves.csv) do laboratorio (com a amostra {am}) NAO encontrado em: "
              + " | ".join(os.path.normpath(x) for x in pastas_lab[:4])
              + "\n        Copie o curves_lab.csv para 00_Inputs (ao lado de 03_Outputs) ou rode com --dados <pasta do curves_lab.csv>. Sem ele so ha o pico do params.dat.")
    df = le_pfc(caminho)
    a.s3 = s3
    # [v3.4.1] janela pos-pico: mesmo f (tempo depois do pico / tempo ate o pico) no lab e no modelo
    jan = janela_comum(df, lab_total, a, inicio_carga_log(base, pasta))
    lab_val = corta_lab_f(lab_total, jan["f_lab"])        # parte do lab que vale (1o terco do tempo pos-pico)
    lab = corta_lab_f(lab_total, jan["f_lab_jan"])        # parte do lab dentro da janela
    c_ap, f_ap, mu_ap, origem_ap, aviso_ap = plano_aplicado(base, pasta, params, a)       # [v3.4.1] c, phi e mu que a RODADA usou
    a_s = copy.copy(a)
    a_s.c, a_s.phi, a_s.mu = c_ap, f_ap, mu_ap
    r, df, lab = analisa(df, lab, params, a_s, modo, jan)
    if lab_val is not None:
        lab_val = lab_val.copy()
        lab_val["d_eps_ax_pos_pct"] = lab_val.eps_ax_pct - lab_val.eps_ax_pct[r["kl"]]
    r["_n"] = range(len(df))
    r["mu_ref"], r["raio_nom"], r["c_plano"] = a_s.mu, a.raio * 1000.0, a_s.c
    r["phi_plano"], r["plano_origem"], r["plano_aviso"], r["params"] = a_s.phi, origem_ap, aviso_ap, params
    r["ajuste"] = le_ajuste_plano(pastas_in)
    r["a_leque"] = params.get("_a_leque") if params.get("_a_leque") is not None else float("nan")      # [v4] a do .dat (so amostras com leque)
    r["leque"] = le_leque(pastas_in) if params.get("_a_leque") is not None else None
    calcula_plano(r, params)
    r["servo_v34"] = servo_v34(base, pasta)
    aneis = le_aneis(base, pasta)
    out = a.saida if a.saida else os.path.join(pasta, "analise")
    os.makedirs(out, exist_ok=True)
    sai = os.path.join(out, base.replace("_Triaxial_Histories", ""))
    df.to_csv(sai + "_Historico.csv", index=False, float_format="%.8g")
    df.to_csv(sai + "_Historico_excel_ptbr.csv", index=False, float_format="%.8g", sep=";", decimal=",", encoding="utf-8-sig")
    painel(df, lab, lab_val, r, am, modo, params, sai + "_painel.png")
    if not a.sem_diagnostico:
        painel_diagnostico(df, lab, lab_val, r, am, modo, params, sai + "_diagnostico.png")
    texto = texto_resumo(base.replace("_Triaxial_Histories", ""), am, modo, r, lab is not None, le_log(base, pasta), aneis)
    open(sai + "_resumo.txt", "w", encoding="utf-8").write(texto)
    print(texto)
    print("gravado em", out, "->", os.path.basename(sai) + "_Historico.csv | _Historico_excel_ptbr.csv | _painel.png" + ("" if a.sem_diagnostico else " | _diagnostico.png") + " | _resumo.txt")
    if lab is not None:
        print("laboratorio:", arq_lab)
    return linha_geral(am, modo, r, aneis), out


def main():
    ap = argparse.ArgumentParser(description="Pos-processamento dos historicos do PFC (03_Outputs)")
    ap.add_argument("arquivos", nargs="*", help="arquivos *_Triaxial_Histories.txt (padrao: todos da pasta atual)")
    ap.add_argument("--dados", default=None, help="pasta com o curves_lab.csv (ou curves.csv) do laboratorio")
    ap.add_argument("--inputs", default=None, help="pasta com os <amostra>_params.dat (padrao: ../00_Inputs)")
    ap.add_argument("--saida", default=None, help="pasta de saida (padrao: ./analise)")
    ap.add_argument("--c", type=float, default=12.0, help="reserva: coesao do plano, MPa (rodadas SEM a linha de parametros no log; Main antigo = 12,0)")
    ap.add_argument("--phi", type=float, default=19.0, help="reserva: atrito do plano, graus (Main antigo = 19,0)")
    ap.add_argument("--mu", type=float, default=0.48, help="reserva: atrito residual do plano (p_sjfric do Main)")
    ap.add_argument("--raio", type=float, default=0.032, help="raio do corpo de prova, m (geo_raio do Main)")
    ap.add_argument("--altura", type=float, default=128.15, help="altura do corpo de prova, mm (geo_alt do Main x 1000)")
    ap.add_argument("--dip", type=float, default=45.0, help="mergulho se nao houver params.dat")
    ap.add_argument("--pos-pico-lab", dest="pos_pico_lab", type=float, default=1.0 / 3.0,
                    help="fracao do tempo pos-pico do lab que vale (padrao 1/3; 1 = usa tudo)")
    ap.add_argument("--janela", choices=["comum", "rodada"], default="comum",
                    help="comum (padrao): lab e modelo no mesmo f pos-pico; rodada: lab ate o 1o terco, modelo ate o fim (janelas diferentes, como na v3.4)")
    ap.add_argument("--sem-diagnostico", dest="sem_diagnostico", action="store_true",
                    help="nao grava o _diagnostico.png (2 graficos); so o painel principal")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    arqs = a.arquivos
    if not arqs:
        arqs = sorted(glob.glob("*_Triaxial_Histories.txt") + glob.glob("*_Triaxial_Histories.csv"))
    if not arqs:
        print("Nenhum *_Triaxial_Histories.txt na pasta atual. Rode dentro de 03_Outputs ou passe o arquivo.")
        sys.exit(1)
    linhas, pasta_saida = [], None
    for arq in arqs:
        try:
            res = processa(arq, a)
            if res:
                linhas.append(res[0])
                pasta_saida = pasta_saida or res[1]
        except Exception as e:  # uma rodada com problema nao impede as outras
            print(f"[erro] {arq}: {e}")
    if len(linhas) >= 2:      # com 1 so rodada nao grava: sobrescreveria o resumo geral anterior
        try:
            resumo_geral(linhas, pasta_saida)
        except Exception as e:
            print(f"[erro] resumo geral: {e}")


if __name__ == "__main__":
    main()
