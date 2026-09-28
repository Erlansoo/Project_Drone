# Resultados de simulación Nubelink H1 (modelo de parámetros concentrados)

Parámetros: pistón Ø32/Ø16 (603 mm²), carrera ±20 mm, válvula 0–20 bar / 12 L/min, pilotaje 25 bar,
resorte del carrete 60 N + 8 N/mm (SUPUESTO), resorte propio del módulo 50 N + 2,5 N/mm, fricción 45 N (SUPUESTO), I_max 1,0 A, zona muerta 0,12 A.

| Escenario | Resultado |
|---|---|
| S1 lazo abierto: posición a 0,3 / 0,6 / 1,0 A | 9.0 / 20.1 / 20.2 mm (tope 20 mm): **satura desde 0,3 A** |
| S1 tiempo al 90 % del primer escalón | 363 ms |
| S1 retorno a neutro al soltar (90 %) | 136 ms |
| S2 histéresis en lazo abierto, sin / con dither | 46 % / 41 % de la carrera (domina fricción/rigidez, no la válvula) |
| S3 corte total, fricción 45 N | vuelve a |x| < 1 mm en 147 ms, posición final 0.00 mm |
| S3 corte total, fricción 120 N (carrete sucio) | 480 ms, **queda en 0.0 mm** |
| S3b retorno activo (lazo cerrado a 0) y dump a los 0,5 s, fricción 120 N | vuelve en 123 ms, posición final -0.00 mm |
| S4 lazo cerrado: error estacionario máx. / t90 del escalón de 10 mm | 0.47 mm / 94 ms |
| S5 lazo abierto, corriente de arranque → tope, base | 0.25 → 0.43 A |
| S5 con fricción 120 N | 0.30 → 0.48 A |
| S5 con pilotaje 15 bar | 0.25 → 0.43 A |
| S6 resorte débil (35 N + 1 N/mm), corte total, sin resorte propio | no vuelve, queda en 8.1 mm |
| S6 ídem con paquete de centrado propio 60 N + 2 N/mm | 283 ms, queda en 0.0 mm |
| S7 PWM → posición, lazo cerrado | histéresis 5 %, desvío máx. respecto a la recta 1.7 mm |
| S7 PWM → posición, lazo abierto (diseño) | histéresis 38 %, desvío máx. 13.3 mm |
| S7 PWM → posición, lazo abierto con sellos PTFE (20 N) | histéresis 28 %, desvío máx. 13.7 mm |
| Modo manual a 0,1 m/s, sin resorte propio | 3.6 L/min, Δp 0.60 bar → 36 N hidr. + 45 N fricción = **81 N** extra en la horquilla |
| Modo manual a 0,1 m/s, con resorte propio 50 N + 2,5 N/mm (diseño) | 36 + 45 + 100 N (resorte a tope) = **181 N** extra en la horquilla |

### Fuerza extra en modo manual según el resorte propio (a 0,1 m/s, a fin de carrera; palanca con relación 3)

| Resorte propio | Fricción | Extra en la horquilla | Extra en la empuñadura |
|---|---|---|---|
| 0 N + 0.0 N/mm | 45 N | 81 N | 27 N |
| 0 N + 0.0 N/mm | 20 N | 56 N | 19 N |
| 50 N + 2.5 N/mm | 45 N | 181 N | 60 N |
| 50 N + 2.5 N/mm | 20 N | 156 N | 52 N |
| 60 N + 4.0 N/mm | 45 N | 221 N | 74 N |
| 60 N + 4.0 N/mm | 20 N | 196 N | 65 N |
| 80 N + 8.0 N/mm | 45 N | 321 N | 107 N |
| 80 N + 8.0 N/mm | 20 N | 296 N | 99 N |

## Conclusiones de diseño

1. **El lazo abierto (presión ∝ corriente, sin sensor) no sirve** con un pistón de 1 200 N sobre un resorte de carrete de
   decenas de N: toda la carrera cabe en 0,1–0,2 A de corriente y la histéresis es del orden de la mitad de la carrera. No es
   un problema de la válvula ni del dither: es fricción / rigidez del resorte. Por eso el MOD10 lleva realimentación mecánica.
2. **Con sensor de posición y lazo PI el módulo posiciona a ≈ ±0,5 mm en menos de 100 ms**, usando el empuje sobrante para vencer la
   fricción. El sensor no es "fase 2": es parte del diseño.
3. **Retorno a neutro**: el paquete de resorte propio (50 N + 2,5 N/mm, obligatorio) devuelve el pistón a neutro en ~0,3 s
   aunque el distribuidor tenga resorte débil o el carrete esté sucio (S6). Además, con energía, la secuencia "retorno activo
   en lazo cerrado → dump 0,5 s después" lo hace más rápido y verifica el neutro con el sensor (S3b).
4. **PWM → posición (S7)**: con el lazo cerrado el recorrido es proporcional a la señal del joystick (desvío < 1 mm). En lazo
   abierto la curva es una S con histéresis grande; sólo con fricción muy baja y resortes más rígidos se acerca a la recta,
   y eso encarece el modo manual (tabla de fuerzas). Conclusión: la proporcionalidad la da el lazo; el resorte, la seguridad.
5. **Modo manual**: el resorte de diseño cuesta ~100 N más en la horquilla a fin de carrera (≈ 35 N en la empuñadura con
   relación de palanca 3). Bajar la fricción (PTFE) importa tanto como el resorte.
6. La presión de pilotaje (15 vs 25 bar) casi no cambia nada; la fricción sí. **Prioridad del banco: medir y minimizar fricción**
   (sellos PTFE en pistón y vástago).

Figuras: S1_escalones.png · S2_histeresis.png · S3_falla_segura.png · S4_lazo_cerrado.png · S5_sensibilidad.png · S6_resorte_debil.png · S7_pwm_posicion.png
