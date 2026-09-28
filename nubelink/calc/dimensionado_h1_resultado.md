# Dimensionado preliminar Nubelink H1

### Fuerza y caudal por opción de pistón (vástago pasante)

| Camisa Ø / vástago Ø | Área útil (mm²) | F @ 10 bar (N) | F @ 20 bar (N) | F @ 30 bar (N) | Vol. neutro→tope 20 mm (cm³) | Caudal para 0.3 s (L/min) |
|---|---|---|---|---|---|---|
| Ø20 / Ø10 | 236 | 236 | 471 | 707 | 4.7 | 0.94 |
| Ø25 / Ø12 | 378 | 378 | 756 | 1133 | 7.6 | 1.51 |
| Ø32 / Ø16 | 603 | 603 | 1206 | 1810 | 12.1 | 2.41 |

### Presión de pilotaje necesaria para F_resorte = 200 N + fricción 40 N (margen ×1.3)

| Camisa Ø / vástago Ø | Área (mm²) | p mínima (bar) | p con margen (bar) | Uso del rango 0–20 bar | Uso del rango 0–35 bar |
|---|---|---|---|---|---|
| Ø20 / Ø10 | 236 | 10.2 | 13.2 | 66 % | 38 % |
| Ø25 / Ø12 | 378 | 6.4 | 8.3 | 41 % | 24 % |
| Ø32 / Ø16 | 603 | 4.0 | 5.2 | 26 % | 15 % |

### Potencia disipada por el bloque de contrapresión (modo remoto activo, distribuidor en neutro)

| Caudal bomba (L/min) | 20 bar (kW) | 25 bar (kW) | 30 bar (kW) |
|---|---|---|---|
| 30 | 1.0 | 1.2 | 1.5 |
| 45 | 1.5 | 1.9 | 2.2 |
| 60 | 2.0 | 2.5 | 3.0 |
| 80 | 2.7 | 3.3 | 4.0 |

### Verificación básica del cuerpo torneado Ø60 ext. / Ø25 interior

Espesor de pared: 17.5 mm. Tensión circunferencial aprox. σ = p·r/t (pared delgada, conservador).

| Presión (bar) | σ hoop (MPa) | Fuerza axial sobre tapa (kN) | FS vs C45 (σy≈350 MPa) | FS vs 6061-T6 (σy≈275 MPa) | FS vs 7075-T6 (σy≈500 MPa) |
|---|---|---|---|---|---|
| 30 | 2.1 | 1.5 | 163 | 128 | 233 |
| 40 | 2.9 | 2.0 | 122 | 96 | 175 |
| 100 | 7.1 | 4.9 | 49 | 38 | 70 |
| 350 | 25.0 | 17.2 | 14 | 11 | 20 |

Nota: la presión de 350 bar sólo se indica como caso de falla (reductora averiada). La válvula de seguridad del bloque debe impedir superar ~40 bar; los sellos y roscas de tapa se dimensionan para 40 bar de ensayo, no para 350 bar.
