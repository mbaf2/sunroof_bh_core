# /// script
# requires-python = ">=3.12"
# dependencies = ["geopandas", "rasterio", "numpy", "pvlib", "scipy", "pyproj", "matplotlib", "pandas", "laspy"]
# ///

import subprocess
import sys
import os
import gc
import argparse
from pathlib import Path
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# ==============================================================================
# CONFIGURAÇÕES DE DIRETÓRIO E PIPELINE
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parents[1] / "Data"
GRID_RES = 0.5

PIPELINE = [
    "dsm.py", "dtm.py", 
    # "intensity.py", 
    "ndsm.py", 
    "buildings_footprint.py", "mds_buildings.py", 
    "slope.py", "aspect.py",
    "solar_simulation.py",
    "zonal_statistics.py", "filter.py"
]

def processar_single_tile(tile_id):
    t0_tile = time.time()
    out_dir = DATA_DIR / f"Resultados_{tile_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    mds_xyz = next((DATA_DIR / "MDS").glob(f"MDS_{tile_id}*.xyz"), DATA_DIR / "MDS" / f"MDS_{tile_id}.xyz")
    mdt_xyz = next((DATA_DIR / "MDT").glob(f"MDT_{tile_id}*.xyz"), DATA_DIR / "MDT" / f"MDT_{tile_id}.xyz")
    
    if not mds_xyz.exists() or not mdt_xyz.exists():
        return tile_id, False, f"[Erro] Dados .xyz ausentes para o tile {tile_id} em {DATA_DIR}."

    env_trabalho = os.environ.copy()
    # RESTAURADO PARA 'RESOLUCAO_ESTEIRA' PARA CONVERSAR COM OS SCRIPTS FILHOS
    env_trabalho["RESOLUCAO_ESTEIRA"] = str(GRID_RES)
    env_trabalho[f"XYZ_MDS_{tile_id}"] = str(mds_xyz.name)
    env_trabalho[f"XYZ_MDT_{tile_id}"] = str(mdt_xyz.name)
    
    for script in PIPELINE:
        proc = subprocess.run(
            [sys.executable, str(BASE_DIR / script), tile_id],
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.PIPE, 
            text=True, 
            env=env_trabalho
        )
        
        if proc.returncode != 0:
            erro_msg = (
                f"    [Falha] Script {script} quebrou no Quadrante {tile_id}!\n"
                f"--- LOG DE ERRO (STDERR) ---\n{proc.stderr}\n"
                f"----------------------------------------"
            )
            return tile_id, False, erro_msg
            
    dt_total = time.time() - t0_tile
    return tile_id, True, f"Quadrante {tile_id} processado com sucesso em {dt_total:.1f}s."

def obter_tiles_dinamicos(args):
    """Lógica inteligente para selecionar quais quadrantes processar"""
    tiles = set()
    
    # 1. Modo Automático: Varre a pasta MDS e pega todos os tiles disponíveis
    if args.all:
        print(">> Modo --all ativado: Mapeando todos os arquivos .xyz na pasta MDS...")
        for arquivo in (DATA_DIR / "MDS").glob("MDS_*.xyz"):
            # Extrai apenas o número do tile do nome do arquivo (ex: MDS_5250.xyz -> 5250)
            tile_str = arquivo.stem.split("_")[1]
            tiles.add(tile_str)
            
    # 2. Modo Lista de Arquivo: Lê um arquivo TXT com um tile por linha
    if args.file:
        arquivo_txt = Path(args.file)
        if arquivo_txt.exists():
            print(f">> Lendo quadrantes do arquivo: {arquivo_txt.name}")
            with open(arquivo_txt, "r") as f:
                tiles.update(linha.strip() for linha in f if linha.strip())
        else:
            sys.exit(f"Erro: Arquivo {arquivo_txt} não encontrado.")
            
    # 3. Modo Manual: Pega os tiles passados diretamente no terminal
    if args.tiles:
        tiles.update(args.tiles)
        
    return sorted(list(tiles))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestrador Paralelo Sunroof BH")
    parser.add_argument("-t", "--tiles", nargs="+", help="Lista de quadrantes específicos (ex: -t 5250 4545)")
    parser.add_argument("-f", "--file", type=str, help="Arquivo TXT contendo os tiles a processar")
    parser.add_argument("-a", "--all", action="store_true", help="Processa TODOS os tiles encontrados na pasta Data/MDS")
    parser.add_argument("-w", "--workers", type=int, default=3, help="Número de threads de CPU (default: 3)")
    
    args = parser.parse_args()
    
    TILES = obter_tiles_dinamicos(args)
    
    if not TILES:
        parser.print_help()
        sys.exit("\nNenhum quadrante selecionado. Use --all, --file ou --tiles.")

    print("-" * 60)
    print("ORQUESTRADOR PARALELO - RASTER 0.25m")
    print("-" * 60)
    print(f">> Iniciando processamento paralelo assíncrono.")
    print(f">> Threads dedicadas na CPU: {args.workers} | Resolução: {GRID_RES}m")
    print(f">> Total de quadrantes na fila: {len(TILES)}")
    print("-" * 60)

    t0_global = time.time()
    sucessos = 0
    falhas = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futuros = {executor.submit(processar_single_tile, tile): tile for tile in TILES}
        
        for futuro in as_completed(futuros):
            tile_concluido, status, log = futuro.result()
            print(log)
            
            if status:
                sucessos += 1
            else:
                falhas += 1
                print(f"[Interrupção] A esteira descartou o tile {tile_concluido} devido ao erro acima.")
            
            gc.collect()

    dt_total_lote = time.time() - t0_global
    print("=" * 60)
    print("PROCESSAMENTO EM LOTE FINALIZADO")
    print(f"-> Tempo: {int(dt_total_lote // 60)}m {dt_total_lote % 60:.1f}s")
    print(f"-> Sucessos: {sucessos} | Falhas: {falhas}")
    print("=" * 60)