#!/usr/bin/env python3
"""
Modelo 3D paramétrico del servopistón Nubelink H1 (1 función, doble vástago pasante).

Concepto: cuerpo cilíndrico torneable en torno convencional; dos tapas roscadas
con sello de vástago + guardapolvo; pistón con aro PTFE; vástago pasante con
horquilla para la varilla del distribuidor manual en un extremo y porta-imán
(sensor de posición) en el otro; dos puertos G1/4 (A y B) y una cara plana
inferior con 4 x M8 para el soporte.

Dimensionado "paridad Scanreco MOD10": empuje >= 1 300 N con pilotaje <= 25 bar
(camisa Ø32 / vástago Ø16 -> 603 mm² -> 1 206 N a 20 bar, 1 508 N a 25 bar).

Todas las medidas están en milímetros y se concentran en la sección PARÁMETROS.
Requiere CadQuery >= 2.4:  pip install cadquery

Salidas (carpeta ./out):
  nubelink_h1_ensamble.step     ensamble completo (para revisar en FreeCAD / Fusion)
  nubelink_h1_cuerpo.step/.stl  cuerpo a tornear
  nubelink_h1_tapa.step         tapa roscada (x2, iguales)
  nubelink_h1_piston.step       pistón
  nubelink_h1_vastago.step      vástago
  nubelink_h1_horquilla.step    horquilla de acople
  nubelink_h1_caja_resorte.step caja del paquete de resorte de centrado (obligatorio: 50 N + 2,5 N/mm)
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
    D_cuerpo=70.0,          # diámetro exterior del cuerpo (barra redonda)
    L_cuerpo=110.0,         # largo total del cuerpo
    D_camisa=32.0,          # diámetro interior (camisa) H8, bruñido
    D_rosca_tapa=56.0,      # rosca de tapa M56x1,5 (modelada como cilindro liso)
    prof_rosca_tapa=14.0,   # profundidad de rosca / alojamiento de tapa en cada extremo
    # Pistón y vástago
    D_vastago=16.0,         # vástago pasante Ø16 f7, cromado duro
    L_vastago=260.0,        # largo total del vástago (260 con paquete de resorte; 220 sin él)
    D_rosca_vastago=12.0,   # rosca en los extremos del vástago (M12)
    L_rosca_vastago=22.0,
    L_piston=20.0,          # espesor del pistón
    ancho_ranura_piston=5.0,  # ranura para aro PTFE + O-ring energizante (ver catálogo)
    carrera_max=20.0,       # carrera máxima desde neutro (±)
    carrera_ajustada=13.0,  # carrera limitada por tuercas tope (ejemplo ±13 mm)
    # Tapa
    esp_brida_tapa=8.0,
    D_sello_vastago=24.0,   # alojamiento sello de vástago (ej. 16x24x5,5) - ajustar al catálogo
    L_sello_vastago=5.5,
    D_guardapolvo=22.0,     # alojamiento guardapolvo (ej. 16x22x5) - ajustar al catálogo
    L_guardapolvo=5.0,
    sep_llave_tapa=27.0,    # separación de los agujeros para llave de espigas
    # Puertos
    D_puerto_paso=7.0,      # taladro de comunicación puerto -> cámara
    D_puerto_rosca=11.5,    # taladro para rosca G1/4 (11,45 mm)
    prof_puerto_rosca=12.0,
    prof_plano_puerto=4.0,  # profundidad de la cara plana (spot-face) en el cuerpo
    ancho_plano_puerto=26.0,
    # Montaje
    ancho_plano_montaje=36.0,
    prof_plano_montaje=4.0,
    L_plano_montaje=100.0,
    D_taladro_M8=6.8,
    prof_taladro_M8=14.0,
    sep_x_M8=80.0,
    sep_y_M8=24.0,
    # Horquilla
    L_horquilla=34.0,
    ancho_horquilla=20.0,
    alto_horquilla=24.0,
    ranura_horquilla=10.0,
    D_perno_horquilla=10.0,
    # Tuerca tope (M16: 24 mm entre caras)
    entre_caras_tuerca=24.0,
    esp_tuerca=8.0,
    # Paquete de resorte de centrado propio (extremo -X, OBLIGATORIO): dos arandelas + resorte de matricería
    # precargado tipo carrete (50 N + 2,5 N/mm de partida)
    resorte_centrado=True,
    D_caja=44.0, D_caja_int=36.0, L_caja=48.0, esp_pared_caja=4.0, D_abertura_caja=30.0,
    L_espaciador=8.0, D_espaciador_int=32.0,
    D_arandela=34.0, esp_arandela=3.0,
    D_resorte_ext=28.0, D_resorte_int=20.0,
    D_collar=24.0, L_collar=5.0,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
ROT_LATERAL = -90  # grados de giro alrededor de Y para las vistas laterales (ver exportar)


def cil_x(d, largo, x0):
    """Cilindro de diámetro d, largo `largo`, eje X, comenzando en x0."""
    return cq.Workplane("YZ").workplane(offset=x0).circle(d / 2.0).extrude(largo)


def x_puerto():
    """Posición axial de los puertos: dentro de la cámara y nunca tapados por el pistón."""
    cam_int = P["L_cuerpo"] / 2.0 - P["prof_rosca_tapa"]        # cara interior de tapa
    cara_piston_max = P["L_piston"] / 2.0 + P["carrera_max"]     # cara del pistón a tope
    x = (cam_int + cara_piston_max) / 2.0
    assert x + P["D_puerto_paso"] / 2 < cam_int and x - P["D_puerto_paso"] / 2 >= cara_piston_max, \
        "El puerto quedaría tapado por el pistón o abierto al alojamiento de tapa: revise carrera/longitud"
    return x


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
    xp = x_puerto()
    z_plano = R - P["prof_plano_puerto"]
    for s in (-1, 1):
        x = s * xp
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
    t = cil_x(P["D_rosca_tapa"], esp, 0)                          # espiga
    t = t.union(cil_x(P["D_cuerpo"], P["esp_brida_tapa"], esp))     # brida
    # ranura de O-ring sobre la espiga (sección 3 mm)
    ranura = cil_x(P["D_rosca_tapa"] + 2, 4.2, 4.0).cut(cil_x(P["D_rosca_tapa"] - 4.6, 4.2, 4.0))
    t = t.cut(ranura)
    # paso de vástago
    t = t.cut(cil_x(P["D_vastago"] + 0.1, esp + P["esp_brida_tapa"] + 2, -1))
    # alojamiento de sello de vástago (interior) y guardapolvo (exterior) - ajustar al catálogo del sello
    t = t.cut(cil_x(P["D_sello_vastago"], P["L_sello_vastago"], 3.0))
    t = t.cut(cil_x(P["D_guardapolvo"], P["L_guardapolvo"], esp + P["esp_brida_tapa"] - P["L_guardapolvo"]))
    # 2 taladros Ø6 en la brida para llave de espigas
    for s in (-1, 1):
        t = t.cut(cq.Workplane("YZ").workplane(offset=esp + P["esp_brida_tapa"] - 4)
                  .center(s * P["sep_llave_tapa"], 0).circle(3.0).extrude(5))
    return t


def piston():
    p = cil_x(P["D_camisa"] - 0.1, P["L_piston"], -P["L_piston"] / 2.0)
    w = P["ancho_ranura_piston"]
    ranura = cil_x(P["D_camisa"] + 2, w, -w / 2.0).cut(cil_x(P["D_camisa"] - 8.0, w, -w / 2.0))
    p = p.cut(ranura)
    p = p.cut(cil_x(P["D_vastago"] + 0.05, P["L_piston"] + 2, -P["L_piston"] / 2.0 - 1))
    return p


def vastago():
    L = P["L_vastago"]
    v = cil_x(P["D_vastago"], L, -L / 2.0)
    # extremos roscados (modelados como cilindro de diámetro nominal de rosca)
    for s in (-1, 1):
        x0 = s * L / 2.0 - (P["L_rosca_vastago"] if s > 0 else 0)
        anillo = cil_x(P["D_vastago"] + 1, P["L_rosca_vastago"], x0).cut(cil_x(P["D_rosca_vastago"], P["L_rosca_vastago"], x0))
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
    rosca = cil_x(P["D_rosca_vastago"], Lh * 0.4 + 1, -1)
    f = f.cut(rosca)
    return f


def tuerca_tope():
    """Tuerca hexagonal usada como tope de carrera ajustable (rosca en el vástago)."""
    circ = P["entre_caras_tuerca"] / math.cos(math.radians(30))
    n = cq.Workplane("YZ").polygon(6, circ).extrude(P["esp_tuerca"])
    return n.cut(cil_x(P["D_vastago"] + 0.2, P["esp_tuerca"] + 2, -1))


def porta_iman():
    d = cil_x(P["D_vastago"] + 8.0, 4.0, 0).cut(cil_x(P["D_rosca_vastago"], 6, -1))
    return d


def paquete_resorte(x_c):
    """Piezas del paquete de centrado, ubicadas. x_c = cara exterior de la brida de la tapa -X.
    Espaciador -> caja con dos paredes (aberturas Ø30) -> arandelas contra las paredes -> resorte entre
    arandelas -> collar fijo al vástago (lado tapa) y tuerca (lado libre) que empujan cada arandela."""
    Le, Lc, e = P["L_espaciador"], P["L_caja"], P["esp_pared_caja"]
    piezas = {}
    piezas["espaciador"] = cil_x(P["D_caja"], Le, x_c - Le).cut(cil_x(P["D_espaciador_int"], Le + 2, x_c - Le - 1))
    caja = cil_x(P["D_caja"], Lc, x_c - Le - Lc)
    caja = caja.cut(cil_x(P["D_caja_int"], Lc - 2 * e, x_c - Le - Lc + e))          # interior
    caja = caja.cut(cil_x(P["D_abertura_caja"], Lc + 2, x_c - Le - Lc - 1))          # aberturas en ambas paredes
    piezas["caja_resorte"] = caja
    ea = P["esp_arandela"]
    ar = lambda x0: cil_x(P["D_arandela"], ea, x0).cut(cil_x(P["D_vastago"] + 0.5, ea + 2, x0 - 1))
    x_a1 = x_c - Le - e - ea            # arandela 1 contra la pared cercana a la tapa
    x_a2 = x_c - Le - Lc + e            # arandela 2 contra la pared lejana
    piezas["arandela_1"] = ar(x_a1)
    piezas["arandela_2"] = ar(x_a2)
    L_res = x_a1 - (x_a2 + ea)
    piezas["resorte"] = cil_x(P["D_resorte_ext"], L_res, x_a2 + ea).cut(cil_x(P["D_resorte_int"], L_res + 2, x_a2 + ea - 1))
    # collar del vástago: atraviesa la abertura de la pared cercana y toca la arandela 1
    piezas["collar"] = cil_x(P["D_collar"], P["L_collar"], x_c - Le - e).cut(cil_x(P["D_vastago"] + 0.05, P["L_collar"] + 2, x_c - Le - e - 1))
    # tuerca: atraviesa la abertura de la pared lejana y toca la arandela 2
    x_n = x_a2 - P["esp_tuerca"]
    piezas["tuerca_resorte"] = cil_x(P["D_collar"], P["esp_tuerca"], x_n).cut(cil_x(P["D_rosca_vastago"], P["esp_tuerca"] + 2, x_n - 1))
    piezas["_x_fin"] = x_n
    return piezas


def ensamble():
    L = P["L_cuerpo"]
    esp = P["prof_rosca_tapa"]
    a = cq.Assembly(name="Nubelink_H1")
    a.add(cuerpo(), name="cuerpo", color=cq.Color(0.55, 0.57, 0.60))
    a.add(tapa(), name="tapa_der", loc=cq.Location(cq.Vector(L / 2.0 - esp, 0, 0)), color=cq.Color(0.35, 0.38, 0.42))
    a.add(tapa(), name="tapa_izq",
          loc=cq.Location(cq.Vector(-(L / 2.0 - esp), 0, 0), cq.Vector(0, 0, 1), 180),
          color=cq.Color(0.35, 0.38, 0.42))
    a.add(piston(), name="piston", color=cq.Color(0.72, 0.53, 0.30))
    a.add(vastago(), name="vastago", color=cq.Color(0.80, 0.80, 0.82))
    x_brida = L / 2.0 + P["esp_brida_tapa"]                     # cara exterior de brida
    x_fin_vastago = P["L_vastago"] / 2.0
    a.add(horquilla(), name="horquilla", loc=cq.Location(cq.Vector(x_fin_vastago, 0, 0)), color=cq.Color(0.30, 0.30, 0.32))
    # tuercas tope: separación = carrera_ajustada respecto a la brida (ejemplo ±13 mm)
    g = P["carrera_ajustada"]
    a.add(tuerca_tope(), name="tope_der", loc=cq.Location(cq.Vector(x_brida + g, 0, 0)), color=cq.Color(0.25, 0.25, 0.28))
    if P["resorte_centrado"]:
        pr = paquete_resorte(-x_brida)
        colores = {"espaciador": (0.45, 0.47, 0.50), "caja_resorte": (0.55, 0.57, 0.60), "arandela_1": (0.30, 0.30, 0.32),
                   "arandela_2": (0.30, 0.30, 0.32), "resorte": (0.85, 0.55, 0.20), "collar": (0.25, 0.25, 0.28),
                   "tuerca_resorte": (0.25, 0.25, 0.28)}
        for n, pieza in pr.items():
            if n.startswith("_"):
                continue
            a.add(pieza, name=n, color=cq.Color(*colores[n]))
        a.add(porta_iman(), name="porta_iman", loc=cq.Location(cq.Vector(pr["_x_fin"] - 5.0, 0, 0)), color=cq.Color(0.20, 0.45, 0.75))
    else:
        a.add(tuerca_tope(), name="tope_izq", loc=cq.Location(cq.Vector(-(x_brida + g) - P["esp_tuerca"], 0, 0)), color=cq.Color(0.25, 0.25, 0.28))
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
    if P["resorte_centrado"]:
        piezas["caja_resorte"] = paquete_resorte(0.0)["caja_resorte"]
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
    print(f"Área útil pistón: {A:.0f} mm²  ->  {A*1e-6*20e5:.0f} N a 20 bar, {A*1e-6*25e5:.0f} N a 25 bar, {A*1e-6*30e5:.0f} N a 30 bar")
    print(f"Cámara interior: {P['L_cuerpo'] - 2*P['prof_rosca_tapa']:.0f} mm; carrera ±{P['carrera_max']:.0f} mm; "
          f"puertos G1/4 en x = ±{x_puerto():.1f} mm")
    print(f"Volumen por media carrera: {A*P['carrera_max']/1000:.1f} cm³ -> {A*P['carrera_max']/1e6/0.3*60:.2f} L/min para 0,3 s")
    print(f"Masa aprox. cuerpo: acero {vol_cuerpo*7.85e-6:.2f} kg / aluminio {vol_cuerpo*2.8e-6:.2f} kg (sin descontar planos ni puertos)")
    print(f"Archivos escritos en {OUT}")


if __name__ == "__main__":
    exportar()
