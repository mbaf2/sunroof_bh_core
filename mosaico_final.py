# /// script
# requires-python = ">=3.12"
# dependencies = ["rasterio"]
# ///

import sys
from pathlib import Path
import rasterio
from rasterio.merge import merge
  
# 1. MAPEAMENTO CORRETO DOS DIRETÓRIOS (SUBINDO PARA A RAIZ 'PROJETO_BH')
# __file__.resolve().parent é 'Python'. O próximo .parent sobe para 'projeto_bh'
raiz_projeto = Path(__file__).resolve().parent.parent
base_dir = raiz_projeto / "Teste"

# O arquivo final mosaico será gerado diretamente na sua raiz (projeto_bh)
raster_mosaico_final = raiz_projeto / "BH_Irradiacao_Completa_50cm.tif"

print(f">> Buscando a pasta de dados em: {base_dir.absolute()}")

# Se a pasta 'Teste' não for encontrada na raiz, interrompe com aviso claro
if not base_dir.exists():
    sys.exit(f"Erro Crítico: A pasta 'Teste' não foi localizada em {base_dir.absolute()}")

print(f">> Varrendo subpastas com resultados dentro de: {base_dir.name}...")

# 2. PROCURA DINAMICAMENTE (BLINDADA CONTRA ACENTUAÇÃO E CAIXA ALTA)
lista_rasters = []
for p in base_dir.glob("Resultados_*/*.tif"):
    nome_minusculo = p.name.lower()
    
    # FORMATO SEGURO: Captura arquivos que começam com 'raster_i'
    # Isola perfeitamente o 'RASTER_Irradiacao_XXXX.tif' sem brigar com acentos no Windows
    if nome_minusculo.startswith("raster_i"):
        lista_rasters.append(p)

if len(lista_rasters) == 0:
    # Diagnóstico amigável caso as subpastas existam mas estejam sem os tifs de irradiação
    exemplo_pasta = next(base_dir.glob("Resultados_*"), None)
    arquivos_na_pasta = [f.name for f in exemplo_pasta.glob("*")] if exemplo_pasta else []
    
    sys.exit(
        f"Abort: Nenhum raster de Irradiação localizado dentro das subpastas de {base_dir.name}.\n"
        f"Diagnóstico: A pasta {exemplo_pasta.name if exemplo_pasta else 'Nenhuma'} foi mapeada, "
        f"mas ela contém apenas: {arquivos_na_pasta}"
    )

print(f"-> Sucesso: {len(lista_rasters)} quadrantes de irradiação localizados para o mosaico.")

# 3. CRIA O MOSAICO GIGANTE (MERGE)
print("\n>> Combinando os quadrantes em um único arquivo mosaico da cidade...")
print("   (Isso consome processamento e RAM, aguarde um instante...)")

# Abre os arquivos de forma segura
arquivos_abertos = [rasterio.open(f) for f in lista_rasters]

# Realiza a colagem geográfica perfeita das bordas
mosaico, transform = merge(arquivos_abertos)

# Configura e atualiza os metadados para a matriz gigante de BH
meta = arquivos_abertos[0].meta.copy()
meta.update({
    "driver": "GTiff",
    "height": mosaico.shape[1],
    "width": mosaico.shape[2],
    "transform": transform,
    "crs": arquivos_abertos[0].crs
})

# Escreve o arquivo consolidado na raiz do projeto (projeto_bh)
with rasterio.open(raster_mosaico_final, "w", **meta) as dest:
    dest.write(mosaico)

# Fecha os descritores para liberar a memória RAM de 8GB
for ras in arquivos_abertos:
    ras.close()

print(f"\n[SUCESSO] Mosaico final gerado com perfeição!")
print(f"-> Arquivo criado: {raster_mosaico_final.name}")
print(f"-> Caminho para arrastar para o QGIS: {raster_mosaico_final.absolute()}")