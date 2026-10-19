# Buscar fotos "de espaldas" en un disco externo

Encuentra las fotos donde dos o más personas aparecen **de espaldas** — el caso
típico: un adulto y un niño caminando de la mano — y te dice **en qué carpetas
están**, para que vayas directo a buscarlas.

## Qué hace

Recorre todo el disco, y por cada imagen:

1. Detecta **personas**.
2. Detecta **caras**.
3. Si hay 2 o más personas y **ninguna cara visible**, la marca como candidata.
4. Sube el puntaje si las dos figuras principales tienen alturas distintas
   (patrón adulto + niño).

Y opcionalmente:

- `--referencia FOTO.jpg` — ordena los resultados por **parecido visual** a una
  foto modelo tuya (mismo tipo de escena, colores, encuadre).
- `--espalda-seca` — baja en el ranking las fotos con **mancha de humedad** en
  la espalda.

## Instalación

```bash
pip install opencv-python pillow numpy
pip install ultralytics mediapipe          # muy recomendado: mucho mejor precisión
pip install pillow-heif                    # solo si tienes fotos .HEIC del iPhone
```

**Importante:** si tienes OpenCV 5, `ultralytics` y `mediapipe` no son
opcionales. OpenCV 5 eliminó los detectores clásicos (HOG y las cascadas Haar),
así que sin ellos el programa no tiene con qué detectar. El script te lo avisa
al arrancar, antes de ponerse a recorrer el disco.

## Uso

Lo mínimo:

```bash
python buscar_espaldas.py --ruta E:\Fotos --salida resultados
```

Recomendado — primero guarda tu foto modelo (la de referencia) en el disco:

```bash
python buscar_espaldas.py --ruta E:\Fotos --salida resultados \
    --referencia modelo.jpg --espalda-seca
```

En Mac o Linux la ruta se ve así: `--ruta /Volumes/MiDisco`

Primero pruébalo con poquitas fotos para ver que todo corre bien:

```bash
python buscar_espaldas.py --ruta E:\Fotos --salida prueba --limite 200
```

## Qué te entrega

En la carpeta de resultados:

| Archivo | Para qué sirve |
|---|---|
| `carpetas.csv` | **Lo que pediste:** ranking de carpetas por cantidad de candidatas |
| `candidatos.csv` | Cada foto candidata con su puntaje, ruta, fecha y motivo |
| `hoja_001.jpg`, … | Mosaicos de 24 fotos para revisar de un vistazo |
| `cache.json` | Permite cortar el escaneo y reanudarlo después sin repetir trabajo |

Además imprime en pantalla las 20 carpetas con más candidatas.

## Opciones

| Opción | Qué hace |
|---|---|
| `--ruta` | Carpeta raíz a escanear (obligatoria) |
| `--salida` | Dónde dejar los reportes (por defecto `resultados`) |
| `--umbral` | Puntaje mínimo, 0 a 100 (por defecto 55). Bájalo si salen pocas |
| `--referencia` | Foto modelo para ordenar por parecido |
| `--espalda-seca` | Castiga las fotos con mancha de humedad en la espalda |
| `--limite` | Analiza solo las primeras N imágenes (para probar) |
| `--procesos` | Procesos en paralelo (por defecto, núcleos − 1) |
| `--sin-hojas` | No generar los mosaicos |

## Cosas que conviene saber

- **Se puede interrumpir.** Corta con Ctrl+C y vuelve a lanzar el mismo comando:
  retoma donde iba gracias a `cache.json`.
- **El filtro de humedad es aproximado**, no un veredicto. Mide qué parte del
  torso se ve claramente más oscura que el resto de la prenda. Con ropa
  estampada o con sombra fuerte se equivoca. Úsalo para ordenar, y decide tú
  mirando las hojas de contacto.
- **Velocidad:** con YOLO, del orden de 10–30 fotos por segundo según el equipo.
  Unas 50.000 fotos es cosa de una o dos horas.
- **Da falsos positivos**, a propósito. Prefiere mostrarte de más a que se te
  escape la foto que buscas. Por eso existen los mosaicos.
