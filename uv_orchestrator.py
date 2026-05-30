# /// script
# requires-python = ">=3.12"
# dependencies = ["geopandas", "rasterio", "numpy", "pvlib", "scipy", "pyproj", "matplotlib", "pandas", "laspy"]
# ///

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
DATA_DIR = BASE_DIR.parents[1] / "Data"
    
# Configuração do processamento
tiles = [
          "4243",
          "4244",
          "4245",
          "4341",
          "4342",
          "4343",
          "4344",
          "4345",
          "4439",
         '''
          "4440",
          "4441",
          "4442",
          "4443",
          "4444",
          "4538",
          "4539",
          "4540",
          "4541",
          "4542",
          "4543",
          "4544",
          "4545",
          "4548",
          "4549",
          "4550",
          "4551",
          "4552",
          "4553",
          "4556",
          "4557",
          "4635",
          "4636",
          "4637",
          "4638",
          "4639",
          "4640",
          "4641",
          "4642",
          "4643",
          "4644",
          "4645",
          "4646",
          "4647",
          "4648",
          "4649",
          "4650",
          "4651",
          "4652",
          "4653",
          "4654",
          "4655",
          "4656",
          "4657",
          "4658",
          "4659",
          "4660",
          "4661",
          "4662",
          "4735",
          "4736",
          "4737",
          "4738",
          "4739",
          "4740",
          "4741",
          "4742",
          "4743",
          "4744",
          "4745",
          "4746",
          "4747",
          "4748",
          "4749",
          "4750",
          "4751",
          "4752",
          "4753",
          "4754",
          "4755",
          "4756",
          "4757",
          "4758",
          "4759",
          "4760",
          "4761",
          "4762",
          "4763",
          "4764",
          "4837",
          "4838",
          "4839",
          "4840",
          "4841",
          "4842",
          "4843",
          "4844",
          "4845",
          "4846",
          "4847",
          "4848",
          "4849",
          "4850",
          "4851",
          "4852",
          "4853",
          "4854",
          "4855",
          "4856",
          "4857",
          "4858",
          "4859",
          "4860",
          "4861",
          "4862",
          "4863",
          "4864",
          "4865",
          "4866",
          "4939",
          "4940",
          "4941",
          "4942",
          "4943",
          "4944",
          "4945",
          "4946",
          "4947",
          "4948",
          "4949",
          "4950",
          "4951",
          "4952",
          "4953",
          "4954",
          "4955",
          "4956",
          "4957",
          "4958",
          "4959",
          "4960",
          "4961",
          "4962",
          "4963",
          "4964",
          "4965",
          "4966",
          "5041",
          "5042",
          "5043",
          "5044",
          "5045",
          "5046",
          "5047",
          "5048",
          "5049",
          "5050",
          "5051",
          "5052",
          "5053",
          "5054",
          "5055",
          "5056",
          "5057",
          "5058",
          "5059",
          "5060",
          "5061",
          "5062",
          "5063",
          "5064",
          "5065",
          "5066",
          "5141",
          "5142",
          "5143",
          "5144",
          "5145",
          "5146",
          "5147",
          "5148",
          "5149",
          "5150",
          "5151",
          "5152",
          "5153",
          "5154",
          "5155",
          "5156",
          "5157",
          "5158",
          "5159",
          "5160",
          "5161",
          "5162",
          "5163",
          "5164",
          "5165",
          "5166",
          "5167",
          "5243",
          "5244",
          "5245",
          "5246",
          "5247",
          "5248",
          "5249",
          "5250",
          "5251",
          "5252",
          "5253",
          "5254",
          "5255",
          "5256",
          "5257",
          "5258",
          "5259",
          "5260",
          "5261",
          "5262",
          "5263",
          "5264",
          "5265",
          "5266",
          "5267",
          "5344",
          "5345",
          "5346",
          "5347",
          "5348",
          "5349",
          "5350",
          "5351",
          "5352",
          "5353",
          "5354",
          "5355",
          "5356",
          "5357",
          "5358",
          "5359",
          "5360",
          "5361",
          "5362",
          "5363",
          "5364",
          "5445",
          "5446",
          "5447",
          "5448",
          "5449",
          "5450",
          "5451",
          "5452",
          "5453",
          "5454",
          "5455",
          "5456",
          "5457",
          "5458",
          "5459",
          "5460",
          "5461",
          "5462",
          "5463",
          "5464",
          "5545",
          "5546",
          "5547",
          "5548",
          "5549",
          "5550",
          "5551",
          "5552",
          "5553",
          "5554",
          "5555",
          "5556",
          "5557",
          "5558",
          "5559",
          "5560",
          "5561",
          "5562",
          "5563",
          "5564",
          "5646",
          "5647",
          "5648",
          "5649",
          "5650",
          "5651",
          "5652",
          "5653",
          "5654",
          "5655",
          "5656",
          "5657",
          "5658",
          "5659",
          "5660",
          "5661",
          "5662",
          "5663",
          "5664",
          "5747",
          "5748",
          "5749",
          "5750",
          "5751",
          "5752",
          "5753",
          "5754",
          "5755",
          "5756",
          "5757",
          "5758",
          "5759",
          "5760",
          "5761",
          "5762",
          "5763",
          "5848",
          "5849",
          "5850",
          "5851",
          "5852",
          "5853",
          "5856",
          "5857",
          "5858",
          "5859",
          "5860",
          "5861",
          "5862",
          "5863",
          "5949",
          "5950",
          "5951",
          "5957",
          "5958",
          "5959",
          "5960",
          "5961",
          "5962",
          "6057",
          "6058",
          '''
          "6061"
         ]

GRID_RES = 1

pipeline = [
    "dsm.py", "dtm.py", 
#    "intensity.py", 
    "ndsm.py", 
    "buildings_footprint.py", "mds_buildings.py", 
    "slope.py", "aspect.py",
    "solar_simulation.py",
    "zonal_statistics.py", "filter.py"
]

def convert_las_to_xyz(search_path, tile_id, out_file):
    """Localiza arquivos LiDAR e unifica em um .xyz"""
    import laspy
    
    las_files = list(search_path.rglob(f"*{tile_id}*.las")) + list(search_path.rglob(f"*{tile_id}*.laz"))
    
    if not las_files:
        return False
        
    print(f"  [LiDAR] {len(las_files)} arquivos encontrados. Unificando...")
    
    created = False
    with open(out_file, "w") as f:
        for arq in las_files:
            try:
                print(f"    - {arq.name}")
                las = laspy.read(arq)
                
                # Stack de dados (x, y, z, intensidade)
                intensity = las.intensity if hasattr(las, 'intensity') else np.zeros_like(las.x)
                data = np.column_stack((las.x, las.y, las.z, intensity))
                
                np.savetxt(f, data, fmt="%.3f %.3f %.3f %d")
                created = True
                del las, data
                
            except Exception as e:
                print(f"    [SKIP] Erro em {arq.name}: {e}")

    return created

print("-" * 50)
print("ORQUESTRADOR - PROJETO BH")
print("Resolução: {GRID_RES:.2f}")
print("-" * 50)

for tile in tiles:
    t0_global = time.time()
    
    out_dir = DATA_DIR / f"Resultados_{tile}"
    os.makedirs(out_dir, exist_ok=True)
    
    # Busca por fontes MDS/MDT dentro da nova pasta Data
    mds_xyz = next((DATA_DIR / "MDS").glob(f"MDS_{tile}*.xyz"), DATA_DIR / "MDS" / f"MDS_{tile}.xyz")
    mdt_xyz = next((DATA_DIR / "MDT").glob(f"MDT_{tile}*.xyz"), DATA_DIR / "MDT" / f"MDT_{tile}.xyz")
    
    print(f"\n>> Iniciando Tile: {tile}")
    
    # Garantia de dados (converte se necessário)
    if not mds_xyz.exists():
        print(f"  MDS .xyz não encontrado. Buscando .las...")
        mds_xyz = DATA_DIR / "MDS" / f"MDS_{tile}.xyz"
        if not convert_las_to_xyz(DATA_DIR / "MDS", tile, mds_xyz):
            print(f"  [ERRO] Sem fonte MDS para o tile {tile}.")
            continue
            
    if not mdt_xyz.exists():
        print(f"  MDT .xyz não encontrado. Buscando .las...")
        mdt_xyz = DATA_DIR / "MDT" / f"MDT_{tile}.xyz"
        if not convert_las_to_xyz(DATA_DIR / "MDT", tile, mdt_xyz):
            print(f"  [ERRO] Sem fonte MDT para o tile {tile}.")
            continue

    # Env vars para os scripts filhos
    os.environ["RESOLUCAO_ESTEIRA"] = str(GRID_RES)
    os.environ[f"XYZ_MDS_{tile}"] = str(mds_xyz.name)
    os.environ[f"XYZ_MDT_{tile}"] = str(mdt_xyz.name)
    
    for script in pipeline:
        print(f"  exec: {script} ... ", end="", flush=True)
        t0_script = time.time()
        
        proc = subprocess.run(
            [sys.executable, str(BASE_DIR / script), tile],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        
        dt_script = time.time() - t0_script
        
        if proc.returncode == 0:
            print(f"OK ({dt_script:.2f}s)")
        else:
            print("FAIL")
            print(f"\n--- STDERR: {script} ---\n{proc.stderr}\n" + "-"*20)
            break
    else:
        dt_global = time.time() - t0_global
        h_time = f"{int(dt_global//60)}m {dt_global%60:.1f}s" if dt_global > 60 else f"{dt_global:.2f}s"
        print(f"\n[DONE] Tile {tile} finalizado em {h_time}")

print("\nProcessamento em lote concluído.")