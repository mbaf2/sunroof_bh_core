import sys
from pathlib import Path
import geopandas as gpd

# Setup de I/O
tile = sys.argv[1] if len(sys.argv) > 1 else "5250"

# ==============================================================================
# AJUSTE DE ENDEREÇAMENTO GERAL - ARQUITETURA GITHUB / REPOSITÓRIO
# Subimos 2 níveis (.parents[2]) para sair de Python/sunroof_bh_core
# e alteramos o nome do diretório de "Teste" para "Data"
# ==============================================================================
res_dir = Path(__file__).resolve().parents[2] / "Data" / f"Resultados_{tile}"

f_in = res_dir / f"buildings_sunroof_pronto_{tile}.gpkg"
f_out = res_dir / f"buildings_sunroof_FILTRADO_{tile}.gpkg"

if not f_in.exists():
    sys.exit(f"Abort: {f_in.name} não encontrado.")

print(f">> Filtrando ruídos geométricos: {tile}")

gdf = gpd.read_file(f_in)
n_initial = len(gdf)

if n_initial == 0:
    sys.exit(f"Aviso: {tile} vazio. Pulando.")

# Garante que a coluna de área existe calculando na hora
# Isso evita o KeyError caso o zonal_statistics tenha falhado ao gravar
gdf['area_m2'] = gdf.geometry.area

# Filtro de área mínima para descartar artefatos do LiDAR
gdf_clean = gdf[gdf['area_m2'] >= 5.0].copy()
n_final = len(gdf_clean)

# Export
gdf_clean.to_file(f_out, driver="GPKG")

print(f"   - Processados: {n_initial}")
print(f"   - Descartados: {n_initial - n_final}")
print(f"   - Validados  : {n_final}")
print(f"OK: {f_out.name}")