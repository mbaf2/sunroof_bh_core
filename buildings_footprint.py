import sys
from pathlib import Path
import geopandas as gpd
import rasterio
from shapely.geometry import box

# Configuração de Tile
tile = sys.argv[1] if len(sys.argv) > 1 else "5250"

# ==============================================================================
# AJUSTE DE ENDEREÇAMENTO GERAL - ARQUITETURA GITHUB / REPOSITÓRIO
# Subimos 2 níveis (.parents[2]) para sair de Python/sunroof_bh_core
# e alteramos o nome do diretório de "Teste" para "Data"
# ==============================================================================
base_dir = Path(__file__).resolve().parents[2] / "Data"
out_dir = base_dir / f"Resultados_{tile}"

# I/O
f_ndsm = out_dir / f"RASTER_nDSM_{tile}.tif"
f_shp = base_dir / "EDIFICACAO" / "EDIFICACAO.shp"
f_out = out_dir / f"buildings_zone_{tile}.gpkg"

if not f_ndsm.exists() or not f_shp.exists():
    sys.exit(f"Abort: Insumos (nDSM ou SHP) ausentes para o tile {tile}")

print(f">> Recortando footprints (Clip): {tile}")

# Obtém o bounding box do raster para leitura otimizada do vetor
with rasterio.open(f_ndsm) as src:
    b = src.bounds
    bbox = (b.left, b.bottom, b.right, b.top)

# Lê o SHP filtrando espacialmente já na carga (economiza memória)
gdf = gpd.read_file(f_shp, bbox=bbox)

# Ajuste de CRS se necessário
target_crs = "EPSG:31983"
if gdf.crs != target_crs:
    gdf = gdf.to_crs(target_crs)
  
# Clip final para garantir geometria exata aos limites do raster
clip_box = box(*bbox)
gdf_clipped = gpd.clip(gdf, clip_box)

# Export
gdf_clipped.to_file(f_out, driver="GPKG")

print(f"   - Edificações: {len(gdf_clipped)}")
print(f"OK: {f_out.name}")