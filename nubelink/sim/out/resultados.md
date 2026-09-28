# Resultados de simulación Nubelink H1 (modelo de parámetros concentrados)

Parámetros: pistón Ø32/Ø16 (603 mm²), carrera ±20 mm, válvula 0–20 bar / 12 L/min, pilotaje 25 bar,
resorte del carrete 60 N + 8 N/mm (SUPUESTO), fricción 45 N (SUPUESTO), I_max 1,0 A, zona muerta 0,12 A.

| Escenario | Resultado |
|---|---|
| S1 lazo abierto: posición a 0,3 / 0,6 / 1,0 A | 17.4 / 20.1 / 20.2 mm (tope 20 mm): **satura desde 0,3 A** |
| S1 tiempo al 90 % del primer escalón | 340 ms |
| S1 retorno a neutro al soltar (90 %) | 259 ms |
| S2 histéresis en lazo abierto, sin / con dither | 49 % / 47 % de la carrera (domina fricción/rigidez, no la válvula) |
| S3 corte total, fricción 45 N | vuelve a |x| < 1 mm en 296 ms, posición final 0.00 mm |
| S3 corte total, fricción 120 N (carrete sucio) | no vuelve, **queda en 6.1 mm** |
| S3b retorno activo (lazo cerrado a 0) y dump a los 0,5 s, fricción 120 N | vuelve en 121 ms, posición final -0.05 mm |
| S4 lazo cerrado: error estacionario máx. / t90 del escalón de 10 mm | 0.55 mm / 80 ms |
| S5 lazo abierto, corriente de arranque → tope, base | 0.22 → 0.36 A |
| S5 con fricción 120 N | 0.26 → 0.42 A |
| S5 con pilotaje 15 bar | 0.22 → 0.36 A |
| S6 resorte débil (35 N + 1 N/mm), corte total, sin resorte propio | no vuelve, queda en 8.1 mm |
| S6 ídem con paquete de centrado propio 60 N + 2 N/mm | 265 ms, queda en 0.0 mm |
| Modo manual a 0,1 m/s, sin resorte propio | 3.6 L/min, Δp 0.60 bar → 36 N hidr. + 45 N fricción = **81 N** extra en la horquilla |
| Modo manual a 0,1 m/s, con resorte propio 60 N + 2 N/mm | 36 + 45 + 100 N (resorte a tope) = **181 N** extra en la horquilla |

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
