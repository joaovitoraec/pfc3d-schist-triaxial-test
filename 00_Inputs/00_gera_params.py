#!/usr/bin/env python3
# =============================================================================
# 00_gera_params.py   [v4]
# =============================================================================
#
# O QUE FAZ
#   Gera um arquivo <amostra>_params.dat para cada amostra.
#   O 00_Main_Run.dat le esse arquivo e usa os valores no modelo.
#   Os dados vem de specimens.csv e targets.csv (a tabela de resultados dos ensaios).
#
#
# COMO USAR
#   Abra o terminal na pasta 00_Inputs, onde estao os dois csv.
#
#   python 00_gera_params.py              PADRAO v4: c, phi e atrito residual pelo LEQUE; kn pelo E secante
#   python 00_gera_params.py --comum      c, phi e kn comuns (.dat identicos aos da v3.4.1, byte a byte)
#
#   Outras opcoes (lista completa: python 00_gera_params.py -h):
#     --dados <pasta>                     pasta dos csv
#     --saida <pasta>                     pasta dos .dat
#     --individual nenhum|c|phi|leque     o que calibrar no plano (secao 1); leque e o padrao
#     --sjfric leque|global               atrito residual do plano: tan(phi) da amostra (padrao) ou o 0.48 do Main
#     --kn nenhum|secante                 como calibrar o kn (secao 2); secante e o padrao
#     --kn-ref  --E-modelo-ref  --kn-min  --kn-max     valores de referencia e limites do kn (secao 2)
#
#   Depois de gerar, rode 01_fit_plano_foliacao.py: confere os .dat e desenha os dois graficos (phi fixo e leque).
#
#
# O QUE CADA .dat RECEBE
#   foliacao_dip     mergulho da foliacao.
#                    E o anisotropy_angle_deg do banco.
#   p_sjcoh          coesao do plano (secao 1).
#   p_sjfa           atrito do plano, no contato colado (secao 1).
#   p_sjfric         [v4] atrito residual do plano, depois que o contato rompe: tan(phi) (secao 1).
#   p_fjkn, p_fjks   rigidez dos contatos. So nas amostras calibradas (secao 2).
#   pressao_conf     sigma3 do ensaio.
#   eps_ax_max       deformacao axial em que o ensaio para (4 x a deformacao do pico do lab, entre 1.0 e 3.0 %).
#   lab_*            referencias do laboratorio: desviador e deformacao no pico, E e nu.
#
#
# QUEM E CALIBRADO
#   Sao as amostras que rompem no plano de foliacao. Cada uma precisa ter:
#     - ruptura no plano (failure_mode = foliation);
#     - confianca high ou medium;
#     - in_analysis = yes;
#     - use_plane_fit = yes.
#   As demais ficam com c, phi e kn comuns (e com o p_sjfric do Main).
#   Excecao: as amostras listadas em SEM_KN (vazia por padrao) recebem c e phi do leque, mas nao recebem kn_i.
#   Uso tipico: amostra cujo plano o modelo nao rompe, de modo que o pico do modelo nao e controlado pelo plano.
#
#   [v4] O LEQUE VALE PARA TODAS (padrao, --leque-em todas): alem das que rompem no plano, recebem c, phi e p_sjfric do
#   leque as amostras que NAO sao de matriz e cujo ponto cai DENTRO do leque (a entre 0 e 1). O kn continua so para as
#   que rompem no plano. Ficam com c, phi e p_sjfric comuns: as de matriz e as que caem fora do leque (outliers).
#   --leque-em 10 restringe o leque as amostras com use_plane_fit = yes.
#   Cuidado ao ler as outras: o ponto (sn, tau) delas so representa o plano se a ruptura foi no plano.
#   Nas mistas, de confianca baixa ou sem modo de ruptura registrado, o a e a posicao do ponto, nao uma propriedade do plano.
#
#
# -----------------------------------------------------------------------------
# 1) COESAO E ATRITO DO PLANO   (p_sjcoh, p_sjfa e p_sjfric)   [v4: LEQUE]
# -----------------------------------------------------------------------------
#
#   PASSO 0 - UM PONTO (sn, tau) POR ENSAIO
#     Cada ensaio da UM ponto no plano de foliacao, no pico:
#         sn  = s3 + D cos^2(theta)
#         tau = D sin(theta) cos(theta)
#     D = desviador no pico.  theta = mergulho.
#
#   ORIGEM DO PROBLEMA
#     O criterio do plano e tau = c + sn tan(phi) ---> duas incognitas: c e phi.
#     Um ensaio so mede a combinacao  c + sn tan(phi) = tau.
#     Por um ponto passam infinitas retas ---> nao existe c e phi proprios de uma amostra so com o ensaio.
#     Fixar o phi resolvia isso a forca: igualava o atrito de todas as amostras.
#     Com dados reais isso nem sempre se sustenta (ajuste com R2 baixo e IC 95 % largo do phi).
#
#   A IDEIA DO LEQUE
#     Em vez de fixar o phi, delimita-se a nuvem de pontos por DUAS RETAS EXTREMAS.
#     O conjunto de retas entre elas e o leque. Cada amostra recebe a reta do leque
#     que passa EXATAMENTE no ponto dela. Isso da um c e um phi para cada amostra,
#     amarrados por uma regra (a posicao dela no leque).
#     Escrita das retas:  tau = c + m sn,  com  m = tan(phi).
#
#   PASSO 1 - RETA DE CIMA (a = 1), por duas amostras ancora (ANC_CIMA, no topo do codigo)
#         m_cima = (tau_2 - tau_1) / (sn_2 - sn_1)
#         c_cima = tau_1 - m_cima sn_1
#         phi_cima = atan(m_cima)
#
#   PASSO 2 - RETA DE BAIXO (a = 0), por duas amostras ancora (ANC_BAIXO, no topo do codigo)
#         mesmas formulas: m_baixo, c_baixo, phi_baixo.
#
#   PASSO 3 - DIFERENCAS
#         dc = c_cima - c_baixo        dm = m_cima - m_baixo
#     As duas retas se cruzam em  sn = -dc / dm  (o pivo), que fica em tracao, fora dos dados.
#     Para sn > 0 elas nao se cruzam (dc e dm positivos): o leque e bem definido.
#
#   PASSO 4 - O LEQUE: uma reta para cada valor do parametro a, de 0 a 1
#         c(a) = c_baixo + a dc
#         m(a) = m_baixo + a dm
#         phi(a) = atan( m(a) )
#     a = 0 e a reta de baixo; a = 1 e a de cima.
#     Passos iguais de a dao a mesma distancia VERTICAL entre retas vizinhas, em qualquer sn.
#     Este e o argumento para dividir o leque igualmente. E uma convencao neutra, nao um resultado estatistico.
#
#   PASSO 5 - A RETA DE CADA AMOSTRA (o a de cada ponto)
#     Exige-se que a reta passe no ponto (sn, tau) da amostra:
#         tau = c(a) + m(a) sn = (c_baixo + a dc) + (m_baixo + a dm) sn
#     Abrindo e isolando a (a unica incognita):
#         a = ( tau - c_baixo - m_baixo sn ) / ( dc + dm sn )
#     Numerador = altura do ponto acima da reta de baixo.
#     Denominador = distancia vertical entre as duas retas extremas nesse sn.
#     Entao a e a FRACAO DA ALTURA do ponto dentro do leque (0 na reta de baixo, 1 na de cima).
#
#   PASSO 6 - DO a SAEM c, phi E O ATRITO RESIDUAL
#         c = c_baixo + a dc               (MPa)  -> p_sjcoh
#         phi = atan( m_baixo + a dm )     (graus) -> p_sjfa
#         p_sjfric = tan(phi)                       -> atrito residual
#     [v4] p_sjfric = tan(phi): a hipotese classica de que a coesao se perde na ruptura
#     e o atrito do plano continua o mesmo. Antes era 0.48 para todas (--sjfric global).
#     Se o a de uma amostra cair fora de [0, 1], ela esta fora do leque: o script avisa e usa o c e o phi comuns.
#
#   EXEMPLO: ver a saida de 01_fit_plano_foliacao.py (fit_plano_resumo.txt) com os dados sinteticos do repositorio.
#
#   O QUE O LEQUE NAO FAZ (declarar no artigo)
#     - O leque e um envelope EMPIRICO, apoiado em 4 amostras ancora. Nao e propriedade do material.
#       Ancoras de ruptura mista ou de confianca baixa enfraquecem o envelope.
#     - A amarra entre c e phi ao longo do leque e uma HIPOTESE imposta pela construcao, nao uma medida.
#     - Qualquer reta que passe no ponto da amostra da o MESMO pico analitico (Jaeger) para ela.
#       O leque nao melhora o pico por construcao: ele muda o phi do contato colado (sj_fa) e o atrito residual (sj_fric).
#
#   OPCOES ANTERIORES (continuam disponiveis)
#   Opcao A - comum   (--comum; amostras fora das 10 ideais)
#     Todas usam o mesmo (c, phi), do ajuste de minimos quadrados das amostras use_plane_fit = yes.
#     Nada e calibrado ao pico do lab.
#   Opcao B - c individual   (--individual c; padrao da v3.4.2)
#     O phi fica comum e   c_i = tau - sn tan(phi).
#   Opcao C - phi individual   (--individual phi)
#     O c fica comum e   phi_i = atan((tau - c) / sn).
#
#   Nos .dat, cada valor vem marcado como 'comum', 'CALIBRADO' ou 'LEQUE'.
#
#
# -----------------------------------------------------------------------------
# 2) RIGIDEZ DOS CONTATOS   (p_fjkn e p_fjks)   [igual a v3.4.2]
# -----------------------------------------------------------------------------
#
#   CONTROLE DO Kn
#     O kn controla o modulo E e a deformacao no pico (E = proporcional a kn).
#     O pico vem da coesao do plano, nao do kn.
#
#   CALCULO DO Kn
#     kn_i = kn_ref x E_alvo_lab / E_modelo_ref
#     ks_i = 0.4 x kn_i        (a razao ks/kn fica mantida)
#
#   DEFINICAO DOS TERMOS
#     kn_ref         6.8e12 Pa/m. E o kn da v3.4.1.
#
#     E_alvo_lab     E SECANTE do laboratorio = desviador no pico / deformacao no pico.
#                    So vale com eps_peak_reliable = yes; sem isso a amostra fica com o kn comum.
#
#     E_modelo_ref   E que o modelo deu com o kn_ref.
#                    Valor padrao: 23.7 GPa (E secante do modelo).
#                    E uma ESTIMATIVA de tres rodadas do modelo; refine com as suas.
#                    Sera refinado com as rodadas novas (--E-modelo-ref).
#
#   DECISAO
#     O kn e calibrado pelo E secante do laboratorio.
#
#   LIMITACOES DO ALVO SECANTE
#     - A curva do lab e em S: comeca mole (fechamento de microfissuras) e depois enrijece.
#     - O modelo e linear ate o pico.
#     - Casando o E secante, o modelo chega ao pico na deformacao do lab.
#     - Em compensacao, fica mais mole que o lab no trecho central da curva.
#     - E_modelo_ref e uma estimativa de tres rodadas. Se errar, todos os kn_i erram na mesma proporcao.
#     - "E proporcional a kn" e uma aproximacao, confirmada so em poucas rodadas.
#     - O E do lab de alguns corpos de prova pode ser atipico (o fator bruto passa do limite e e cortado).
#
#   LIMITES DOS FATORES DE Kn
#     O fator kn_i / kn_ref fica entre 0.75 e 1.40 (--kn-min e --kn-max).
#     Quando o limite age, o script avisa.
#     Motivo: o E de laboratorio de alguns corpos de prova pode ser atipico.
#
#
#   SAIDAS
#     <amostra>_params.dat   um por amostra.
#     params_resumo.csv      c, phi, a do leque, atrito residual, kn, fator de kn e origem de cada amostra.
#
#
# -----------------------------------------------------------------------------
# HISTORICO DE VERSOES
# -----------------------------------------------------------------------------
#
#   v3.4.1   Reescrito; mesmos nomes de arquivo de saida.
#            - Sairam: a escolha banco/celula (--angulo), foliacao_fonte, lab_ang_rupt, a coluna conflito_angulo
#              e os comentarios ATENCAO. O mergulho passou a ser so o anisotropy_angle_deg.
#            - Le specimens.csv e targets.csv da pasta atual (--dados e --saida mudam isso).
#            - Cada .dat ganhou p_sjcoh e p_sjfa. Padrao: (c, phi) comum do ajuste de minimos quadrados.
#            - Entrou a calibracao opcional --individual c|phi, rotulada no .dat.
#            - Cabecalho do .dat: 'ajuste do plano = yes/no/check' e a linha com o c e o phi gravados.
#            - params_resumo.csv: sairam foliacao_fonte e conflito_angulo.
#              Entraram c_MPa, phi_deg, plano e ajuste_plano.
#
#   v3.4.2   c e kn por amostra viram o PADRAO para as amostras que rompem no plano.
#            - O padrao mudou: [--individual c] e [--kn secante]. O atalho [--comum] devolve a saida da v3.4.1.
#            - Novo [--kn nenhum|secante], com [--kn-ref], [--E-modelo-ref], [--kn-min] e [--kn-max].
#            - Os .dat calibrados ganham p_fjkn, p_fjks e a linha de comentario '; Rigidez dos contatos: ...'.
#            - [c_i] e [kn_i] so para [use_plane_fit = yes].
#            - Amostras 'check' voltam ao c e ao kn comuns.
#            - Amostras em SEM_KN recebem [c_i], mas nao [kn_i].
#            - params_resumo.csv: colunas novas [kn_fator], [kn_Pa_m] e [kn_origem].
#            - Cabecalho reorganizado e historico de versoes incluido aqui.
#
#   v4       c e phi por amostra pelo LEQUE (a = 0 na reta de baixo, a = 1 na de cima); phi deixa de ser fixo.
#            - Novo [--individual leque] (PADRAO). Ancoras no topo do codigo: ANC_CIMA e ANC_BAIXO.
#            - Novo [--leque-em todas|10]: o leque vale para toda amostra fora da matriz que caia dentro dele (padrao);
#              [10] restringe as amostras com use_plane_fit = yes.
#            - Novo [--sjfric leque|global]: o atrito residual p_sjfric vira tan(phi) de cada amostra (padrao).
#              Com [global] o .dat nao traz o p_sjfric e vale o 0.48 do Main.
#            - Os .dat com leque ganham a linha 'p_sjfric' e comentarios 'LEQUE a = ...'.
#            - params_resumo.csv: colunas novas [a_leque] e [sjfric].
#            - O calculo do kn nao mudou. A rugosidade fica para depois.
#
import argparse
import math
import os
import sys
import unicodedata

import numpy as np
import pandas as pd

# Quem rompeu no plano de forma confiavel (recebe c e phi proprios)
RUPTURA_OK = ("foliation",)
CONFIANCA_OK = ("high", "medium")
# [v4] amostras ancora das duas retas extremas do leque (editaveis; 01_fit_plano_foliacao.py usa as mesmas)
# Aqui: as ancoras do conjunto SINTETICO do repositorio (escolhidas por busca, para o leque conter todos os pontos).
# Com dados reais, escolha as suas (duas amostras para cada reta) e confira o grafico de 01_fit_plano_foliacao.py.
ANC_CIMA = ("ITA901", "ITA906")    # reta de cima, a = 1
ANC_BAIXO = ("ITA902", "ITA905")   # reta de baixo, a = 0
TOL_A = 1.0e-6                     # tolerancia para a cair em [0, 1]
# [v3.4.2] kn por amostra
KN_REF = 6.8e12              # Pa/m, kn da v3.4.1 (Main: p_fjkn)
KS_SOBRE_KN = 0.4            # razao ks/kn mantida
E_MODELO_REF = 23.7         # GPa, E secante que o modelo deu com KN_REF (estimativa; ver cabecalho)
SEM_KN = ()                  # ids que recebem c e phi mas nao kn_i (ex.: o modelo nao rompe o plano deles)


def ascii_only(s):
    s = unicodedata.normalize("NFKD", str(s))
    return s.encode("ascii", "ignore").decode("ascii")


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def acha(pasta, nomes):
    for n in nomes:
        p = os.path.join(pasta, n)
        if os.path.isfile(p):
            return p
    sys.exit("Nao achei %s em %s" % (" ou ".join(nomes), os.path.abspath(pasta)))


def tensoes_plano(s3, D, dip):
    """Tensao normal e cisalhante no plano de mergulho dip (graus) quando sigma1 = s3 + D."""
    th = math.radians(dip)
    return s3 + D * math.cos(th) ** 2, D * math.sin(th) * math.cos(th)


# ----------------------------------------------------------------------------
# [v4] LEQUE (passos 1 a 6 do cabecalho). Funcoes puras: o 01_fit_plano_foliacao.py importa estas.
# ----------------------------------------------------------------------------
def reta_por_dois_pontos(p1, p2):
    """Reta tau = c + m sn por dois pontos (sn, tau). Devolve (c, m)."""
    (x1, y1), (x2, y2) = p1, p2
    m = (y2 - y1) / (x2 - x1)
    return y1 - m * x1, m


def monta_leque(pontos_cima, pontos_baixo):
    """Passos 1 a 3: as duas retas extremas e suas diferencas. Cada argumento: dois pontos (sn, tau)."""
    cu, mu = reta_por_dois_pontos(*pontos_cima)
    cl, ml = reta_por_dois_pontos(*pontos_baixo)
    dc, dm = cu - cl, mu - ml
    if dc <= 0 or dm <= 0:
        sys.exit("As duas retas extremas se cruzam para sn > 0 (dc = %.3f, dm = %.4f): o leque nao esta bem definido. "
                 "Confira ANC_CIMA e ANC_BAIXO." % (dc, dm))
    return dict(cu=cu, mu=mu, cl=cl, ml=ml, dc=dc, dm=dm, pivo=-dc / dm,
                phi_cima=math.degrees(math.atan(mu)), phi_baixo=math.degrees(math.atan(ml)))


def posicao_a(L, sn, tau):
    """Passo 5: a da reta do leque que passa no ponto (sn, tau)."""
    return (tau - L["cl"] - L["ml"] * sn) / (L["dc"] + L["dm"] * sn)


def reta_do_leque(L, a):
    """Passos 4 e 6: (c [MPa], m = tan(phi), phi [graus]) para um valor de a."""
    c = L["cl"] + a * L["dc"]
    m = L["ml"] + a * L["dm"]
    return c, m, math.degrees(math.atan(m))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados", default=".", help="pasta com specimens.csv e targets.csv")
    ap.add_argument("--saida", default=".", help="pasta de saida dos *_params.dat (padrao: a pasta atual, 00_Inputs)")
    ap.add_argument("--individual", default="leque", choices=["nenhum", "c", "phi", "leque"],
                    help="leque (padrao v4): c e phi de cada amostra pela reta do leque que passa no ponto dela; "
                         "c: calibra so o c (v3.4.2); phi: calibra so o phi; nenhum: c e phi comuns do ajuste")
    ap.add_argument("--leque-em", default="todas", choices=["todas", "10"],
                    help="[v4] quem recebe o leque: todas (padrao) = as que rompem no plano + toda amostra fora da matriz que caia dentro do leque; "
                         "10 = so as com use_plane_fit = yes")
    ap.add_argument("--sjfric", default="leque", choices=["leque", "global"],
                    help="[v4] atrito residual do plano: leque (padrao) = tan(phi) da amostra; global = o p_sjfric do Main (0.48)")
    ap.add_argument("--kn", default="secante", choices=["nenhum", "secante"],
                    help="[v3.4.2] secante (padrao): CALIBRA kn de cada amostra ao E secante do lab; nenhum: kn unico do Main")
    ap.add_argument("--comum", action="store_true",
                    help="atalho: --individual nenhum --kn nenhum --sjfric global (c e phi comuns, kn unico: saida identica a da v3.4.1)")
    ap.add_argument("--kn-ref", type=float, default=KN_REF, help="kn de referencia (Pa/m); padrao 6.8e12")
    ap.add_argument("--E-modelo-ref", type=float, default=None, help="E secante (GPa) do modelo com kn-ref; padrao: 23.7")
    ap.add_argument("--kn-min", type=float, default=0.75, help="fator minimo de kn (padrao 0.75)")
    ap.add_argument("--kn-max", type=float, default=1.40, help="fator maximo de kn (padrao 1.40)")
    a = ap.parse_args()
    if a.comum:
        a.individual, a.kn, a.sjfric = "nenhum", "nenhum", "global"

    spec = pd.read_csv(acha(a.dados, ["specimens.csv", "ita_specimens_overview.csv"])).set_index("id_ita")
    tgt = pd.read_csv(acha(a.dados, ["targets.csv", "ita_targets.csv"])).set_index("id_ita")
    os.makedirs(a.saida, exist_ok=True)

    # ---- 1) dados de cada amostra
    am = []
    for ita in tgt.index:
        t = tgt.loc[ita]
        sigma3 = num(t.get("sigma3_target_MPa"))
        if sigma3 is None:
            print("AVISO:", ita, "sem sigma3_target_MPa; pulado")
            continue
        dip = num(spec.loc[ita].get("anisotropy_angle_deg")) if ita in spec.index else None
        if dip is None:
            dip = num(t.get("anisotropy_angle_deg"))
        if dip is None:
            print("AVISO:", ita, "sem anisotropy_angle_deg; pulado")
            continue
        dip = round(dip, 2)
        D = num(t.get("dev_peak_MPa")) or 0.0
        sn, tau = tensoes_plano(sigma3, D, dip)
        am.append(dict(ita=ita, s3=sigma3, dip=dip, D=D, sn=sn, tau=tau,
                       eps_pk=num(t.get("eps_ax_peak_pct")) or 0.0,
                       E=num(t.get("E_fit_40_60_GPa")) or 0.0,
                       nu=num(t.get("nu_fit_40_60")) or 0.0,
                       modo=ascii_only(t.get("failure_mode", "n.a.")),
                       conf=ascii_only(t.get("confidence", "n.a.")),
                       em_analise=ascii_only(t.get("in_analysis", "?")),
                       ajuste=ascii_only(t.get("use_plane_fit", "no")),
                       eps_ok=ascii_only(t.get("eps_peak_reliable", "no")) == "yes"))

    # ---- 2) ajuste comum do plano: tau = c + sn tan(phi)   (amostras fora do leque, --comum e o grafico "phi fixo")
    no_ajuste = [r for r in am if r["ajuste"] == "yes" and r["D"] > 0 and r["dip"] > 0]
    if len(no_ajuste) < 4:
        sys.exit("Poucas amostras com use_plane_fit = yes: %d" % len(no_ajuste))
    tanphi, c_aj = np.polyfit([r["sn"] for r in no_ajuste], [r["tau"] for r in no_ajuste], 1)
    phi_comum = round(math.degrees(math.atan(tanphi)), 2)       # graus
    c_comum = round(c_aj, 2)                                     # MPa
    print("Ajuste comum do plano (%d amostras: %s): c = %.2f MPa, phi = %.2f graus"
          % (len(no_ajuste), ", ".join(r["ita"] for r in no_ajuste), c_comum, phi_comum))

    # ---- 2b) [v4] leque pelas amostras ancora
    L = None
    if a.individual == "leque":
        por = {r["ita"]: r for r in am}
        faltam = [k for k in ANC_CIMA + ANC_BAIXO if k not in por or por[k]["D"] <= 0 or por[k]["dip"] <= 0]
        if faltam:
            sys.exit("Amostra(s) ancora sem dados no banco: " + ", ".join(faltam))
        pt = lambda k: (por[k]["sn"], por[k]["tau"])
        L = monta_leque([pt(k) for k in ANC_CIMA], [pt(k) for k in ANC_BAIXO])
        print("Leque (ancoras: cima = %s, baixo = %s)" % (" + ".join(ANC_CIMA), " + ".join(ANC_BAIXO)))
        print("  a = 1 (cima):  m = %.4f  c = %.2f MPa  phi = %.2f graus" % (L["mu"], L["cu"], L["phi_cima"]))
        print("  a = 0 (baixo): m = %.4f  c = %.2f MPa  phi = %.2f graus" % (L["ml"], L["cl"], L["phi_baixo"]))
        print("  dc = %.3f  dm = %.4f  pivo em sn = %.1f MPa (tracao, fora dos dados)" % (L["dc"], L["dm"], L["pivo"]))

    # ---- 3) c e phi de cada amostra, e os arquivos
    resumo = []
    for r in am:
        c, phi, origem = c_comum, phi_comum, "comum"
        a_lq, sjfric = None, None
        no_plano = (r["modo"] in RUPTURA_OK and r["conf"] in CONFIANCA_OK and r["em_analise"] == "yes"
                    and r["ajuste"] == "yes" and r["D"] > 0 and r["dip"] > 0)   # so as amostras com use_plane_fit = yes
        if a.individual == "nenhum":
            no_plano = False
        if no_plano and a.individual == "c":
            ci = round(r["tau"] - r["sn"] * math.tan(math.radians(phi_comum)), 2)
            if ci > 0:
                c, origem = ci, "calibrado"
            else:
                print("AVISO:", r["ita"], "c individual = %.2f MPa <= 0; usei o c comum" % ci)
        elif no_plano and a.individual == "phi":
            pi = round(math.degrees(math.atan((r["tau"] - c_comum) / r["sn"])), 2)
            if 0.0 < pi < r["dip"]:
                phi, origem = pi, "calibrado"
            else:
                print("AVISO:", r["ita"], "phi individual = %.2f fora de (0, mergulho); usei o phi comum" % pi)
        elif a.individual == "leque" and (no_plano or (a.leque_em == "todas" and r["modo"] != "matrix"
                                                       and r["D"] > 0 and r["dip"] > 0)):
            aa = posicao_a(L, r["sn"], r["tau"])
            if aa < -TOL_A or aa > 1.0 + TOL_A:
                print("AVISO:", r["ita"], "a = %.3f fora de [0, 1] (fora do leque); usei o c e o phi comuns" % aa)
            else:
                aa = min(1.0, max(0.0, aa))
                c_l, m_l, phi_l = reta_do_leque(L, aa)
                c_l, phi_l = round(c_l, 2), round(phi_l, 2)
                if c_l > 0 and 0.0 < phi_l < r["dip"]:
                    c, phi, origem, a_lq = c_l, phi_l, "leque", aa
                    if a.sjfric == "leque":
                        sjfric = math.tan(math.radians(phi))      # [v4] atrito residual = tan(phi gravado)
                else:
                    print("AVISO:", r["ita"], "c = %.2f MPa, phi = %.2f graus do leque fora de (c > 0, 0 < phi < mergulho); usei o c e o phi comuns"
                          % (c_l, phi_l))

        if origem == "leque":
            c_txt = "c = %.2f MPa (LEQUE a = %.3f: c = c_baixo + a (c_cima - c_baixo))" % (c, a_lq)
            f_txt = "phi = %.2f graus (LEQUE a = %.3f: tan(phi) = m_baixo + a (m_cima - m_baixo))" % (phi, a_lq)
        elif origem == "calibrado" and a.individual == "c":
            c_txt = "c = %.2f MPa (CALIBRADO ao pico do lab desta amostra: tau - sn tan(phi))" % c
            f_txt = "phi = %.2f graus (comum: ajuste do plano)" % phi
        elif origem == "calibrado":
            c_txt = "c = %.2f MPa (comum: ajuste do plano)" % c
            f_txt = "phi = %.2f graus (CALIBRADO ao pico do lab desta amostra: atan((tau - c) / sn))" % phi
        else:
            c_txt = "c = %.2f MPa (comum: ajuste do plano)" % c
            f_txt = "phi = %.2f graus (comum: ajuste do plano)" % phi

        # [v3.4.2] kn por amostra (so com --kn secante)
        kn, kn_fator, kn_origem, kn_txt = None, 1.0, "comum", None
        if a.kn != "nenhum":
            ok_kn = (r["modo"] in RUPTURA_OK and r["conf"] in CONFIANCA_OK and r["em_analise"] == "yes" and r["ajuste"] == "yes"
                     and r["D"] > 0 and r["dip"] > 0 and r["ita"] not in SEM_KN)
            E_alvo = (r["D"] / (r["eps_pk"] / 100.0) / 1000.0) if (r["eps_pk"] > 0 and r["eps_ok"]) else None   # E secante do lab, GPa
            E_ref = a.E_modelo_ref if a.E_modelo_ref else E_MODELO_REF
            if not ok_kn or E_alvo is None:
                print("kn:", r["ita"], "-> kn comum (fora da regra ou sem E confiavel)")
            else:
                f_raw = E_alvo / E_ref
                f = min(a.kn_max, max(a.kn_min, f_raw))
                if abs(f - f_raw) > 1e-9:
                    print("AVISO kn:", r["ita"], "fator %.2f (E alvo %.1f GPa) limitado a %.2f" % (f_raw, E_alvo, f))
                kn, kn_fator, kn_origem = a.kn_ref * f, f, "calibrado"
                kn_txt = ("kn = %.3e Pa/m = %.2f x kn_ref (CALIBRADO ao E %s do lab = %.1f GPa; E modelo ref = %.1f GPa) | ks = %.1f kn"
                          % (kn, f, a.kn, E_alvo, E_ref, KS_SOBRE_KN))

        # parada por deformacao: 4x a deformacao do pico do lab, entre 1.0 e 3.0 %
        eps_max = min(3.0, max(1.0, round(4.0 * abs(r["eps_pk"]), 1)))
        linhas = []
        linhas.append("; Parametros da amostra %s (gerado por 00_gera_params.py [v4]; nao edite a mao)" % r["ita"])
        linhas.append("; Laboratorio: ruptura = %s | confianca = %s | em analise = %s | ajuste do plano = %s"
                      % (r["modo"], r["conf"], r["em_analise"], r["ajuste"]))
        linhas.append("; Plano de foliacao: %s | %s" % (c_txt, f_txt))
        if sjfric is not None:
            linhas.append("; Atrito residual do plano: p_sjfric = tan(phi) = %.4f (LEQUE; antes 0.48 para todas)" % sjfric)
        if kn_txt:
            linhas.append("; Rigidez dos contatos: " + kn_txt)
        if r["modo"] == "matrix":
            linhas.append("; Ruptura na matriz: rode com usa_foliacao = 0 no Main (e comente o call do 02).")
        linhas.append("fish define params_amostra")
        linhas.append("    pressao_conf   = %.1f" % (-r["s3"] * 1.0e6))
        linhas.append("    foliacao_dip   = %.2f" % r["dip"])
        linhas.append("    p_sjcoh        = %.1f" % (c * 1.0e6))
        linhas.append("    p_sjfa         = %.2f" % phi)
        if sjfric is not None:
            linhas.append("    p_sjfric       = %.4f" % sjfric)
        if kn is not None:
            linhas.append("    p_fjkn         = %.4e" % kn)
            linhas.append("    p_fjks         = %.4e" % (kn * KS_SOBRE_KN))
        linhas.append("    eps_ax_max     = %.1f" % eps_max)
        linhas.append("    lab_dev_pico   = %.3f" % r["D"])
        linhas.append("    lab_eps_pico   = %.4f" % r["eps_pk"])
        linhas.append("    lab_E_GPa      = %.2f" % r["E"])
        linhas.append("    lab_nu         = %.3f" % r["nu"])
        linhas.append("end")
        linhas.append("[params_amostra]")
        txt = "\r\n".join(linhas) + "\r\n"
        assert all(ord(ch) < 128 for ch in txt)
        with open(os.path.join(a.saida, "%s_params.dat" % r["ita"]), "w", newline="") as f:
            f.write(txt)
        resumo.append(dict(id_ita=r["ita"], sigma3_MPa=r["s3"], foliacao_dip=r["dip"], c_MPa=c, phi_deg=phi,
                           plano=origem, eps_ax_max=eps_max, lab_dev_pico=r["D"], lab_E_GPa=r["E"],
                           modo_lab=r["modo"], confianca=r["conf"], em_analise=r["em_analise"],
                           ajuste_plano=r["ajuste"],
                           kn_fator=round(kn_fator, 3), kn_Pa_m=(kn if kn is not None else a.kn_ref), kn_origem=kn_origem,
                           a_leque=(round(a_lq, 4) if a_lq is not None else ""),
                           sjfric=(round(sjfric, 4) if sjfric is not None else "global")))

    res = pd.DataFrame(resumo)
    res.to_csv(os.path.join(a.saida, "params_resumo.csv"), index=False)
    print(res.to_string(index=False))
    print("\nGerados %d arquivos em %s" % (len(res), os.path.abspath(a.saida)))


if __name__ == "__main__":
    sys.exit(main())
