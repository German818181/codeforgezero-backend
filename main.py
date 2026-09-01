import os
import time
import tracemalloc
import gc
import json
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from sandbox import probar_codigo_aislado
import os
import requests
from fastapi import APIRouter, Request, Header, HTTPException
import hmac
import hashlib
import json
from github import Github, Auth

# Tus credenciales desde las Variables de Entorno de Render
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

# Si no encuentra el secreto en las variables, poné el tuyo por defecto para pruebas
if not GITHUB_WEBHOOK_SECRET:
    GITHUB_WEBHOOK_SECRET = "wqguf280@d398j92k3i2oqwk,@k3210d209k" 

@app.post("/api/webhook")
async def procesar_webhook_github(request: Request, x_hub_signature_256: str = Header(None)):
    payload_body = await request.body()
    
    # 1. Seguridad (Verificamos que sea GitHub)
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Falta firma")
        
    hash_esperado = "sha256=" + hmac.new(GITHUB_WEBHOOK_SECRET.encode(), payload_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(hash_esperado, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Firma inválida")

    data = json.loads(payload_body)
    action = data.get("action")
    
    # 2. Solo actuamos si abren o actualizan un PR
    if "pull_request" in data and action in ["opened", "synchronize"]:
        repo_nombre = data["repository"]["full_name"]
        pr_numero = data["pull_request"]["number"]
        
        # El ID de instalación es CLAVE: le dice a GitHub en qué cuenta específica está instalado tu bot
        installation_id = data["installation"]["id"]
        
        print(f"🚀 Iniciando análisis para {repo_nombre} | PR #{pr_numero}")

        try:
            # 3. Autenticación de tu App
            auth = Auth.AppAuth(GITHUB_APP_ID, GITHUB_PRIVATE_KEY)
            
            # Pedimos el "pase temporal" para este repo en particular
            token_instalacion = auth.get_installation_auth(installation_id).token
            
            # 4. Descargar el Diff (Las líneas modificadas)
            # Usamos la API de GitHub pidiéndole específicamente el formato "diff"
            url_pr_api = data["pull_request"]["url"]
            headers = {
                "Authorization": f"Bearer {token_instalacion}",
                "Accept": "application/vnd.github.v3.diff" # Esto es magia: nos da solo los cambios
            }
            
            respuesta = requests.get(url_pr_api, headers=headers)
            diff_codigo = respuesta.text
            
            print("✅ Diff descargado con éxito. Cantidad de caracteres:", len(diff_codigo))
            
            # --- AQUÍ VA LA CONEXIÓN CON NEMOTRON Y EL COLISEO ---
            # texto_optimizado = enviar_a_nemotron(diff_codigo)
            
            return {"status": "procesando", "mensaje": "Código descargado"}

        except Exception as e:
            print(f"❌ Error al descargar el código: {e}")
            raise HTTPException(status_code=500, detail="Error interno del bot")
            
    return {"status": "ignorado", "mensaje": "No es un evento de PR relevante"}

load_dotenv()

# --- NUEVO MOTOR: Conexión a OpenRouter ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

app = FastAPI(title="CodeForgeZero Engine - V8 (Corridas Adaptativas)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UMBRAL_AHORRO_MINIMO = 5.0
CORRIDAS = 5

class PeticionOptimizacion(BaseModel):
    codigo_sucio: str
    archivo: str = "landing_directo"
    repositorio: str = "prueba_manual"

def guardar_en_supabase(archivo, repositorio, ahorro_ram, ahorro_cpu, ya_optimizado, metricas_disponibles, metodo_usado):
    """
    Guarda un registro del análisis en la tabla 'analisis' de Supabase.
    Nunca lanza excepciones hacia afuera — si falla, solo lo loguea,
    para que un problema de historial no rompa la respuesta al cliente.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("⚠️ Supabase no configurado (faltan variables de entorno) — se omite el guardado de historial.")
        return

    try:
        url = f"{SUPABASE_URL}/rest/v1/analisis"
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        payload = {
            "archivo": archivo,
            "repositorio": repositorio,
            "ahorro_ram": ahorro_ram,
            "ahorro_cpu": ahorro_cpu,
            "ya_optimizado": ya_optimizado,
            "metricas_disponibles": metricas_disponibles,
            "metodo_usado": metodo_usado,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code in (200, 201):
            print("💾 Análisis guardado en historial (Supabase).")
        else:
            print(f"⚠️ No se pudo guardar en Supabase: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"⚠️ Error guardando en Supabase: {e}")

def medir_codigo_promedio(funcion_a_medir, nombre_version, corridas_max=CORRIDAS):
    """
    Mide rendimiento varias veces y promedia.
    Incluye una corrida de "warmup" que además sirve para decidir CUÁNTAS
    mediciones reales hacer: código lento necesita menos repeticiones
    (el ruido relativo ya es bajo), código rápido necesita más.
    Retorna (rams_promedio, tiempos_promedio, error_import)
    Si hay un ImportError, retorna (0, 0, nombre_modulo_faltante)
    """
    rams = []
    tiempos = []
    modulo_faltante = None

    # --- Warmup: se ejecuta una vez, se descarta, y su duración decide las corridas ---
    inicio_warmup = time.perf_counter()
    try:
        funcion_a_medir()
    except ModuleNotFoundError as e:
        modulo_faltante = str(e).replace("No module named ", "").strip("'")
        print(f"⚠️ Librería externa no disponible en sandbox ({nombre_version}): {modulo_faltante}")
        return 0.0, 0.0, modulo_faltante
    except Exception as e:
        print(f"Error en warmup {nombre_version}: {e}")
    duracion_warmup = time.perf_counter() - inicio_warmup

    # Código lento -> menos corridas (el ruido relativo ya es bajo, y cuesta caro repetir)
    # Código rápido -> las corridas_max completas (necesita repetición para vencer el ruido)
    if duracion_warmup > 3.0:
        corridas = 2
    elif duracion_warmup > 1.0:
        corridas = 3
    else:
        corridas = corridas_max

    print(f"⏱️ Warmup de {nombre_version}: {duracion_warmup:.2f}s -> usando {corridas} corridas")

    # --- Mediciones reales ---
    for i in range(corridas):
        gc.collect()
        tracemalloc.clear_traces()
        tracemalloc.start()

        inicio_tiempo = time.perf_counter()
        try:
            funcion_a_medir()
        except ModuleNotFoundError as e:
            tracemalloc.stop()
            modulo_faltante = str(e).replace("No module named ", "").strip("'")
            print(f"⚠️ Librería externa no disponible en sandbox ({nombre_version}): {modulo_faltante}")
            return 0.0, 0.0, modulo_faltante
        except Exception as e:
            print(f"Error en ejecución {nombre_version} (corrida {i+1}): {e}")

        fin_tiempo = time.perf_counter()
        _, pico_memoria = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        rams.append(pico_memoria / (1024 * 1024))
        tiempos.append(fin_tiempo - inicio_tiempo)

    if not rams:
        return 0.0, 0.0, None

    return sum(rams) / len(rams), sum(tiempos) / len(tiempos), None

@app.post("/api/optimize")
async def optimizar_codigo(peticion: PeticionOptimizacion):
    print(f"🚀 Conectando a OpenRouter (GLM) - V8 Honest Metrics...")

    instruccion_sistema = f"""
Eres CodeForgeZero, un Arquitecto de Software Senior experto en optimización de rendimiento.
Tu trabajo es refactorizar código Python para mejorar su eficiencia real en RAM y CPU.

REGLAS CRÍTICAS:
1. Mantené exactamente los mismos nombres de funciones, clases y parámetros públicos del código original.
2. Si el código ya está bien optimizado y tus cambios generarían menos de {UMBRAL_AHORRO_MINIMO}% de mejora real, devolvé el código ORIGINAL sin modificar y explicalo en el reporte.
3. Generá un campo "codigo_test": un bloque Python que instancie las clases e invoque las funciones principales con datos de ejemplo representativos. Usá entre 1500 y 3000 elementos cuando la estructura lo permita — suficiente para que las diferencias reales de rendimiento sean medibles, sin ser tan grande que vuelva lenta la ejecución en casos con complejidad alta (O(n²) o peor). No debe imprimir nada ni usar assertions que puedan fallar.
4. El campo "codigo_optimizado" debe ser el código completo, listo para ejecutar.

DEBES responder EXCLUSIVAMENTE con un JSON válido con esta estructura, sin texto extra, sin markdown:
{{
    "codigo_optimizado": "string con el código completo",
    "codigo_test": "string con el arnés de pruebas",
    "ya_optimizado": false,
    "reporte": "explicación de qué se cambió y por qué",
    "metricas": {{"metodo_usado": "explicación técnica del método de optimización aplicado"}}
}}
"""

    try:
        respuesta = client.chat.completions.create(
            # OJO ACÁ: Si en OpenRouter el ID exacto es otro, cambialo.
            model="nvidia/nemotron-3-ultra-550b-a55b:free", 
            messages=[
                {"role": "system", "content": instruccion_sistema},
                {"role": "user", "content": peticion.codigo_sucio}
            ],
            temperature=0.1,
            timeout=45.0
        )

        texto_ia = respuesta.choices[0].message.content.strip()

        if texto_ia.startswith("```json"):
            texto_ia = texto_ia.replace("```json", "", 1)
        if texto_ia.endswith("```"):
            texto_ia = texto_ia.rsplit("```", 1)[0]

        datos_ia = json.loads(texto_ia.strip())
        codigo_test = datos_ia.get("codigo_test", "")

        def test_original():
            ns = {}
            exec(peticion.codigo_sucio, ns)
            exec(codigo_test, ns)

        def test_optimizado():
            ns = {}
            exec(datos_ia.get("codigo_optimizado", ""), ns)
            exec(codigo_test, ns)

        print("📊 Midiendo rendimiento original...")
        ram_mala, tiempo_malo, error_original = medir_codigo_promedio(test_original, "Original")

        print("📊 Midiendo rendimiento optimizado...")
        ram_buena, tiempo_bueno, error_optimizado = medir_codigo_promedio(test_optimizado, "Optimizado")

        # Detectar si hubo imports externos no disponibles
        modulo_faltante = error_original or error_optimizado
        metricas_disponibles = modulo_faltante is None

        if "metricas" not in datos_ia:
            datos_ia["metricas"] = {}

        if metricas_disponibles:
            ahorro_ram = ((ram_mala - ram_buena) / ram_mala * 100) if ram_mala > 0 else 0.0
            ahorro_tiempo = ((tiempo_malo - tiempo_bueno) / tiempo_malo * 100) if tiempo_malo > 0 else 0.0

            ahorro_ram_final = max(round(ahorro_ram, 1), 0.0) if ahorro_ram >= UMBRAL_AHORRO_MINIMO else 0.0
            ahorro_tiempo_final = max(round(ahorro_tiempo, 1), 0.0) if ahorro_tiempo >= UMBRAL_AHORRO_MINIMO else 0.0
            ya_optimizado = datos_ia.get("ya_optimizado", False) or (ahorro_ram_final == 0.0 and ahorro_tiempo_final == 0.0)

            datos_ia["metricas"]["porcentaje_ahorro_ram"] = ahorro_ram_final
            datos_ia["metricas"]["porcentaje_ahorro_cpu"] = ahorro_tiempo_final
            datos_ia["metricas"]["tiempo_original_seg"] = round(tiempo_malo, 6)
            datos_ia["metricas"]["tiempo_optimizado_seg"] = round(tiempo_bueno, 6)
            datos_ia["metricas"]["ya_optimizado"] = ya_optimizado
            datos_ia["metricas"]["metricas_disponibles"] = True
            datos_ia["metricas"]["mensaje_metricas"] = None

            print(f"✅ RAM: {ahorro_ram_final}% | CPU: {ahorro_tiempo_final}% | Ya optimizado: {ya_optimizado}")

            guardar_en_supabase(
                archivo=peticion.archivo,
                repositorio=peticion.repositorio,
                ahorro_ram=ahorro_ram_final,
                ahorro_cpu=ahorro_tiempo_final,
                ya_optimizado=ya_optimizado,
                metricas_disponibles=True,
                metodo_usado=datos_ia["metricas"].get("metodo_usado"),
            )
        else:
            # Librerías externas no disponibles — refactor válido pero sin métricas
            datos_ia["metricas"]["porcentaje_ahorro_ram"] = None
            datos_ia["metricas"]["porcentaje_ahorro_cpu"] = None
            datos_ia["metricas"]["ya_optimizado"] = False
            datos_ia["metricas"]["metricas_disponibles"] = False
            datos_ia["metricas"]["mensaje_metricas"] = f"Métricas no disponibles — el código usa '{modulo_faltante}', una librería externa no instalada en el sandbox. El refactor es correcto pero no podemos medir el ahorro exacto."

            print(f"⚠️ Refactor entregado sin métricas — librería faltante: {modulo_faltante}")

            guardar_en_supabase(
                archivo=peticion.archivo,
                repositorio=peticion.repositorio,
                ahorro_ram=None,
                ahorro_cpu=None,
                ya_optimizado=False,
                metricas_disponibles=False,
                metodo_usado=datos_ia["metricas"].get("metodo_usado"),
            )

        return {
            "status": "exito",
            "datos_optimizados": datos_ia,
            "resultado_ejecucion_real": probar_codigo_aislado(datos_ia.get("codigo_optimizado", ""))
        }

    except Exception as e:
        print(f"❌ Error con el motor: {e}")
        return {"error": str(e)}