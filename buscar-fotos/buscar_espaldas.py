#!/usr/bin/env python3
"""
Busca en un disco (o cualquier carpeta) las fotos donde dos o mas personas
aparecen DE ESPALDAS -- tipicamente un adulto y un nino caminando -- y reporta
en que carpetas estan concentradas.

Idea central: una foto "de espaldas" es aquella donde se detectan personas pero
NO se detectan caras. Sobre eso se agregan dos filtros opcionales:

  --referencia FOTO.jpg  ordena por parecido visual a una foto modelo
  --espalda-seca         descarta las que tienen mancha de humedad en la espalda

Salidas en la carpeta de resultados:
  candidatos.csv   todas las fotos candidatas, ordenadas por puntaje
  carpetas.csv     ranking de CARPETAS por cantidad de candidatos
  hoja_NNN.jpg     mosaicos para revisar rapido con la vista

Uso minimo:
    python buscar_espaldas.py --ruta E:\\Fotos --salida resultados

Uso recomendado (con la foto modelo guardada en el disco):
    python buscar_espaldas.py --ruta E:\\Fotos --salida resultados \
        --referencia modelo.jpg --espalda-seca

Requisitos:
    pip install opencv-python pillow numpy
Opcionales (mejoran mucho la precision):
    pip install ultralytics          # muy recomendado: detector bueno
    pip install pillow-heif          # solo si tienes fotos .HEIC del iPhone
"""

import argparse
import csv
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

import cv2
import numpy as np
from PIL import Image, ExifTags

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

EXTENSIONES = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp",
               ".bmp", ".tif", ".tiff"}

LADO_MAX = 960          # se reescala antes de analizar (velocidad)
_detectores = {}        # cache por proceso
_REFERENCIA = None      # histograma de la foto modelo (se fija por proceso)


# --------------------------------------------------------------------------
# Detectores
# --------------------------------------------------------------------------

def _cargar_detectores():
    """
    Carga una sola vez por proceso.

    Preferido: YOLOv8n-pose. Da los 17 puntos del cuerpo, entre ellos nariz,
    ojos y orejas, asi que dice directamente si cada persona mira a camara o
    esta de espaldas. Es mas fiable que detectar caras por separado.

    Respaldo: HOG (personas) + cascadas Haar (caras) de OpenCV. Ojo: OpenCV 5
    elimino los dos, asi que ahi este respaldo no existe.
    """
    if _detectores:
        return _detectores

    _detectores["modo"] = None

    try:
        from ultralytics import YOLO
        _detectores["pose"] = YOLO("yolov8n-pose.pt")
        _detectores["modo"] = "pose"
        return _detectores
    except Exception:
        pass

    try:
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        base = cv2.data.haarcascades
        frontal = cv2.CascadeClassifier(base + "haarcascade_frontalface_default.xml")
        perfil = cv2.CascadeClassifier(base + "haarcascade_profileface.xml")
        if not frontal.empty():
            _detectores["hog"] = hog
            _detectores["frontal"] = frontal
            _detectores["perfil"] = perfil
            _detectores["modo"] = "clasico"
    except Exception:
        pass

    return _detectores


def verificar_entorno():
    """Comprueba que haya detectores utilizables ANTES de recorrer el disco."""
    d = _cargar_detectores()
    if d["modo"] is None:
        sys.exit(
            "No hay detectores disponibles.\n\n"
            "Tu version de OpenCV (" + cv2.__version__ + ") no incluye los\n"
            "respaldos clasicos: HOG y las cascadas Haar se eliminaron en OpenCV 5.\n\n"
            "Instala el detector bueno (recomendado):\n"
            "    pip install ultralytics\n\n"
            "O baja OpenCV a la serie 4, que si trae los respaldos:\n"
            '    pip install "opencv-python<5"\n'
        )
    return d["modo"]


# Indices de los puntos del cuerpo en el formato COCO
NARIZ, OJO_IZQ, OJO_DER, OREJA_IZQ, OREJA_DER = 0, 1, 2, 3, 4
CONF_PUNTO = 0.5


def _centro_dentro(caja_chica, caja_grande):
    x, y, w, h = caja_chica
    cx, cy = x + w / 2, y + h / 2
    X, Y, W, H = caja_grande
    return X <= cx <= X + W and Y <= cy <= Y + H


def analizar_personas(img):
    """
    Devuelve una lista con una entrada por persona:
        {"caja": (x, y, w, h), "mira_a_camara": bool}
    """
    d = _cargar_detectores()

    if d["modo"] == "pose":
        personas = []
        for r in d["pose"].predict(img, conf=0.35, verbose=False):
            if r.keypoints is None or r.keypoints.conf is None:
                continue
            cajas = r.boxes.xyxy.cpu().numpy()
            confs = r.keypoints.conf.cpu().numpy()
            for caja, kp in zip(cajas, confs):
                x1, y1, x2, y2 = caja[:4]
                # Si se le ve la nariz, o los dos ojos, esta mirando hacia aca.
                # De espaldas solo suelen quedar visibles hombros y orejas.
                mira = (kp[NARIZ] > CONF_PUNTO or
                        (kp[OJO_IZQ] > CONF_PUNTO and kp[OJO_DER] > CONF_PUNTO))
                personas.append({
                    "caja": (int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
                    "mira_a_camara": bool(mira),
                })
        return personas

    # Respaldo clasico: personas por un lado, caras por otro, y se cruzan
    rects, _ = d["hog"].detectMultiScale(img, winStride=(8, 8),
                                         padding=(8, 8), scale=1.05)
    gris = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    caras = [tuple(int(v) for v in c) for c in
             d["frontal"].detectMultiScale(gris, 1.1, 5, minSize=(30, 30))]
    caras += [tuple(int(v) for v in c) for c in
              d["perfil"].detectMultiScale(gris, 1.1, 5, minSize=(30, 30))]

    personas = []
    for r in rects:
        caja = tuple(int(v) for v in r)
        personas.append({
            "caja": caja,
            "mira_a_camara": any(_centro_dentro(c, caja) for c in caras),
        })
    return personas


# --------------------------------------------------------------------------
# Mancha de humedad en la espalda
# --------------------------------------------------------------------------

def mancha_humeda(img, persona):
    """
    Estima que fraccion del torso se ve mojada.

    Una espalda mojada es una zona de la MISMA prenda notablemente mas oscura
    que el resto. Se mira el torso, se toma la luminosidad mediana como el tono
    "seco" de la prenda, y se mide cuanto del torso cae muy por debajo de ella.

    Devuelve 0.0 - 1.0. Es una estimacion, no un veredicto: con ropa estampada
    o con sombra fuerte se dispara. Sirve para ordenar, no para borrar.
    """
    x, y, w, h = persona
    # torso: franja vertical 15%-55% de la persona, 60% central del ancho
    ty0, ty1 = y + int(0.15 * h), y + int(0.55 * h)
    tx0, tx1 = x + int(0.20 * w), x + int(0.80 * w)
    alto, ancho = img.shape[:2]
    ty0, ty1 = max(0, ty0), min(alto, ty1)
    tx0, tx1 = max(0, tx0), min(ancho, tx1)
    if ty1 - ty0 < 20 or tx1 - tx0 < 20:
        return 0.0

    torso = img[ty0:ty1, tx0:tx1]
    lab = cv2.cvtColor(torso, cv2.COLOR_BGR2LAB)
    luz = cv2.GaussianBlur(lab[:, :, 0].astype(np.float32), (9, 9), 0)

    desv = float(np.std(luz))
    if desv < 4:                      # prenda pareja: no hay mancha
        return 0.0

    # Tono "seco" de la prenda: percentil alto, no la mediana. Si se usa la
    # mediana, una mancha que cubre mas de la mitad del torso arrastra la
    # referencia hacia abajo y la mancha se vuelve invisible al calculo.
    seco = float(np.percentile(luz, 70))
    fraccion = float((luz < seco - max(8.0, 0.9 * desv)).mean())

    # una mancha real ocupa una parte del torso, no casi todo ni casi nada
    if fraccion < 0.05 or fraccion > 0.75:
        return 0.0
    return round(fraccion, 3)


# --------------------------------------------------------------------------
# Parecido a una foto de referencia
# --------------------------------------------------------------------------

def histograma(img):
    """Descriptor de color simple (HSV, 3 bandas horizontales)."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    alto = hsv.shape[0]
    partes = []
    for i in range(3):
        banda = hsv[i * alto // 3:(i + 1) * alto // 3]
        h = cv2.calcHist([banda], [0, 1, 2], None, [16, 8, 8],
                         [0, 180, 0, 256, 0, 256])
        partes.append(cv2.normalize(h, h).flatten())
    return np.concatenate(partes)


def similitud(img, ref):
    if ref is None:
        return 0.0
    a, b = histograma(img), ref
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return round(float(np.dot(a, b) / denom), 3)


# --------------------------------------------------------------------------
# Puntaje
# --------------------------------------------------------------------------

def _centro_dentro(caja_chica, caja_grande):
    x, y, w, h = caja_chica
    cx, cy = x + w / 2, y + h / 2
    X, Y, W, H = caja_grande
    return X <= cx <= X + W and Y <= cy <= Y + H


def puntuar(personas):
    """
    0 a 100. Alto = probablemente varias personas de espaldas.
    Premia: >=2 de espaldas, nadie mirando a camara, y alturas distintas
    (patron adulto + nino).
    """
    if len(personas) < 2:
        return 0, "menos de 2 personas"

    mirando = [p for p in personas if p["mira_a_camara"]]
    de_espaldas = [p for p in personas if not p["mira_a_camara"]]
    if len(de_espaldas) < 2:
        return 0, f"{len(mirando)} mirando a camara"

    puntaje = 55
    razones = [f"{len(de_espaldas)} de espaldas"]

    if not mirando:
        puntaje += 25
        razones.append("nadie mirando a camara")
    else:
        puntaje -= 12 * len(mirando)
        razones.append(f"{len(mirando)} mirando a camara")

    alturas = sorted((p["caja"][3] for p in de_espaldas), reverse=True)[:2]
    if len(alturas) == 2 and alturas[0] > 0:
        razon = alturas[1] / alturas[0]
        if 0.45 <= razon <= 0.85:
            puntaje += 18
            razones.append(f"alturas tipo adulto+nino ({razon:.2f})")

    if len(personas) == 2:
        puntaje += 8
        razones.append("exactamente 2 personas")

    return max(0, min(100, puntaje)), "; ".join(razones)


# --------------------------------------------------------------------------
# Procesamiento de una imagen
# --------------------------------------------------------------------------

def fecha_exif(ruta):
    try:
        with Image.open(ruta) as im:
            exif = im.getexif()
            if exif:
                for tag, valor in exif.items():
                    if ExifTags.TAGS.get(tag) == "DateTimeOriginal":
                        return str(valor)
    except Exception:
        pass
    try:
        return datetime.fromtimestamp(
            os.path.getmtime(ruta)).strftime("%Y:%m:%d %H:%M:%S")
    except Exception:
        return ""


def cargar(ruta):
    with Image.open(ruta) as im:
        im = im.convert("RGB")
        escala = LADO_MAX / max(im.size)
        if escala < 1:
            im = im.resize((int(im.width * escala), int(im.height * escala)))
        return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def _init_proceso(ref):
    global _REFERENCIA
    _REFERENCIA = np.array(ref) if ref is not None else None


def procesar(ruta):
    try:
        img = cargar(ruta)
    except Exception as e:
        return {"ruta": ruta, "error": str(e), "puntaje": 0}

    personas = analizar_personas(img)
    puntaje, motivo = puntuar(personas)

    humedad = 0.0
    if personas and puntaje > 0:
        # se evalua sobre la persona de espaldas mas grande (el adulto)
        adulto = max((p for p in personas if not p["mira_a_camara"]),
                     key=lambda p: p["caja"][2] * p["caja"][3])
        humedad = mancha_humeda(img, adulto["caja"])

    return {
        "ruta": ruta,
        "carpeta": os.path.dirname(ruta),
        "puntaje": puntaje,
        "personas": len(personas),
        "de_espaldas": sum(1 for p in personas if not p["mira_a_camara"]),
        "mancha_humeda": humedad,
        "similitud": similitud(img, _REFERENCIA) if puntaje > 0 else 0.0,
        "motivo": motivo,
        "fecha": fecha_exif(ruta),
        "error": "",
    }


# --------------------------------------------------------------------------
# Hojas de contacto
# --------------------------------------------------------------------------

def hojas_de_contacto(resultados, salida, por_hoja=24, miniatura=320):
    cols = 6
    filas = por_hoja // cols
    hechas = []
    for n in range(0, len(resultados), por_hoja):
        lote = resultados[n:n + por_hoja]
        hoja = Image.new("RGB", (cols * miniatura, filas * miniatura), "white")
        for i, r in enumerate(lote):
            try:
                with Image.open(r["ruta"]) as im:
                    im = im.convert("RGB")
                    im.thumbnail((miniatura, miniatura))
                    hoja.paste(im, ((i % cols) * miniatura,
                                    (i // cols) * miniatura))
            except Exception:
                continue
        destino = os.path.join(salida, f"hoja_{n // por_hoja + 1:03d}.jpg")
        hoja.save(destino, quality=85)
        hechas.append(destino)
    return hechas


# --------------------------------------------------------------------------
# Principal
# --------------------------------------------------------------------------

def listar_imagenes(raiz):
    for carpeta, _, archivos in os.walk(raiz):
        for a in archivos:
            if os.path.splitext(a)[1].lower() in EXTENSIONES:
                yield os.path.join(carpeta, a)


def main():
    ap = argparse.ArgumentParser(
        description="Encuentra fotos con personas de espaldas.")
    ap.add_argument("--ruta", required=True,
                    help="Carpeta raiz a escanear (ej: E:\\ o /Volumes/Disco)")
    ap.add_argument("--salida", default="resultados",
                    help="Carpeta donde dejar los reportes")
    ap.add_argument("--umbral", type=int, default=55,
                    help="Puntaje minimo para considerar candidata (0-100)")
    ap.add_argument("--referencia", default="",
                    help="Foto modelo: ordena los candidatos por parecido")
    ap.add_argument("--espalda-seca", action="store_true",
                    help="Baja en el ranking las fotos con mancha de humedad")
    ap.add_argument("--procesos", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--limite", type=int, default=0,
                    help="Procesar solo las primeras N imagenes (para probar)")
    ap.add_argument("--sin-hojas", action="store_true",
                    help="No generar los mosaicos de revision")
    args = ap.parse_args()

    if not os.path.isdir(args.ruta):
        sys.exit(f"No existe la ruta: {args.ruta}")
    os.makedirs(args.salida, exist_ok=True)

    print(f"Detector: {verificar_entorno()}")

    ref = None
    if args.referencia:
        if not os.path.isfile(args.referencia):
            sys.exit(f"No existe la foto de referencia: {args.referencia}")
        ref = histograma(cargar(args.referencia)).tolist()
        print(f"Referencia cargada: {args.referencia}")

    cache_path = os.path.join(args.salida, "cache.json")
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)
        print(f"Reanudando: {len(cache)} imagenes ya analizadas.")

    print(f"Recorriendo {args.ruta} ...")
    imagenes = [p for p in listar_imagenes(args.ruta) if p not in cache]
    if args.limite:
        imagenes = imagenes[:args.limite]
    print(f"{len(imagenes)} imagenes nuevas por analizar "
          f"(con {args.procesos} procesos).")

    hecho = 0
    with ProcessPoolExecutor(max_workers=args.procesos,
                             initializer=_init_proceso,
                             initargs=(ref,)) as pool:
        futuros = {pool.submit(procesar, p): p for p in imagenes}
        for fut in as_completed(futuros):
            r = fut.result()
            cache[r["ruta"]] = r
            hecho += 1
            if hecho % 100 == 0:
                print(f"  {hecho}/{len(imagenes)}", flush=True)
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(cache, f)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f)

    candidatos = [r for r in cache.values() if r.get("puntaje", 0) >= args.umbral]

    def orden(r):
        v = r["puntaje"]
        if ref is not None:
            v += 40 * r.get("similitud", 0.0)      # parecido a la foto modelo
        if args.espalda_seca:
            v -= 60 * r.get("mancha_humeda", 0.0)  # castiga espalda mojada
        return -v

    candidatos.sort(key=orden)

    campos = ["puntaje", "similitud", "mancha_humeda", "ruta", "carpeta",
              "personas", "de_espaldas", "fecha", "motivo"]
    with open(os.path.join(args.salida, "candidatos.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(candidatos)

    por_carpeta = {}
    for r in candidatos:
        d = por_carpeta.setdefault(r["carpeta"],
                                   {"candidatos": 0, "mejor": 0, "ejemplo": ""})
        d["candidatos"] += 1
        if r["puntaje"] > d["mejor"]:
            d["mejor"] = r["puntaje"]
            d["ejemplo"] = os.path.basename(r["ruta"])

    ranking = sorted(por_carpeta.items(),
                     key=lambda kv: (-kv[1]["candidatos"], -kv[1]["mejor"]))
    with open(os.path.join(args.salida, "carpetas.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["candidatos", "mejor_puntaje", "carpeta", "ejemplo"])
        for carpeta, d in ranking:
            w.writerow([d["candidatos"], d["mejor"], carpeta, d["ejemplo"]])

    if not args.sin_hojas and candidatos:
        hojas = hojas_de_contacto(candidatos[:240], args.salida)
        print(f"\n{len(hojas)} hojas de contacto en {args.salida}/")

    print(f"\n{len(candidatos)} fotos candidatas de {len(cache)} analizadas.")
    print("\nCARPETAS DONDE BUSCAR (las 20 primeras):")
    print(f"{'Fotos':>6}  {'Mejor':>5}  Carpeta")
    for carpeta, d in ranking[:20]:
        print(f"{d['candidatos']:>6}  {d['mejor']:>5}  {carpeta}")
    print(f"\nDetalle completo: {args.salida}/candidatos.csv y carpetas.csv")


if __name__ == "__main__":
    main()
