import sys
from pathlib import Path
import numpy as np
import rasterio

# Config de caminhos
tile = sys.argv[1] if len(sys.argv) > 1 else "5250"

# ==============================================================================
# AJUSTE DE ENDEREÇAMENTO GERAL - ARQUITETURA GITHUB / REPOSITÓRIO
# Subimos 2 níveis (.parents[2]) para sair de Python/sunroof_bh_core
# e alteramos o nome do diretório de "Teste" para "Data"
# ==============================================================================
res_dir = Path(__file__).resolve().parents[2] / "Data" / f"Resultados_{tile}"

# Nomes corrigidos e padronizados
f_mds = res_dir / f"RASTER_MDS_{tile}.tif"
f_mdt = res_dir / f"RASTER_MDT_{tile}.tif"
f_out = res_dir / f"RASTER_nDSM_{tile}.tif"

if not f_mds.exists() or not f_mdt.exists():
    sys.exit(f"Abort: Raster de entrada ausente in {res_dir}")

print(f">> Gerando nDSM: {tile}")

with rasterio.open(f_mds) as s_mds, rasterio.open(f_mdt) as s_mdt:
    m_mds = s_mds.read(1)
    m_mdt = s_mdt.read(1)
    meta = s_mds.meta.copy()

# ==============================================================================
# TRAVA 3: RECORTE DINÂMICO DE SEGURANÇA (INTERSECTION CROP)
# Evita o ValueError calculando a interseção matricial exata se houver descompasso
# ==============================================================================
min_linhas = min(m_mds.shape[0], m_mdt.shape[0])
min_colunas = min(m_mds.shape[1], m_mdt.shape[1])

if m_mds.shape != m_mdt.shape:
    print(f"   - [Aviso Borda] Shapes divergentes detectados: MDS {m_mds.shape} | MDT {m_mdt.shape}")
    print(f"   - [Aviso Borda] Aplicando corte comum de segurança: ({min_linhas}, {min_colunas})")

# Fatiamos cirurgicamente as duas matrizes antes de qualquer mascaramento ou cálculo
m_mds_c = m_mds[:min_linhas, :min_colunas]
m_mdt_c = m_mdt[:min_linhas, :min_colunas]
  
# Mascaramento de nodata para cálculo seguro usando as matrizes recortadas
mds_val = np.where(m_mds_c == -9999.0, np.nan, m_mds_c)
mdt_val = np.where(m_mdt_c == -9999.0, np.nan, m_mdt_c)

# nDSM = MDS - MDT (Agora matematicamente à prova de falhas)
ndsm = mds_val - mdt_val

# Correção de ruído (alturas negativas) e restauração de nodata
ndsm = np.where(ndsm < 0.0, 0.0, ndsm)
ndsm[np.isnan(mds_val) | np.isnan(mdt_val)] = -9999.0

# ==============================================================================
# ATUALIZAÇÃO RESTRITA DOS METADADOS
# Atualizamos height e width caso a matriz tenha sofrido o corte de segurança
# ==============================================================================
meta.update(
    dtype="float32", 
    nodata=-9999.0,
    height=min_linhas,
    width=min_colunas
)

with rasterio.open(f_out, "w", **meta) as dst:
    dst.write(ndsm.astype(np.float32), 1)

print(f"OK: {f_out.name} | Shape Resultante: ({min_linhas}, {min_colunas})")