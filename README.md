# Raíz Capital — Sistema de Gestión Inmobiliaria

## Instalación local

```bash
pip install -r requirements.txt
python app.py
```
Abrí http://localhost:5000 en tu browser.

**Usuario:** tomas  
**Contraseña:** raiz2026  
(cambiarla desde el sistema después del primer login)

## Deploy en Railway (gratis, datos permanentes)

1. Creá cuenta en https://railway.app
2. New Project → Deploy from GitHub repo (subí esta carpeta)
3. O usá Railway CLI: `railway up`
4. La URL pública queda lista en segundos

## Tecnologías
- Python / Flask
- SQLite (base de datos local) → PostgreSQL en producción
- Flask-Login (autenticación)
- HTML/CSS/JS (frontend idéntico a la versión standalone)
