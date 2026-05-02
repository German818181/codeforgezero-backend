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
import gc

def medir_codigo(funcion_a_medir, nombre_version):
    gc.collect() 
    tracemalloc.clear_traces() 
    
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

app = FastAPI(title="CodeForgeZero Engine", version="3.0_MultiAgent")

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
    print("🚀 Iniciando Pipeline Multi-Agente CodeForgeZero...")
    
    try:
        # =================================================================
        # AGENTE 1: EL SABUESO (Inspector de Código)
        # =================================================================
        print("🔍 Paso 1: Agente Sabueso analizando el código...")
        prompt_sabueso = """Rol: Inspector Técnico.
        Tu ÚNICA tarea es leer el código Python provisto y detectar bucles ineficientes (for dentro de for) o búsquedas repetitivas en listas.
        Reglas:
        1. NO modifiques la lógica ni reescribas el código.
        2. Solo debes insertar este comentario EXACTAMENTE arriba del cuello de botella detectado: '# BOMBA_NUCLEAR: BUCLE ANIDADO DETECTADO. APLICAR HASH MAP / DICCIONARIO AQUI.'
        3. Devuelve únicamente el código original con tus comentarios insertados. Nada de texto extra."""

        respuesta_sabueso = cliente_groq.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_sabueso},
                {"role": "user", "content": peticion.codigo_sucio}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            top_p=0.01,
            seed=42
            # Sin JSON format, queremos texto plano (código comentado)
        )
        
        codigo_con_pistas = respuesta_sabueso.choices[0].message.content
        print("🎯 Pistas insertadas con éxito. Pasando al Arquitecto...")

        # =================================================================
        # AGENTE 2: EL ARQUITECTO (Refactorizador FinOps)
        # =================================================================
        print("⚙️ Paso 2: Agente Arquitecto refactorizando...")
        prompt_maestro = """Rol: Arquitecto Cloud FinOps de Élite.
        Objetivo: Optimizar código Python reduciendo memoria a O(n) y CPU a O(1), SIN romper la lógica original.
        El código que vas a recibir ya tiene comentarios de otro auditor indicando dónde están las '# BOMBA_NUCLEAR'. Sigue esas pistas.

        REGLAS DE ORO (ESTRICTAS):
        1. Usa diccionarios (Hash Maps) o conjuntos (Sets) para eliminar los bucles anidados marcados.
        2. DEBES aplanar la estructura. El ahorro de RAM debe ser la prioridad absoluta.
        3. FORMATO (ESTRICTO): El campo "reporte" DEBE ser una lista estructurada con guiones ('- ').
        4. ANTI-COSMÉTICA (CRÍTICO): IGNORA la estética. NO renombres funciones ni variables.

        RESPONDE ÚNICAMENTE CON UN JSON VÁLIDO:
        {
          "codigo_optimizado": "...",
          "reporte": "- Explicación 1\\n- Explicación 2",
          "script_prueba": "print('test')",
          "metricas": {
            "complejidad_espacial": "<CALCULA_LA_COMPLEJIDAD_REAL: ej O(1), O(n)>",
            "metodo_usado": "<DESCRIBE_BREVEMENTE_EL_METODO_APLICADO>"
          }
        }"""

        chat_completion = cliente_groq.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_maestro},
                {"role": "user", "content": codigo_con_pistas} # Le pasamos el código con el machete
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            top_p=0.01,  
            seed=42,     
            response_format={"type": "json_object"} 
        )
        
        respuesta_texto = chat_completion.choices[0].message.content
        resultado_json = json.loads(respuesta_texto)
        
        # =================================================================
        # AUDITORÍA LOCAL DE RAM
        # =================================================================
        print("✅ Refactorización finalizada. Iniciando auditoría física de RAM...")
        
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

        ram_mala, tiempo_malo = medir_codigo(test_original, "Ejecución original")
        ram_buena, tiempo_bueno = medir_codigo(test_optimizado, "Ejecución optimizada")
        
        if ram_mala > 0:
            ahorro_ram = ((ram_mala - ram_buena) / ram_mala) * 100
        else:
            ahorro_ram = 99.9
            
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
    return {"status": "success", "message": "Endpoint CI/CD activo"}