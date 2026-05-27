import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from scipy.interpolate import NearestNDInterpolator

# Setup de execução
tile = sys.argv[1] if len(sys.argv) > 1 else "5250"
base_dir = Path(__file__).resolve().parents[1] / "Teste"
out_dir = base_dir / f"Resultados_{tile}"
out_dir.mkdir(parents=True, exist_ok=True)
  
# Parâmetros da esteira
res = float(os.environ.get("RESOLUCAO_ESTEIRA", 1.0))
f_name = os.environ.get(f"XYZ_MDS_{tile}", f"MDS_{tile}.xyz")
f_path = base_dir / "MDS" / f_name

if not f_path.exists():
    sys.exit(f"Abort: Arquivo {f_path.name} não encontrado.")

print(f">> Rasterizando Intensidade: {f_name} | Res: {res}m")

# Carga de dados (X, Y, Z, Intensity)
df = pd.read_csv(f_path, sep=r"\s+", names=["X", "Y", "Z", "I"], usecols=["X", "Y", "I"])

df = df.sort_values(by="I", ascending=False).drop_duplicates(subset=["X", "Y"], keep="first")

x_min, x_max = df["X"].min(), df["X"].max()
y_min, y_max = df["Y"].min(), df["Y"].max()

x_vec = np.arange(x_min, x_max, res)
y_vec = np.arange(y_max, y_min, -res)
gx, gy = np.meshgrid(x_vec, y_vec)

# Interpolação Nearest Neighbor
print(f"   - Interpolando {len(df)} pontos...")
interp = NearestNDInterpolator(np.column_stack((df.X, df.Y)), df.I)
m_intensity = interp(gx, gy)

# Meta e Export
h, w = m_intensity.shape
transform = from_origin(x_min, y_max, res, res)

meta = {
    "driver": "GTiff", "height": h, "width": w, "count": 1,
    "dtype": "float32", "crs": "EPSG:31983", "transform": transform, "nodata": -9999.0
}

f_out = out_dir / f"RASTER_LIDAR_{tile}.tif"
with rasterio.open(f_out, "w", **meta) as dst:
    dst.write(m_intensity.astype(np.float32), 1)

print(f"OK: {f_out.name}")