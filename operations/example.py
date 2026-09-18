# %%
import pandas as pd
import re
from pathlib import Path

# ── Caminhos ──────────────────────────────────────────────────────────────────
BASE        = Path("C:/Users/hiury/Desktop/IFCE/meus_projetos/schedule_strength")
PATH_SEQ    = BASE / "data/raw/sequencias_times.csv"
PATH_CLASS  = BASE / "data/raw/classificacao.csv"
PATH_HTML   = BASE / "tabela_sos.html"

# %%
# ── Carrega os dados ──────────────────────────────────────────────────────────
df             = pd.read_csv(PATH_SEQ)
df_classificacao = pd.read_csv(PATH_CLASS)

# %%
# ── Corrige slug do Bragantino ────────────────────────────────────────────────
df['adversario'] = df['adversario'].replace('bragantino', 'red-bull-bragantino')

# %%
# ── Pesos de mando ────────────────────────────────────────────────────────────
pesos      = {'mandante': 0.8, 'visitante': 1.2}
df['peso'] = df['mando'].map(pesos)

# %%
# ── Merge com aproveitamento do adversário ────────────────────────────────────
df_merged = df.merge(
    df_classificacao[['slug', 'aproveitamento']],
    left_on='adversario',
    right_on='slug',
    how='left'
)

# %%
# ── Calcula SOS ponderado ─────────────────────────────────────────────────────
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

# %%
# ── Siglas oficiais ───────────────────────────────────────────────────────────
SIGLAS = {
    'flamengo':             'FLA',
    'palmeiras':            'PAL',
    'sao-paulo':            'SAO',
    'fluminense':           'FLU',
    'bahia':                'BAH',
    'athletico-paranaense': 'CAP',
    'coritiba':             'CFC',
    'atletico-mg':          'CAM',
    'red-bull-bragantino':  'RBB',
    'vitoria':              'VIT',
    'botafogo':             'BOT',
    'gremio':               'GRE',
    'vasco-da-gama':        'VAS',
    'internacional':        'INT',
    'santos':               'SAN',
    'corinthians':          'COR',
    'cruzeiro':             'CRU',
    'remo':                 'REM',
    'chapecoense':          'CHA',
    'mirassol':             'MIR',
}

def montar_sequencia(time_base, df_merged, siglas):
    jogos = df_merged[df_merged['time_base'] == time_base].sort_values('sequencia')
    partes = []
    for _, row in jogos.iterrows():
        sigla = siglas.get(row['adversario'], row['adversario'][:3].upper())
        mando = 'C' if row['mando'] == 'mandante' else 'F'
        partes.append(f"{sigla} ({mando})")
    return ' - '.join(partes)

df_sos['sequencia'] = df_sos['time'].apply(
    lambda t: montar_sequencia(t, df_merged, SIGLAS)
)

print(df_sos)

# %%
# ── Gera HTML atualizado ──────────────────────────────────────────────────────
def gerar_html(df_sos, caminho_html: Path):
    linhas_js = []
    for _, row in df_sos.iterrows():
        partes  = row['sequencia'].split(' - ')
        seq_js  = []
        for parte in partes:
            sigla = parte[:3]
            mando = 'C' if '(C)' in parte else 'F'
            seq_js.append(f'["{sigla}","{mando}"]')
        seq_str = '[' + ','.join(seq_js) + ']'
        linhas_js.append(
            f'{{ time: "{row["time"]}", sos: {row["sos"]}, seq: {seq_str} }}'
        )

    dados_js = ',\n  '.join(linhas_js)

    with open(caminho_html, 'r', encoding='utf-8') as f:
        html = f.read()

    novo_html = re.sub(
        r'const data = \[.*?\];',
        f'const data = [\n  {dados_js}\n];',
        html,
        flags=re.DOTALL
    )

    with open(caminho_html, 'w', encoding='utf-8') as f:
        f.write(novo_html)

    print(f"HTML atualizado: {caminho_html}")

gerar_html(df_sos, PATH_HTML)