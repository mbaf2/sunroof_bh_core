import sys
from pathlib import Path
import numpy as np
import rasterio

# Identificador do tile
tile = sys.argv[1] if len(sys.argv) > 1 else "5250"

# ==============================================================================
# AJUSTE DE ENDEREÇAMENTO GERAL - ARQUITETURA GITHUB / REPOSITÓRIO
# Subimos 2 níveis (.parents[2]) para sair de Python/sunroof_bh_core,
# apontamos para a nova pasta "Data" e unificamos a nomenclatura do MDS.
# ==============================================================================
work_dir = Path(__file__).resolve().parents[2] / "Data" / f"Resultados_{tile}"
  
# Nomenclatura unificada para ler o MDS real gerado na esteira
f_mds = work_dir / f"RASTER_MDS_{tile}.tif"
f_slp = work_dir / f"RASTER_Slope_{tile}.tif"
f_out = work_dir / f"RASTER_Aspect_{tile}.tif"

if not f_mds.exists() or not f_slp.exists():
    sys.exit(f"Abort: Insumos ausentes em {work_dir}")

print(f">> Calculando Orientação (Aspect): {tile}")

with rasterio.open(f_mds) as src_mds, rasterio.open(f_slp) as src_slp:
    m_mds = src_mds.read(1)
    m_slp = src_slp.read(1)
    meta = src_mds.meta.copy()
    res = src_mds.res[0]

# ==============================================================================
# CÁLCULO SEGURO DA ORIENTAÇÃO DO RELEVO
# Calculamos os gradientes direto na matriz cheia para shapes idênticos garantidos
# ==============================================================================
gy, gx = np.gradient(m_mds, res)

# arctan2 retorna valores entre -pi e +pi. 
# Convertemos para azimute em graus (0° a 360°), onde 0°/360° é o Norte
aspect = np.degrees(np.arctan2(-gx, gy))
aspect = np.where(aspect < 0.0, aspect + 360.0, aspect)

# REGRA DE SEGURANÇA ESPACIAL: Onde o telhado/terreno for plano (Slope < 1°), 
# não existe uma direção de escoamento real. Forçamos o valor padrão -1.0.
# Agora com as duas matrizes vindo da mesma fôrma tridimensional, o broadcast funciona perfeito!
aspect = np.where(m_slp < 1.0, -1.0, aspect)

# Restauração estrita do NoData original do MDS
aspect[m_mds == -9999.0] = -9999.0

# Export final para o SIG
meta.update(dtype="float32", nodata=-9999.0)
with rasterio.open(f_out, "w", **meta) as dst:
    dst.write(aspect.astype(np.float32), 1)

print(f"OK: {f_out.name}")