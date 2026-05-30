import sys
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from pathlib import Path

# Identificador do tile
tile = sys.argv[1] if len(sys.argv) > 1 else "5250"

# ==============================================================================
# AJUSTE DE ENDEREÇAMENTO GERAL - ARQUITETURA GITHUB / REPOSITÓRIO
# Subimos 2 níveis (.parents[2]) para sair de Python/sunroof_bh_core,
# apontamos para a nova pasta "Data" e padronizamos o arquivo de saída.
# ==============================================================================
res_dir = Path(__file__).resolve().parents[2] / "Data" / f"Resultados_{tile}"

f_mds = res_dir / f"RASTER_MDS_{tile}.tif"
f_vec = res_dir / f"buildings_zone_{tile}.gpkg"

f_out = res_dir / f"RASTER_MDS_{tile}.tif"

if not f_mds.exists() or not f_vec.exists():
    sys.exit(f"Abort: Insumos ausentes para mascaramento do MDS no tile {tile}")

print(f">> Isolando MDS apenas para as Edificações: {tile}")

# Carrega o vetor recortado dos prédios
gdf = gpd.read_file(f_vec)

with rasterio.open(f_mds) as src:
    m_mds = src.read(1)
    meta = src.meta.copy()
    transform = src.transform
    shape_raster = m_mds.shape

if len(gdf) > 0 and not gdf.geometry.is_empty.all():
    mask_predios = geometry_mask(gdf.geometry, out_shape=shape_raster, transform=transform, invert=True)
    
    # Tudo o que NÃO for prédio vira NoData (-9999.0)
    m_mds_buildings = np.where(mask_predios, m_mds, -9999.0)
else:
    # Se o quadrante não tiver nenhum prédio, o raster inteiro vira NoData
    m_mds_buildings = np.full(shape_raster, -9999.0, dtype=np.float32)

# Salva o MDS exclusivo dos telhados
meta.update(dtype="float32", nodata=-9999.0)
with rasterio.open(f_out, "w", **meta) as dst:
    dst.write(m_mds_buildings.astype(np.float32), 1)

print(f"OK: {f_out.name}")