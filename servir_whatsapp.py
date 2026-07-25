"""
Deja el canal WhatsApp TOTALMENTE listo para que un chatbot externo se enlace.

Arranca y mantiene vivo:
  - el agente (Flask, puerto 5000)
  - el tunel publico (localtunnel, URL fija: https://haceb-agente.loca.lt)

Si alguno se cae, lo reinicia solo. Muestra la URL en grande. No necesitas saber
de WhatsApp: tu compañero apunta su chatbot a esa URL (ver whatsapp-bot/CONECTAR.md).

    python servir_whatsapp.py        (o doble clic en servir_whatsapp.bat)

Deja la ventana abierta. Para apagar todo, cierra la ventana o Ctrl+C.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
SUBDOMINIO = "haceb-agente"
URL = f"https://{SUBDOMINIO}.loca.lt"
PUERTO = 5000


def log(msg: str) -> None:
    print(msg, flush=True)


def agente_sano() -> bool:
    try:
        with urllib.request.urlopen(f"http://localhost:{PUERTO}/", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def lanzar_agente() -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", "channels.whatsapp"],
        cwd=RAIZ,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def lanzar_tunel() -> subprocess.Popen:
    # npx en Windows es npx.cmd; shell=True lo resuelve en cualquier sistema.
    return subprocess.Popen(
        f"npx --yes localtunnel --port {PUERTO} --subdomain {SUBDOMINIO}",
        cwd=RAIZ,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def tunel_responde() -> bool:
    try:
        req = urllib.request.Request(
            f"{URL}/",
            headers={"bypass-tunnel-reminder": "1", "User-Agent": "haceb-check"},
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status == 200
    except Exception:
        return False


def main() -> None:
    linea = "=" * 56
    log(linea)
    log("  Canal WhatsApp del agente Haceb  —  dejando todo listo")
    log(linea)

    # 1) Agente
    agente = None
    if agente_sano():
        log("  [1/2] Agente ya estaba corriendo (puerto 5000). OK.")
    else:
        log("  [1/2] Iniciando el agente...")
        agente = lanzar_agente()
        for _ in range(20):
            time.sleep(1)
            if agente_sano():
                break
        log("        Agente listo." if agente_sano() else
            "        ! El agente no respondio; revisa el .env (GOOGLE/GROQ/OLLAMA).")

    # 2) Tunel
    log("  [2/2] Abriendo el tunel publico...")
    tunel = lanzar_tunel()
    ok = False
    for _ in range(20):
        time.sleep(1.5)
        if tunel_responde():
            ok = True
            break

    log("")
    if ok:
        log("  >>> TODO LISTO. Pasa esta URL a tu compañero para el enlace:")
        log("")
        log(f"        {URL}/message")
        log("")
        log("      (contrato de la API: whatsapp-bot/CONECTAR.md)")
    else:
        log("  ! El tunel no confirmo todavia. La URL sera:")
        log(f"        {URL}/message")
        log("    Si no responde en 1 min, cierra y vuelve a abrir este lanzador.")
    log("")
    log("  Deja esta ventana ABIERTA. Se reinicia solo si algo se cae.")
    log(linea)

    # Supervision: mantener vivos agente y tunel.
    try:
        while True:
            time.sleep(6)
            if not agente_sano():
                log("  ! Agente caido. Reiniciando...")
                agente = lanzar_agente()
                time.sleep(5)
            if tunel.poll() is not None:
                log("  ! Tunel caido. Reiniciando (misma URL)...")
                tunel = lanzar_tunel()
                time.sleep(5)
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
