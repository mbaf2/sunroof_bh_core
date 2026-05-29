import subprocess
import sys
import os
from pathlib import Path
import numpy as np
import time

# ==============================================================================
# AJUSTE DE ENDEREÇAMENTO GERAL - ARQUITETURA GITHUB / REPOSITÓRIO
# Como este script roda dentro de Python/sunroof_bh_core, subimos 2 níveis (.parents[1])
# para encontrar a raiz do projeto e alteramos a pasta de "Teste" para "Data"
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parents[1] / "Data"

tiles = [
    "5050",
#    "5051",
#    "5052",
#    "5053",
#    "5054",
#    "5055",
#    "5056",
#    "5057",
#    "5058",
#    "5059",
#    "5060"
         ]
RESOLUTION = 0.25

scripts = [
    "dsm.py", "dtm.py", 
#    "intensity.py", 
    "ndsm.py", 
    "buildings_footprint.py", "mds_buildings.py", 
    "slope.py", "aspect.py",
    "solar_simulation.py",
    "zonal_statistics.py", "filter.py"
]

def process_las_files(src_path, tile_id, out_xyz):
    """Localiza arquivos .las/.laz e exporta para um único .xyz via numpy"""
    import laspy
    
    files = list(src_path.rglob(f"*{tile_id}*.las")) + list(src_path.rglob(f"*{tile_id}*.laz"))
    if not files:
        return False
        
    print(f"  [LiDAR] {len(files)} arquivos encontrados. Unificando...")
    
    with open(out_xyz, "w") as f:
        for p in files:
            try:
                print(f"    -> {p.name}")
                las = laspy.read(p)
                
                # Stack de coordenadas e intensidade
                intensity = las.intensity if hasattr(las, 'intensity') else np.zeros_like(las.x)
                pts = np.column_stack((las.x, las.y, las.z, intensity))
                
                np.savetxt(f, pts, fmt="%.3f %.3f %.3f %d")
                del las, pts
                
            except Exception as e:
                print(f"    [ERR] Falha em {p.name}: {e}")

    return True

print("-" * 60)
print(f"ORQUESTRADOR - PROJETO BH | Res: {RESOLUTION}m")
print("-" * 60)

for tile in tiles:
    t0 = time.time()
    
    out_path = ROOT_DIR / f"Resultados_{tile}"
    os.makedirs(out_path, exist_ok=True)
    
    # Busca por fontes MDS/MDT dentro da nova pasta Data
    f_mds = next((ROOT_DIR / "MDS").glob(f"MDS_{tile}*.xyz"), ROOT_DIR / "MDS" / f"MDS_{tile}.xyz")
    f_mdt = next((ROOT_DIR / "MDT").glob(f"MDT_{tile}*.xyz"), ROOT_DIR / "MDT" / f"MDT_{tile}.xyz")
    
    print(f"\n>> Tile: {tile}")
    
    # Garantia de insumos
    if not f_mds.exists():
        print(f"  MDS .xyz não encontrado. Buscando .las...")
        f_mds = ROOT_DIR / "MDS" / f"MDS_{tile}.xyz"
        if not process_las_files(ROOT_DIR / "MDS", tile, f_mds):
            print(f"  [CRITICAL] Falha ao obter dados MDS.")
            continue
            
    if not f_mdt.exists():
        print(f"  MDT .xyz não encontrado. Buscando .las...")
        f_mdt = ROOT_DIR / "MDT" / f"MDT_{tile}.xyz"
        if not process_las_files(ROOT_DIR / "MDT", tile, f_mdt):
            print(f"  [CRITICAL] Falha ao obter dados MDT.")
            continue

    # Env vars para comunicação com scripts filhos
    os.environ["RESOLUCAO_ESTEIRA"] = str(RESOLUTION)
    os.environ[f"XYZ_MDS_{tile}"] = f_mds.name
    os.environ[f"XYZ_MDT_{tile}"] = f_mdt.name
    
    for s in scripts:
        print(f"  exec: {s} ... ", end="", flush=True)
        ts = time.time()
        
        proc = subprocess.run(
            [sys.executable, str(BASE_DIR / s), tile],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
          
        d_ts = time.time() - ts
        
        if proc.returncode == 0:
            print(f"OK ({d_ts:.2f}s)")
        else:
            print("FAIL")
            print(f"\n--- STDERR: {s} ---\n{proc.stderr}\n" + "-"*30)
            break
    else:
        dt = time.time() - t0
        h_time = f"{int(dt//60)}m {dt%60:.1f}s" if dt >= 60 else f"{dt:.2f}s"
        print(f"\n[DONE] Tile {tile} concluído em {h_time}")

print("\nFim do processamento.")