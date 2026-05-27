import sys
import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
from pathlib import Path

# Config inicial
tile_id = sys.argv[1] if len(sys.argv) > 1 else "5250"
root_dir = Path(__file__).resolve().parents[1] / "Teste" / f"Resultados_{tile_id}"

files = {
    "vector": root_dir / f"buildings_zone_{tile_id}.gpkg",
    "mds": root_dir / f"RASTER_MDS_{tile_id}.tif",
    "mdt": root_dir / f"RASTER_MDT_{tile_id}.tif",
    "ndsm": root_dir / f"RASTER_nDSM_{tile_id}.tif",
    "slope": root_dir / f"RASTER_Slope_{tile_id}.tif",
    "aspect": root_dir / f"RASTER_Aspect_{tile_id}.tif",
    "solar": root_dir / f"RASTER_Irradiacao_{tile_id}.tif"
}

if not all(f.exists() for f in files.values()):
    sys.exit(f"Erro: Insumos ausentes in {root_dir}")

print(f">> Processando Quadrante {tile_id} com Otimização de Micro-Janelas...")

gdf = gpd.read_file(files["vector"])
out_path = root_dir / f"buildings_sunroof_pronto_{tile_id}.gpkg"

if gdf.empty:
    print(f"Aviso: o quadrante {tile_id} n�o possui edificac�es vetorizadas.")
    cols = ['h_mean','h_max', 'slope_mean', 'aspect_pred', 'kwh_m2_avg', 'kwh_total_ yr', 'area_util_m2', 'area_tot_m2']
    for col in cols: 
        gdf[col] = None
    gdf.to_file(out_path, driver="GPKG")
    print(f"Ok: {out_path.name} (Salvo vazio por consistencia)")
    sys.exit(0)	

THRESHOLD_SOLAR = 1200.0 
results = []

# ==============================================================================
# ESTRATÉGIA DE ALTA PERFORMANCE: LEITURA POR JANELAS GEOMÉTRICAS LOCAIS
# Abrimos os arquivos raster mantendo os ponteiros prontos para leituras cirúrgicas.
# Evitamos alocar e varrer matrizes globais de 16 milhões de pixels repetitivamente.
# ==============================================================================
with rasterio.open(files["ndsm"]) as src_h, \
     rasterio.open(files["slope"]) as src_s, \
     rasterio.open(files["aspect"]) as src_a, \
     rasterio.open(files["solar"]) as src_rad:
     
    px_area = abs(src_rad.res[0] * src_rad.res[1])
    
    for geom in gdf.geometry:
        if geom is None or geom.is_empty:
            results.append([0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0])
            continue
            
        try:
            # O GRANDE TRUQUE: Captura os limites geométricos exatos do polígono do prédio
            bounds = geom.bounds  # (minx, miny, maxx, maxy)
            
            # Cria uma janela local (Bounding Box) correspondente a esses limites no raster
            window = from_bounds(*bounds, transform=src_rad.transform)
            
            # Arredonda os limites da janela para índices inteiros de pixels
            window = window.round_shape()
            
            # Obtém a matriz de transformação afim local e o shape específico da janela pequena
            win_transform = src_rad.window_transform(window)
            win_shape = (window.height, window.width)
            
            # Lê apenas o micro-retângulo de dados correspondente ao prédio (fração de milissegundos)
            arr_h = src_h.read(1, window=window)
            arr_s = src_s.read(1, window=window)
            arr_a = src_a.read(1, window=window)
            arr_r = src_rad.read(1, window=window)
            
            # Desenha a máscara booleana estritamente sobre o tamanho reduzido da micro-janela
            mask_geom = geometry_mask([geom], out_shape=win_shape, transform=win_transform, invert=True)
            
            # Isolamos os valores válidos ignorando o NoData dentro da micro-janela
            val_h = arr_h[mask_geom & (arr_h != -9999.0)]
            val_s = arr_s[mask_geom & (arr_s != -9999.0)]
            val_a = arr_a[mask_geom & (arr_a != -9999.0)]
            val_r = arr_r[mask_geom & (arr_r != -9999.0)]

            # Estatísticas descritivas otimizadas com NumPy nativo
            h_med = float(np.mean(val_h)) if val_h.size > 0 else 0.0
            h_max = float(np.max(val_h)) if val_h.size > 0 else 0.0
            s_med = float(np.mean(val_s)) if val_s.size > 0 else 0.0
            
            if val_a.size > 0:
                vals, counts = np.unique(val_a, return_counts=True)
                a_pred = float(vals[np.argmax(counts)])
            else:
                a_pred = -1.0
                
            # Análise de Potencial Solar vetorizada no subset mapeado
            if val_r.size > 0:
                r_med = float(np.mean(val_r))
                mask_util = val_r >= THRESHOLD_SOLAR
                a_util = float(np.sum(mask_util) * px_area)
                r_total = float(np.sum(val_r[mask_util]) * px_area)
            else:
                r_med = a_util = r_total = 0.0
            
            results.append([h_med, h_max, s_med, a_pred, r_med, r_total, a_util])
                
        except Exception:
            results.append([0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0])

# Acoplamento dos resultados na tabela geoespacial
cols = ['h_mean', 'h_max', 'slope_mean', 'aspect_pred', 'kwh_m2_avg', 'kwh_total_yr', 'area_util_m2']
res_df = np.array(results)

for i, col in enumerate(cols):
    gdf[col] = res_df[:, i]

gdf['area_tot_m2'] = gdf.geometry.area

# Export do banco consolidado
gdf.to_file(out_path, driver="GPKG")
print(f"OK: {out_path.name}")

# ==============================================================================
# LIXEIRO AUTOMÁTICO - FAXINA DE ÚLTIMA HORA
# ==============================================================================

print(f"[Limpeza] Executando remoção de rasters intermediários para {tile_id}...")

arquivos_para_deletar = [
    files["mds"],
    files["mdt"],
    files["ndsm"],
    files["slope"],
    files["aspect"]
]

removidos = 0
for caminho in arquivos_para_deletar:
    try:
        if caminho.exists():
            os.remove(caminho)
            print(f"  [Lixeiro] Excluído: {caminho.name}")
            print(f"  [Lixeiro] Excluído: {caminho.name}")
            removidos += 1
    except Exception as e:
        print(f"  [Aviso] Falha ao deletar {caminho.name}: {e}")

print(f"[Limpeza] Concluída. {removidos} rasters apagados. Apenas a irradiação e o gpkg foram mantidos!\n")
  