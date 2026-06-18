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
import laspy
import numpy as np

# ==============================================================================
# CONFIGURAÇÕES DE DIRETÓRIO E PIPELINE
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parents[1] / "Data"
GRID_RES = 0.25

PIPELINE = [
    "dsm.py",
    "dtm.py",
    "intensity.py",
    "ndsm.py",
    "buildings_footprint.py",
    "mds_buildings.py",
    "slope.py",
    "aspect.py",
    "solar_simulation.py",
    "zonal_statistics.py",
    "filter.py",
]


def garantir_xyz(tile_id, pasta_alvo, prefixo):
    """
    Verifica se o .xyz existe. Se não existir, procura um .las/.laz e converte.
    Retorna o caminho do arquivo .xyz ou None se falhar.
    """
    pasta = DATA_DIR / pasta_alvo

    # 1. Tenta achar o .xyz pronto (caminho mais rápido)
    xyz_files = list(pasta.glob(f"{prefixo}_{tile_id}*.xyz"))
    if xyz_files:
        return xyz_files[0]

    # 2. Se não achar, procura a nuvem de pontos bruta (.las ou .laz)
    las_files = list(pasta.glob(f"{prefixo}_{tile_id}*.las")) + list(
        pasta.glob(f"{prefixo}_{tile_id}*.laz")
    )

    if not las_files:
        return None

    las_path = las_files[0]
    xyz_path = pasta / f"{prefixo}_{tile_id}.xyz"

    try:
        # Abre o arquivo binário LAS/LAZ
        las = laspy.read(las_path)

        # Tenta extrair X, Y, Z e a Intensidade
        try:
            dados = np.column_stack((las.x, las.y, las.z, las.intensity))
            formato = "%.3f %.3f %.3f %d"
        except AttributeError:
            # Caso o LAS seja muito antigo e não tenha a coluna de intensidade
            dados = np.column_stack((las.x, las.y, las.z))
            formato = "%.3f %.3f %.3f"

        # Salva o arquivo de texto bruto no disco
        np.savetxt(xyz_path, dados, fmt=formato, delimiter=" ")

        # Gestão rigorosa de RAM (Limpa o objeto pesadão do laspy)
        del las
        del dados
        gc.collect()

        return xyz_path
    except Exception as e:
        print(f"Erro ao converter {las_path.name}: {e}")
        return None


def processar_single_tile(tile_id):
    t0_tile = time.time()
    out_dir = DATA_DIR / f"Resultados_{tile_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Invoca a função conversora em tempo real
    mds_xyz = garantir_xyz(tile_id, "MDS", "MDS")
    mdt_xyz = garantir_xyz(tile_id, "MDT", "MDT")

    if not mds_xyz or not mdt_xyz:
        return (
            tile_id,
            False,
            f"[Erro] Dados brutos (.xyz, .las ou .laz) ausentes para o tile {tile_id} em {DATA_DIR}.",
        )

    env_trabalho = os.environ.copy()
    # RESTAURADO PARA 'RESOLUCAO_ESTEIRA' PARA CONVERSAR COM OS SCRIPTS FILHOS
    env_trabalho["RESOLUCAO_ESTEIRA"] = str(GRID_RES)
    env_trabalho[f"XYZ_MDS_{tile_id}"] = str(Path(mds_xyz).name)
    env_trabalho[f"XYZ_MDT_{tile_id}"] = str(Path(mdt_xyz).name)

    for script in PIPELINE:
        proc = subprocess.run(
            [sys.executable, str(BASE_DIR / script), tile_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            env=env_trabalho,
        )

        if proc.returncode != 0:
            erro_msg = (
                f"    [Falha] Script {script} quebrou no Quadrante {tile_id}!\n"
                f"--- LOG DE ERRO (STDERR) ---\n{proc.stderr}\n"
                f"----------------------------------------"
            )
            return tile_id, False, erro_msg

    dt_total = time.time() - t0_tile
    return (
        tile_id,
        True,
        f"Quadrante {tile_id} processado com sucesso em {dt_total:.1f}s.",
    )


def obter_tiles_dinamicos(args):
    """Lógica inteligente para selecionar quais quadrantes processar"""
    tiles = set()

    # 1. Modo Automático: Varre a pasta MDS e pega arquivos .xyz, .las e .laz
    if args.all:
        print(">> Modo --all ativado: Mapeando todos os dados brutos na pasta MDS...")
        arquivos = (
            list((DATA_DIR / "MDS").glob("MDS_*.xyz"))
            + list((DATA_DIR / "MDS").glob("MDS_*.las"))
            + list((DATA_DIR / "MDS").glob("MDS_*.laz"))
        )

        for arquivo in arquivos:
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
    parser.add_argument(
        "-t",
        "--tiles",
        nargs="+",
        help="Lista de quadrantes específicos (ex: -t 5250 4545)",
    )
    parser.add_argument(
        "-f", "--file", type=str, help="Arquivo TXT contendo os tiles a processar"
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Processa TODOS os tiles encontrados na pasta Data/MDS",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=3,
        help="Número de threads de CPU (default: 3)",
    )

    args = parser.parse_args()

    TILES = obter_tiles_dinamicos(args)

    if not TILES:
        parser.print_help()
        sys.exit("\nNenhum quadrante selecionado. Use --all, --file ou --tiles.")

    print("-" * 60)
    print(f"ORQUESTRADOR PARALELO - RASTER {GRID_RES}m")
    print("-" * 60)
    print(">> Iniciando processamento paralelo assíncrono.")
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
                print(
                    f"[Interrupção] A pipeline descartou o tile {tile_concluido} devido ao erro acima."
                )

            # Limpeza preventiva a cada quadrante processado
            gc.collect()

    dt_total_lote = time.time() - t0_global
    print("=" * 60)
    print("PROCESSAMENTO EM LOTE FINALIZADO")
    print(f"-> Tempo: {int(dt_total_lote // 60)}m {dt_total_lote % 60:.1f}s")
    print(f"-> Sucessos: {sucessos} | Falhas: {falhas}")
    print("=" * 60)
