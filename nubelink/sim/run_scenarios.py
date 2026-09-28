#!/usr/bin/env python3
"""
Corre los escenarios de diseño del módulo Nubelink H1 con el modelo de
servopiston_model.py y escribe figuras PNG + resumen Markdown en ./out.

    python3 run_scenarios.py          (~20 s)

Escenarios:
  S1  escalones de corriente en lazo abierto (0,3 / 0,6 / 1,0 A)      -> demuestra que el lazo abierto satura
  S2  rampa triangular lenta con y sin dither                          -> histéresis x(I) en lazo abierto
  S3  falla segura: corte de corriente y de presión a carrera máxima   -> tiempo de retorno a neutro por resorte
  S3b secuencia segura: retorno ACTIVO a neutro en lazo cerrado y luego dump  -> lo que hace el MOD10
  S4  lazo cerrado de posición PI con sensor                           -> seguimiento y error
  S5  sensibilidad: fricción 45 vs 120 N, pilotaje 25 vs 15 bar        -> x(I) en lazo abierto
  S6  distribuidor de resorte débil (35 N + 1 N/mm) con y sin resorte propio -> ¿vuelve a neutro sin energía?
"""
import json
import os
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from servopiston_model import (BAR, default_params, hysteresis_width, manual_mode_force, rise_time,
                               settle_time, simulate)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

# Paleta de referencia (modo claro): series en orden fijo, tinta neutra, rejilla recesiva
C = dict(s1="#2a78d6", s2="#eb6834", s3="#1baf7a", ink="#0b0b0b", ink2="#52514e", muted="#898781",
         grid="#e1e0d9", axis="#c3c2b7", surface="#fcfcfb")
plt.rcParams.update({
    "figure.facecolor": C["surface"], "axes.facecolor": C["surface"], "savefig.facecolor": C["surface"],
    "axes.edgecolor": C["axis"], "axes.labelcolor": C["ink2"], "xtick.color": C["muted"], "ytick.color": C["muted"],
    "text.color": C["ink"], "grid.color": C["grid"], "grid.linewidth": 0.6, "axes.grid": True,
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.6,
    "font.family": "sans-serif", "font.size": 10, "legend.frameon": False, "figure.dpi": 130,
})


def fig_ax(rows=1, h=3.0, title=""):
    fig, axs = plt.subplots(rows, 1, figsize=(9, h * rows), sharex=(rows > 1))
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, fontweight="bold", color=C["ink"])
    return fig, (axs if rows > 1 else [axs])


def fmt_ms(s):
    return "no vuelve" if (s is None or s != s) else f"{s*1e3:.0f} ms"


def main():
    p = default_params()
    res = {}
    t0 = time.time()
    x_at = lambda r, tt: float(r.x[np.searchsorted(r.t, tt)] * 1e3)

    # ---------------- S1: escalones de corriente en lazo abierto ----------------
    def cmd1(t):
        IA = 0.3 if 0.2 <= t < 0.9 else 0.6 if 0.9 <= t < 1.6 else 1.0 if 1.6 <= t < 2.3 else 0.0
        return IA, 0.0
    r1 = simulate(p, 2.6, cmd=cmd1)
    res["S1"] = dict(
        x_mm_0p3A=x_at(r1, 0.88), x_mm_0p6A=x_at(r1, 1.58), x_mm_1p0A=x_at(r1, 2.28),
        t90_0p3A_s=rise_time(r1.t, r1.x, 0.2, x_at(r1, 0.88) / 1e3),
        t_return_s=rise_time(r1.t, (x_at(r1, 2.28) / 1e3 - r1.x), 2.3, x_at(r1, 2.28) / 1e3),
    )
    fig, axs = fig_ax(3, 2.2, "S1 · Escalones de corriente en V_A (lazo abierto, sin sensor)")
    axs[0].plot(r1.t, r1.IA_cmd, color=C["ink2"], ls="--", lw=1.2, label="consigna")
    axs[0].plot(r1.t, r1.IA, color=C["s1"], label="corriente en bobina (con dither)")
    axs[0].set_ylabel("I_A [A]"); axs[0].legend(loc="upper left")
    axs[1].plot(r1.t, r1.pA / BAR, color=C["s1"], label="cámara A")
    axs[1].plot(r1.t, r1.pB / BAR, color=C["s2"], label="cámara B")
    axs[1].set_ylabel("presión [bar]"); axs[1].legend(loc="upper left")
    axs[2].plot(r1.t, r1.x * 1e3, color=C["s1"])
    axs[2].set_ylabel("posición horquilla [mm]"); axs[2].set_xlabel("t [s]")
    for tt, key in ((0.88, "x_mm_0p3A"), (1.58, "x_mm_0p6A"), (2.28, "x_mm_1p0A")):
        axs[2].annotate(f"{res['S1'][key]:.1f} mm", (tt, res["S1"][key]), textcoords="offset points",
                        xytext=(-4, 6), ha="right", fontsize=9, color=C["ink2"])
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "S1_escalones.png")); plt.close(fig)
    print(f"S1 listo ({time.time()-t0:.0f} s)")

    # ---------------- S2: histéresis con y sin dither ----------------
    def cmd2(t):
        return (p["I_max"] * min(t / 3.0, (6.0 - t) / 3.0) if t < 6.0 else 0.0), 0.0
    fig, axs = fig_ax(1, 4.2, "S2 · Histéresis posición–corriente en lazo abierto (rampa 0 → 1 A → 0 en 6 s)")
    res["S2"] = {}
    for dith, col, lab in ((False, C["s2"], "sin dither"), (True, C["s1"], "con dither 150 Hz, 5 %")):
        p2 = dict(p, dither_on=dith)
        r2 = simulate(p2, 6.0, cmd=cmd2)
        w = hysteresis_width(r2.IA_cmd, r2.x, p["I_max"])
        res["S2"][lab] = dict(histeresis_pct_carrera=w)
        axs[0].plot(r2.IA_cmd, r2.x * 1e3, color=col, label=f"{lab}: histéresis {w:.0f} % de la carrera")
    axs[0].set_xlabel("consigna de corriente I_A [A]"); axs[0].set_ylabel("posición [mm]"); axs[0].legend(loc="lower right")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "S2_histeresis.png")); plt.close(fig)
    print(f"S2 listo ({time.time()-t0:.0f} s)")

    # ---------------- S3: falla segura pasiva (corte de todo a carrera máxima) ----------------
    def cmd3(t):
        return (p["I_max"] if t < 1.0 else 0.0), 0.0
    r3 = simulate(p, 2.0, cmd=cmd3, supply_cut_t=1.0)
    r3b = simulate(dict(p, Fc=120.0), 2.0, cmd=cmd3, supply_cut_t=1.0)
    res["S3"] = dict(t_retorno_1mm_s=settle_time(r3.t, r3.x, 1.0), x_final_mm=float(r3.x[-1] * 1e3),
                     t_retorno_1mm_s_friccion120N=settle_time(r3b.t, r3b.x, 1.0), x_final_mm_friccion120N=float(r3b.x[-1] * 1e3))
    # ---------------- S3b: secuencia segura activa: consigna 0 en lazo cerrado, luego dump ----------------
    def xref3(t):
        return 0.020 if t < 1.0 else 0.0
    r3c = simulate(dict(p, Fc=120.0), 2.0, x_ref=xref3, supply_cut_t=1.5, ctrl_off_t=1.5)
    res["S3b"] = dict(t_retorno_activo_1mm_s=settle_time(r3c.t, r3c.x, 1.0), x_final_mm=float(r3c.x[-1] * 1e3))
    fig, axs = fig_ax(2, 2.6, "S3 · Falla segura en t = 1 s: corte total vs. retorno activo + dump (t = 1,5 s)")
    axs[0].plot(r3.t, r3.pA / BAR, color=C["s1"], label="cámara A, corte total"); axs[0].plot(r3.t, r3.pB / BAR, color=C["s2"], label="cámara B, corte total")
    axs[0].set_ylabel("presión [bar]"); axs[0].legend(loc="upper right")
    axs[1].plot(r3.t, r3.x * 1e3, color=C["s1"], label=f"corte total, fricción 45 N → {fmt_ms(res['S3']['t_retorno_1mm_s'])}")
    axs[1].plot(r3b.t, r3b.x * 1e3, color=C["s2"], label=f"corte total, fricción 120 N → {fmt_ms(res['S3']['t_retorno_1mm_s_friccion120N'])}, queda en {res['S3']['x_final_mm_friccion120N']:.1f} mm")
    axs[1].plot(r3c.t, r3c.x * 1e3, color=C["s3"], label=f"retorno activo + dump, fricción 120 N → {fmt_ms(res['S3b']['t_retorno_activo_1mm_s'])}")
    axs[1].axvline(1.0, color=C["muted"], lw=0.8, ls=":"); axs[1].axvline(1.5, color=C["muted"], lw=0.8, ls=":")
    axs[1].set_ylabel("posición [mm]"); axs[1].set_xlabel("t [s]"); axs[1].legend(loc="upper right")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "S3_falla_segura.png")); plt.close(fig)
    print(f"S3 listo ({time.time()-t0:.0f} s)")

    # ---------------- S4: lazo cerrado de posición ----------------
    def xref(t):
        return 1e-3 * (5.0 if 0.2 <= t < 1.2 else 15.0 if 1.2 <= t < 2.2 else -10.0 if 2.2 <= t < 3.2 else 0.0)
    r4 = simulate(p, 3.4, x_ref=xref)
    err = [abs(x_at(r4, tt) - target) for tt, target in ((1.15, 5.0), (2.15, 15.0), (3.15, -10.0))]
    res["S4"] = dict(error_estacionario_mm_max=float(max(err)), t90_10mm_s=rise_time(r4.t, r4.x - 5e-3, 1.2, 10e-3))
    fig, axs = fig_ax(2, 2.6, "S4 · Lazo cerrado de posición (PI + sensor en el vástago)")
    axs[0].plot(r4.t, r4.x_ref * 1e3, color=C["ink2"], ls="--", lw=1.2, label="consigna")
    axs[0].plot(r4.t, r4.x * 1e3, color=C["s1"], label="posición medida")
    axs[0].set_ylabel("posición [mm]"); axs[0].legend(loc="upper left")
    axs[1].plot(r4.t, r4.IA_cmd, color=C["s1"], label="I_A"); axs[1].plot(r4.t, r4.IB_cmd, color=C["s2"], label="I_B")
    axs[1].set_ylabel("corriente [A]"); axs[1].set_xlabel("t [s]"); axs[1].legend(loc="upper left")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "S4_lazo_cerrado.png")); plt.close(fig)
    print(f"S4 listo ({time.time()-t0:.0f} s)")

    # ---------------- S5: sensibilidad (rampa lenta 0 -> I_max, lazo abierto) ----------------
    def cmd5(t):
        return p["I_max"] * min(t / 3.0, 1.0), 0.0
    casos = [("base: fricción 45 N, pilotaje 25 bar", dict(), C["s1"]),
             ("fricción 120 N (carrete sucio)", dict(Fc=120.0), C["s2"]),
             ("pilotaje 15 bar (standby PVG 32)", dict(p_s=15 * BAR), C["s3"])]
    fig, axs = fig_ax(1, 4.2, "S5 · Sensibilidad de la curva posición–corriente (lazo abierto)")
    res["S5"] = {}
    for lab, over, col in casos:
        r5 = simulate(dict(p, **over), 3.2, cmd=cmd5)
        I_start = float(r5.IA_cmd[np.argmax(r5.x > 0.5e-3)])
        I_full = float(r5.IA_cmd[np.argmax(r5.x > 19.5e-3)]) if np.any(r5.x > 19.5e-3) else float("nan")
        res["S5"][lab] = dict(I_arranque_A=I_start, I_tope_A=I_full, x_max_mm=float(r5.x[-1] * 1e3))
        axs[0].plot(r5.IA_cmd, r5.x * 1e3, color=col, label=f"{lab} · arranca {I_start:.2f} A, tope a {I_full:.2f} A")
    axs[0].set_xlabel("consigna de corriente I_A [A]"); axs[0].set_ylabel("posición [mm]"); axs[0].legend(loc="lower right")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "S5_sensibilidad.png")); plt.close(fig)
    print(f"S5 listo ({time.time()-t0:.0f} s)")

    # ---------------- S6: distribuidor de resorte débil, con y sin resorte propio ----------------
    debil = dict(F0=35.0, c=1000.0, Fc=35.0)      # p. ej. PVG 32 visto desde la horquilla (relación de palanca ~3)
    casos6 = [("sin resorte propio", dict(), C["s2"]),
              ("con paquete de centrado propio 60 N + 2 N/mm", dict(F0_mod=60.0, c_mod=2000.0), C["s1"])]
    fig, axs = fig_ax(1, 3.4, "S6 · Corte total con distribuidor de resorte débil (35 N + 1 N/mm, fricción 35 N)")
    res["S6"] = {}
    for lab, over, col in casos6:
        r6 = simulate(dict(p, **debil, **over), 2.0, cmd=cmd3, supply_cut_t=1.0)
        ts = settle_time(r6.t, r6.x, 1.0)
        res["S6"][lab] = dict(t_retorno_1mm_s=ts, x_final_mm=float(r6.x[-1] * 1e3))
        axs[0].plot(r6.t, r6.x * 1e3, color=col, label=f"{lab} → {fmt_ms(ts)}, queda en {r6.x[-1]*1e3:.1f} mm")
    axs[0].axvline(1.0, color=C["muted"], lw=0.8, ls=":")
    axs[0].set_ylabel("posición [mm]"); axs[0].set_xlabel("t [s]"); axs[0].legend(loc="upper right")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "S6_resorte_debil.png")); plt.close(fig)
    print(f"S6 listo ({time.time()-t0:.0f} s)")

    res["modo_manual"] = manual_mode_force(p, 0.1)
    res["modo_manual_con_resorte"] = manual_mode_force(dict(p, F0_mod=60.0, c_mod=2000.0), 0.1)
    res["parametros"] = {k: (v if isinstance(v, (int, float, bool)) else str(v)) for k, v in p.items()}
    with open(os.path.join(OUT, "resultados.json"), "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    S1, S2, S3, S3b, S4, S5, S6 = res["S1"], res["S2"], res["S3"], res["S3b"], res["S4"], res["S5"], res["S6"]
    mm, mmr = res["modo_manual"], res["modo_manual_con_resorte"]
    md = f"""# Resultados de simulación Nubelink H1 (modelo de parámetros concentrados)

Parámetros: pistón Ø32/Ø16 (603 mm²), carrera ±20 mm, válvula 0–20 bar / 12 L/min, pilotaje 25 bar,
resorte del carrete 60 N + 8 N/mm (SUPUESTO), fricción 45 N (SUPUESTO), I_max 1,0 A, zona muerta 0,12 A.

| Escenario | Resultado |
|---|---|
| S1 lazo abierto: posición a 0,3 / 0,6 / 1,0 A | {S1['x_mm_0p3A']:.1f} / {S1['x_mm_0p6A']:.1f} / {S1['x_mm_1p0A']:.1f} mm (tope 20 mm): **satura desde 0,3 A** |
| S1 tiempo al 90 % del primer escalón | {S1['t90_0p3A_s']*1e3:.0f} ms |
| S1 retorno a neutro al soltar (90 %) | {S1['t_return_s']*1e3:.0f} ms |
| S2 histéresis en lazo abierto, sin / con dither | {S2['sin dither']['histeresis_pct_carrera']:.0f} % / {S2['con dither 150 Hz, 5 %']['histeresis_pct_carrera']:.0f} % de la carrera (domina fricción/rigidez, no la válvula) |
| S3 corte total, fricción 45 N | vuelve a |x| < 1 mm en {fmt_ms(S3['t_retorno_1mm_s'])}, posición final {S3['x_final_mm']:.2f} mm |
| S3 corte total, fricción 120 N (carrete sucio) | {fmt_ms(S3['t_retorno_1mm_s_friccion120N'])}, **queda en {S3['x_final_mm_friccion120N']:.1f} mm** |
| S3b retorno activo (lazo cerrado a 0) y dump a los 0,5 s, fricción 120 N | vuelve en {fmt_ms(S3b['t_retorno_activo_1mm_s'])}, posición final {S3b['x_final_mm']:.2f} mm |
| S4 lazo cerrado: error estacionario máx. / t90 del escalón de 10 mm | {S4['error_estacionario_mm_max']:.2f} mm / {S4['t90_10mm_s']*1e3:.0f} ms |
| S5 lazo abierto, corriente de arranque → tope, base | {S5[casos[0][0]]['I_arranque_A']:.2f} → {S5[casos[0][0]]['I_tope_A']:.2f} A |
| S5 con fricción 120 N | {S5[casos[1][0]]['I_arranque_A']:.2f} → {S5[casos[1][0]]['I_tope_A']:.2f} A |
| S5 con pilotaje 15 bar | {S5[casos[2][0]]['I_arranque_A']:.2f} → {S5[casos[2][0]]['I_tope_A']:.2f} A |
| S6 resorte débil (35 N + 1 N/mm), corte total, sin resorte propio | {fmt_ms(S6[casos6[0][0]]['t_retorno_1mm_s'])}, queda en {S6[casos6[0][0]]['x_final_mm']:.1f} mm |
| S6 ídem con paquete de centrado propio 60 N + 2 N/mm | {fmt_ms(S6[casos6[1][0]]['t_retorno_1mm_s'])}, queda en {S6[casos6[1][0]]['x_final_mm']:.1f} mm |
| Modo manual a 0,1 m/s, sin resorte propio | {mm['Q_lpm']:.1f} L/min, Δp {mm['dp_bar']:.2f} bar → {mm['F_hyd']:.0f} N hidr. + {mm['F_fric']:.0f} N fricción = **{mm['F_total']:.0f} N** extra en la horquilla |
| Modo manual a 0,1 m/s, con resorte propio 60 N + 2 N/mm | {mmr['F_hyd']:.0f} + {mmr['F_fric']:.0f} + {mmr['F_resorte_modulo_tope']:.0f} N (resorte a tope) = **{mmr['F_total']:.0f} N** extra en la horquilla |

## Conclusiones de diseño

1. **El lazo abierto (presión ∝ corriente, sin sensor) no sirve** con un pistón de 1 200 N sobre un resorte de carrete de
   decenas de N: toda la carrera cabe en 0,1–0,2 A de corriente y la histéresis es del orden de la mitad de la carrera. No es
   un problema de la válvula ni del dither: es fricción / rigidez del resorte. Por eso el MOD10 lleva realimentación mecánica.
2. **Con sensor de posición y lazo PI el módulo posiciona a ≈ ±0,5 mm en menos de 100 ms**, usando el empuje sobrante para vencer la
   fricción. El sensor no es "fase 2": es parte del diseño.
3. **Retorno a neutro**: con el resorte del distribuidor y fricción baja vuelve solo (~0,3 s); con carrete sucio (120 N) o
   distribuidor de resorte débil (PVG 32 visto desde la horquilla) **se queda fuera de neutro**. Dos medidas, ambas:
   (a) secuencia "retorno activo a neutro en lazo cerrado → dump" (0,5 s), como el dump retardado del MOD10;
   (b) paquete de resorte de centrado propio en el módulo (≈ 60 N + 2 N/mm) para el caso sin energía.
4. **Modo manual**: el resorte propio cuesta ~100 N más en la horquilla a fin de carrera (≈ 30–35 N en la empuñadura con
   relación de palanca 3). Si un cliente lo rechaza, la alternativa es el perno de desacople rápido en la horquilla.
5. La presión de pilotaje (15 vs 25 bar) casi no cambia nada; la fricción sí. **Prioridad del banco: medir y minimizar fricción**
   (sellos PTFE en pistón y vástago).

Figuras: S1_escalones.png · S2_histeresis.png · S3_falla_segura.png · S4_lazo_cerrado.png · S5_sensibilidad.png · S6_resorte_debil.png
"""
    with open(os.path.join(OUT, "resultados.md"), "w") as f:
        f.write(md)
    print(md)
    print(f"Total {time.time()-t0:.0f} s. Archivos en {OUT}")


if __name__ == "__main__":
    main()
