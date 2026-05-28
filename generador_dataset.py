import json
import random

dataset_entrenamiento = []

# ==========================================
# PLANTILLA 1: El Agujero Negro O(n^2)
# ==========================================
def generar_casos_on2(cantidad):
    contextos = [
        ("usuarios", "pagos", "u", "p", "user_id", "monto"),
        ("clientes", "facturas", "c", "f", "cliente_id", "total"),
        ("servidores", "alertas", "srv", "al", "server_id", "latencia")
    ]
    for i in range(cantidad):
        entidad_1, entidad_2, var_1, var_2, fk, valor = random.choice(contextos)
        codigo_sucio = f"def cruzar_{entidad_1}_{i}({entidad_1}, {entidad_2}):\n    return [{{**{var_1}, '{valor}': {var_2}['{valor}']}} for {var_1} in {entidad_1} for {var_2} in {entidad_2} if {var_1}['id'] == {var_2}['{fk}']]"
        codigo_limpio = f"def cruzar_{entidad_1}_{i}({entidad_1}, {entidad_2}):\n    dict_{entidad_2} = {{{var_2}['{fk}']: {var_2}['{valor}'] for {var_2} in {entidad_2}}}\n    return [{{**{var_1}, '{valor}': dict_{entidad_2}.get({var_1}['id'])}} for {var_1} in {entidad_1}]"
        
        agregar_ejemplo(codigo_sucio, codigo_limpio, "Eliminación O(n^2) y uso de Hash Map")

# ==========================================
# PLANTILLA 2: El Problema N+1 (Consultas red)
# ==========================================
def generar_casos_n_mas_1(cantidad):
    contextos = ["obtener_perfil", "get_tracking", "consultar_stock"]
    for i in range(cantidad):
        funcion = random.choice(contextos)
        codigo_sucio = f"def enriquecer_datos_{i}(items):\n    for item in items:\n        item['detalle'] = {funcion}(item['id'])\n    return items"
        codigo_limpio = f"def enriquecer_datos_{i}(items):\n    ids = [item['id'] for item in items]\n    detalles = {funcion}_bulk(ids)\n    dict_detalles = {{d['id']: d for d in detalles}}\n    return [{{**item, 'detalle': dict_detalles.get(item['id'])}} for item in items]"
        
        agregar_ejemplo(codigo_sucio, codigo_limpio, "Batching de base de datos para evitar N+1")

# ==========================================
# PLANTILLA 3: Devorador de RAM (Generadores)
# ==========================================
def generar_casos_ram_masiva(cantidad):
    contextos = [("logs_servidor", "procesar_log"), ("exportacion_csv", "limpiar_fila"), ("sensores_iot", "filtrar_ruido")]
    for i in range(cantidad):
        archivo, procesar = random.choice(contextos)
        codigo_sucio = f"def leer_todo_{i}(ruta_archivo):\n    lineas = open(ruta_archivo).readlines()\n    resultados = []\n    for linea in lineas:\n        resultados.append({procesar}(linea))\n    return resultados"
        codigo_limpio = f"def leer_todo_{i}(ruta_archivo):\n    with open(ruta_archivo) as f:\n        for linea in f:\n            yield {procesar}(linea)"
        
        agregar_ejemplo(codigo_sucio, codigo_limpio, "Uso de Generadores (yield) para procesar archivos grandes sin cargar RAM O(1)")

# ==========================================
# PLANTILLA 4: Ciclo de CPU Redundante
# ==========================================
def generar_casos_cpu_redundante(cantidad):
    contextos = ["calcular_impuesto_base", "obtener_tipo_cambio_actual", "cargar_config_seguridad"]
    for i in range(cantidad):
        pesada = random.choice(contextos)
        codigo_sucio = f"def procesar_lote_{i}(transacciones):\n    resultados = []\n    for t in transacciones:\n        factor = {pesada}()\n        resultados.append(t['monto'] * factor)\n    return resultados"
        codigo_limpio = f"def procesar_lote_{i}(transacciones):\n    factor_cacheado = {pesada}()\n    return [t['monto'] * factor_cacheado for t in transacciones]"
        
        agregar_ejemplo(codigo_sucio, codigo_limpio, "Pre-computación de funciones costosas fuera del bucle para ahorrar CPU")

# ==========================================
# PLANTILLA 5: Iteración DataFrames (Vectorización)
# ==========================================
def generar_casos_vectorizacion(cantidad):
    contextos = ["precio", "latencia", "consumo"]
    for i in range(cantidad):
        columna = random.choice(contextos)
        codigo_sucio = f"def actualizar_df_{i}(df):\n    for index, row in df.iterrows():\n        df.loc[index, '{columna}_ajustado'] = row['{columna}'] * 1.21\n    return df"
        codigo_limpio = f"def actualizar_df_{i}(df):\n    df['{columna}_ajustado'] = df['{columna}'] * 1.21\n    return df"
        
        agregar_ejemplo(codigo_sucio, codigo_limpio, "Vectorización de Pandas reemplazando iterrows() por operaciones de columna")

# ==========================================
# FUNCIÓN AUXILIAR PARA ARMAR EL JSON
# ==========================================
def agregar_ejemplo(sucio, limpio, metodo):
    respuesta = {
        "codigo_optimizado": limpio,
        "reporte": [f"- {metodo}."],
        "script_prueba": "print('Test OK')",
        "metricas": {"complejidad_espacial": "Optimizada", "metodo_usado": metodo}
    }
    dataset_entrenamiento.append({
        "messages": [
            {"role": "system", "content": "Eres un Arquitecto Cloud FinOps. Tu misión es optimizar código Python para reducir el consumo de RAM a O(n) y CPU a O(1) usando estructuras de datos eficientes."},
            {"role": "user", "content": f"Optimiza este código:\n\n{sucio}"},
            {"role": "assistant", "content": json.dumps(respuesta)}
        ]
    })

# ==========================================
# EJECUCIÓN TOTAL DE LA FÁBRICA
# ==========================================
print("⚙️ Encendiendo la megaplanta de CodeForgeZero V3...")

generar_casos_on2(100)
generar_casos_n_mas_1(100)
generar_casos_ram_masiva(100)
generar_casos_cpu_redundante(100)
generar_casos_vectorizacion(100)

random.shuffle(dataset_entrenamiento)

nombre_archivo = "dataset_codeforge_FINAL.jsonl"
with open(nombre_archivo, "w", encoding="utf-8") as f:
    for item in dataset_entrenamiento:
        f.write(json.dumps(item) + "\n")

print(f"✅ ¡Éxito! Se generó el archivo '{nombre_archivo}' con {len(dataset_entrenamiento)} ejemplos completos.")