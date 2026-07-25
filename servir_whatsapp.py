"""
Deja el canal WhatsApp TOTALMENTE listo para que un chatbot externo se enlace.

Arranca y mantiene vivo:
  - el agente (Flask, puerto 5000)
  - un tunel publico con Cloudflare (cloudflared), estable y gratis

Muestra la URL publica en grande. Si algo se cae, lo reinicia solo. No necesitas
saber de WhatsApp: tu compañero apunta su chatbot a esa URL
(contrato: whatsapp-bot/CONECTAR.md).

    python servir_whatsapp.py        (o doble clic en servir_whatsapp.bat)

Deja la ventana abierta. Para apagar todo, cierra la ventana o Ctrl+C.

Nota: cloudflared da una URL nueva cada vez que arranca (https://algo.trycloudflare.com).
El lanzador la muestra; pasasela a tu compañero. Mientras la ventana siga abierta,
la URL no cambia.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
PUERTO = 5000
CF_BIN = os.path.join(RAIZ, "bin", "cloudflared.exe")
CF_URL_DESCARGA = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    "cloudflared-windows-amd64.exe"
)
CF_LOG = os.path.join(RAIZ, "bin", "_cf_output.log")
RE_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def log(msg: str) -> None:
    print(msg, flush=True)


# --- Agente -----------------------------------------------------------------

def agente_sano() -> bool:
    try:
        with urllib.request.urlopen(f"http://localhost:{PUERTO}/", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def lanzar_agente() -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", "channels.whatsapp"],
        cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


# --- Tunel (cloudflared) ----------------------------------------------------

def asegurar_cloudflared() -> bool:
    if os.path.exists(CF_BIN):
        return True
    log("  cloudflared no está; descargándolo (una sola vez, ~50 MB)...")
    os.makedirs(os.path.dirname(CF_BIN), exist_ok=True)
    try:
        urllib.request.urlretrieve(CF_URL_DESCARGA, CF_BIN)
        return os.path.exists(CF_BIN)
    except Exception as e:
        log(f"  ! No pude descargar cloudflared: {e}")
        return False


def lanzar_tunel() -> subprocess.Popen:
    f = open(CF_LOG, "w", encoding="utf-8", errors="replace")
    return subprocess.Popen(
        [CF_BIN, "tunnel", "--url", f"http://localhost:{PUERTO}"],
        cwd=RAIZ, stdout=f, stderr=subprocess.STDOUT,
    )


def leer_url(espera_seg: int = 30) -> str | None:
    for _ in range(espera_seg * 2):
        time.sleep(0.5)
        try:
            with open(CF_LOG, encoding="utf-8", errors="replace") as fh:
                m = RE_URL.search(fh.read())
                if m:
                    return m.group(0)
        except FileNotFoundError:
            pass
    return None


# --- Principal --------------------------------------------------------------

def mostrar_listo(url: str) -> None:
    linea = "=" * 60
    log("")
    log(linea)
    log("  >>> CANAL WHATSAPP LISTO")
    log("")
    log("  URL para tu compañero (su chatbot hace POST aquí):")
    log(f"        {url}/message")
    log("")
    log("  Para probarlo TÚ ahora mismo, abre en el navegador:")
    log(f"        {url}/demo")
    log("")
    log("  Contrato de la API: whatsapp-bot/CONECTAR.md")
    log("  Deja esta ventana ABIERTA. Se reinicia solo si algo se cae.")
    log(linea)
    log("")


def main() -> None:
    log("=" * 60)
    log("  Canal WhatsApp del agente Haceb  —  dejando todo listo")
    log("=" * 60)

    # 1) Agente
    agente = None
    if agente_sano():
        log("  [1/2] Agente ya estaba corriendo (puerto 5000). OK.")
    else:
        log("  [1/2] Iniciando el agente...")
        agente = lanzar_agente()
        for _ in range(25):
            time.sleep(1)
            if agente_sano():
                break
        log("        Agente listo." if agente_sano() else
            "        ! El agente no respondió; revisa el .env.")

    # 2) Tunel
    log("  [2/2] Abriendo el túnel público (Cloudflare)...")
    if not asegurar_cloudflared():
        log("  ! Sin cloudflared no hay URL pública. Descárgalo manualmente en bin/.")
        return
    tunel = lanzar_tunel()
    url = leer_url()
    if url:
        mostrar_listo(url)
    else:
        log("  ! El túnel no dio URL a tiempo. Reintentando en el bucle...")

    # Supervisión
    try:
        while True:
            time.sleep(6)
            if not agente_sano():
                log("  ! Agente caído. Reiniciando...")
                agente = lanzar_agente()
                time.sleep(5)
            if tunel.poll() is not None:
                log("  ! Túnel caído. Reiniciando...")
                tunel = lanzar_tunel()
                nueva = leer_url()
                if nueva and nueva != url:
                    url = nueva
                    log("  (nueva URL tras reinicio)")
                    mostrar_listo(url)
    except KeyboardInterrupt:
        log("\n  Apagando canal WhatsApp...")
    finally:
        for p in (agente, tunel):
            if p is not None:
                try:
                    p.terminate()
                except Exception:
                    pass


if __name__ == "__main__":
    main()
