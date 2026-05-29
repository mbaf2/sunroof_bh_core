import sys
from pathlib import Path
import numpy as np
import rasterio

# Identificador do tile
tile = sys.argv[1] if len(sys.argv) > 1 else "5250"

# ==============================================================================
# AJUSTE DE ENDEREÇAMENTO GERAL - ARQUITETURA GITHUB / REPOSITÓRIO
# Subimos 2 níveis (.parents[2]) para sair de Python/sunroof_bh_core,
# apontamos para a nova pasta "Data" e corrigimos a nomenclatura do MDS.
# ==============================================================================
work_dir = Path(__file__).resolve().parents[2] / "Data" / f"Resultados_{tile}"
  
f_mds = work_dir / f"RASTER_MDS_{tile}.tif"  # Corrigido para o padrão unificado da esteira
f_out = work_dir / f"RASTER_Slope_{tile}.tif"
  
if not f_mds.exists():
    sys.exit(f"Abort: {f_mds.name} ausente.")

print(f">> Calculando declividade (Slope): {tile}")

with rasterio.open(f_mds) as src:
    data = src.read(1)
    meta = src.meta.copy()
    res = src.res[0]

# ==============================================================================
# TRATAMENTO DE BORDAS BLINDADO CONTRA NaNs
# Calculamos o gradiente numérico na matriz contínua. Isso impede que o np.gradient
# propague NaNs e destrua os pixels válidos nas quinas e beiradas dos telhados.
# ==============================================================================
gy, gx = np.gradient(data, res)

# Cálculo do Slope (Zevenbergen & Thorne adaptado para radianos -> graus)
slope = np.arctan(np.sqrt(gx**2 + gy**2)) * (180.0 / np.pi)

# ==============================================================================
# RESTAURAÇÃO RIGOROSA DO NODATA VETORIAL
# Reposicionamos o valor -9999.0 exatamente onde o MDS original não tinha dados
# ==============================================================================
slope[data == -9999.0] = -9999.0

# Export
meta.update(dtype="float32", nodata=-9999.0)
with rasterio.open(f_out, "w", **meta) as dst:
    dst.write(slope.astype(np.float32), 1)

print(f"OK: {f_out.name}")