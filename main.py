from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 👈 1. NUEVA IMPORTACIÓN
from pydantic import BaseModel
import os
import json
from dotenv import load_dotenv
from groq import Groq
from sandbox import probar_codigo_aislado

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
        
        # ... (código anterior donde llamas a la IA)
        respuesta_texto = chat_completion.choices[0].message.content
        resultado_json = json.loads(respuesta_texto)
        
        print("✅ ¡IA respondió con éxito! Mandando código al Coliseo...")
        
        # ⚔️ ABRIMOS LAS PUERTAS DEL COLISEO
        # Juntamos la función optimizada y el script de prueba para ejecutarlos juntos
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