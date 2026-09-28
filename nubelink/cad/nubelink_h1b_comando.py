#!/usr/bin/env python3
"""
Nubelink H1-B "comando": bloque INTEGRADO de una función para prueba, en una sola pieza mecanizada.

En un solo bloque de aluminio (o acero) van:
  * la camisa del servopistón (Ø20 H8 pasante, vástago Ø10 pasante),
  * las dos cavidades FC08-3 para los cartuchos HYDAC PDR08-01 (V_A y V_B),
  * las galerías P y T (entran por las caras extremas y se tapan con tapones G1/8),
  * las salidas A y B de la nariz de cada cavidad a su cámara (sin mangueras),
  * los puertos P (cara frontal) y T (cara trasera) G1/4,
  * 4 x M6 por extremo para las tapas y 4 x M8 en la base para el soporte.
Tapas redondas atornilladas con O-ring de cara, sello de vástago y guardapolvo; paquete de resorte de
centrado en el extremo -X; horquilla en +X.

Diseñado para LAZO ABIERTO (corriente ∝ PWM): pistón pequeño (236 mm² -> 472 N a 20 bar) y resorte propio
rígido (40 N + 6 N/mm) según el estudio sim/estudio_lazo_abierto.py.

ATENCIÓN: la cavidad FC08-3 es un marcador de posición; mecanizar según el plano oficial HYDAC.
Los alojamientos de sellos se ajustan al catálogo del sello elegido.

Salidas en ./out: nubelink_h1b_comando_bloque.step/.stl (pieza a mecanizar), nubelink_h1b_comando_ensamble.step,
nubelink_h1b_comando_tapa/piston/vastago/horquilla/caja_resorte.step, vistas SVG iso / corte / frente.
"""
import math
import os
import sys

try:
    import cadquery as cq
except ImportError:  # pragma: no cover
    sys.exit("Falta CadQuery: pip install cadquery")

# --------------------------------------------------------------------------
# PARÁMETROS (mm)
# --------------------------------------------------------------------------
P = dict(
    # Bloque
    L=110.0, W=60.0, H=90.0,          # largo (X), ancho (Y), alto (Z)
    z_eje=30.0,                       # altura del eje de la camisa
    # Camisa / pistón / vástago
    D_camisa=20.0,                    # Ø20 H8 (escariar + bruñir)
    D_vastago=10.0,                   # Ø10 f7 cromado
    D_rosca_vastago=8.0,              # M8 en los extremos
    L_rosca_vastago=18.0,
    L_vastago=240.0,
    L_piston=14.0,
    ancho_ranura_piston=4.0,
    carrera_max=20.0,
    # Tapas (redondas, atornilladas)
    D_brida_tapa=50.0, esp_brida_tapa=10.0,
    L_espiga_tapa=6.0,                # guía dentro de la camisa
    D_oring_cara=34.0, ancho_oring_cara=2.6, prof_oring_cara=1.6,   # ranura para O-ring 30x2 (aprox.)
    PCD_tornillos=40.0, D_tornillo=5.0, D_rosca_M6=5.0, prof_M6=12.0,
    D_sello_vastago=18.0, L_sello_vastago=5.0,      # sello 10x18x5 (ajustar al catálogo)
    D_guardapolvo=16.0, L_guardapolvo=4.0,          # guardapolvo 10x16x4
    # Cavidades (marcador FC08-3) en la cara superior, x = ±x_cav
    x_cav=40.0,
    # Galerías (eje X) y puertos
    D_galeria=8.0,
    y_P=-5.0, z_P=62.0,               # galería P: anillo 2 de la cavidad
    y_T=5.0, z_T=70.0,                # galería T: anillo 3
    D_salida=6.0,                     # nariz -> cámara
    D_rosca_G14=11.5, prof_G14=12.0,  # puertos P y T
    D_rosca_G18=8.6, prof_G18=9.0,    # tapones de galería en las caras extremas
    # Base
    D_M8=6.8, prof_M8=14.0, x_M8=40.0, y_M8=20.0,
    # Horquilla
    L_horquilla=30.0, ancho_horquilla=16.0, alto_horquilla=20.0, ranura_horquilla=8.0, D_perno=8.0,
    # Paquete de resorte (extremo -X)
    D_caja=44.0, D_caja_int=36.0, L_caja=48.0, esp_pared_caja=4.0, D_abertura_caja=24.0,
    L_espaciador=8.0, D_espaciador_int=30.0, D_arandela=34.0, esp_arandela=3.0,
    D_resorte_ext=28.0, D_resorte_int=20.0, D_collar=18.0, L_collar=5.0, esp_tuerca=6.5,
)

CAV = dict(   # marcador de posición de cavidad SAE-08 3 vías (profundidades desde la cara superior)
    d_entrada=19.5, prof_entrada=1.5,
    d_rosca=17.5, prof_rosca=17.0,
    d_anillo3=15.0, prof_anillo3=22.0,
    d_anillo2=14.5, prof_anillo2=32.0,
    d_nariz=12.7, prof_nariz=36.0,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
ROT_LATERAL = 90


def cil_x(d, largo, x0, y=0.0, z=None):
    z = P["z_eje"] if z is None else z
    return cq.Workplane("YZ").workplane(offset=x0).center(y, z).circle(d / 2.0).extrude(largo)


def cavidad(x):
    H = P["H"]
    c = None
    for d, prof in ((CAV["d_entrada"], CAV["prof_entrada"]), (CAV["d_rosca"], CAV["prof_rosca"]),
                    (CAV["d_anillo3"], CAV["prof_anillo3"]), (CAV["d_anillo2"], CAV["prof_anillo2"]),
                    (CAV["d_nariz"], CAV["prof_nariz"])):
        s = cq.Workplane("XY").workplane(offset=H + 1).center(x, 0).circle(d / 2.0).extrude(-(prof + 1))
        c = s if c is None else c.union(s)
    return c


def x_salida():
    """Posición axial de las salidas A/B: dentro de la cámara y nunca tapadas por el pistón."""
    cam_int = P["L"] / 2.0 - P["L_espiga_tapa"]
    cara_piston_max = P["L_piston"] / 2.0 + P["carrera_max"]
    x = P["x_cav"]
    assert cara_piston_max + P["D_salida"] / 2 <= x <= cam_int - P["D_salida"] / 2, "salida A/B tapada o fuera de cámara"
    return x


def bloque():
    L, W, H, ze = P["L"], P["W"], P["H"], P["z_eje"]
    b = cq.Workplane("XY").box(L, W, H).translate((0, 0, H / 2.0))
    # camisa pasante
    b = b.cut(cil_x(P["D_camisa"], L + 2, -L / 2.0 - 1))
    # 4 x M6 por cara extrema (PCD 40, patrón a 45°)
    r = P["PCD_tornillos"] / 2.0
    for s in (-1, 1):
        for k in range(4):
            a = math.radians(45 + 90 * k)
            y, z = r * math.cos(a), ze + r * math.sin(a)
            x0 = s * L / 2.0 - (P["prof_M6"] if s > 0 else 0)
            b = b.cut(cil_x(P["D_rosca_M6"], P["prof_M6"] + 1, x0 - (1 if s < 0 else 0), y, z))
    # cavidades
    for s in (-1, 1):
        b = b.cut(cavidad(s * P["x_cav"]))
    # galería P: entra por la cara -X (tapón G1/8), ciega pasada la 2.ª cavidad
    fin = P["x_cav"] + CAV["d_anillo2"] / 2.0 + 2.0
    b = b.cut(cil_x(P["D_galeria"], L / 2.0 + 1 + fin, -L / 2.0 - 1, P["y_P"], P["z_P"]))
    b = b.cut(cil_x(P["D_rosca_G18"], P["prof_G18"] + 1, -L / 2.0 - 1, P["y_P"], P["z_P"]))
    # galería T: entra por la cara +X (tapón G1/8), ciega pasada la 1.ª cavidad
    b = b.cut(cil_x(P["D_galeria"], L / 2.0 + 1 + fin, L / 2.0 + 1, P["y_T"], P["z_T"]).translate((-(L / 2.0 + 1 + fin), 0, 0)))
    b = b.cut(cil_x(P["D_rosca_G18"], P["prof_G18"] + 1, L / 2.0 - P["prof_G18"], P["y_T"], P["z_T"]))
    # puerto P en cara frontal (y = -W/2) hasta la galería P; puerto T en cara trasera (y = +W/2) hasta la galería T
    def puerto_y(x, z, desde, hasta):
        largo = abs(hasta - desde) + 1
        y0 = min(desde, hasta) - (1 if desde < hasta else 0)
        return cq.Workplane("XZ").workplane(offset=-y0).center(x, z).circle(P["D_salida"] / 2.0).extrude(-largo)
    b = b.cut(cq.Workplane("XZ").workplane(offset=W / 2.0 + 1).center(0, P["z_P"]).circle(P["D_salida"] / 2.0).extrude(-(W / 2.0 + 1 + P["y_P"])))
    b = b.cut(cq.Workplane("XZ").workplane(offset=W / 2.0 + 1).center(0, P["z_P"]).circle(P["D_rosca_G14"] / 2.0).extrude(-(P["prof_G14"] + 1)))
    b = b.cut(cq.Workplane("XZ").workplane(offset=-W / 2.0 - 1).center(0, P["z_T"]).circle(P["D_salida"] / 2.0).extrude(W / 2.0 + 1 - P["y_T"]))
    b = b.cut(cq.Workplane("XZ").workplane(offset=-W / 2.0 - 1).center(0, P["z_T"]).circle(P["D_rosca_G14"] / 2.0).extrude(P["prof_G14"] + 1))
    # salidas A/B: de la nariz de cada cavidad a la cámara (vertical)
    xs = x_salida()
    for s in (-1, 1):
        b = b.cut(cq.Workplane("XY").workplane(offset=H - CAV["prof_nariz"] + 1).center(s * xs, 0)
                  .circle(P["D_salida"] / 2.0).extrude(-(H - CAV["prof_nariz"] + 1 - ze)))
    # base: 4 x M8
    for sx in (-1, 1):
        for sy in (-1, 1):
            b = b.cut(cq.Workplane("XY").workplane(offset=-1).center(sx * P["x_M8"], sy * P["y_M8"])
                      .circle(P["D_M8"] / 2.0).extrude(P["prof_M8"] + 1))
    return b


def tapa():
    """Tapa redonda atornillada; espiga hacia -X (cara interior en x=0), brida hacia +X."""
    e, eb = P["L_espiga_tapa"], P["esp_brida_tapa"]
    t = cil_x(P["D_camisa"] - 0.1, e, 0, 0, 0).union(cil_x(P["D_brida_tapa"], eb, e, 0, 0))
    # ranura de O-ring de cara (en la cara de la brida que apoya en el bloque, x = e)
    ranura = cil_x(P["D_oring_cara"] + P["ancho_oring_cara"], P["prof_oring_cara"], e, 0, 0) \
        .cut(cil_x(P["D_oring_cara"] - P["ancho_oring_cara"], P["prof_oring_cara"], e, 0, 0))
    t = t.cut(ranura)
    # paso de vástago, sello y guardapolvo
    t = t.cut(cil_x(P["D_vastago"] + 0.1, e + eb + 2, -1, 0, 0))
    t = t.cut(cil_x(P["D_sello_vastago"], P["L_sello_vastago"], e + 1.0, 0, 0))
    t = t.cut(cil_x(P["D_guardapolvo"], P["L_guardapolvo"], e + eb - P["L_guardapolvo"], 0, 0))
    # 4 taladros de tornillo
    r = P["PCD_tornillos"] / 2.0
    for k in range(4):
        a = math.radians(45 + 90 * k)
        t = t.cut(cil_x(P["D_tornillo"] + 1.5, eb + 2, e - 1, r * math.cos(a), r * math.sin(a)))
    return t


def piston():
    p = cil_x(P["D_camisa"] - 0.1, P["L_piston"], -P["L_piston"] / 2.0)
    w = P["ancho_ranura_piston"]
    p = p.cut(cil_x(P["D_camisa"] + 2, w, -w / 2.0).cut(cil_x(P["D_camisa"] - 6.0, w, -w / 2.0)))
    return p.cut(cil_x(P["D_vastago"] + 0.05, P["L_piston"] + 2, -P["L_piston"] / 2.0 - 1))


def vastago():
    L = P["L_vastago"]
    v = cil_x(P["D_vastago"], L, -L / 2.0)
    for s in (-1, 1):
        x0 = s * L / 2.0 - (P["L_rosca_vastago"] if s > 0 else 0)
        v = v.cut(cil_x(P["D_vastago"] + 1, P["L_rosca_vastago"], x0).cut(cil_x(P["D_rosca_vastago"], P["L_rosca_vastago"], x0)))
    return v


def horquilla():
    Lh, a, h = P["L_horquilla"], P["ancho_horquilla"], P["alto_horquilla"]
    f = cq.Workplane("XY").box(Lh, a, h).translate((Lh / 2.0, 0, P["z_eje"]))
    f = f.cut(cq.Workplane("XY").box(Lh * 0.6 + 1, P["ranura_horquilla"], h + 2).translate((Lh - Lh * 0.3, 0, P["z_eje"])))
    f = f.cut(cq.Workplane("XZ").center(Lh - Lh * 0.3, P["z_eje"]).circle(P["D_perno"] / 2.0).extrude(a, both=True))
    return f.cut(cil_x(P["D_rosca_vastago"], Lh * 0.4 + 1, -1))


def paquete_resorte(x_c):
    Le, Lc, e = P["L_espaciador"], P["L_caja"], P["esp_pared_caja"]
    pz = {}
    pz["espaciador"] = cil_x(P["D_caja"], Le, x_c - Le).cut(cil_x(P["D_espaciador_int"], Le + 2, x_c - Le - 1))
    caja = cil_x(P["D_caja"], Lc, x_c - Le - Lc)
    caja = caja.cut(cil_x(P["D_caja_int"], Lc - 2 * e, x_c - Le - Lc + e))
    caja = caja.cut(cil_x(P["D_abertura_caja"], Lc + 2, x_c - Le - Lc - 1))
    pz["caja_resorte"] = caja
    ea = P["esp_arandela"]
    ar = lambda x0: cil_x(P["D_arandela"], ea, x0).cut(cil_x(P["D_vastago"] + 0.5, ea + 2, x0 - 1))
    x_a1 = x_c - Le - e - ea
    x_a2 = x_c - Le - Lc + e
    pz["arandela_1"], pz["arandela_2"] = ar(x_a1), ar(x_a2)
    L_res = x_a1 - (x_a2 + ea)
    pz["resorte"] = cil_x(P["D_resorte_ext"], L_res, x_a2 + ea).cut(cil_x(P["D_resorte_int"], L_res + 2, x_a2 + ea - 1))
    pz["collar"] = cil_x(P["D_collar"], P["L_collar"], x_c - Le - e).cut(cil_x(P["D_vastago"] + 0.05, P["L_collar"] + 2, x_c - Le - e - 1))
    x_n = x_a2 - P["esp_tuerca"]
    pz["tuerca_resorte"] = cil_x(P["D_collar"], P["esp_tuerca"], x_n).cut(cil_x(P["D_rosca_vastago"], P["esp_tuerca"] + 2, x_n - 1))
    pz["_x_fin"] = x_n
    return pz


def ensamble():
    L, e, eb = P["L"], P["L_espiga_tapa"], P["esp_brida_tapa"]
    a = cq.Assembly(name="Nubelink_H1B_comando")
    a.add(bloque(), name="bloque", color=cq.Color(0.60, 0.62, 0.66))
    z = P["z_eje"]
    a.add(tapa(), name="tapa_der", loc=cq.Location(cq.Vector(L / 2.0 - e, 0, z)), color=cq.Color(0.35, 0.38, 0.42))
    a.add(tapa(), name="tapa_izq", loc=cq.Location(cq.Vector(-(L / 2.0 - e), 0, z), cq.Vector(0, 0, 1), 180), color=cq.Color(0.35, 0.38, 0.42))
    a.add(piston(), name="piston", color=cq.Color(0.72, 0.53, 0.30))
    a.add(vastago(), name="vastago", color=cq.Color(0.80, 0.80, 0.82))
    a.add(horquilla(), name="horquilla", loc=cq.Location(cq.Vector(P["L_vastago"] / 2.0, 0, 0)), color=cq.Color(0.30, 0.30, 0.32))
    x_c = -(L / 2.0 + eb)
    pr = paquete_resorte(x_c)
    col = {"espaciador": (0.45, 0.47, 0.50), "caja_resorte": (0.55, 0.57, 0.60), "arandela_1": (0.3, 0.3, 0.32),
           "arandela_2": (0.3, 0.3, 0.32), "resorte": (0.85, 0.55, 0.20), "collar": (0.25, 0.25, 0.28), "tuerca_resorte": (0.25, 0.25, 0.28)}
    for n, pieza in pr.items():
        if not n.startswith("_"):
            a.add(pieza, name=n, color=cq.Color(*col[n]))
    return a


def compuesto(assy, corte=False):
    solidos = []
    caja = cq.Workplane("XY").box(600, 300, 300).translate((0, -150, 0))
    for nombre, obj in assy.traverse():
        if obj.obj is None or nombre == assy.name:
            continue
        shp = obj.obj.val() if hasattr(obj.obj, "val") else obj.obj
        shp = shp.located(obj.loc) if hasattr(shp, "located") else shp.moved(obj.loc)
        if corte:
            shp = cq.Workplane("XY").add(shp).cut(caja).val()
        solidos.append(shp)
    return cq.Compound.makeCompound(solidos)


def exportar():
    os.makedirs(OUT, exist_ok=True)
    assy = ensamble()
    assy.export(os.path.join(OUT, "nubelink_h1b_comando_ensamble.step"))
    piezas = {"bloque": bloque(), "tapa": tapa(), "piston": piston(), "vastago": vastago(),
              "horquilla": horquilla(), "caja_resorte": paquete_resorte(0.0)["caja_resorte"]}
    for n, wp in piezas.items():
        cq.exporters.export(wp, os.path.join(OUT, f"nubelink_h1b_comando_{n}.step"))
    cq.exporters.export(piezas["bloque"], os.path.join(OUT, "nubelink_h1b_comando_bloque.stl"), tolerance=0.02, angularTolerance=0.1)
    base_opt = dict(width=1100, height=560, marginLeft=20, marginTop=20, showAxes=False,
                    strokeWidth=0.6, strokeColor=(20, 20, 20), hiddenColor=(170, 170, 170), showHidden=False)
    vistas = {"iso": (dict(projectionDir=(0.55, -0.75, 0.45)), False),
              "corte": (dict(projectionDir=(0.25, -0.9, 0.35)), True),
              "frente": (dict(projectionDir=(0.0, -1.0, 0.0)), False)}
    for nombre, (opt, corte) in vistas.items():
        comp = compuesto(assy, corte=corte)
        if nombre in ("frente", "corte"):
            comp = comp.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), ROT_LATERAL)
        cq.exporters.export(comp, os.path.join(OUT, f"nubelink_h1b_comando_{nombre}.svg"), opt={**base_opt, **opt})
    # bloque solo, con líneas ocultas (para ver galerías y cavidades)
    cq.exporters.export(piezas["bloque"], os.path.join(OUT, "nubelink_h1b_comando_bloque_iso.svg"),
                        opt={**base_opt, "showHidden": True, "projectionDir": (0.6, -0.7, 0.45), "width": 900})
    A = math.pi / 4 * (P["D_camisa"] ** 2 - P["D_vastago"] ** 2)
    vol = piezas["bloque"].val().Volume()
    print(f"Área útil: {A:.0f} mm² -> {A*1e-6*14e5:.0f} N a 14 bar, {A*1e-6*20e5:.0f} N a 20 bar")
    print(f"Bloque {P['L']:g} x {P['W']:g} x {P['H']:g}: volumen {vol/1000:.0f} cm³ -> aluminio {vol*2.75e-6:.2f} kg / acero {vol*7.85e-6:.2f} kg")
    print(f"Salidas A/B en x = ±{x_salida():.0f}; cámara ±{P['L']/2 - P['L_espiga_tapa']:.0f}; cara del pistón a tope ±{P['L_piston']/2 + P['carrera_max']:.0f}")
    print(f"Archivos escritos en {OUT}")


if __name__ == "__main__":
    exportar()
