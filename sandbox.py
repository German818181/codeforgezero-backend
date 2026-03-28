import subprocess
import tempfile
import os

def probar_codigo_aislado(codigo_a_probar: str):
    # 1. Creamos un archivo temporal oculto en tu compu
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as archivo_temp:
        archivo_temp.write(codigo_a_probar)
        ruta_archivo = archivo_temp.name

    try:
        print(f"⚔️ Ejecutando código en el Coliseo: {ruta_archivo}")
        
        # 2. Ejecutamos un "subproceso". Es como abrir OTRA terminal invisible.
        # Le damos un máximo de 3 segundos de vida.
        resultado = subprocess.run(
            ["python", ruta_archivo], 
            capture_output=True, 
            text=True, 
            timeout=3
        )
        
        # 3. Revisamos si sobrevivió o si tiró error de sintaxis
        if resultado.returncode == 0:
            return {"sobrevivio": True, "salida_consola": resultado.stdout}
        else:
            return {"sobrevivio": False, "error": resultado.stderr}
            
    except subprocess.TimeoutExpired:
        # Si tardó más de 3 segundos, lo matamos por seguridad.
        return {"sobrevivio": False, "error": "Timeout ⏱️: El código entró en bucle infinito o es muy pesado."}
        
    finally:
        # 4. Limpiamos la sangre de la arena (borramos el archivo temporal)
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
            print("🧹 Coliseo limpiado.")