# Nubelink – bloque electrohidráulico para grúas con distribuidor manual

Carpeta de ingeniería del proyecto **Nubelink**: convertir grúas cargadoras con
distribuidor manual (sin electroválvulas) a radiocontrol proporcional,
reutilizando la electrónica de radio que ya se instala hoy en grúas Hiab /
Palfinger / Danfoss.

| Carpeta / archivo | Contenido |
|---|---|
| [`docs/nubelink_h1_analisis_y_especificacion.md`](docs/nubelink_h1_analisis_y_especificacion.md) | Análisis del Scanreco MOD10, principio de funcionamiento, arquitectura propuesta, **especificación del prototipo H1**, válvulas comerciales candidatas, fabricación, seguridad, protocolo de ensayos, costos y hoja de ruta. |
| [`docs/esquema_hidraulico_h1.svg`](docs/esquema_hidraulico_h1.svg) | Esquema hidráulico de un módulo con su alimentación de pilotaje (contrapresión, reductora, filtro, dump, seguridad). |
| [`cad/nubelink_h1.py`](cad/nubelink_h1.py) | Modelo 3D paramétrico (CadQuery) del servopistón H1: cuerpo torneable, tapas roscadas, pistón, vástago pasante, horquilla, topes. |
| [`cad/out/`](cad/out/) | STEP del ensamble y de cada pieza, STL del cuerpo, vistas SVG (isométrica, medio corte, frente, planta). |
| [`calc/dimensionado_h1.py`](calc/dimensionado_h1.py) | Cálculo de área/fuerza/caudal, presión de pilotaje necesaria, calor de contrapresión y verificación del cuerpo. Resultado en `calc/dimensionado_h1_resultado.md`. |

## Regenerar el 3D

```bash
pip install cadquery
python3 nubelink/cad/nubelink_h1.py        # escribe nubelink/cad/out/*
python3 nubelink/calc/dimensionado_h1.py --fuerza 200 --friccion 40
```

Los STEP se abren en FreeCAD, Fusion 360, SolidWorks o cualquier CAM. Cambie las
medidas en el diccionario `P` al inicio de `nubelink_h1.py` y vuelva a ejecutar.

> Estado: **concepto de ingeniería para banco de pruebas**. No es un diseño
> validado para instalarse en una grúa con carga. Ver la sección de seguridad del
> documento principal.
