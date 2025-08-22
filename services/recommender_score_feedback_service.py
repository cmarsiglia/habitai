import pandas as pd
from sklearn.ensemble import RandomForestRegressor

class RecommenderScoreFeedbackService:
    def __init__(self):
        pass
    
    def recomendar(self, ciudad: str, criterios_usuario: dict):
        
        top_n = 8

        # ==========================
        #  Dataset base de barrios
        # ==========================
        barrios = pd.read_csv("assets/dataset-barrios.csv")

        # ==========================
        #  Feedback histórico (simulado)
        # ==========================
        feedbackData = pd.DataFrame([
            {"dist_parques_km": 0.6, "dist_colegios_km": 1.2, "dist_clinicas_km": 1.8, "dist_centroscom_km": 0.7,
             "pref_parques": 1, "pref_colegios": 1, "pref_clinicas": 0, "pref_centroscom": 0, "rating": 5},
            {"dist_parques_km": 0.9, "dist_colegios_km": 0.8, "dist_clinicas_km": 2.0, "dist_centroscom_km": 0.5,
             "pref_parques": 0.9, "pref_colegios": 1, "pref_clinicas": 0.7, "pref_centroscom": 0.7, "rating": 2},
            {"dist_parques_km": 0.9, "dist_colegios_km": 0.8, "dist_clinicas_km": 1.0, "dist_centroscom_km": 0.8,
             "pref_parques": 0.9, "pref_colegios": 1, "pref_clinicas": 0.8, "pref_centroscom": 0.8, "rating": 4},
            {"dist_parques_km": 0.5, "dist_colegios_km": 1.8, "dist_clinicas_km": 1.1, "dist_centroscom_km": 0.9,
             "pref_parques": 0.5, "pref_colegios": 1, "pref_clinicas": 0.5, "pref_centroscom": 0.5, "rating": 3},
            {"dist_parques_km": 0.2, "dist_colegios_km": 1.2, "dist_clinicas_km": 1.6, "dist_centroscom_km": 0.5,
             "pref_parques": 0.2, "pref_colegios": 1, "pref_clinicas": 0.2, "pref_centroscom": 0.2, "rating": 5},
            {"dist_parques_km": 0.3, "dist_colegios_km": 1.1, "dist_clinicas_km": 1.9, "dist_centroscom_km": 0.1,
             "pref_parques": 1, "pref_colegios": 1, "pref_clinicas": 0.3, "pref_centroscom": 0.3, "rating": 4},
            {"dist_parques_km": 0.7, "dist_colegios_km": 2.8, "dist_clinicas_km": 2.4, "dist_centroscom_km": 1.5,
             "pref_parques": 0.7, "pref_colegios": 1, "pref_clinicas": 0.7, "pref_centroscom": 0.7, "rating": 5}
        ])

        feedback = pd.DataFrame([])
        # Filtrar por ciudad
        df_ciudad = barrios[barrios["ciudad"].str.lower() == ciudad.lower()].copy()
        if df_ciudad.empty:
            return {"error": f"No hay barrios en {ciudad}"}

        # Mapear criterios
        criterio_map = {
            "parques": "dist_parques_km",
            "colegios": "dist_colegios_km",
            "clinicas": "dist_clinicas_km",
            "hospitales": "dist_clinicas_km",
            "centros comerciales": "dist_centroscom_km",
            "malls": "dist_centroscom_km"
        }

        # Codificar preferencias como features binarios
        for key in criterio_map.keys():
            df_ciudad[f"pref_{key}"] = 1 if key in criterios_usuario["positivos"] else 0

        # ==========================
        #  Caso 1: Hay feedback suficiente → usar modelo
        # ==========================
        if len(feedback) >= 5:  # mínimo 5 ejemplos para entrenar
            X = feedback.drop("rating", axis=1)
            y = feedback["rating"]
            model = RandomForestRegressor(n_estimators=500, random_state=42, max_depth=5, n_jobs=-1)
            model.fit(X, y)

            predicciones = []
            for _, row in df_ciudad.iterrows():
                features = {
                    "dist_parques_km": row["dist_parques_km"],
                    "dist_colegios_km": row["dist_colegios_km"],
                    "dist_clinicas_km": row["dist_clinicas_km"],
                    "dist_centroscom_km": row["dist_centroscom_km"],
                    "pref_parques": row.get("pref_parques", 0),
                    "pref_colegios": row.get("pref_colegios", 0),
                    "pref_clinicas": row.get("pref_clinicas", 0),
                    "pref_centroscom": row.get("pref_centroscom", 0)
                }
                pred_rating = model.predict(pd.DataFrame([features]))[0]
                predicciones.append({
                    "barrio": row["barrio"],
                    "ciudad": row["ciudad"],
                    "dist_parques_km": row["dist_parques_km"],
                    "dist_colegios_km": row["dist_colegios_km"],
                    "dist_clinicas_km": row["dist_clinicas_km"],
                    "dist_centroscom_km": row["dist_centroscom_km"],
                    "predicted_rating": round(pred_rating, 2)
                })
            
            return sorted(predicciones, key=lambda x: x["predicted_rating"], reverse=True)[:top_n]

        # ==========================
        #  Caso 2: No hay feedback suficiente → usar score básico
        # ==========================
        else:
            df_ciudad["score"] = 0.0

            # Positivos (cercanía)
            for criterio in criterios_usuario.get("positivos", []):
                col = criterio_map.get(criterio)
                if col and col in df_ciudad.columns:
                    df_ciudad["score"] += 1 / (df_ciudad[col] + 0.001)

            # Negativos (lejanía)
            for criterio in criterios_usuario.get("negativos", []):
                col = criterio_map.get(criterio)
                if col and col in df_ciudad.columns:
                    max_val = df_ciudad[col].max()
                    df_ciudad["score"] += df_ciudad[col] / max_val

            recomendados = df_ciudad.sort_values(by="score", ascending=False).head(top_n)
            return recomendados[["barrio", "ciudad", "dist_parques_km", "dist_colegios_km", "dist_clinicas_km", "dist_centroscom_km", "score"]].to_dict(orient="records")
