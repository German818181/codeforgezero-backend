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

# Cliente conectado a la infraestructura de GitHub Models
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN")
)

app = FastAPI(title="CodeForgeZero Engine - V4 (Multi-Run + Honesty Threshold)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UMBRAL_AHORRO_MINIMO = 5.0  # Si el ahorro es menor a esto, se reporta como "ya optimizado"
CORRIDAS = 5                 # Cuántas veces se mide cada versión para promediar

class PeticionOptimizacion(BaseModel):
    codigo_sucio: str

def medir_codigo_promedio(funcion_a_medir, nombre_version, corridas=CORRIDAS):
    """Mide el rendimiento varias veces y devuelve el promedio para eliminar ruido del servidor."""
    rams = []
    tiempos = []

    for i in range(corridas):
        gc.collect()
        tracemalloc.clear_traces()
        tracemalloc.start()

        inicio_tiempo = time.perf_counter()
        try:
            funcion_a_medir()
        except Exception as e:
            print(f"Error en ejecución {nombre_version} (corrida {i+1}): {e}")

        fin_tiempo = time.perf_counter()
        _, pico_memoria = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        rams.append(pico_memoria / (1024 * 1024))
        tiempos.append(fin_tiempo - inicio_tiempo)

    return sum(rams) / len(rams), sum(tiempos) / len(tiempos)

@app.post("/api/optimize")
async def optimizar_codigo(peticion: PeticionOptimizacion):
    print(f"🚀 Conectando a GitHub Models (GPT-4o) - Multi-Run ({CORRIDAS} corridas)...")

    instruccion_sistema = f"""
Eres CodeForgeZero, un Arquitecto de Software Senior experto en optimización de rendimiento.
Tu trabajo es refactorizar código Python para mejorar su eficiencia real en RAM y CPU.

REGLAS CRÍTICAS:
1. Mantené exactamente los mismos nombres de funciones, clases y parámetros públicos del código original. Esto es indispensable para que el test funcione en ambas versiones.
2. Si el código ya está bien optimizado y tus cambios generarían menos de {UMBRAL_AHORRO_MINIMO}% de mejora real, devolvé el código ORIGINAL sin modificar y explicalo en el reporte. No hagas cambios cosméticos que no mejoran el rendimiento.
3. Generá un campo "codigo_test": un bloque Python que instancie las clases e invoque las funciones principales con datos de ejemplo representativos (mínimo 500-1000 elementos para que la diferencia de rendimiento sea medible). No debe imprimir nada ni usar assertions que puedan fallar.
4. El campo "codigo_optimizado" debe ser el código completo, listo para ejecutar.

DEBES responder EXCLUSIVAMENTE con un JSON válido con esta estructura, sin texto extra, sin markdown:
{{
    "codigo_optimizado": "string con el código completo",
    "codigo_test": "string con el arnés de pruebas",
    "ya_optimizado": false,
    "reporte": "explicación de qué se cambió y por qué, o por qué no se cambió nada",
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
        ram_mala, tiempo_malo = medir_codigo_promedio(test_original, "Original")

        print("📊 Midiendo rendimiento optimizado...")
        ram_buena, tiempo_bueno = medir_codigo_promedio(test_optimizado, "Optimizado")

        # Cálculos de impacto porcentual
        ahorro_ram = ((ram_mala - ram_buena) / ram_mala * 100) if ram_mala > 0 else 0.0
        ahorro_tiempo = ((tiempo_malo - tiempo_bueno) / tiempo_malo * 100) if tiempo_malo > 0 else 0.0

        # Umbral de honestidad: si los ahorros son menores al mínimo, forzamos a 0
        ahorro_ram_final = max(round(ahorro_ram, 1), 0.0) if ahorro_ram >= UMBRAL_AHORRO_MINIMO else 0.0
        ahorro_tiempo_final = max(round(ahorro_tiempo, 1), 0.0) if ahorro_tiempo >= UMBRAL_AHORRO_MINIMO else 0.0

        ya_optimizado = datos_ia.get("ya_optimizado", False) or (ahorro_ram_final == 0.0 and ahorro_tiempo_final == 0.0)

        print(f"✅ RAM: {ahorro_ram_final}% | CPU: {ahorro_tiempo_final}% | Ya optimizado: {ya_optimizado}")

        if "metricas" not in datos_ia:
            datos_ia["metricas"] = {}

        datos_ia["metricas"]["porcentaje_ahorro_ram"] = ahorro_ram_final
        datos_ia["metricas"]["porcentaje_ahorro_cpu"] = ahorro_tiempo_final
        datos_ia["metricas"]["tiempo_original_seg"] = round(tiempo_malo, 6)
        datos_ia["metricas"]["tiempo_optimizado_seg"] = round(tiempo_bueno, 6)
        datos_ia["metricas"]["ya_optimizado"] = ya_optimizado

        return {
            "status": "exito",
            "datos_optimizados": datos_ia,
            "resultado_ejecucion_real": probar_codigo_aislado(datos_ia.get("codigo_optimizado", ""))
        }

    except Exception as e:
        print(f"❌ Error con el motor: {e}")
        return {"error": str(e)}