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
slugs_calendario = set(df['adversario'].unique())
slugs_classificacao = set(df_classificacao['slug'].unique())

print("No calendário mas não na classificação:")
print(slugs_calendario - slugs_classificacao)

print("\nNa classificação mas não no calendário:")
print(slugs_classificacao - slugs_calendario)      
# %%
# ── Corrige o slug do Bragantino 
df['adversario'] = df['adversario'].replace('bragantino', 'red-bull-bragantino')

# ── Define os pesos de mando 
pesos = {'mandante': 0.8, 'visitante': 1.2}
df['peso'] = df['mando'].map(pesos)

# ── Merge: traz o aproveitamento do adversário 
df_merged = df.merge(
    df_classificacao[['slug', 'aproveitamento']],
    left_on='adversario',
    right_on='slug',
    how='left'
)

# ── Calcula o SOS ponderado por time 
df_merged['sos_parcial'] = df_merged['aproveitamento'] * df_merged['peso']

df_sos = (
    df_merged
    .groupby('time_base')['sos_parcial']
    .mean()
    .reset_index()
    .rename(columns={'sos_parcial': 'sos', 'time_base': 'time'})
    .sort_values('sos', ascending=False)
    .reset_index(drop=True)
)

df_sos['sos'] = df_sos['sos'].round(4)
print(df_sos)
# %%
print(df_merged[df_merged['time_base'] == 'Flamengo'][['time_base', 'sequencia', 'adversario', 'mando']].to_string())
# %%

# %%
# Após calcular o df_sos, você adiciona a coluna de sequência formatada

SIGLAS = {
    'flamengo':              'FLA',
    'palmeiras':             'PAL',
    'sao-paulo':             'SAO',
    'fluminense':            'FLU',
    'bahia':                 'BAH',
    'athletico-paranaense':  'CAP',
    'coritiba':              'CFC',
    'atletico-mg':           'CAM',
    'red-bull-bragantino':   'RBB',
    'vitoria':               'VIT',
    'botafogo':              'BOT',
    'gremio':                'GRE',
    'vasco-da-gama':         'VAS',
    'internacional':         'INT',
    'santos':                'SAN',
    'corinthians':           'COR',
    'cruzeiro':              'CRU',
    'remo':                  'REM',
    'chapecoense':           'CHA',
    'mirassol':              'MIR',
}
# Monta a string de sequência para cada time
def montar_sequencia(time_base, df_merged, siglas):
    jogos = df_merged[df_merged['time_base'] == time_base].sort_values('sequencia')
    partes = []
    for _, row in jogos.iterrows():
        sigla = siglas.get(row['adversario'], row['adversario'][:3].upper())
        mando = 'C' if row['mando'] == 'mandante' else 'F'
        partes.append(f"{sigla} ({mando})")
    return ' - '.join(partes)

# Aplica para todos os times
df_sos['sequencia'] = df_sos['time'].apply(
    lambda t: montar_sequencia(t, df_merged, SIGLAS)
)
# %%
df_sos.head(3)

# %%
