import sys
import os
from pathlib import Path
import numpy as np
import rasterio

# Identificador do quadrante
tile = sys.argv[1] if len(sys.argv) > 1 else "5250"
tile_dir = Path(__file__).resolve().parent.parent / "Teste" / f"Resultados_{tile}"
  
# ==============================================================================
# NOMENCLATURA UNIFICADA: MDS apontando para o padrão correto RASTER_MDS_
# ==============================================================================
  
src_files = {
    "mds": tile_dir / f"RASTER_MDS_Buildings_{tile}.tif", # Alterado aqui!
    "slope": tile_dir / f"RASTER_Slope_{tile}.tif",
    "aspect": tile_dir / f"RASTER_Aspect_{tile}.tif"
}

out_solar = tile_dir / f"RASTER_Irradiacao_{tile}.tif"

if not all(p.exists() for p in src_files.values()):
    sys.exit(f"Erro: Insumos geométricos ausentes em {tile_dir}")

print(f">> Iniciando simulação solar: Tile {tile}")

with rasterio.open(src_files["mds"]) as s_mds, \
     rasterio.open(src_files["slope"]) as s_slp, \
     rasterio.open(src_files["aspect"]) as s_asp:
     
    mds = s_mds.read(1)
    slp = np.radians(s_slp.read(1))
    asp = np.radians(s_asp.read(1))
    meta = s_mds.meta.copy()

# Constantes (BH: -19.92)
LAT = np.radians(-19.92)
G_SC = 1367.0  # Solar constant W/m2

# Dias médios mensais e pesos
doy_list = [17, 47, 75, 105, 135, 162, 198, 228, 258, 288, 318, 344]
weights = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

acc_energy = np.zeros_like(mds, dtype=np.float32)

# Loop de integração temporal
for doy, w in zip(doy_list, weights):
    # Declinação (Cooper)
    dec = np.radians(23.45 * np.sin(2 * np.pi * (284 + doy) / 365))
    e_day = np.zeros_like(mds, dtype=np.float32)
    
    # Integração comercial (08h - 16h)
    for h in range(8, 17, 2):
        hra = np.radians((h - 12) * 15)
        
        # Geometria solar
        sin_el = (np.sin(LAT) * np.sin(dec) + np.cos(LAT) * np.cos(dec) * np.cos(hra))
        
        # Só calcula se o sol estiver de fato acima do horizonte para a latitude de BH
        if sin_el > 0:
            el = np.arcsin(np.clip(sin_el, 0, 1))
            
            cos_az = ((np.sin(dec) - np.sin(LAT) * sin_el) / (np.cos(LAT) * np.cos(el)))
            az = np.arccos(np.clip(cos_az, -1, 1))
            az = np.where(hra > 0, 2 * np.pi - az, az)
            
            # Incidência na superfície do telhado
            cos_theta = (sin_el * np.cos(slp) + np.cos(el) * np.sin(slp) * np.cos(az - asp))
            cos_theta = np.clip(cos_theta, 0, None)
            
            # Modelo simplificado (Beam + Diffuse)
            beam = G_SC * 0.7 * cos_theta
            diff = G_SC * 0.2 * (1 + np.cos(slp)) / 2
            
            e_inst = beam + diff
            
            # Acumula apenas onde não é NoData
            e_day += np.where(mds == -9999.0, 0.0, e_inst) * 2
            
    acc_energy += e_day * w

# Conversão Wh -> kWh e Nodata
kwh_yr = acc_energy / 1000.0
kwh_yr[mds == -9999.0] = -9999.0

# Export
meta.update(dtype="float32", nodata=-9999.0)
with rasterio.open(out_solar, "w", **meta) as dst:
    dst.write(kwh_yr.astype(np.float32), 1)

print(f"OK: {out_solar.name}")