import requests

# 1. Apuntamos a tu taller local (asegurate de que sea el puerto correcto, ej: 8000 o 5000)
URL_LOCAL = "http://localhost:8000/api/cicd/analyze"

# 2. El código ineficiente que un programador "intentó" subir a producción
codigo_basura = """
def sumar_numeros():
    lista = []
    for i in range(1000000):
        lista.append(i * 2)
    return lista
"""

# 3. Armamos el paquete de datos
payload = {
    "code": codigo_basura,
    "language": "python"
}

print("🚀 Disparando misil de prueba al servidor local...")

try:
    # 4. Apretamos el gatillo
    respuesta = requests.post(URL_LOCAL, json=payload)
    
    print("\n🎯 RESPUESTA DEL PATOVICA (IA):")
    print(respuesta.json())

except Exception as e:
    print("❌ Error de conexión. ¿Está prendido el servidor local?:", e)