# -*- coding: utf-8 -*-
import geopandas as gpd
import pandas as pd
import osmnx as ox
from shapely.geometry import Point
from pathlib import Path

# =========================
# PARÁMETROS
# =========================
# Nombre del shapefile (usa el .shp).
# SHAPEFILE = "shapefiles/barrios_mtr/Bariios_Mtr.shp"
# CIUDAD = "Montería, Córdoba, Colombia"

SHAPEFILE = "shapefiles/barrios_veredas_medellin/BarrioVereda_2014.shp"
CIUDAD = "Medellín, Antioquia, Colombia"

# Sistema de referencia para medir distancias en metros.
# Web Mercator (EPSG:3857) para distancias urbanas.
CRS_METROS = 3857
CRS_GEO = 4326

# Radio extra para ampliar el polígono de la ciudad (en metros) y captar POIs cercanos al borde
BUFFER_M = 3000

# =========================
# 1) Cargar barrios y preparar centroides
# =========================
gdf = gpd.read_file(SHAPEFILE)

# Nos aseguramos de tener geometría válida
gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notnull()]

# Guardar el CRS original por si hace falta
if gdf.crs is None:
    # Si no tiene CRS, asumimos WGS84 (ajusta si sabes otro)
    gdf = gdf.set_crs(epsg=CRS_GEO)

# Para centroides geométricamente más sensatos, calculamos en CRS métrico
gdf_m = gdf.to_crs(epsg=CRS_METROS)
gdf_m["centroid_geom"] = gdf_m.geometry.centroid

# Luego pasamos esos centroides a WGS84 y guardamos lat/lon
centroids_wgs = gdf_m.set_geometry("centroid_geom").to_crs(epsg=CRS_GEO)
gdf["lat"] = centroids_wgs.geometry.y
gdf["lon"] = centroids_wgs.geometry.x

# =========================
# 2) Descargar POIs OSM UNA SOLA VEZ
# =========================
# Polígono de la ciudad desde OSM
city_poly = ox.geocode_to_gdf(CIUDAD).to_crs(epsg=CRS_METROS)
city_poly_buffer = city_poly.buffer(BUFFER_M).to_crs(epsg=CRS_GEO)  # buffer en metros y regreso a WGS84 para OSM

# Definimos tags de OSM por categoría:
TAGS = {
    "parques": {"leisure": "park"},
    "colegios": {"amenity": "school"},
    # hospitales y clínicas (dos tags posibles):
    "salud": [{"amenity": "hospital"}, {"amenity": "clinic"}],
    # centros comerciales
    "centroscom": {"shop": "mall"},
}

def _get_pois_from_polygon(polygon_gdf, tags):
    """
    Descarga POIs para uno o varios diccionarios de tags OSM.
    Acepta dict o lista de dicts.
    """
    if isinstance(tags, dict):
        tags = [tags]
    frames = []
    for tg in tags:
        pois = ox.features_from_polygon(polygon_gdf.union_all(), tags=tg)
        if not pois.empty:
            # Reset index to ensure no duplicate indices
            # pois = pois.reset_index(drop=True)
            frames.append(pois)
    if frames:
        out = pd.concat(frames, ignore_index=True)
        # conservar solo geometría y algunas columnas estándar
        out = gpd.GeoDataFrame(out, geometry="geometry", crs="EPSG:4326")
        return out
    return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

pois_parques = _get_pois_from_polygon(city_poly_buffer, TAGS["parques"])
pois_colegios = _get_pois_from_polygon(city_poly_buffer, TAGS["colegios"])
pois_salud   = _get_pois_from_polygon(city_poly_buffer, TAGS["salud"])
pois_malls   = _get_pois_from_polygon(city_poly_buffer, TAGS["centroscom"])

# Si alguna categoría viene vacía, creamos un GDF vacío con el CRS correcto
def ensure_gdf(gdf_in):
    if gdf_in is None or gdf_in.empty:
        return gpd.GeoDataFrame({"dummy":[0]}, geometry=[Point()], crs="EPSG:4326").iloc[0:0].copy()
    return gdf_in

pois_parques = ensure_gdf(pois_parques)
pois_colegios = ensure_gdf(pois_colegios)
pois_salud = ensure_gdf(pois_salud)
pois_malls = ensure_gdf(pois_malls)

# =========================
# 3) Medir distancias con sjoin_nearest (rápido)
# =========================
# Usamos centroides como geometría de barrios para el nearest
barrios_pts = gpd.GeoDataFrame(
    gdf.drop(columns=["lat","lon"]).copy(),
    geometry=gpd.points_from_xy(gdf["lon"], gdf["lat"]),
    crs="EPSG:4326"
)

# Proyectamos todo a CRS métrico para que la distancia salga en metros
barrios_pts_m = barrios_pts.to_crs(epsg=CRS_METROS)
parques_m  = pois_parques.to_crs(epsg=CRS_METROS)
colegios_m = pois_colegios.to_crs(epsg=CRS_METROS)
salud_m    = pois_salud.to_crs(epsg=CRS_METROS)
malls_m    = pois_malls.to_crs(epsg=CRS_METROS)

# def nearest_distance_km(orig_points_m, dest_points_m, distance_col_name):
#     if dest_points_m is None or dest_points_m.empty:
#         # No hay POIs: devolvemos NaN
#         return pd.Series([pd.NA]*len(orig_points_m), index=orig_points_m.index, name=distance_col_name)
#     joined = gpd.sjoin_nearest(orig_points_m, dest_points_m[["geometry"]], how="left", distance_col=distance_col_name)
#     # Distancia viene en unidades del CRS (metros). Convertimos a km.
#     joined[distance_col_name] = joined[distance_col_name].astype(float) / 1000.0
#     return joined[distance_col_name]

from scipy.spatial import cKDTree
import numpy as np

def nearest_distance_km(orig_points_m, dest_points_m, distance_col_name):
    """
    Calcula la distancia mínima de cada punto de orig_points_m
    al conjunto de dest_points_m usando cKDTree (rápido y vectorizado).
    Devuelve una serie con la distancia en km.
    """
    # Filtramos geometrías vacías o nulas
    orig_points_m = orig_points_m[~orig_points_m.geometry.is_empty & orig_points_m.geometry.notnull()]
    dest_points_m = dest_points_m[~dest_points_m.geometry.is_empty & dest_points_m.geometry.notnull()]

    if dest_points_m.empty:
        return pd.Series([pd.NA]*len(orig_points_m), index=orig_points_m.index, name=distance_col_name)

    # Extraemos coordenadas X/Y de barrios (ya son puntos)
    orig_coords = np.array(list(orig_points_m.geometry.apply(lambda p: (p.x, p.y))))

    # Extraemos coordenadas de POIs: si son polígonos usamos centroides
    dest_coords = np.array(list(dest_points_m.geometry.apply(lambda g: g.centroid.coords[0] if g.type != "Point" else (g.x, g.y))))

    # Construimos KDTree
    tree = cKDTree(dest_coords)

    # Query: distancia mínima
    dists, _ = tree.query(orig_coords, k=1)  # k=1 = más cercano

    # Convertimos a km
    dists_km = dists / 1000.0

    # Devolvemos serie alineada
    return pd.Series(dists_km, index=orig_points_m.index, name=distance_col_name)


barrios_pts_m["dist_parques_km"]    = nearest_distance_km(barrios_pts_m, parques_m, "dist_parques_m")
barrios_pts_m["dist_colegios_km"]   = nearest_distance_km(barrios_pts_m, colegios_m, "dist_colegios_m")
barrios_pts_m["dist_clinicas_km"]   = nearest_distance_km(barrios_pts_m, salud_m, "dist_clinicas_m")
barrios_pts_m["dist_centroscom_km"] = nearest_distance_km(barrios_pts_m, malls_m, "dist_centroscom_m")


# Definimos las columnas de distancias que calculamos
campos_join = ["dist_parques_km", "dist_colegios_km", "dist_clinicas_km", "dist_centroscom_km"]

# Creamos un ID único para cada fila
gdf["barrio_id"] = gdf.index
barrios_pts_m["barrio_id"] = barrios_pts_m.index

# Unimos usando barrio_id
gdf_out = gdf.merge(
    barrios_pts_m[["barrio_id"] + campos_join],
    on="barrio_id",
    how="left"
)

# Añadimos lat/lon de centroides
gdf_out["lat"] = gdf["lat"]
gdf_out["lon"] = gdf["lon"]

# =========================
# 4) Exportar GeoJSON + CSV
# =========================
out_geojson = "barrios_medellin_distancias.geojson"
out_csv     = "barrios_medellin_distancias.csv"

gdf_out.to_crs(epsg=CRS_GEO).to_file(out_geojson, driver="GeoJSON")
# Para CSV quitamos la geometría
df_csv = pd.DataFrame(gdf_out.drop(columns="geometry"))
df_csv.to_csv(out_csv, index=False)

print("✅ Listo.")
print(f"GeoJSON: {Path(out_geojson).resolve()}")
print(f"CSV    : {Path(out_csv).resolve()}")
