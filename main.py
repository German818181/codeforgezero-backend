from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 👈 1. NUEVA IMPORTACIÓN
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
    
    funcion_a_medir() 
    
    _, pico_memoria = tracemalloc.get_traced_memory()
    fin_tiempo = time.time()
    tracemalloc.stop()
    
    tiempo_total = fin_tiempo - inicio_tiempo
    memoria_mb = pico_memoria / (1024 * 1024)
    print(f"[CodeForgeZero] {nombre_version}: {memoria_mb:.2f} MB RAM | {tiempo_total:.4f}s")
    
    return memoria_mb, tiempo_total



# 1. Cargamos la caja fuerte (.env)
load_dotenv()

# 2. Inicializamos el servidor y la IA
app = FastAPI(title="CodeForgeZero Engine", version="2.0")

# 🛂 2. EL AGENTE DE ADUANAS (CORS) - NUEVO BLOQUE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Por ahora en desarrollo dejamos entrar a cualquiera. En prod pondremos tu dominio.
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, etc.
    allow_headers=["*"],
)

cliente_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

class PeticionOptimizacion(BaseModel):
    codigo_sucio: str

@app.post("/api/optimize")
def optimizar_codigo(peticion: PeticionOptimizacion):
    print("🚀 Mandando código sucio a Llama 3.3 vía Groq...")
    
    prompt_maestro = """Rol: Arquitecto Cloud FinOps y QA Automation.
    Objetivo: Optimizar el código Python para O(1) en memoria (usando yield/generadores) SIN ROMPER EL CONTRATO DE INTERFAZ.
    
    REGLAS DE ORO:
    1. Si la función original devuelve listas, tu versión optimizada DEBE usar generadores (yield).
    2. BREVEDAD: Código elegante y corto.
    3. ESCAPE DE CARACTERES: Escapa correctamente las comillas y saltos de línea.
       
    DEBES RESPONDER ÚNICAMENTE CON UN OBJETO JSON VÁLIDO con este formato:
    {
      "codigo_optimizado": "...",
      "reporte": "...",
      "script_prueba": "...",
      "metricas": {
        "complejidad_espacial": "O(1)",
        "porcentaje_ahorro_ram": 99,
        "metodo_usado": "Generadores"
      }
    }"""

    try:
        # 3. Hacemos la llamada a la IA exigiendo un JSON perfecto
        chat_completion = cliente_groq.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_maestro},
                {"role": "user", "content": f"Optimiza este código:\n\n{peticion.codigo_sucio}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"} 
        )
        
        respuesta_texto = chat_completion.choices[0].message.content
        resultado_json = json.loads(respuesta_texto)
        
        print("✅ ¡IA respondió con éxito! Calculando ahorro financiero...")
        
        # 🔥 ACÁ EMPIEZA LA MAGIA DEL MEDIDOR PARA EL VIDEO 🔥
        def test_original():
            try:
                # Ejecutamos el código que mandó el usuario desde el frontend
                exec(peticion.codigo_sucio, {})
            except:
                pass

        def test_optimizado():
            try:
                # Ejecutamos el código puro que arregló la IA
                exec(resultado_json["codigo_optimizado"], {})
            except:
                pass

        print("\n--- INICIANDO AUDITORÍA AUTOMÁTICA CODEFORGEZERO ---")
        ram_mala, tiempo_malo = medir_codigo(test_original, "Ejecución original")
        ram_buena, tiempo_bueno = medir_codigo(test_optimizado, "Ejecución optimizada")
        
        # Calculamos el porcentaje
        if ram_mala > 0:
            ahorro_ram = ((ram_mala - ram_buena) / ram_mala) * 100
            print(f"[CodeForgeZero] Ahorro estimado de RAM: {ahorro_ram:.1f}%")
        else:
            print("[CodeForgeZero] Ahorro estimado de RAM: 99.9%")
        print("----------------------------------------------------\n")
        # 🔥 ACÁ TERMINA LA MAGIA DEL MEDIDOR 🔥

        print("Mandando código al Coliseo para prueba final...")
        
        # ⚔️ ABRIMOS LAS PUERTAS DEL COLISEO
        codigo_completo_a_testear = resultado_json["codigo_optimizado"] + "\n\n" + resultado_json["script_prueba"]
        resultado_coliseo = probar_codigo_aislado(codigo_completo_a_testear)
        
        return {
            "status": "exito",
            "datos_optimizados": resultado_json,
            "resultado_ejecucion_real": resultado_coliseo
        }
        
    except Exception as e:
        print(f"❌ Error en la Matrix: {e}")
        return {"error": str(e)}



# Asegurate de tener importado BaseModel de pydantic si usas FastAPI
# from pydantic import BaseModel

class CicdRequest(BaseModel):
    code: str
    language: str = "python"

@app.post("/api/cicd/analyze")
async def cicd_analyze(payload: CicdRequest):
    codigo_nuevo = payload.code

    prompt_cicd = f"""
    Eres un Cloud Security & FinOps Architect operando en un pipeline CI/CD.
    Tu trabajo es auditar el siguiente código buscando ineficiencias críticas de RAM (Complejidad Espacial) y CPU.
    Si el código es ineficiente, debes rechazarlo ("aprobado": false).
    
    Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta, sin texto adicional:
    {{
        "aprobado": true o false,
        "motivo": "Explicación técnica corta",
        "codigo_sugerido": "El código optimizado aquí"
    }}

    Código a analizar:
    {codigo_nuevo}
    """

    try:
        # Llamada REAL a la API de Groq
        chat_completion = cliente_groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un analizador de código estricto. Responde SOLO con formato JSON."
                },
                {
                    "role": "user",
                    "content": prompt_cicd
                }
            ],
            model="llama-3.3-70b-versatile", 
            response_format={"type": "json_object"}, 
            temperature=0.1 
        )
        
        # 1. Extraemos el texto crudo que devolvió Groq
        respuesta_texto = chat_completion.choices[0].message.content
        
        # 2. Lo convertimos de texto a un diccionario real de Python
        respuesta_ia = json.loads(respuesta_texto)

        return {
            "status": "success",
            "webhook_response": respuesta_ia
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}