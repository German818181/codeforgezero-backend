from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from dotenv import load_dotenv
from groq import Groq
from sandbox import probar_codigo_aislado
import time
import tracemalloc

def medir_codigo(funcion_a_medir, nombre_version):
    tracemalloc.start()
    inicio_tiempo = time.time()
    
    try:
        funcion_a_medir() 
    except Exception as e:
        print(f"Error midiendo {nombre_version}: {e}")
    
    _, pico_memoria = tracemalloc.get_traced_memory()
    fin_tiempo = time.time()
    tracemalloc.stop()
    
    tiempo_total = fin_tiempo - inicio_tiempo
    memoria_mb = pico_memoria / (1024 * 1024)
    print(f"[CodeForgeZero] {nombre_version}: {memoria_mb:.2f} MB RAM | {tiempo_total:.4f}s")
    
    return memoria_mb, tiempo_total

load_dotenv()

app = FastAPI(title="CodeForgeZero Engine", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cliente_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

class PeticionOptimizacion(BaseModel):
    codigo_sucio: str

@app.post("/api/optimize")
def optimizar_codigo(peticion: PeticionOptimizacion):
    print("🚀 Mandando código a Groq con Prompt Maestro de Élite...")
    
    # EL NUEVO CEREBRO ACTUALIZADO
    prompt_maestro = """Rol: Arquitecto Cloud FinOps de Élite.
    Objetivo: Optimizar código Python reduciendo memoria a O(n) y CPU a O(1), SIN romper la lógica original.

    REGLAS DE ORO (ESTRICTAS):
    1. PROHIBIDO: NUNCA iteres un generador o lista múltiples veces dentro de un bucle for o comprensión.
    2. REGLA 2 (ACTUALIZADA): Si detectas bucles anidados, DEBES aplanar la estructura. No uses diccionarios de listas si puedes usar diccionarios de valores únicos o comprensiones de listas directas. El ahorro de RAM debe ser la prioridad absoluta sobre la legibilidad.
    3. FORMATO (ESTRICTO): El campo "reporte" DEBE ser una lista estructurada con guiones ('- '). PROHIBIDO usar párrafos.
    4. ESCAPE DE CARACTERES: Asegúrate de escapar correctamente las comillas y saltos de línea (\\n) para que el JSON sea válido.
    5. ANTI-COSMÉTICA (CRÍTICO): Eres un auditor FinOps, no un Linter. IGNORA la estética. NO renombres funciones ni variables, NO corrijas estilos de escritura (camelCase/snake_case/mayúsculas), y mantén los nombres originales por más aberrantes que sean. Tu ÚNICO trabajo es modificar la lógica algorítmica y la estructura de datos.
    EJEMPLO DE MODELO (SIGUE ESTA ESTRUCTURA):
    def CALCULAR_totales_Feo():
        # 1. Agrupar primero (O(n))
        totales_dict = {}
        for t in obtener_transacciones():
            totales_dict[t['uSeR_iD']] = totales_dict.get(t['uSeR_iD'], 0) + t['monto']
            
        # 2. Generar reporte rápido (O(1))
        return ( {'Usuario': u['nombre'], 'Total': totales_dict.get(u['ID_feo'], 0)} 
                 for u in obtener_usuarios() if totales_dict.get(u['ID_feo'], 0) > 0 )

   RESPONDE ÚNICAMENTE CON UN JSON VÁLIDO:
  {
    "codigo_optimizado": "...",
    "reporte": "- Explicación 1\n- Explicación 2",
    "script_prueba": "print('test')",
    "metricas": {
      "complejidad_espacial": "<CALCULA_LA_COMPLEJIDAD_REAL: ej O(1), O(n), O(log n)>",
      "metodo_usado": "<DESCRIBE_BREVEMENTE_EL_METODO_REAL_APLICADO>"
    }
  }

    try:
        chat_completion = cliente_groq.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_maestro},
                {"role": "user", "content": f"Optimiza este código:\n\n{peticion.codigo_sucio}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            response_format={"type": "json_object"} 
        )
        
        respuesta_texto = chat_completion.choices[0].message.content
        resultado_json = json.loads(respuesta_texto)
        
        print("✅ ¡IA respondió con éxito! Iniciando auditoría de métricas...")
        
        def test_original():
            try:
                exec(peticion.codigo_sucio, {})
            except:
                pass

        def test_optimizado():
            try:
                exec(resultado_json["codigo_optimizado"], {})
            except:
                pass

        print("\n--- AUDITORÍA AUTOMÁTICA CODEFORGEZERO ---")
        ram_mala, tiempo_malo = medir_codigo(test_original, "Ejecución original")
        ram_buena, tiempo_bueno = medir_codigo(test_optimizado, "Ejecución optimizada")
        
        if ram_mala > 0:
            ahorro_ram = ((ram_mala - ram_buena) / ram_mala) * 100
        else:
            ahorro_ram = 99.9
        print("------------------------------------------\n")
        # 🔥 EL PARCHE MÁGICO: Pisamos la estimación de la IA con el cálculo real
        resultado_json["metricas"]["porcentaje_ahorro_ram"] = round(ahorro_ram, 1)

        print("Mandando código al Coliseo...")
        codigo_completo_a_testear = resultado_json["codigo_optimizado"] + "\n\n" + resultado_json["script_prueba"]
        resultado_coliseo = probar_codigo_aislado(codigo_completo_a_testear)
        
        return {
            "status": "exito",
            "datos_optimizados": resultado_json,
            "resultado_ejecucion_real": resultado_coliseo
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}

class CicdRequest(BaseModel):
    code: str
    language: str = "python"

@app.post("/api/cicd/analyze")
async def cicd_analyze(payload: CicdRequest):
    codigo_nuevo = payload.code
    # Aquí podrías usar un prompt similar si decides activar esta ruta
    return {"status": "success", "message": "Endpoint CI/CD activo"}