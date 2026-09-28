#!/usr/bin/env python3
"""
Estudio paramétrico para la versión en LAZO ABIERTO del comando Nubelink H1-B
(corriente ∝ PWM del joystick, sin sensor). Busca la combinación pistón / resorte propio /
fricción que dé la mejor proporcionalidad con una fuerza manual aceptable, para dos
distribuidores extremos (resorte débil 35 N + 1 N/mm y fuerte 60 N + 8 N/mm).

Métricas por combinación (rampa 0 -> 100 % -> 0 en 8 s):
  hist  : histéresis, % de la carrera total (40 mm)
  I_ini : corriente (A) a la que empieza a moverse            (zona muerta a compensar en el driver)
  I_fin : corriente (A) a la que llega al tope de 20 mm       (debe quedar <= ~0,85 A para tener margen)
  banda : I_fin - I_ini (A)                                   (resolución: cuanto mayor, mejor)
  F_man : fuerza extra en la horquilla en modo manual, fin de carrera, 0,1 m/s (N)

    python3 estudio_lazo_abierto.py      (~2 min)
"""
import itertools
import math
import os

import numpy as np

from servopiston_model import BAR, default_params, hysteresis_width, manual_mode_force, simulate

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

PISTONES = {"Ø20/Ø10": (20, 10), "Ø25/Ø12": (25, 12), "Ø32/Ø16": (32, 16)}
RESORTES = {"2,5 N/mm": (50.0, 2500.0), "4 N/mm": (50.0, 4000.0), "6 N/mm": (40.0, 6000.0)}
FRICCION = {"PTFE 20 N": 20.0, "PU 40 N": 40.0}
DISTRIB = {"débil (35 N + 1 N/mm)": (35.0, 1000.0), "fuerte (60 N + 8 N/mm)": (60.0, 8000.0)}


def duty(t):
    return min(t / 4.0, (8.0 - t) / 4.0) if t < 8.0 else 0.0


def evaluar(p):
    cmd = lambda t: (p["I0"] + duty(t) * (p["I_max"] - p["I0"]), 0.0)
    r = simulate(p, 8.0, cmd=cmd)
    D = np.array([duty(tt) for tt in r.t])
    hist = hysteresis_width(D, r.x, 1.0)
    n = len(D) // 2
    Iu = p["I0"] + D[:n] * (p["I_max"] - p["I0"])
    xu = r.x[:n]
    i_ini = float(Iu[np.argmax(xu > 0.5e-3)]) if np.any(xu > 0.5e-3) else float("nan")
    i_fin = float(Iu[np.argmax(xu > 19.5e-3)]) if np.any(xu > 19.5e-3) else float("nan")
    return hist, i_ini, i_fin


def main():
    base = default_params()
    filas = []
    for (pn, (D, d)), (rn, (F0m, cm)), (fn, Fc) in itertools.product(PISTONES.items(), RESORTES.items(), FRICCION.items()):
        A = math.pi / 4 * ((D * 1e-3) ** 2 - (d * 1e-3) ** 2)
        # fricción escala aprox. con el perímetro de sellado
        Fc_eff = Fc * (D + 2 * d) / (32 + 2 * 16)
        res = {}
        for dn, (F0, c) in DISTRIB.items():
            p = dict(base, A=A, F0=F0, c=c, F0_mod=F0m, c_mod=cm, Fc=Fc_eff)
            res[dn] = evaluar(p)
        fman = manual_mode_force(dict(base, A=A, F0_mod=F0m, c_mod=cm, Fc=Fc_eff), 0.1)["F_total"]
        filas.append((pn, rn, fn, Fc_eff, res, fman))
        h_d, ii_d, if_d = res["débil (35 N + 1 N/mm)"]
        h_f, ii_f, if_f = res["fuerte (60 N + 8 N/mm)"]
        print(f"{pn:8s} {rn:9s} {fn:10s} | débil: hist {h_d:4.0f}% I {ii_d:.2f}->{if_d:.2f} A | "
              f"fuerte: hist {h_f:4.0f}% I {ii_f:.2f}->{if_f:.2f} A | F_man {fman:.0f} N", flush=True)

    md = ["# Estudio paramétrico: comando H1-B en lazo abierto", "",
          "Rampa de PWM 0 → 100 % → 0 en 8 s; corriente = I0 + PWM·(I_max − I0); válvula 0–20 bar; pilotaje 25 bar; "
          "fricción escalada con el perímetro de sellado (referencia Ø32/Ø16).", "",
          "| Pistón | Resorte propio | Sellos | Fricción (N) | Distribuidor débil: hist. / I_ini → I_fin | Distribuidor fuerte: hist. / I_ini → I_fin | F extra manual a tope (N) |",
          "|---|---|---|---|---|---|---|"]
    for pn, rn, fn, Fc_eff, res, fman in filas:
        h_d, ii_d, if_d = res["débil (35 N + 1 N/mm)"]
        h_f, ii_f, if_f = res["fuerte (60 N + 8 N/mm)"]
        md.append(f"| {pn} | {rn} | {fn} | {Fc_eff:.0f} | {h_d:.0f} % / {ii_d:.2f} → {if_d:.2f} A | "
                  f"{h_f:.0f} % / {ii_f:.2f} → {if_f:.2f} A | {fman:.0f} |")
    with open(os.path.join(OUT, "estudio_lazo_abierto.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    print("escrito", os.path.join(OUT, "estudio_lazo_abierto.md"))


if __name__ == "__main__":
    main()
