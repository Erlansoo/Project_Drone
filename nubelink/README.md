# Nubelink – bloque electrohidráulico para grúas con distribuidor manual

Carpeta de ingeniería del proyecto **Nubelink**: convertir grúas cargadoras con
distribuidor manual (sin electroválvulas) a radiocontrol proporcional,
reutilizando la electrónica de radio que ya se instala hoy en grúas Hiab /
Palfinger / Danfoss. Dimensionado a paridad con el Scanreco MOD10
(carrera ±13/±20 mm, empuje ≥ 1 300 N) con pilotaje de 20–25 bar.

| Carpeta / archivo | Contenido |
|---|---|
| [`docs/nubelink_h1_analisis_y_especificacion.md`](docs/nubelink_h1_analisis_y_especificacion.md) | Análisis del Scanreco MOD10, principio de funcionamiento, **diseño del sistema completo** (entrada desde la línea de la grúa, bloque de alimentación, bloque de válvulas, servopistón), especificación del prototipo H1, válvulas comerciales (HYDAC PDR08‑01), fabricación, seguridad, protocolo de ensayos, costos y hoja de ruta. |
| [`docs/esquema_hidraulico_h1.svg`](docs/esquema_hidraulico_h1.svg) | Esquema hidráulico de un módulo con su alimentación de pilotaje (contrapresión venteada, reductora, filtro, dump, seguridad). |
| [`cad/nubelink_h1.py`](cad/nubelink_h1.py) | Modelo 3D paramétrico (CadQuery) del **servopistón H1**: cuerpo torneable Ø70 × 110, camisa Ø32, vástago pasante Ø16, tapas roscadas M56×1,5, horquilla, tope y **paquete de resorte de centrado**. |
| [`cad/nubelink_h1b_comando.py`](cad/nubelink_h1b_comando.py) · [`docs/hoja_fabricacion_h1b.md`](docs/hoja_fabricacion_h1b.md) | **H1‑B "comando" integrado para lazo abierto — la versión a fabricar primero**: un solo bloque 110 × 60 × 90 con camisa Ø20, 2 cavidades FC08‑3, galerías P/T y salidas internas; tapas atornilladas, resorte de centrado 40 N + 6 N/mm. Hoja de fabricación con cotas, tolerancias, dónde fabricar (CNC sí, SLM no) y check‑list. |
| [`cad/nubelink_h1_bloque_valvulas.py`](cad/nubelink_h1_bloque_valvulas.py) | Modelo 3D del **bloque de válvulas** de aluminio (2 cavidades FC08‑3 para HYDAC PDR08‑01, galerías P/T sin tapones, salidas A/B G1/4). |
| [`cad/out/`](cad/out/) | STEP del ensamble y de cada pieza, STL, vistas SVG (isométrica, medio corte, frente, planta). |
| [`docs/simulacion_y_compras.md`](docs/simulacion_y_compras.md) | Qué simular con qué programa (Simscape Fluids / SolidWorks Simulation / lo que no vale la pena), blueprint del modelo Simscape, cálculos a mano, y **compras y fabricación en China** (cartuchos, bloques, cilindros, sellos). |
| [`sim/servopiston_model.py`](sim/servopiston_model.py) · [`sim/servopiston_model.m`](sim/servopiston_model.m) | Modelo dinámico del módulo (válvulas proporcionales + cámaras + pistón + resorte del carrete + lazo de corriente con dither + PI de posición), en Python y su gemelo MATLAB. |
| [`sim/estudio_lazo_abierto.py`](sim/estudio_lazo_abierto.py) → `sim/out/estudio_lazo_abierto.md` | Estudio paramétrico pistón × resorte × sellos × distribuidor para la versión en lazo abierto. |
| [`sim/run_scenarios.py`](sim/run_scenarios.py) → [`sim/out/`](sim/out/) | Escenarios: escalones, histéresis con/sin dither, falla segura (pasiva y retorno activo + dump), lazo cerrado, sensibilidad, resorte débil, **PWM del joystick → posición**. Figuras PNG + `resultados.md`. |
| [`calc/dimensionado_h1.py`](calc/dimensionado_h1.py) | Cálculo de área/fuerza/caudal, presión para 1 300 N, presión de pilotaje necesaria, calor de contrapresión y verificación del cuerpo. Resultado en `calc/dimensionado_h1_resultado.md`. |

## Regenerar el 3D

```bash
pip install cadquery
python3 nubelink/cad/nubelink_h1.py                  # servopistón -> nubelink/cad/out/*
python3 nubelink/cad/nubelink_h1_bloque_valvulas.py  # bloque de válvulas (H1 lazo cerrado)
python3 nubelink/cad/nubelink_h1b_comando.py         # H1-B comando integrado (lazo abierto)
python3 nubelink/calc/dimensionado_h1.py --fuerza 250 --friccion 50
pip install numpy scipy matplotlib && python3 nubelink/sim/run_scenarios.py   # simulación (~3 min)
```

Los STEP se abren en FreeCAD, Fusion 360, SolidWorks o cualquier CAM. Cambie las
medidas en los diccionarios `P` / `B` al inicio de cada script y vuelva a ejecutar.

> Estado: **concepto de ingeniería para banco de pruebas**. No es un diseño
> validado para instalarse en una grúa con carga. La cavidad FC08‑3 del bloque de
> válvulas es un marcador de posición: mecanizar según el plano oficial HYDAC.
> Ver la sección de seguridad del documento principal.
