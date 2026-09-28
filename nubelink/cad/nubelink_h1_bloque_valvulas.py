#!/usr/bin/env python3
"""
Bloque de válvulas Nubelink H1: manifold de aluminio con 2 cavidades para cartuchos
reductores-relevadores proporcionales de 3 vías (HYDAC PDR08-01, cavidad FC08-3 /
"SAE-08 3 vías") que alimentan las cámaras A y B de UN servopistón.

Este es el bloque que sí conviene fabricar en la CNC 6090 (aluminio 6082-T6 / 7075-T6):
galerías P y T pasantes por ambas cavidades, salidas A y B en la cara frontal, todo con
puertos G1/4 y SIN tapones (las galerías entran por las caras extremas como puertos).

ATENCIÓN - CAVIDAD: la geometría de la cavidad que se modela aquí es un MARCADOR DE
POSICIÓN con proporciones típicas de una cavidad SAE-08 de 3 vías (rosca 3/4-16 UNF,
dos anillos de sellado y nariz). Antes de mecanizar hay que sustituirla por el plano
oficial FC08-3 de HYDAC (o el de la cavidad del cartucho elegido) y mecanizarla con la
herramienta de forma correspondiente; las tolerancias de los diámetros de sellado son
del orden de ±0,02 mm.

Para el H1 de banco también es válido comprar dos cuerpos en línea HYDAC FH083-AB3
(aluminio, G3/8, 210 bar, ref. 3011427) y unir con mangueras; este bloque es la versión
integrada que después se replica por sección en el H2 modular.

Salidas en ./out: nubelink_h1_bloque_valvulas.step/.stl, _iso.svg, _corte.svg
"""
import os
import sys

try:
    import cadquery as cq
except ImportError:  # pragma: no cover
    sys.exit("Falta CadQuery: pip install cadquery")

# --------------------------------------------------------------------------
# PARÁMETROS (mm)
# --------------------------------------------------------------------------
B = dict(
    L=100.0, W=60.0, H=45.0,       # largo (X), ancho (Y), alto (Z)
    x_cav=25.0,                    # cavidades en x = ±x_cav, y = 0, desde la cara superior
    # Galerías (eje X)
    D_galeria=8.0,
    y_P=-4.0, z_P=15.0,            # galería P (anillo medio de la cavidad = puerto 2)
    y_T=4.0, z_T=25.0,             # galería T (anillo superior de la cavidad = puerto 3)
    # Salidas A/B desde la nariz de la cavidad (puerto 1) hacia la cara frontal (y = -W/2)
    D_salida=7.0, z_salida=10.0,
    # Puertos roscados G1/4 (taladro 11,5, prof. 12) en caras extremas y frontal
    D_rosca_G14=11.5, prof_rosca_G14=12.0,
    # Fijación
    D_fijacion=9.0, x_fij=40.0, y_fij=22.0,
)

# Marcador de posición de cavidad SAE-08 3 vías (profundidades desde la cara superior).
# SUSTITUIR por el plano oficial FC08-3 antes de mecanizar.
CAV = dict(
    d_entrada=19.5, prof_entrada=1.5,     # chaflán / entrada de rosca 3/4-16 UNF
    d_rosca=17.5, prof_rosca=17.0,        # diámetro de taladro previo a la rosca
    d_anillo3=15.0, prof_anillo3=22.0,    # zona de sellado / anillo puerto 3 (T)
    d_anillo2=14.5, prof_anillo2=32.0,    # anillo puerto 2 (P)
    d_nariz=12.7, prof_nariz=36.0,        # nariz, puerto 1 (salida regulada)
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def cavidad(x):
    """Cavidad escalonada desde la cara superior (z = H) en (x, 0)."""
    H = B["H"]
    c = None
    escalones = [
        (CAV["d_entrada"], CAV["prof_entrada"]),
        (CAV["d_rosca"], CAV["prof_rosca"]),
        (CAV["d_anillo3"], CAV["prof_anillo3"]),
        (CAV["d_anillo2"], CAV["prof_anillo2"]),
        (CAV["d_nariz"], CAV["prof_nariz"]),
    ]
    for d, prof in escalones:
        s = cq.Workplane("XY").workplane(offset=H + 1).center(x, 0).circle(d / 2.0).extrude(-(prof + 1))
        c = s if c is None else c.union(s)
    return c


def bloque():
    L, W, H = B["L"], B["W"], B["H"]
    b = cq.Workplane("XY").box(L, W, H).translate((0, 0, H / 2.0))
    # cavidades
    for s in (-1, 1):
        b = b.cut(cavidad(s * B["x_cav"]))
    # galería P: entra por la cara -X como puerto G1/4 y termina pasada la 2.ª cavidad (ciega)
    fin_P = B["x_cav"] + CAV["d_anillo2"] / 2.0 + 2.0
    gP = cq.Workplane("YZ").workplane(offset=-L / 2.0 - 1).center(B["y_P"], B["z_P"]) \
        .circle(B["D_galeria"] / 2.0).extrude(L / 2.0 + 1 + fin_P)
    rP = cq.Workplane("YZ").workplane(offset=-L / 2.0 - 1).center(B["y_P"], B["z_P"]) \
        .circle(B["D_rosca_G14"] / 2.0).extrude(B["prof_rosca_G14"] + 1)
    b = b.cut(gP).cut(rP)
    # galería T: entra por la cara +X como puerto G1/4 y termina pasada la 1.ª cavidad (ciega)
    gT = cq.Workplane("YZ").workplane(offset=L / 2.0 + 1).center(B["y_T"], B["z_T"]) \
        .circle(B["D_galeria"] / 2.0).extrude(-(L / 2.0 + 1 + fin_P))
    rT = cq.Workplane("YZ").workplane(offset=L / 2.0 + 1).center(B["y_T"], B["z_T"]) \
        .circle(B["D_rosca_G14"] / 2.0).extrude(-(B["prof_rosca_G14"] + 1))
    b = b.cut(gT).cut(rT)
    # salidas A (x = -x_cav) y B (x = +x_cav): de la nariz a la cara frontal y = -W/2
    for s in (-1, 1):
        x = s * B["x_cav"]
        sal = cq.Workplane("XZ").workplane(offset=W / 2.0 + 1).center(x, B["z_salida"]) \
            .circle(B["D_salida"] / 2.0).extrude(-(W / 2.0 + 1))
        ros = cq.Workplane("XZ").workplane(offset=W / 2.0 + 1).center(x, B["z_salida"]) \
            .circle(B["D_rosca_G14"] / 2.0).extrude(-(B["prof_rosca_G14"] + 1))
        b = b.cut(sal).cut(ros)
    # fijación: 4 x Ø9 pasantes
    for sx in (-1, 1):
        for sy in (-1, 1):
            f = cq.Workplane("XY").workplane(offset=-1).center(sx * B["x_fij"], sy * B["y_fij"]) \
                .circle(B["D_fijacion"] / 2.0).extrude(H + 2)
            b = b.cut(f)
    return b


def exportar():
    os.makedirs(OUT, exist_ok=True)
    b = bloque()
    cq.exporters.export(b, os.path.join(OUT, "nubelink_h1_bloque_valvulas.step"))
    cq.exporters.export(b, os.path.join(OUT, "nubelink_h1_bloque_valvulas.stl"), tolerance=0.02, angularTolerance=0.1)
    opt = dict(width=900, height=520, marginLeft=20, marginTop=20, showAxes=False,
               strokeWidth=0.6, strokeColor=(20, 20, 20), hiddenColor=(170, 170, 170), showHidden=True,
               projectionDir=(0.6, -0.7, 0.45))
    cq.exporters.export(b, os.path.join(OUT, "nubelink_h1_bloque_valvulas_iso.svg"), opt=opt)
    # corte por el plano de las cavidades (y = 0): se elimina y > 0
    caja = cq.Workplane("XY").box(400, 200, 200).translate((0, 100, 0))
    corte = b.cut(caja)
    opt2 = {**opt, "showHidden": False, "projectionDir": (0.0, 1.0, 0.0)}
    comp = corte.val().rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), -90)
    cq.exporters.export(cq.Workplane("XY").add(comp), os.path.join(OUT, "nubelink_h1_bloque_valvulas_corte.svg"), opt=opt2)
    vol = b.val().Volume()
    print(f"Bloque {B['L']:g} x {B['W']:g} x {B['H']:g} mm, volumen {vol/1000:.0f} cm³ -> aluminio {vol*2.75e-6:.2f} kg")
    print(f"Archivos escritos en {OUT}")


if __name__ == "__main__":
    exportar()
