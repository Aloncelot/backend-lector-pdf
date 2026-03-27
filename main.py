from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
import re
import os 
import uvicorn

# Inicializamos nuestra API
app = FastAPI()

# Permisos para que la app móvil se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

@app.post("/limpiar-pdf")
async def limpiar_pdf(file: UploadFile = File(...)):
    # 1. Leemos los bytes del archivo
    contenido_pdf = await file.read()
    
    # 2. PyMuPDF abre el archivo
    doc = fitz.open(stream=contenido_pdf, filetype="pdf")
    texto_final = []

    for pagina in doc:
        bloques = pagina.get_text("blocks")
        alto_pagina = pagina.rect.height

        for b in bloques:
            texto_bloque = b[4]
            y_pos = b[1]
            
            # --- FILTRO 1: MÁRGENES (Restaurado) ---
            # Ignoramos encabezados y pies de página fijos
            if y_pos < 20 or y_pos > (alto_pagina - 50):
                continue
            
            # --- FILTRO 2: REGEX PARA BASURA VISUAL ---
            texto_limpio = texto_bloque.strip()
            
            # Ignoramos los números de página con guiones viejos: "- 1 -"
            if re.match(r"^\s*-\d+-\s*$", texto_limpio):
                continue
                
            # NUEVO: Ignoramos paginación de libros: "Página 4", "PÁGINA 170"
            if re.match(r"(?i)^Página\s*\d+$", texto_limpio):
                continue

            # --- FILTRO 3: UNIÓN DE PALABRAS CORTADAS ---
            # Si una palabra se cortó con guion al final del renglón (ej: cons-\ntrucción), la unimos.
            texto_bloque = texto_bloque.replace("-\n", "")

            # --- FILTRO 4: LIMPIEZA DE SALTOS Y ESPACIOS ---
            limpio = texto_bloque.replace("\n", " ").strip()
            limpio = re.sub(r'\[\d+\]', '', limpio)  
            
            # Si quedaron dobles espacios por la fusión, los reducimos a uno
            limpio = re.sub(r'\s+', ' ', limpio)

            if limpio:
                texto_final.append(limpio)

    # 3. Unimos todos los bloques limpios con un solo espacio para que Flutter lo corte bien por puntos
    texto_completo = " ".join(texto_final)
    
    return {"texto_limpio": texto_completo}

if __name__ == "__main__":
    # Lee el puerto que asigne el servidor, o usa 8000 en local
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)