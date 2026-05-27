# /// script
# requires-python = ">=3.12"
# dependencies = ["geopandas", "rasterio", "numpy", "pvlib", "scipy", "pyproj", "matplotlib", "pandas", "laspy"]
# ///

import subprocess
import sys
import os
import gc
from pathlib import Path
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# Configs de diretório
BASE_DIR = Path(__file__).resolve().parent
TEST_DIR = BASE_DIR.parent / "Teste"

# RESOLUÇÃO ULTRA-DENSA (Cada quadrante tem 4x mais pixels que em 0.5m)
GRID_RES = 0.25

# Pipeline sequencial por quadrante
PIPELINE = [
    "dsm.py", "dtm.py", "intensity.py", "ndsm.py", 
    "buildings_footprint.py", "mds_buildings.py", 
    "slope.py", "aspect.py",
    "solar_simulation.py",
    "zonal_statistics.py", "filter.py"
]
  
# Lista consolidada de quadrantes

TILES = [
          "4243",
          "4244",
          "4245",
          "4341",
          "4342",
          "4343",
          "4344",
          "4345",
          "4439",
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
          "6061"
]


def processar_single_tile(tile_id):
    """Worker de alta performance executado de forma paralela por núcleo"""
    t0_tile = time.time()
    out_dir = TEST_DIR / f"Resultados_{tile_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    mds_xyz = next((TEST_DIR / "MDS").glob(f"MDS_{tile_id}*.xyz"), TEST_DIR / "MDS" / f"MDS_{tile_id}.xyz")
    mdt_xyz = next((TEST_DIR / "MDT").glob(f"MDT_{tile_id}*.xyz"), TEST_DIR / "MDT" / f"MDT_{tile_id}.xyz")
    
    if not mds_xyz.exists() or not mdt_xyz.exists():
        return tile_id, False, f"⚠️ [Erro] Insumos .xyz ausentes para o tile {tile_id}."

    env_trabalho = os.environ.copy()
    env_trabalho["RESOLUCAO_ESTEIRA"] = str(GRID_RES)
    env_trabalho[f"XYZ_MDS_{tile_id}"] = str(mds_xyz.name)
    env_trabalho[f"XYZ_MDT_{tile_id}"] = str(mdt_xyz.name)
    
    # Execução otimizada de subprocessos em nível de kernel
    for script in PIPELINE:
        # Passar stdout=None acelera o processo pois joga a saída direto no buffer de IO oculto
        proc = subprocess.run(
            [sys.executable, str(BASE_DIR / script), tile_id],
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.PIPE, 
            text=True, 
            env=env_trabalho
        )
        
        if proc.returncode != 0:
            erro_msg = (
                f"❌ [Falha] Script {script} quebrou no Quadrante {tile_id}!\n"
                f"--- LOG DE ERRO (STDERR) ---\n{proc.stderr}\n"
                f"----------------------------------------"
            )
            return tile_id, False, erro_msg
            
    dt_total = time.time() - t0_tile
    return tile_id, True, f"✅ Quadrante {tile_id} processado com sucesso em {dt_total:.1f}s."


if __name__ == "__main__":
    print("-" * 60)
    print("ORQUESTRADOR PARALELO DE MÁXIMA EFICIÊNCIA - RASTER 0.25m")
    print("-" * 60)
    
    # EQUILÍBRIO ULTRA-RÁPIDO PARA 8GB DE RAM (Evita paginação forçada no SSD)
    MAX_WORKERS = 4
    
    t0_global = time.time()
    sucessos = 0
    falhas = 0
    
    print(f">> Iniciando processamento paralelo assíncrono.")
    print(f">> Threads dedicadas na CPU: {MAX_WORKERS} | Resolução: {GRID_RES}m")
    print(f">> Total de quadrantes a processar: {len(TILES)}")
    print("-" * 60)

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futuros = {executor.submit(processar_single_tile, tile): tile for tile in TILES}
        
        for futuro in as_completed(futuros):
            tile_concluido, status, log = futuro.result()
            print(log)
            
            if status:
                sucessos += 1
            else:
                falhas += 1
                print(f"🛑 [Interrupção] A esteira descartou o tile {tile_concluido} devido ao erro acima.")
            
            # Limpeza cirúrgica da RAM a cada ciclo finalizado
            gc.collect()

    dt_total_lote = time.time() - t0_global
    print("=" * 60)
    print("PROCESSAMENTO EM LOTE FINALIZADO")
    print(f"-> Tempo de corrida: {int(dt_total_lote // 60)}m {dt_total_lote % 60:.1f}s")
    print(f"-> Sucessos acumulados: {sucessos} | Falhas em quarentena: {falhas}")
    print("=" * 60)