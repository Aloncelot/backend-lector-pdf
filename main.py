from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware  # <-- NUEVA LIBRERÍA
import fitz  # PyMuPDF
import re

# Inicializamos nuestra API (como const app = express())
app = FastAPI()

# Agregamos esta línea para permitir que la app móvil se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite que cualquier origen se conecte (puedes restringirlo después)
    allow_credentials=True,
    allow_methods=["*"],  # Permite métodos GET, POST, etc.
    allow_headers=["*"],
)

# Creamos una ruta POST para recibir el archivo
@app.post("/limpiar-pdf")
async def limpiar_pdf(file: UploadFile = File(...)):
    # 1. Leemos los "bytes" del archivo que enviará la app móvil
    contenido_pdf = await file.read()
    
    # 2. PyMuPDF abre el archivo directamente desde la memoria
    doc = fitz.open(stream=contenido_pdf, filetype="pdf")
    texto_final = []

    for pagina in doc:
        bloques = pagina.get_text("blocks")
        alto_pagina = pagina.rect.height

        for b in bloques:
            texto_bloque = b[4]
            y_pos = b[1]
            
            # FILTRO DE MÁRGENES: Ignoramos "Universidad ARCIS"
            if y_pos < 60 or y_pos > (alto_pagina - 50):
                continue
            
            # FILTRO REGEX: Ignoramos los números "- 1 -"
            if re.match(r"^\s*-\d+-\s*$", texto_bloque.strip()):
                continue

            # Limpiamos saltos de línea y guardamos
            limpio = texto_bloque.replace("\n", " ").strip()
            if limpio:
                texto_final.append(limpio)

    # 3. Respondemos con un JSON listo para ser leído en voz alta
    return {"texto_limpio": "\n\n".join(texto_final)}