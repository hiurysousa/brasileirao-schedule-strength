#%%
import pandas as pd

#%%
caminho_arquivo = "C:/Users/hiury/Desktop/IFCE/meus_projetos/schedule_strength/data/raw/sequencias_times.csv"
df = pd.read_csv(caminho_arquivo)
df.head(15)
# %%
df_bragantino = df[df['time_base'] == 'Bragantino']
df_bragantino.head()
# %%
caminho_arquivo_tabela = "C:/Users/hiury/Desktop/IFCE/meus_projetos/schedule_strength/data/raw/classificacao.csv"
df_classificacao = pd.read_csv(caminho_arquivo_tabela)
df_classificacao.head(20)
# %%
            