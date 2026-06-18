import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from scipy.interpolate import NearestNDInterpolator
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
  
# Setup de execução
tile = sys.argv[1] if len(sys.argv) > 1 else "5250"

# ==============================================================================
# AJUSTE DE ENDEREÇAMENTO GERAL - ARQUITETURA GITHUB / REPOSITÓRIO
# Subimos 2 níveis (.parents[2]) para sair de Python/sunroof_bh_core
# e alteramos o nome do diretório de "Teste" para "Data"
# ==============================================================================

base_dir = Path(__file__).resolve().parents[2] / "Data"
out_dir = base_dir / f"Resultados_{tile}"
out_dir.mkdir(parents=True, exist_ok=True)

res = float(os.environ.get("RESOLUCAO_PIPELINE", 1.0))
f_name = os.environ.get(f"XYZ_MDS_{tile}", f"MDS_{tile}.xyz")
f_path = base_dir / "MDS" / f_name

if not f_path.exists():
    sys.exit(f"Abort: {f_path.name} não encontrado.")

print(f">> Gerando Raster MDS {f_name} | Res: {res}m")

df = pd.read_csv(f_path, sep=r"\s+", names=["X", "Y", "Z", "I"], usecols=["X", "Y", "Z"])
df = df.sort_values(by="Z", ascending=False).drop_duplicates(subset=["X", "Y"], keep="first")

# MOLDURA FIXA TRAVADA
x_min = np.floor(df.X.min() / 100.0) * 100.0
x_max = np.ceil(df.X.max() / 100.0) * 100.0
y_min = np.floor(df.Y.min() / 100.0) * 100.0
y_max = np.ceil(df.Y.max() / 100.0) * 100.0

gx, gy = np.mgrid[
    x_min : x_max : res, 
    y_max : y_min : -res
]

# PASSO 1: INTERPOLAÇÃO JATO (NEAREST NEIGHBOR)
print(f"   - Interpolando {len(df)} pontos com Nearest...")
interp = NearestNDInterpolator(np.column_stack((df.X, df.Y)), df.Z)
m_mds = interp(gx, gy)

# PASSO 2: SUAVIZAÇÃO MATRICIAL
# sigma=1.0 define o raio de suavização
# Mantém as quinas dos prédios razoavelmente firmes e tira o serrilhado do teto.
print("   - Aplicando suavização Gaussiana na matriz...")
m_mds_suave = gaussian_filter(m_mds, sigma=1.0)

arvore = cKDTree(np.column_stack((df.X, df.Y)))
grid_pontos = np.column_stack((gx.ravel(), gy.ravel()))
distancias, _ = arvore.query(grid_pontos, k=1)

matriz_distancias = distancias.reshape(gx.shape)

m_mds_suave[matriz_distancias > 1.0] = -9999.0

# ==============================================================================
# GEOTRANSFORM AFIM AJUSTADO E CORREÇÃO DE SHAPE
# ==============================================================================
m_mds_final = m_mds_suave.T
h, w = m_mds_final.shape

transform = from_origin(
    west = x_min - (res / 2.0), 
    north = y_max + (res / 2.0), 
    xsize = res, 
    ysize = res
)

meta = {
    "driver": "GTiff", 
    "height": h, 
    "width": w, 
    "count": 1,
    "dtype": "float32", 
    "crs": "EPSG:31983", 
    "transform": transform, 
    "nodata": -9999.0
}

f_out = out_dir / f"RASTER_MDS_{tile}.tif"
with rasterio.open(f_out, "w", **meta) as dst:
    dst.write(m_mds_final.astype(np.float32), 1)

print(f"OK: {f_out.name} | Shape: ({h}, {w})")