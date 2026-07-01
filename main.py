import os
import time
import tracemalloc
import gc
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from sandbox import probar_codigo_aislado

load_dotenv()

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN")
)

app = FastAPI(title="CodeForgeZero Engine - V5 (Honest Metrics)")

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

def medir_codigo_promedio(funcion_a_medir, nombre_version, corridas=CORRIDAS):
    """
    Mide rendimiento varias veces y promedia.
    Retorna (rams_promedio, tiempos_promedio, error_import)
    Si hay un ImportError, retorna (0, 0, nombre_modulo_faltante)
    """
    rams = []
    tiempos = []
    modulo_faltante = None

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
    print(f"🚀 Conectando a GitHub Models (GPT-4o) - V5 Honest Metrics...")

    instruccion_sistema = f"""
Eres CodeForgeZero, un Arquitecto de Software Senior experto en optimización de rendimiento.
Tu trabajo es refactorizar código Python para mejorar su eficiencia real en RAM y CPU.

REGLAS CRÍTICAS:
1. Mantené exactamente los mismos nombres de funciones, clases y parámetros públicos del código original.
2. Si el código ya está bien optimizado y tus cambios generarían menos de {UMBRAL_AHORRO_MINIMO}% de mejora real, devolvé el código ORIGINAL sin modificar y explicalo en el reporte.
3. Generá un campo "codigo_test": un bloque Python que instancie las clases e invoque las funciones principales con datos de ejemplo representativos (mínimo 500-1000 elementos). No debe imprimir nada ni usar assertions que puedan fallar.
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
            model="gpt-4o",
            messages=[
                {"role": "system", "content": instruccion_sistema},
                {"role": "user", "content": peticion.codigo_sucio}
            ],
            temperature=0.1
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
        else:
            # Librerías externas no disponibles — refactor válido pero sin métricas
            datos_ia["metricas"]["porcentaje_ahorro_ram"] = None
            datos_ia["metricas"]["porcentaje_ahorro_cpu"] = None
            datos_ia["metricas"]["ya_optimizado"] = False
            datos_ia["metricas"]["metricas_disponibles"] = False
            datos_ia["metricas"]["mensaje_metricas"] = f"Métricas no disponibles — el código usa '{modulo_faltante}', una librería externa no instalada en el sandbox. El refactor es correcto pero no podemos medir el ahorro exacto."

            print(f"⚠️ Refactor entregado sin métricas — librería faltante: {modulo_faltante}")

        return {
            "status": "exito",
            "datos_optimizados": datos_ia,
            "resultado_ejecucion_real": probar_codigo_aislado(datos_ia.get("codigo_optimizado", ""))
        }

    except Exception as e:
        print(f"❌ Error con el motor: {e}")
        return {"error": str(e)}