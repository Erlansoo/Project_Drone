#!/usr/bin/env python3
"""
Modelo 3D paramétrico del servopistón Nubelink H1 (1 función, doble vástago pasante).

Concepto: cuerpo cilíndrico torneable en torno convencional; dos tapas roscadas
(M48x1,5) con sello de vástago + guardapolvo; pistón con aro PTFE; vástago pasante
Ø12 con horquilla para la varilla del distribuidor manual en un extremo y
porta-imán (sensor de posición) en el otro; dos puertos G1/4 (A y B) y una cara
plana inferior con 4 x M8 para el soporte.

Todas las medidas están en milímetros y se concentran en la sección PARÁMETROS.
Requiere CadQuery >= 2.4:  pip install cadquery

Salidas (carpeta ./out):
  nubelink_h1_ensamble.step     ensamble completo (para revisar en FreeCAD / Fusion)
  nubelink_h1_cuerpo.step/.stl  cuerpo a tornear
  nubelink_h1_tapa.step         tapa roscada (x2, iguales)
  nubelink_h1_piston.step       pistón
  nubelink_h1_vastago.step      vástago
  nubelink_h1_horquilla.step    horquilla de acople
  nubelink_h1_iso.svg           vista isométrica
  nubelink_h1_corte.svg         medio corte longitudinal (muestra cámaras, puertos y pistón)
  nubelink_h1_frente.svg / _planta.svg  vistas ortogonales

IMPORTANTE: es un modelo CONCEPTUAL para dimensionar y cotizar. Los alojamientos
de sellos deben ajustarse al catálogo del sello elegido antes de mecanizar.
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
    # Cuerpo
    D_cuerpo=60.0,          # diámetro exterior del cuerpo (barra redonda)
    L_cuerpo=100.0,         # largo total del cuerpo
    D_camisa=25.0,          # diámetro interior (camisa) H8, bruñido
    D_rosca_tapa=48.0,      # rosca de tapa M48x1,5 (modelada como cilindro liso)
    prof_rosca_tapa=14.0,   # profundidad de rosca / alojamiento de tapa en cada extremo
    # Pistón y vástago
    D_vastago=12.0,         # vástago pasante Ø12 f7, cromado duro
    L_vastago=200.0,        # largo total del vástago
    L_piston=16.0,          # espesor del pistón
    carrera_max=20.0,       # carrera máxima desde neutro (±)
    carrera_ajustada=13.0,  # carrera limitada por tuercas tope (ejemplo ±13 mm)
    # Puertos
    D_puerto_paso=7.0,      # taladro de comunicación puerto -> cámara
    D_puerto_rosca=11.5,    # taladro para rosca G1/4 (11,45 mm)
    prof_puerto_rosca=12.0,
    prof_plano_puerto=4.0,  # profundidad de la cara plana (spot-face) en el cuerpo
    ancho_plano_puerto=24.0,
    # Montaje
    ancho_plano_montaje=32.0,
    prof_plano_montaje=4.0,
    L_plano_montaje=90.0,
    D_taladro_M8=6.8,
    prof_taladro_M8=14.0,
    sep_x_M8=70.0,
    sep_y_M8=20.0,
    # Tapa
    esp_brida_tapa=8.0,
    # Horquilla
    L_horquilla=30.0,
    ancho_horquilla=16.0,
    alto_horquilla=20.0,
    ranura_horquilla=8.0,
    D_perno_horquilla=8.0,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
ROT_LATERAL = -90  # grados de giro alrededor de Y para las vistas laterales (ver exportar)


def cil_x(d, largo, x0):
    """Cilindro de diámetro d, largo `largo`, eje X, comenzando en x0."""
    return cq.Workplane("YZ").workplane(offset=x0).circle(d / 2.0).extrude(largo)


def cuerpo():
    R = P["D_cuerpo"] / 2.0
    L = P["L_cuerpo"]
    b = cil_x(P["D_cuerpo"], L, -L / 2.0)
    # camisa pasante
    b = b.cut(cil_x(P["D_camisa"], L + 2, -L / 2.0 - 1))
    # alojamientos roscados de tapa en ambos extremos
    for s in (-1, 1):
        x0 = s * L / 2.0 - (P["prof_rosca_tapa"] if s > 0 else 0)
        b = b.cut(cil_x(P["D_rosca_tapa"], P["prof_rosca_tapa"], x0))
    # posición axial de los puertos: siempre dentro de la cámara, nunca tapados por el pistón
    cam_int = L / 2.0 - P["prof_rosca_tapa"]                 # cara interior de tapa (36)
    cara_piston_max = P["L_piston"] / 2.0 + P["carrera_max"]  # cara del pistón a tope (28)
    x_puerto = (cam_int + cara_piston_max) / 2.0             # 32
    assert x_puerto + P["D_puerto_paso"] / 2 < cam_int and x_puerto - P["D_puerto_paso"] / 2 >= cara_piston_max, \
        "El puerto quedaría tapado por el pistón o abierto al alojamiento de tapa: revise carrera/longitud"
    z_plano = R - P["prof_plano_puerto"]
    for s in (-1, 1):
        x = s * x_puerto
        plano = cq.Workplane("XY").box(P["ancho_plano_puerto"], P["ancho_plano_puerto"], P["prof_plano_puerto"] + 2) \
            .translate((x, 0, R + 1 - (P["prof_plano_puerto"] + 2) / 2.0))
        b = b.cut(plano)
        rosca = cq.Workplane("XY").workplane(offset=z_plano).center(x, 0) \
            .circle(P["D_puerto_rosca"] / 2.0).extrude(-P["prof_puerto_rosca"])
        paso = cq.Workplane("XY").workplane(offset=z_plano).center(x, 0) \
            .circle(P["D_puerto_paso"] / 2.0).extrude(-z_plano)
        b = b.cut(rosca).cut(paso)
    # plano de montaje inferior + 4 x M8
    z_m = -(R - P["prof_plano_montaje"])
    plano_m = cq.Workplane("XY").box(P["L_plano_montaje"], P["ancho_plano_montaje"], P["prof_plano_montaje"] + 2) \
        .translate((0, 0, -R - 1 + (P["prof_plano_montaje"] + 2) / 2.0))
    b = b.cut(plano_m)
    for sx in (-1, 1):
        for sy in (-1, 1):
            h = cq.Workplane("XY").workplane(offset=z_m) \
                .center(sx * P["sep_x_M8"] / 2.0, sy * P["sep_y_M8"] / 2.0) \
                .circle(P["D_taladro_M8"] / 2.0).extrude(P["prof_taladro_M8"])
            b = b.cut(h)
    return b


def tapa():
    """Tapa roscada: espiga con ranura de O-ring + brida; alojamiento de sello de vástago y guardapolvo.
    Se modela con la espiga hacia -X y la brida hacia +X, con la cara interior de la espiga en x=0."""
    esp = P["prof_rosca_tapa"]
    t = cil_x(P["D_rosca_tapa"], esp, 0)                      # espiga 0..14
    t = t.union(cil_x(P["D_cuerpo"], P["esp_brida_tapa"], esp))  # brida 14..22
    # ranura de O-ring sobre la espiga (O-ring 44x3 aprox.)
    ranura = cil_x(P["D_rosca_tapa"] + 2, 4.2, 4.0).cut(cil_x(P["D_rosca_tapa"] - 4.6, 4.2, 4.0))
    t = t.cut(ranura)
    # paso de vástago
    t = t.cut(cil_x(P["D_vastago"] + 0.1, esp + P["esp_brida_tapa"] + 2, -1))
    # alojamiento de sello de vástago (interior) y guardapolvo (exterior) - ajustar al catálogo del sello
    t = t.cut(cil_x(20.0, 5.5, 3.0))                                        # sello vástago 12x20x5,5
    t = t.cut(cil_x(18.0, 5.0, esp + P["esp_brida_tapa"] - 5.0))            # guardapolvo 12x18x5
    # hexágono/agujeros de llave en la brida: 2 taladros Ø6 para llave de espigas
    for s in (-1, 1):
        t = t.cut(cq.Workplane("YZ").workplane(offset=esp + P["esp_brida_tapa"] - 4)
                  .center(s * 22, 0).circle(3.0).extrude(5))
    return t


def piston():
    p = cil_x(P["D_camisa"] - 0.1, P["L_piston"], -P["L_piston"] / 2.0)
    # ranura para aro PTFE (glyd ring) + O-ring energizante, centrada
    ranura = cil_x(P["D_camisa"] + 2, 4.5, -2.25).cut(cil_x(P["D_camisa"] - 8.0, 4.5, -2.25))
    p = p.cut(ranura)
    p = p.cut(cil_x(P["D_vastago"] + 0.05, P["L_piston"] + 2, -P["L_piston"] / 2.0 - 1))
    return p


def vastago():
    L = P["L_vastago"]
    v = cil_x(P["D_vastago"], L, -L / 2.0)
    # extremos roscados M10 (modelados como Ø10 x 20)
    for s in (-1, 1):
        x0 = s * L / 2.0 - (20 if s > 0 else 0)
        anillo = cil_x(P["D_vastago"] + 1, 20, x0).cut(cil_x(10.0, 20, x0))
        v = v.cut(anillo)
    return v


def horquilla():
    """Horquilla (clevis) roscada al extremo +X del vástago; se modela con su base en x=0."""
    Lh, a, h = P["L_horquilla"], P["ancho_horquilla"], P["alto_horquilla"]
    f = cq.Workplane("XY").box(Lh, a, h).translate((Lh / 2.0, 0, 0))
    ranura = cq.Workplane("XY").box(Lh * 0.6 + 1, P["ranura_horquilla"], h + 2).translate((Lh - Lh * 0.3, 0, 0))
    f = f.cut(ranura)
    perno = cq.Workplane("XZ").center(Lh - Lh * 0.3, 0).circle(P["D_perno_horquilla"] / 2.0).extrude(a, both=True)
    f = f.cut(perno)
    rosca = cil_x(10.0, Lh * 0.4 + 1, -1)
    f = f.cut(rosca)
    return f


def tuerca_tope():
    """Tuerca hexagonal M12 (19 mm entre caras) usada como tope de carrera ajustable."""
    circ = 19.0 / math.cos(math.radians(30))
    n = cq.Workplane("YZ").polygon(6, circ).extrude(6.0)
    return n.cut(cil_x(P["D_vastago"] + 0.2, 8, -1))


def porta_iman():
    d = cil_x(20.0, 4.0, 0).cut(cil_x(10.0, 6, -1))
    return d


def ensamble():
    L = P["L_cuerpo"]
    esp = P["prof_rosca_tapa"]
    a = cq.Assembly(name="Nubelink_H1")
    a.add(cuerpo(), name="cuerpo", color=cq.Color(0.55, 0.57, 0.60))
    # tapa +X: cara interior de espiga en x = L/2 - esp  -> trasladar en +(L/2 - esp)
    a.add(tapa(), name="tapa_der", loc=cq.Location(cq.Vector(L / 2.0 - esp, 0, 0)), color=cq.Color(0.35, 0.38, 0.42))
    # tapa -X: espejada (rotación 180° alrededor de Z) y trasladada
    a.add(tapa(), name="tapa_izq",
          loc=cq.Location(cq.Vector(-(L / 2.0 - esp), 0, 0), cq.Vector(0, 0, 1), 180),
          color=cq.Color(0.35, 0.38, 0.42))
    a.add(piston(), name="piston", color=cq.Color(0.72, 0.53, 0.30))
    a.add(vastago(), name="vastago", color=cq.Color(0.80, 0.80, 0.82))
    x_brida = L / 2.0 + P["esp_brida_tapa"]                     # cara exterior de brida (58)
    x_fin_vastago = P["L_vastago"] / 2.0                        # 100
    a.add(horquilla(), name="horquilla", loc=cq.Location(cq.Vector(x_fin_vastago, 0, 0)), color=cq.Color(0.30, 0.30, 0.32))
    # tuercas tope: separación = carrera_ajustada respecto a la brida (ejemplo ±13 mm)
    g = P["carrera_ajustada"]
    a.add(tuerca_tope(), name="tope_der", loc=cq.Location(cq.Vector(x_brida + g, 0, 0)), color=cq.Color(0.25, 0.25, 0.28))
    a.add(tuerca_tope(), name="tope_izq", loc=cq.Location(cq.Vector(-(x_brida + g) - 6.0, 0, 0)), color=cq.Color(0.25, 0.25, 0.28))
    a.add(porta_iman(), name="porta_iman", loc=cq.Location(cq.Vector(-x_fin_vastago - 4.0, 0, 0)), color=cq.Color(0.20, 0.45, 0.75))
    return a


def compuesto(assy, corte=False):
    """Devuelve un Compound con todas las piezas ubicadas; opcionalmente medio corte (elimina y<0)."""
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
    assy.export(os.path.join(OUT, "nubelink_h1_ensamble.step"))
    piezas = {
        "cuerpo": cuerpo(), "tapa": tapa(), "piston": piston(),
        "vastago": vastago(), "horquilla": horquilla(),
    }
    for n, wp in piezas.items():
        cq.exporters.export(wp, os.path.join(OUT, f"nubelink_h1_{n}.step"))
    cq.exporters.export(piezas["cuerpo"], os.path.join(OUT, "nubelink_h1_cuerpo.stl"), tolerance=0.02, angularTolerance=0.1)

    base_opt = dict(width=1100, height=520, marginLeft=20, marginTop=20, showAxes=False,
                    strokeWidth=0.6, strokeColor=(20, 20, 20), hiddenColor=(170, 170, 170), showHidden=False)
    vistas = {
        "iso": (dict(projectionDir=(0.55, -0.75, 0.45)), False),
        "corte": (dict(projectionDir=(0.25, -0.9, 0.35)), True),
        "frente": (dict(projectionDir=(0.0, -1.0, 0.0)), False),
        "planta": (dict(projectionDir=(0.0, 0.0, 1.0)), False),
    }
    for nombre, (opt, corte) in vistas.items():
        comp = compuesto(assy, corte=corte)
        if nombre in ("frente", "corte"):
            # el exportador SVG pone el eje X vertical en la vista lateral; giramos la pieza
            # para que el eje del cilindro quede horizontal y los puertos arriba
            comp = comp.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), ROT_LATERAL)
        cq.exporters.export(comp, os.path.join(OUT, f"nubelink_h1_{nombre}.svg"), opt={**base_opt, **opt})

    # resumen numérico útil para el informe
    A = math.pi / 4 * (P["D_camisa"] ** 2 - P["D_vastago"] ** 2)
    vol_cuerpo = math.pi / 4 * (P["D_cuerpo"] ** 2 - P["D_camisa"] ** 2) * P["L_cuerpo"]
    print(f"Área útil pistón: {A:.0f} mm²  ->  {A*1e-6*30e5:.0f} N a 30 bar")
    print(f"Cámara interior: {P['L_cuerpo'] - 2*P['prof_rosca_tapa']:.0f} mm; carrera ±{P['carrera_max']:.0f} mm; "
          f"puertos G1/4 en x = ±{(P['L_cuerpo']/2 - P['prof_rosca_tapa'] + P['L_piston']/2 + P['carrera_max'])/2:.1f} mm")
    print(f"Masa aprox. cuerpo: acero {vol_cuerpo*7.85e-6:.2f} kg / aluminio {vol_cuerpo*2.8e-6:.2f} kg (sin descontar planos ni puertos)")
    print(f"Archivos escritos en {OUT}")


if __name__ == "__main__":
    exportar()
