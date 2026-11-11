"""
01_fit_plano_foliacao.py   [v4]

Confere os <amostra>_params.dat gerados por 00_gera_params.py e desenha os DOIS graficos do plano de foliacao:
  1) phi FIXO   : a reta unica de minimos quadrados (c e phi comuns);
  2) LEQUE      : as duas retas extremas (a = 0 embaixo, a = 1 em cima), pelas amostras ancora.
O metodo do leque (passos 0 a 6, formulas e limites) esta explicado no cabecalho do 00_gera_params.py.
As ancoras e as funcoes do leque vem de la, para as duas contas nunca divergirem.

Uso (Windows, terminal na pasta 00_Inputs):
    python 01_fit_plano_foliacao.py
ou apontando a pasta:
    python 01_fit_plano_foliacao.py "C:\\caminho\\para\\00_Inputs"

Dependencias: numpy, pandas, scipy, matplotlib

Saidas (pasta fit_plano/ dentro da pasta de entrada):
    fit_plano.png            os dois graficos
    fit_plano_pontos.csv     por amostra: sn, tau, a do leque, c e phi do leque, c e phi do .dat
    fit_plano_resumo.txt     a mesma informacao em texto, com a reta de phi fixo, o IC 95 % e as duas retas do leque
"""
import importlib.util
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from scipy import stats

# ----------------------------------------------------------------------------
# CONFIGURACAO (mude aqui, nao no meio do codigo)
# ----------------------------------------------------------------------------
# Quem entra no ajuste de phi fixo: o cabecalho de cada .dat diz "ajuste do plano = yes" (use_plane_fit do targets.csv).
# Se o .dat nao tiver essa palavra (arquivo antigo), vale a regra abaixo.
RUPTURA_OK = ("foliation",)
CONFIANCA_OK = ("high", "medium")
FORCAR_INCLUIR = []              # ex.: ["ITA42"]
FORCAR_EXCLUIR = []              # ex.: ["ITA47"]

CAMPOS = ["pressao_conf", "foliacao_dip", "p_sjcoh", "p_sjfa", "p_sjfric", "lab_dev_pico"]
LOG = []

# Funcoes e ancoras do leque: as mesmas do 00_gera_params.py (mesma pasta)
_spec = importlib.util.spec_from_file_location("gera_params", Path(__file__).resolve().parent / "00_gera_params.py")
gp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gp)


def log(txt=""):
    print(txt)
    LOG.append(txt)


# ----------------------------------------------------------------------------
# 1) LEITURA DOS .dat
# ----------------------------------------------------------------------------
def le_params(arq):
    txt = arq.read_text(errors="ignore")
    d = {"id": re.search(r"ITA\d+", arq.name).group(0)}
    m = re.search(r"Laboratorio:\s*ruptura\s*=\s*(\S+)\s*\|\s*confianca\s*=\s*(\S+)"
                  r"\s*\|\s*em analise\s*=\s*(\S+)", txt)
    d["ruptura"], d["confianca"], d["em_analise"] = m.groups() if m else ("?", "?", "?")
    m = re.search(r"ajuste do plano\s*=\s*(\S+)", txt)
    d["ajuste"] = m.group(1) if m else None
    for k in CAMPOS:
        m = re.search(r"^\s*" + k + r"\s*=\s*(.+?)\s*$", txt, re.M)
        d[k] = m.group(1).strip().strip("'") if m else None
    return d


def carrega(pasta):
    arqs = sorted(pasta.glob("*_params.dat"))
    if not arqs:
        sys.exit("Nenhum *_params.dat em " + str(pasta))
    linhas = []
    for a in arqs:
        d = le_params(a)
        try:
            d["s3"] = -float(d["pressao_conf"]) / 1e6          # MPa, positivo
            d["theta"] = float(d["foliacao_dip"])               # graus (anisotropy_angle_deg do banco)
            d["D"] = float(d["lab_dev_pico"])                   # MPa
            d["c_dat"] = float(d["p_sjcoh"]) / 1e6              # MPa, o que o PFC vai usar
            d["phi_dat"] = float(d["p_sjfa"])                   # graus, o que o PFC vai usar
            d["sjfric_dat"] = float(d["p_sjfric"]) if d["p_sjfric"] else np.nan   # so nos .dat com leque
        except (TypeError, ValueError):
            log("AVISO: " + a.name + " sem dados completos (arquivo antigo? rode 00_gera_params.py); ignorado.")
            continue
        linhas.append(d)
    df = pd.DataFrame(linhas).set_index("id")
    df = df[(df.theta > 0) & (df.D > 0)].copy()
    ok = np.where(df.ajuste.notna(), df.ajuste == "yes",
                  df.ruptura.isin(RUPTURA_OK) & df.confianca.isin(CONFIANCA_OK))
    ok = pd.Series(ok, index=df.index)
    ok = ok | df.index.isin(FORCAR_INCLUIR)
    ok = ok & ~df.index.isin(FORCAR_EXCLUIR)
    df["usado"] = ok
    th = np.radians(df.theta)
    df["sn"] = df.s3 + df.D * np.cos(th) ** 2
    df["tau"] = df.D * np.sin(th) * np.cos(th)
    return df


# ----------------------------------------------------------------------------
# 2) phi FIXO: reta de minimos quadrados + IC 95 %
# ----------------------------------------------------------------------------
def ajusta(sn, tau):
    n = len(sn)
    r = stats.linregress(sn, tau)
    t = stats.t.ppf(0.975, n - 2)
    return dict(n=n, c=r.intercept, tanphi=r.slope, phi=np.degrees(np.arctan(r.slope)), r2=r.rvalue ** 2,
                ci_c=(r.intercept - t * r.intercept_stderr, r.intercept + t * r.intercept_stderr),
                ci_phi=(np.degrees(np.arctan(r.slope - t * r.stderr)),
                        np.degrees(np.arctan(r.slope + t * r.stderr))))


# ----------------------------------------------------------------------------
# 3) RODA E IMPRIME
# ----------------------------------------------------------------------------
def main():
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    saida = pasta / "fit_plano"
    saida.mkdir(exist_ok=True)
    df = carrega(pasta)
    u = df[df.usado]
    if len(u) < 4:
        sys.exit("Poucos corpos no ajuste: " + str(len(u)))
    faltam = [k for k in gp.ANC_CIMA + gp.ANC_BAIXO if k not in df.index]
    if faltam:
        sys.exit("Amostra(s) ancora sem .dat: " + ", ".join(faltam))

    f = ajusta(u.sn.values, u.tau.values)
    pt = lambda k: (float(df.loc[k, "sn"]), float(df.loc[k, "tau"]))
    L = gp.monta_leque([pt(k) for k in gp.ANC_CIMA], [pt(k) for k in gp.ANC_BAIXO])

    # posicao de cada amostra no leque
    df["a"] = [gp.posicao_a(L, r.sn, r.tau) for r in df.itertuples()]
    df["dentro"] = (df.a >= -gp.TOL_A) & (df.a <= 1 + gp.TOL_A)
    df["c_leque"] = [gp.reta_do_leque(L, a)[0] for a in df.a]
    df["phi_leque"] = [gp.reta_do_leque(L, a)[2] for a in df.a]
    df["sjfric_leque"] = [gp.reta_do_leque(L, a)[1] for a in df.a]

    log("=" * 74)
    log("PLANO DE FOLIACAO [v4]  -  pasta: " + str(pasta))
    log("=" * 74)
    log("")
    log("1) phi FIXO (minimos quadrados, n = %d: %s)" % (f["n"], ", ".join(u.index)))
    log("   tau = c + sn tan(phi):  c = %.2f MPa (IC95%% %.1f a %.1f),  phi = %.2f graus (IC95%% %.1f a %.1f),  R2 = %.2f" % (
        f["c"], f["ci_c"][0], f["ci_c"][1], f["phi"], f["ci_phi"][0], f["ci_phi"][1], f["r2"]))
    log("")
    log("2) LEQUE (ancoras: cima = %s, baixo = %s)" % (" + ".join(gp.ANC_CIMA), " + ".join(gp.ANC_BAIXO)))
    log("   a = 1 (cima):  c = %.2f MPa  phi = %.2f graus  (tan = %.4f)" % (L["cu"], L["phi_cima"], L["mu"]))
    log("   a = 0 (baixo): c = %.2f MPa  phi = %.2f graus  (tan = %.4f)" % (L["cl"], L["phi_baixo"], L["ml"]))
    log("   pivo (onde as retas se cruzam): sn = %.1f MPa (tracao, fora dos dados)" % L["pivo"])
    log("")
    log("   EQUACOES (tau e sn em MPa):")
    log("     ponto de cada ensaio:   sn = s3 + D cos^2(theta)      tau = D sen(theta) cos(theta)")
    log("                             (theta = mergulho do plano, D = desviador de pico do lab, s3 = confinamento)")
    log("     reta a = 0 (baixo):     tau = %.2f + %.4f sn" % (L["cl"], L["ml"]))
    log("     reta a = 1 (cima):      tau = %.2f + %.4f sn" % (L["cu"], L["mu"]))
    log("     reta de qualquer a:     tau = c(a) + tan(phi(a)) sn")
    log("                             c(a)        = %.2f + %.2f a   [MPa]" % (L["cl"], L["dc"]))
    log("                             tan(phi(a)) = %.4f + %.4f a" % (L["ml"], L["dm"]))
    log("     a do ensaio (reta que passa no ponto dele; vem de impor tau = c(a) + tan(phi(a)) sn e isolar a):")
    log("                             a = (tau - %.2f - %.4f sn) / (%.2f + %.4f sn)" % (L["cl"], L["ml"], L["dc"], L["dm"]))
    log("     atrito residual no PFC: p_sjfric = tan(phi(a))")
    log("   phi fixo (referencia):    tau = %.2f + %.4f sn" % (f["c"], f["tanphi"]))
    log("")
    log("%-6s %5s %7s %8s %8s %8s %8s %8s %9s  %s" % ("corpo", "s3", "theta", "sn", "tau", "a", "c", "phi", "p_sjfric", "obs"))
    for i, r in df.sort_values("a").iterrows():
        obs = ("no ajuste" if r.usado else "") + ("" if r.dentro else "  FORA do leque")
        log("%-6s %5.0f %7.2f %8.2f %8.2f %8.3f %8.2f %8.2f %9.4f  %s" % (
            i, r.s3, r.theta, r.sn, r.tau, r.a, r.c_leque, r.phi_leque, r.sjfric_leque, obs))
    log("")
    log("Conferencia com os .dat (todas as amostras que trazem p_sjfric, isto e, que receberam o leque):")
    erros = df
    tem_leque = erros.sjfric_dat.notna()
    if tem_leque.any():
        dif = ((erros.c_dat - erros.c_leque).abs() > 0.02) | ((erros.phi_dat - erros.phi_leque).abs() > 0.02)
        dif = dif & tem_leque
        if dif.any():
            log("  AVISO: o c e o phi do .dat diferem do leque em: " + ", ".join(erros.index[dif]) + " (rode 00_gera_params.py de novo).")
        else:
            log("  OK: c, phi e p_sjfric dos .dat batem com o leque.")
    else:
        log("  Estes .dat NAO trazem p_sjfric (nao sao do leque): rode 00_gera_params.py (padrao v4).")

    df.to_csv(saida / "fit_plano_pontos.csv", sep=";", decimal=",", encoding="utf-8-sig")
    (saida / "fit_plano_resumo.txt").write_text("\n".join(LOG), encoding="utf-8")
    desenha(df, u, f, L, saida / "fit_plano.png")
    log("")
    log("Arquivos em: " + str(saida))
    plt.show()


# ----------------------------------------------------------------------------
# 4) FIGURA: dois graficos simples
# ----------------------------------------------------------------------------
# deslocamento do nome de cada ponto (pontos): (dx, dy, alinhamento); o padrao e abaixo e a direita
# ajuste dos rotulos no grafico: {"ITA901": (dx, dy, "left"|"right")}, em pontos (aqui: o conjunto sintetico)
OFFS = {"ITA902": (6, -13, "left"), "ITA904": (-6, 6, "right"), "ITA908": (6, 3, "left"), "ITA910": (-6, -12, "right")}
# idem, so para o grafico do leque (o nome leva o a e fica mais largo)
OFFS_LEQUE = {}


def pontos(ax, df, u, ancoras_vazias, com_a=False):
    laranja, cinza, tinta = "#D9731A", "#5B6770", "#16232B"
    for i, r in u.iterrows():
        ax.scatter(r.sn, r.tau, s=70, color=laranja, edgecolor="white", linewidth=1.2, zorder=5)
        dx, dy, ha = (OFFS_LEQUE if com_a else OFFS).get(i, OFFS.get(i, (6, -12, "left")))
        nome = (i + (" (a = %.2f)" % df.loc[i, "a"]).replace(".", ",")) if com_a else i
        ax.annotate(nome, (r.sn, r.tau), xytext=(dx, dy), textcoords="offset points", fontsize=9, color=tinta, ha=ha,
                    path_effects=[pe.withStroke(linewidth=3, foreground="white")], zorder=6)
    for i in ancoras_vazias:
        r = df.loc[i]
        ax.scatter(r.sn, r.tau, s=70, facecolor="white", edgecolor=laranja, linewidth=1.5, zorder=5)
        ax.annotate(i + " (\u00e2ncora)", (r.sn, r.tau), xytext=(0, 10), textcoords="offset points",
                    fontsize=9, color=cinza, ha="center")


def vg(x, n=2):
    """numero com virgula decimal"""
    return (("%." + str(n) + "f") % x).replace(".", ",")


def desenha(df, u, f, L, arq_png):
    azul, laranja, tinta = "#2A6FBB", "#D9731A", "#16232B"
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 6.7), sharex=True, sharey=True)
    xs = np.linspace(0, 85, 200)
    sg, ta, ph = "\u03c3", "\u03c4", "\u03c6"

    # (1) phi fixo
    a1.plot(xs, f["c"] + f["tanphi"] * xs, color=azul, lw=2.4)
    pontos(a1, df, u, [])
    a1.set_title(("%s fixo: c = %.1f MPa, %s = %.1f\u00b0" % (ph, f["c"], ph, f["phi"])).replace(".", ","), loc="left", fontsize=12)
    a1.text(85, f["c"] + f["tanphi"] * 85 + 1.5, "%s = %s + %s %sn" % (ta, vg(f["c"]), vg(f["tanphi"], 4), sg),
            color=azul, fontsize=10, ha="right")

    # (2) leque
    cima, baixo = L["cu"] + L["mu"] * xs, L["cl"] + L["ml"] * xs
    a2.fill_between(xs, baixo, cima, color=azul, alpha=0.10, lw=0)
    a2.plot(xs, cima, color=azul, lw=2.4)
    a2.plot(xs, baixo, color=azul, lw=2.4)
    a2.text(85, cima[-1] + 1.5, "a = 1:  %s = %s + %s %sn" % (ta, vg(L["cu"]), vg(L["mu"], 4), sg),
            color=azul, fontsize=10, ha="right", fontweight="bold")
    a2.text(85, baixo[-1] - 14.0, "a = 0:  %s = %s + %s %sn" % (ta, vg(L["cl"]), vg(L["ml"], 4), sg),
            color=azul, fontsize=10, ha="right", fontweight="bold")
    pontos(a2, df, u, [k for k in gp.ANC_BAIXO + gp.ANC_CIMA if k not in u.index], com_a=True)
    a2.set_title("Leque: reta de baixo (a = 0) e de cima (a = 1)", loc="left", fontsize=12)

    for ax in (a1, a2):
        ax.set_xlim(0, 86)
        ax.set_ylim(0, 62)
        ax.set_xlabel("Tens\u00e3o normal no plano, %sn [MPa]" % sg)
        ax.spines[["top", "right"]].set_visible(False)
    a1.set_ylabel("Tens\u00e3o cisalhante no plano, %s [MPa]" % ta)

    eq = ["Cada ponto:  %sn = %s3 + D cos\u00b2\u03b8     %s = D sen\u03b8 cos\u03b8      (\u03b8 = mergulho do plano, D = desviador de pico do laborat\u00f3rio)" % (sg, sg, ta),
          "Leque:  c(a) = %s + %s a  [MPa]     tan%s(a) = %s + %s a     (a = 0 na reta de baixo, a = 1 na de cima)     p_sjfric = tan%s(a)"
          % (vg(L["cl"]), vg(L["dc"]), ph, vg(L["ml"], 4), vg(L["dm"], 4), ph),
          "a de cada ponto (reta do leque que passa nele):  a = (%s \u2212 %s \u2212 %s %sn) / (%s + %s %sn)"
          % (ta, vg(L["cl"]), vg(L["ml"], 4), sg, vg(L["dc"]), vg(L["dm"], 4), sg)]
    fig.tight_layout(rect=(0, 0.14, 1, 1))
    for k, t in enumerate(eq):
        fig.text(0.04, 0.095 - 0.032 * k, t, fontsize=10, color=tinta, ha="left", va="center")
    fig.savefig(arq_png, dpi=150)


if __name__ == "__main__":
    main()
