# /// script
# requires-python = ">=3.12"
# dependencies = ["rasterio"]
# ///

import sys
from pathlib import Path
import rasterio
from rasterio.merge import merge
  
# ==============================================================================
# AJUSTE DE ENDEREÇAMENTO GERAL - ARQUITETURA GITHUB / REPOSITÓRIO
# Como este script roda dentro de Python/sunroof_bh_core, subimos 2 níveis (.parents[1])
# para encontrar a raiz do projeto (projeto_bh) e alteramos a pasta de "Teste" para "Data"
# ==============================================================================
ROOT_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT_DIR / "Data"

raster_mosaico_final = ROOT_DIR / "BH_Irradiacao_Completa.tif"

print(f">> Buscando a pasta de dados em: {BASE_DIR.absolute()}")

if not BASE_DIR.exists():
    sys.exit(f"Erro Crítico: A pasta 'Data' não foi localizada em {BASE_DIR.absolute()}")

print(f">> Varrendo subpastas com resultados dentro de: {BASE_DIR.name}...")

lista_rasters = []
for p in BASE_DIR.glob("Resultados_*/*.tif"):
    nome_minusculo = p.name.lower()

    if nome_minusculo.startswith("raster_i"):
        lista_rasters.append(p)

if len(lista_rasters) == 0:
    exemplo_pasta = next(BASE_DIR.glob("Resultados_*"), None)
    arquivos_na_pasta = [f.name for f in exemplo_pasta.glob("*")] if exemplo_pasta else []
    
    sys.exit(
        f"Abort: Nenhum raster de Irradiação localizado dentro das subpastas de {BASE_DIR.name}.\n"
        f"Diagnóstico: A pasta {exemplo_pasta.name if exemplo_pasta else 'Nenhuma'} foi mapeada, "
        f"mas ela contém apenas: {arquivos_na_pasta}"
    )

print(f"-> Sucesso: {len(lista_rasters)} quadrantes de irradiação localizados para o mosaico.")

print("\n>>> Combinando os quadrantes em um único arquivo mosaico da cidade...")

arquivos_abertos = [rasterio.open(f) for f in lista_rasters]

mosaico, transform = merge(arquivos_abertos)

meta = arquivos_abertos[0].meta.copy()
meta.update({
    "driver": "GTiff",
    "height": mosaico.shape[1],
    "width": mosaico.shape[2],
    "transform": transform,
    "crs": arquivos_abertos[0].crs
})

with rasterio.open(raster_mosaico_final, "w", **meta) as dest:
    dest.write(mosaico)

for ras in arquivos_abertos:
    ras.close()

print(f"\n[SUCESSO] Mosaico final gerado com perfeição!")
print(f"-> Arquivo criado: {raster_mosaico_final.name}")
print(f"-> Caminho: {raster_mosaico_final.absolute()}")