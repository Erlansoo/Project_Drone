#!/usr/bin/env python3
"""
Dimensionado preliminar del servopistón Nubelink H1.

Calcula, para varias combinaciones de camisa/vástago, la fuerza disponible a
distintas presiones de pilotaje, el volumen desplazado por carrera, el caudal
de pilotaje necesario, la potencia disipada por el bloque de contrapresión y
una verificación básica de resistencia del cuerpo.

Uso:
    python3 dimensionado_h1.py            # imprime tablas Markdown
    python3 dimensionado_h1.py --fuerza 250 --friccion 40

Sólo depende de la biblioteca estándar.
"""
import argparse
import math

BAR = 1e5  # Pa


def area_anular_mm2(d_camisa: float, d_vastago: float) -> float:
    """Área útil (mm²) de un pistón de doble vástago pasante."""
    return math.pi / 4.0 * (d_camisa**2 - d_vastago**2)


def fuerza_N(area_mm2: float, p_bar: float) -> float:
    return area_mm2 * 1e-6 * p_bar * BAR


def volumen_cm3(area_mm2: float, carrera_mm: float) -> float:
    return area_mm2 * carrera_mm / 1000.0


def caudal_lmin(volumen_cm3: float, t_s: float) -> float:
    return volumen_cm3 / 1000.0 / t_s * 60.0


def tabla_pistones(opciones, presiones, carrera_medio=20.0, t_llenado=0.3):
    print("### Fuerza y caudal por opción de pistón (vástago pasante) — referencia Scanreco MOD10: 1 300 N a 30 bar\n")
    cab = "| Camisa Ø / vástago Ø | Área útil (mm²) |"
    cab += "".join(f" F @ {p:g} bar (N) |" for p in presiones)
    cab += f" p para 1300 N (bar) | Vol. neutro→tope {carrera_medio:g} mm (cm³) | Caudal para {t_llenado:g} s (L/min) |"
    print(cab)
    print("|" + "---|" * (cab.count("|") - 1))
    for D, d in opciones:
        A = area_anular_mm2(D, d)
        V = volumen_cm3(A, carrera_medio)
        Q = caudal_lmin(V, t_llenado)
        fila = f"| Ø{D:g} / Ø{d:g} | {A:.0f} |"
        fila += "".join(f" {fuerza_N(A, p):.0f} |" for p in presiones)
        fila += f" {1300.0 / (A * 1e-6) / BAR:.1f} | {V:.1f} | {Q:.2f} |"
        print(fila)
    print()


def tabla_presion_requerida(opciones, f_resorte, friccion, margen=1.3):
    print(
        f"### Presión de pilotaje necesaria para F_resorte = {f_resorte:g} N "
        f"+ fricción {friccion:g} N (margen ×{margen:g})\n"
    )
    print("| Camisa Ø / vástago Ø | Área (mm²) | p mínima (bar) | p con margen (bar) | Uso del rango 0–20 bar | Uso del rango 0–35 bar |")
    print("|---|---|---|---|---|---|")
    F = f_resorte + friccion
    for D, d in opciones:
        A = area_anular_mm2(D, d)
        p_min = F / (A * 1e-6) / BAR
        p_m = p_min * margen
        print(
            f"| Ø{D:g} / Ø{d:g} | {A:.0f} | {p_min:.1f} | {p_m:.1f} | "
            f"{min(p_m / 20 * 100, 999):.0f} % | {min(p_m / 35 * 100, 999):.0f} % |"
        )
    print()


def tabla_calor(p_contra_bar, caudales_lmin):
    print("### Potencia disipada por el bloque de contrapresión (modo remoto activo, distribuidor en neutro)\n")
    print("| Caudal bomba (L/min) |" + "".join(f" {p:g} bar (kW) |" for p in p_contra_bar))
    print("|---|" + "---|" * len(p_contra_bar))
    for Q in caudales_lmin:
        fila = f"| {Q:g} |"
        for p in p_contra_bar:
            kw = p * BAR * (Q / 1000.0 / 60.0) / 1000.0
            fila += f" {kw:.1f} |"
        print(fila)
    print()


def verificacion_cuerpo(D_ext, D_bore, p_list, sigma_adm_MPa):
    print(f"### Verificación básica del cuerpo torneado Ø{D_ext:g} ext. / Ø{D_bore:g} interior\n")
    t = (D_ext - D_bore) / 2.0
    r = D_bore / 2.0
    print(f"Espesor de pared: {t:.1f} mm. Tensión circunferencial aprox. σ = p·r/t (pared delgada, conservador).\n")
    print("| Presión (bar) | σ hoop (MPa) | Fuerza axial sobre tapa (kN) |" + "".join(f" FS vs {n} |" for n in sigma_adm_MPa))
    print("|---|---|---|" + "---|" * len(sigma_adm_MPa))
    for p in p_list:
        sig = p * BAR * r / t / 1e6
        F_tapa = p * BAR * (math.pi / 4 * (D_bore * 1e-3) ** 2) / 1000.0
        fila = f"| {p:g} | {sig:.1f} | {F_tapa:.1f} |"
        for n, s_adm in sigma_adm_MPa.items():
            fila += f" {s_adm / sig:.0f} |"
        print(fila)
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fuerza", type=float, default=200.0, help="Fuerza del resorte del distribuidor a fin de carrera, en el punto de acople (N)")
    ap.add_argument("--friccion", type=float, default=40.0, help="Fricción estimada de sellos del servopistón (N)")
    args = ap.parse_args()

    opciones = [(20, 10), (25, 12), (28, 14), (32, 16)]
    presiones = [10, 20, 30]

    print("# Dimensionado preliminar Nubelink H1\n")
    tabla_pistones(opciones, presiones)
    tabla_presion_requerida(opciones, args.fuerza, args.friccion)
    tabla_calor([20, 25, 30], [30, 45, 60, 80])
    verificacion_cuerpo(
        70, 32, [30, 40, 100, 350],
        {"C45 (σy≈350 MPa)": 350, "6061-T6 (σy≈275 MPa)": 275, "7075-T6 (σy≈500 MPa)": 500},
    )
    print("Nota: la presión de 350 bar sólo se indica como caso de falla (reductora averiada). "
          "La válvula de seguridad del bloque debe impedir superar ~40 bar; los sellos y roscas de tapa "
          "se dimensionan para 40 bar de ensayo, no para 350 bar.")


if __name__ == "__main__":
    main()
