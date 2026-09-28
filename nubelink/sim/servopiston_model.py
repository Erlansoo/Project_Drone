#!/usr/bin/env python3
"""
Modelo dinámico de parámetros concentrados del módulo Nubelink H1:

    joystick -> controlador de corriente (PWM + dither) -> 2 válvulas reductoras-relevadoras
    proporcionales (V_A, V_B) -> cámaras A y B (compresibilidad) -> pistón de doble vástago
    -> resorte de centrado del carrete del distribuidor (+ resorte de centrado propio opcional)
    + fricción + topes.

Es el mismo sistema físico que después se construye en Simscape Fluids (bloques
"Pressure-Reducing 3-Way Valve (IL)", "Double-Acting Actuator (IL)", "Translational
Spring / Friction / Hard Stop", "Solenoid"), pero en ~200 líneas y sin licencias, para
fijar órdenes de magnitud antes de fabricar. Ver servopiston_model.m para el gemelo
en MATLAB.

Unidades SI. Todos los parámetros están en `default_params()`; los que NO están
respaldados por una ficha técnica se marcan "SUPUESTO" y son lo primero que hay
que medir en el banco (sección 10 del documento principal).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

BAR = 1e5
LPM = 1.0 / 60000.0   # m³/s por L/min


def default_params() -> dict:
    return dict(
        # --- pistón (cad/nubelink_h1.py) ---
        A=math.pi / 4 * (0.032**2 - 0.016**2),  # 603e-6 m², camisa Ø32 / vástago Ø16
        x_max=0.020,                            # carrera ±20 mm (tope mecánico)
        m=0.8,                                  # kg, masa móvil equivalente (SUPUESTO: pistón+vástago+horquilla+palanca)
        # --- carga: resorte de centrado del carrete referido a la horquilla ---
        F0=60.0,                                # N, precarga del resorte (SUPUESTO; medir)
        c=8000.0,                               # N/m, rigidez (SUPUESTO; 8 N/mm -> 220 N a 20 mm; medir)
        # --- resorte de centrado PROPIO del módulo (paquete tipo carrete en el extremo trasero); 0 = sin resorte ---
        F0_mod=0.0,                             # N, precarga
        c_mod=0.0,                              # N/m, rigidez
        # --- fricción (pistón PTFE + sellos de vástago + carrete) ---
        Fc=45.0,                                # N, Coulomb (SUPUESTO; objetivo de ensayo T2 < 40 N)
        b=300.0,                                # N·s/m, viscosa
        v0=0.002,                               # m/s, velocidad de transición de Stribeck
        # --- topes mecánicos ---
        k_stop=5e6, d_stop=5e3,
        # --- hidráulica de pilotaje ---
        p_s=25 * BAR,                           # presión de pilotaje disponible (bloque de alimentación)
        V0=60e-6,                               # m³, volumen muerto por cámara + manguera 1/4" x 1 m (SUPUESTO)
        beta=8e8,                               # Pa, módulo efectivo aceite + manguera + algo de aire (SUPUESTO)
        # --- válvula HYDAC PDR08-01 código 30 (0-20 bar, 12 L/min) ---
        p_range=20 * BAR,                       # presión regulada a corriente máxima
        I_max=1.0,                              # A, corriente de fondo de escala (SUPUESTO: confirmar bobina 24PG)
        I0=0.12,                                # A, corriente de arranque / zona muerta (SUPUESTO típico 10-15 %)
        tau_v=0.015,                            # s, retardo dinámico del carrete de la válvula (SUPUESTO típico 10-25 ms)
        Q_max=12 * LPM,                         # caudal nominal
        G_v=(12 * LPM) / (2 * BAR),             # conductancia: 12 L/min con 2 bar de desequilibrio (SUPUESTO)
        h_bl=0.04,                              # A pico a pico, histéresis mecánica de la válvula ~4 % de I_max (SUPUESTO)
        # --- electrónica ---
        tau_i=0.003,                            # s, lazo de corriente cerrado (PWM 200 Hz + sensado)
        dither_on=True, f_d=150.0, I_d_frac=0.05,   # dither 150 Hz, 5 % de I_max
        # --- lazo de posición ---
        Kp=15.0,                                # A/m  (0,015 A/mm)
        Ki=250.0,                               # A/(m·s)
    )


@dataclass
class Result:
    t: np.ndarray
    x: np.ndarray
    v: np.ndarray
    pA: np.ndarray
    pB: np.ndarray
    IA: np.ndarray
    IB: np.ndarray
    IA_cmd: np.ndarray
    IB_cmd: np.ndarray
    x_ref: np.ndarray
    notes: dict = field(default_factory=dict)


def spring_force(x, F0, c):
    """Resorte de centrado con precarga: F = (F0 + c|x|)·sign(x); suavizado cerca de 0."""
    return (F0 * math.tanh(x / 0.0002) + c * x)


def friction_force(v, Fc, b, v0):
    return Fc * math.tanh(v / v0) + b * v


def backlash(I, I_eff, h):
    """Histéresis mecánica de la válvula como holgura de ancho h sobre la corriente."""
    if I > I_eff + h / 2:
        return I - h / 2
    if I < I_eff - h / 2:
        return I + h / 2
    return I_eff


def simulate(p: dict, T: float, cmd=None, x_ref=None, dt: float = 1e-5, decim: int = 100,
             supply_cut_t: float | None = None, ctrl_off_t: float | None = None) -> Result:
    """
    Integra el modelo con Euler semi-implícito de paso fijo.

    cmd(t)       -> (IA_cmd, IB_cmd) en A, lazo abierto (se ignora si x_ref se da)
    x_ref(t)     -> consigna de posición en m (lazo cerrado PI sobre las corrientes)
    supply_cut_t -> instante en que desaparece la presión de pilotaje (dump abierta / bomba parada)
    ctrl_off_t   -> instante en que la electrónica deja de energizar las bobinas (paro, pérdida de enlace)
    """
    n = int(round(T / dt))
    n_out = n // decim + 1
    out = {k: np.zeros(n_out) for k in ("t", "x", "v", "pA", "pB", "IA", "IB", "IA_cmd", "IB_cmd", "x_ref")}

    A, m = p["A"], p["m"]
    x = v = 0.0
    pA = pB = 0.0
    IA = IB = 0.0                 # corriente real en bobina
    IA_eff = IB_eff = 0.0         # corriente "vista" por el carrete tras la holgura
    pA_ref = pB_ref = 0.0         # presión de consigna filtrada por la dinámica de la válvula
    integ = 0.0                   # integrador del PI
    K_v = p["p_range"] / (p["I_max"] - p["I0"])
    I_d = p["I_d_frac"] * p["I_max"] if p["dither_on"] else 0.0
    k = 0
    for i in range(n + 1):
        t = i * dt
        # ---------- consignas ----------
        xr = 0.0
        if x_ref is not None:
            xr = x_ref(t)
            e = xr - x
            integ += e * dt
            u = p["Kp"] * e + p["Ki"] * integ
            lim = p["I_max"] - p["I0"]
            if abs(u) > lim:              # anti-windup por recorte
                integ -= e * dt
                u = max(-lim, min(lim, u))
            IA_c = p["I0"] + u if u > 0 else 0.0
            IB_c = p["I0"] - u if u < 0 else 0.0
        else:
            IA_c, IB_c = cmd(t) if cmd else (0.0, 0.0)
        if ctrl_off_t is not None and t >= ctrl_off_t:
            IA_c = IB_c = 0.0
        dth = I_d * math.sin(2 * math.pi * p["f_d"] * t)
        IA_c_d = max(0.0, IA_c + dth) if IA_c > 0 else 0.0
        IB_c_d = max(0.0, IB_c + dth) if IB_c > 0 else 0.0
        # ---------- lazo de corriente ----------
        IA += (IA_c_d - IA) / p["tau_i"] * dt
        IB += (IB_c_d - IB) / p["tau_i"] * dt
        IA_eff = backlash(IA, IA_eff, p["h_bl"])
        IB_eff = backlash(IB, IB_eff, p["h_bl"])
        # ---------- válvulas: presión de consigna y dinámica del carrete ----------
        p_s = p["p_s"] if (supply_cut_t is None or t < supply_cut_t) else 0.0
        pA_set = min(max(K_v * (IA_eff - p["I0"]), 0.0), p["p_range"], p_s)
        pB_set = min(max(K_v * (IB_eff - p["I0"]), 0.0), p["p_range"], p_s)
        pA_ref += (pA_set - pA_ref) / p["tau_v"] * dt
        pB_ref += (pB_set - pB_ref) / p["tau_v"] * dt
        # caudal reductor-relevador: entrega si p_cámara < consigna, alivia a T si es mayor
        QA = max(-p["Q_max"], min(p["Q_max"], p["G_v"] * (pA_ref - pA)))
        QB = max(-p["Q_max"], min(p["Q_max"], p["G_v"] * (pB_ref - pB)))
        # ---------- cámaras ----------
        VA = p["V0"] + A * x
        VB = p["V0"] - A * x
        pA += p["beta"] / VA * (QA - A * v) * dt
        pB += p["beta"] / VB * (QB + A * v) * dt
        pA = max(pA, -0.5 * BAR)   # cavitación limitada
        pB = max(pB, -0.5 * BAR)
        # ---------- mecánica ----------
        F = (A * (pA - pB) - spring_force(x, p["F0"], p["c"]) - spring_force(x, p["F0_mod"], p["c_mod"])
             - friction_force(v, p["Fc"], p["b"], p["v0"]))
        if x > p["x_max"]:
            F -= p["k_stop"] * (x - p["x_max"]) + p["d_stop"] * v
        elif x < -p["x_max"]:
            F -= p["k_stop"] * (x + p["x_max"]) + p["d_stop"] * v
        v += F / m * dt
        x += v * dt
        # ---------- registro ----------
        if i % decim == 0:
            out["t"][k] = t; out["x"][k] = x; out["v"][k] = v
            out["pA"][k] = pA; out["pB"][k] = pB
            out["IA"][k] = IA; out["IB"][k] = IB
            out["IA_cmd"][k] = IA_c; out["IB_cmd"][k] = IB_c; out["x_ref"][k] = xr
            k += 1
    for key in out:
        out[key] = out[key][:k]
    return Result(**out)


# ---------------------------------------------------------------- utilidades de análisis

def rise_time(t, x, t0, x_final, frac=0.9):
    """Tiempo desde t0 hasta alcanzar frac·x_final."""
    idx = np.where((t >= t0) & (np.abs(x) >= frac * abs(x_final)))[0]
    return float(t[idx[0]] - t0) if len(idx) else float("nan")


def settle_time(t, x, t0, tol=1e-3):
    """Tiempo desde t0 hasta que |x| queda por debajo de tol (m) de forma permanente."""
    mask = t >= t0
    tt, xx = t[mask], np.abs(x[mask])
    outside = np.where(xx >= tol)[0]
    if len(outside) == 0:
        return 0.0
    if outside[-1] == len(xx) - 1:
        return float("nan")            # nunca se queda dentro de la tolerancia
    return float(tt[outside[-1] + 1] - t0)


def hysteresis_width(I, x, I_max):
    """Ancho máximo de la curva x(I) subiendo vs. bajando, en % de la carrera total."""
    n = len(I) // 2
    Iu, xu = I[:n], x[:n]
    Id, xd = I[n:][::-1], x[n:][::-1]
    grid = np.linspace(0.1 * I_max, 0.9 * I_max, 200)
    xu_i = np.interp(grid, Iu, xu)
    xd_i = np.interp(grid, Id, xd)
    return float(np.max(np.abs(xd_i - xu_i)) / (2 * 0.020) * 100.0)


def manual_mode_force(p: dict, v_manual: float = 0.1) -> dict:
    """Fuerza extra en la horquilla al mover la palanca a mano con las válvulas sin energía."""
    Q = p["A"] * v_manual
    dp = Q / p["G_v"]                       # el aceite sale por la vía A->T de la válvula
    F_hyd = dp * p["A"]
    F_spring = p["F0_mod"] + p["c_mod"] * p["x_max"]
    return dict(v=v_manual, Q_lpm=Q / LPM, dp_bar=dp / BAR, F_hyd=F_hyd, F_fric=p["Fc"],
                F_resorte_modulo_tope=F_spring, F_total=F_hyd + p["Fc"] + F_spring)
