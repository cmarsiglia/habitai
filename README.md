# 🏙️ API de Recomendación de Zonas

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)  
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)  
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange.svg)](https://scikit-learn.org/stable/)  
[![pandas](https://img.shields.io/badge/pandas-data--analysis-yellow.svg)](https://pandas.pydata.org/)  
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)  
[![Status](https://img.shields.io/badge/status-active-success.svg)]()  

La **API de Recomendación de Zonas** permite a los usuarios recibir sugerencias de barrios en una ciudad con base en criterios definidos (por ejemplo, cercanía a centros comerciales).  
Está construida con **FastAPI** y utiliza modelos de **Machine Learning** para realizar las recomendaciones.  

---

## 🚀 Tecnologías

- [FastAPI](https://fastapi.tiangolo.com/) – Framework web para la API.  
- [Pydantic](https://docs.pydantic.dev/) – Validación de datos.  
- [scikit-learn](https://scikit-learn.org/) – Algoritmos de Machine Learning.  
- [pandas](https://pandas.pydata.org/) – Manejo de datasets.  

---

## ⚙️ Instalación y ejecución

1. Clonar el repositorio:

```bash
git clone https://github.com/tu-usuario/api-recomendacion-zonas.git
cd api-recomendacion-zonas
```

2. Crear entorno virtual e instalar dependencias:

```bash
python -m venv venv
source venv/bin/activate   # En Linux/Mac
venv\Scripts\activate      # En Windows

pip install -r requirements.txt
```

3. Ejecutar la API:

```bash
uvicorn main:app --reload
```

4. Documentación interactiva:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)  

---

## 📌 Endpoints principales

### 🔹 `POST /recomendar`

Recibe una ciudad y los criterios del usuario, devuelve una lista de barrios recomendados.

#### **Request Body**
```json
{
  "ciudad": "Monteria",
  "criterios_usuario": {
    "positivos": ["centros comerciales"]
  }
}
```

#### **Response (ejemplo)**
```json
{
  "ciudad": "Monteria",
  "recomendaciones": [
    {"barrio": "Cantaclaro", "score": 0.87},
    {"barrio": "Los Ángeles", "score": 0.76}
  ]
}
```

---

## 🧪 Ejemplo en cURL

```bash
curl -X POST http://127.0.0.1:8000/recomendar   -H "Content-Type: application/json"   -d '{
    "ciudad": "Monteria",
    "criterios_usuario": {
      "positivos": ["centros comerciales"]
    }
  }'
```

---

## 📂 Estructura del proyecto

```
api-recomendacion-zonas/
│── assets/                  # Datasets base
│── services/                # Servicios de recomendación
│── models/                  # Modelos Pydantic
│── main.py                  # Punto de entrada FastAPI
│── requirements.txt         # Dependencias
│── README.md                # Documentación
```

---

## 📝 Roadmap

- [ ] Agregar soporte para criterios negativos (ej: evitar ruido).  
- [ ] Conectar con base de datos externa (Supabase/Postgres).  
- [ ] Incluir feedback de usuarios en el modelo.  
- [ ] Entrenamiento y actualización automática del modelo ML.  

---

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).  
