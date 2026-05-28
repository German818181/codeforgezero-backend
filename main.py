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

app = FastAPI(title="CodeForgeZero Engine - V3 (Dual Metrics)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PeticionOptimizacion(BaseModel):
    codigo_sucio: str

def medir_codigo(funcion_a_medir, nombre_version):
    gc.collect()
    tracemalloc.clear_traces()
    tracemalloc.start()
    
    # Captura precisa del tiempo de inicio
    inicio_tiempo = time.perf_counter() 
    try:
        funcion_a_medir()
    except Exception as e:
        print(f"Error en ejecución {nombre_version}: {e}")
    
    # Captura precisa del tiempo de finalización
    fin_tiempo = time.perf_counter()
    _, pico_memoria = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return pico_memoria / (1024 * 1024), fin_tiempo - inicio_tiempo

@app.post("/api/optimize")
async def optimizar_codigo(peticion: PeticionOptimizacion):
    print("🚀 Conectando a GitHub Models (GPT-4o) - Ejecución Dual...")

    instruccion_sistema = """
    Eres CodeForgeZero, un Arquitecto de Software Senior experto en optimización de rendimiento.
    Refactoriza el código de Python para mejorar la eficiencia. Balancea el uso de RAM y CPU.
    Si el código ya es óptimo o cambiarlo añade overhead innecesario, mantén la estructura básica y acláralo en el reporte.
    DEBES responder EXCLUSIVAMENTE con un JSON válido con esta estructura exacta, sin texto extra, sin markdown:
    {
        "codigo_optimizado": "string con el código",
        "reporte": "breve explicación",
        "metricas": {"metodo_usado": "explicación técnica"}
    }
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

        # Auditoría de hardware en paralelo
        def test_original(): exec(peticion.codigo_sucio, {})
        def test_optimizado(): exec(datos_ia.get("codigo_optimizado", ""), {})

        ram_mala, tiempo_malo = medir_codigo(test_original, "Original")
        ram_buena, tiempo_bueno = medir_codigo(test_optimizado, "Optimizado")
        
        # Cálculos de impacto porcentual
        ahorro_ram = ((ram_mala - ram_buena) / ram_mala * 100) if ram_mala > 0 else 0.0
        ahorro_tiempo = ((tiempo_malo - tiempo_bueno) / tiempo_malo * 100) if tiempo_malo > 0 else 0.0

        # Inyectamos los resultados reales en el JSON para el frontend
        if "metricas" not in datos_ia:
            datos_ia["metricas"] = {}
            
        datos_ia["metricas"]["porcentaje_ahorro_ram"] = round(ahorro_ram, 1)
        datos_ia["metricas"]["porcentaje_ahorro_cpu"] = round(ahorro_tiempo, 1)
        datos_ia["metricas"]["tiempo_original_seg"] = round(tiempo_malo, 6)
        datos_ia["metricas"]["tiempo_optimizado_seg"] = round(tiempo_bueno, 6)

        return {
            "status": "exito",
            "datos_optimizados": datos_ia,
            "resultado_ejecucion_real": probar_codigo_aislado(datos_ia.get("codigo_optimizado", ""))
        }
        
    except Exception as e:
        print(f"❌ Error con el motor: {e}")
        return {"error": str(e)}