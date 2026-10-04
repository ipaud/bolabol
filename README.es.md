<p align="center"><img src="docs/images/logo.png" alt="BolaBol" width="320"></p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ca.md">Català</a> · <b>Español</b>
</p>

# BolaBol: gachapon con moneda, imprimible en 3D

Máquina de cápsulas sorpresa totalmente imprimible en 3D. Mete una ficha impresa, gira la manivela y cae una cápsula de 50 mm.
Diseño paramétrico generado con código Python/Blender, con STL y camas listas para una impresora de 220 × 220 mm.

<p align="center"><img src="docs/images/v4_duo.jpg" alt="BolaBol de una moneda (menta) y de dos (azul cielo)" width="720"></p>

<p align="center"><img src="docs/images/explode.gif" alt="Animación del despiece" width="400"></p>

## Características

- Cápsula de **50 × 54 mm**, en dos piezas, también imprimible; caben **10**.
- **Con ficha**: rueda de monedas + trinquete de bloqueo + gatillo. La manivela solo da la vuelta si hay una ficha de 25 × 4 mm. Validado con una simulación dinámica de ~200 casos (`codi/gacha/coin_battery.py`).
- Dos versiones: **1 moneda** (menta) y **2 monedas** (azul cielo, en `2monedes/`).
- **Casi todo en PETG**, más ventanas de acrílico (corte láser o lámina transparente) y tornillos M3. Mira [`BOM.md`](BOM.md).
- Piezas de prueba (engranajes, monedero) para validar tu impresora antes de hacer la máquina entera.

## Blueprint

<p align="center"><a href="docs/blueprints/blueprint-bb01.jpg"><img src="docs/blueprints/blueprint-bb01.jpg" alt="Blueprint técnico BB-01" width="720"></a></p>

Fichas técnicas en [`docs/blueprints/`](docs/blueprints): blueprint general, despiece completo con ferretería y ficha de la máquina y la moneda. Kit de marca (logo, paleta, tipografía, mascota, colores) en [`docs/brand/`](docs/brand).
Son ilustraciones de comunicación. **[`BOM.md`](BOM.md) y los STL son la fuente de verdad** para medidas y ferretería; el panel de "funcionamiento" del blueprint está simplificado (la máquina real es puramente mecánica: sin microinterruptor ni sensor).

## Qué hay

| Ruta | Contenido |
|---|---|
| [`imprimir/`](imprimir) | Cada pieza ya orientada para imprimir, y en [`imprimir/llits/`](imprimir/llits) las **20 camas** listas (3MF, Flash Forge AD5M Pro / Flash Studio) |
| [`stl/`](stl) | Cada pieza tal como está en el modelo, pruebas en `stl/proves/`, la insignia en `bolabol_logo.3mf` |
| [`2monedes/`](2monedes) | Las 3 piezas que cambian en la versión de 2 monedas |
| `BolaBol-v1*.blend` | Modelos de Blender: 1 moneda, 2 monedas, y las dos juntas |
| [`codi/`](codi) | El código Python que genera el modelo (`gacha/`) y traza los logos (`brand/`) |
| [`docs/`](docs) | Renders e imágenes del montaje paso a paso de las pruebas |
| [`BOM.md`](BOM.md), [`BOM_2monedes.md`](BOM_2monedes.md) | Lista de piezas, orientación, ferretería y cambios del diseño (en catalán) |

## Cómo hacerla

1. **Imprime primero las piezas de prueba** (`stl/proves/`) con tu impresora y material. Si los engranajes engranan y el trinquete bloquea a mano, la máquina entera también funcionará. Imágenes del montaje: [`docs/assembly/`](docs/assembly).
2. Imprime las piezas: usa las camas de `imprimir/llits/` o los STL de `imprimir/`. Colores y cantidades en [`BOM.md`](BOM.md).
3. Reúne la ferretería (tornillos M3, muelle de bolígrafo, lastre de 500 g, 4 cristales de acrílico…), también en [`BOM.md`](BOM.md).
4. Imprime **30 fichas** (`imprimir/llits/llit_19_monedes.3mf`, unas 3 h).
5. Monta. El orden y los detalles de fijación están en el BOM; los modelos 3D muestran cómo encaja cada pieza.

## Regenerar / modificar el modelo

Necesitas [Blender](https://www.blender.org/) (desarrollado con 5.1) y Python con `numpy`; el trazado de logos necesita `Pillow` y `potrace`. El código se ejecuta dentro de Blender:

```python
import sys; sys.path.insert(0, "codi/gacha")
import build; build.main()                 # máquina de 1 moneda
# build.main(coins=2)                      # máquina de 2 monedas
```

Todas las medidas están en [`codi/gacha/params.py`](codi/gacha/params.py). `export.py` escribe los STL y comprueba que caben en la cama y que son manifold. `print3mf.py` crea las camas y necesita el addon FlashPrep (no incluido).

## Licencia

[Creative Commons Atribución-NoComercial-CompartirIgual 4.0](LICENSE) (CC BY-NC-SA 4.0). Puedes compartir y remezclar dando crédito, sin uso comercial y con la misma licencia. BolaBol, Boli, BBOL y los logos son obra original de Pau Avila.

¿Dudas o una impresión que enseñar? Abre un issue.
