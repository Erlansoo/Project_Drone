# Dimensionado preliminar Nubelink H1

### Fuerza y caudal por opción de pistón (vástago pasante) — referencia Scanreco MOD10: 1 300 N a 30 bar

| Camisa Ø / vástago Ø | Área útil (mm²) | F @ 10 bar (N) | F @ 20 bar (N) | F @ 30 bar (N) | p para 1300 N (bar) | Vol. neutro→tope 20 mm (cm³) | Caudal para 0.3 s (L/min) |
|---|---|---|---|---|---|---|---|
| Ø20 / Ø10 | 236 | 236 | 471 | 707 | 55.2 | 4.7 | 0.94 |
| Ø25 / Ø12 | 378 | 378 | 756 | 1133 | 34.4 | 7.6 | 1.51 |
| Ø28 / Ø14 | 462 | 462 | 924 | 1385 | 28.1 | 9.2 | 1.85 |
| Ø32 / Ø16 | 603 | 603 | 1206 | 1810 | 21.6 | 12.1 | 2.41 |

### Presión de pilotaje necesaria para F_resorte = 250 N + fricción 50 N (margen ×1.3)

| Camisa Ø / vástago Ø | Área (mm²) | p mínima (bar) | p con margen (bar) | Uso del rango 0–20 bar | Uso del rango 0–35 bar |
|---|---|---|---|---|---|
| Ø20 / Ø10 | 236 | 12.7 | 16.6 | 83 % | 47 % |
| Ø25 / Ø12 | 378 | 7.9 | 10.3 | 52 % | 29 % |
| Ø28 / Ø14 | 462 | 6.5 | 8.4 | 42 % | 24 % |
| Ø32 / Ø16 | 603 | 5.0 | 6.5 | 32 % | 18 % |

### Potencia disipada por el bloque de contrapresión (modo remoto activo, distribuidor en neutro)

| Caudal bomba (L/min) | 20 bar (kW) | 25 bar (kW) | 30 bar (kW) |
|---|---|---|---|
| 30 | 1.0 | 1.2 | 1.5 |
| 45 | 1.5 | 1.9 | 2.2 |
| 60 | 2.0 | 2.5 | 3.0 |
| 80 | 2.7 | 3.3 | 4.0 |

### Verificación básica del cuerpo torneado Ø70 ext. / Ø32 interior

Espesor de pared: 19.0 mm. Tensión circunferencial aprox. σ = p·r/t (pared delgada, conservador).

| Presión (bar) | σ hoop (MPa) | Fuerza axial sobre tapa (kN) | FS vs C45 (σy≈350 MPa) | FS vs 6061-T6 (σy≈275 MPa) | FS vs 7075-T6 (σy≈500 MPa) |
|---|---|---|---|---|---|
| 30 | 2.5 | 2.4 | 139 | 109 | 198 |
| 40 | 3.4 | 3.2 | 104 | 82 | 148 |
| 100 | 8.4 | 8.0 | 42 | 33 | 59 |
| 350 | 29.5 | 28.1 | 12 | 9 | 17 |

Nota: la presión de 350 bar sólo se indica como caso de falla (reductora averiada). La válvula de seguridad del bloque debe impedir superar ~40 bar; los sellos y roscas de tapa se dimensionan para 40 bar de ensayo, no para 350 bar.
