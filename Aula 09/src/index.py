import pandas as pd
import numpy as np


dados = {
    "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "nome": [
        "Ana",
        "Bruno",
        "Carla",
        "Diego",
        "Elena",
        "Fabio",
        "Gabi",
        "Hugo",
        "Ines",
        "Joao",
    ],
    "turma": ["A", "A", "A", "A", "A", "B", "B", "B", "B", "B"],
    "idade": [20, 22, 21, np.nan, 20, 23, 21, 22, 20, np.nan],
    "faltas": [1, 3, 0, 5, 2, 0, 4, 6, 1, 3],
    "nota_1b": [8.5, 6.0, 9.5, 4.0, 7.5, 9.0, 6.5, 3.5, 7.5, 6.0],
    "nota_2b": [9.0, np.nan, 10.0, 5.0, 8.0, 8.5, 7.0, 4.5, 8.0, np.nan],
    "nota_3b": [7.5, 7.0, 9.0, np.nan, 7.0, 9.5, 6.0, 4.0, 7.5, 5.5],
    "nota_4b": [8.0, 5.5, 9.8, 4.5, 7.5, 8.0, np.nan, 3.5, 8.0, 6.0],
}

df = pd.DataFrame(dados)

print("=== Inspeção Inicial ===")
print(f"Shape: {df.shape}")
print(df.dtypes)
print()
print("Valores ausentes por coluna:")
print(df.isna().sum())
print()
print(df.describe().round(2))

# Idade: preencher com a mediana por turma
# (mediana é mais robusta a outliers do que a média)
df["idade"] = df.groupby("turma")["idade"].transform(lambda x: x.fillna(x.median()))

# Notas ausentes: preencher com a média do aluno nos outros bimestres
colunas_nota = ["nota_1b", "nota_2b", "nota_3b", "nota_4b"]

for col in colunas_nota:
    media_aluno = df[colunas_nota].mean(axis=1)  # média por linha
    df[col] = df[col].fillna(media_aluno.round(2))

# Verificar: não deve restar NaN
print("NaN restantes:", df.isna().sum().sum())
# NaN restantes: 0

print(df[["nome", "idade", "nota_2b", "nota_3b", "nota_4b"]].to_string(index=False))

# ── 4. Calcular média final e situação ───────────────────────
df['media_final'] = df[colunas_nota].mean(axis=1).round(2)

# Regra: aprovado se média >= 7.0 E faltas <= 5
TOTAL_AULAS = 80
df['presenca_pct'] = ((TOTAL_AULAS - df['faltas']) / TOTAL_AULAS * 100).round(1)

df['situacao'] = np.where((df['media_final'] >= 7.0) & (df['presenca_pct'] >= 75.0), 'Aprovado', 'Reprovado')

# Conceito por faixa de média
def conceito(media):
    if media >= 9.0: return 'A'
    
    if media >= 7.0: return 'B'
    
    if media >= 5.0: return 'C'
    
    return 'D'

df['conceito'] = df['media_final'].apply(conceito)

# ── 5. Filtros analíticos ────────────────────────────────────

aprovados = df[df['situacao'] == 'Aprovado']
reprovados = df[df['situacao'] == 'Reprovado']
turma_a = df[df['turma'] == 'A']
alto_risco = df[(df['media_final'] < 7.0) & (df['faltas'] >= 3)]

print('=== Resultado Individual ===')

cols_exib = ['nome','turma','media_final','presenca_pct','situacao','conceito']

print(df[cols_exib].sort_values('media_final', ascending=False).to_string(index=False))

print(f'\nAprovados: {len(aprovados)} | Reprovados: {len(reprovados)}')
print(f'Alto risco (media<7 E faltas>=3): {len(alto_risco)} aluno(s)')
print(alto_risco[['nome','turma','media_final','faltas']].to_string(index=False))

# ── 6. Resumo por turma com groupby().agg() ─────────────────
resumo_turma = df.groupby('turma').agg(
n_alunos = ('nome', 'count'),
media_turma = ('media_final', 'mean'),
melhor_nota = ('media_final', 'max'),
pior_nota = ('media_final', 'min'),
total_faltas = ('faltas', 'sum'),
aprovados = ('situacao', lambda x: (x == 'Aprovado').sum()),
).round(2).reset_index()

resumo_turma['pct_aprovacao'] = (
resumo_turma['aprovados'] / resumo_turma['n_alunos'] * 100).round(1)

print('=== Resumo por Turma ===')
print(resumo_turma.to_string(index=False))

# ── 7. Exportar datasets ─────────────────────────────────────
# Dataset completo — será importado na Aula 10 para merge e visualização
df.to_csv('alunos_tratados.csv', index=False, encoding='utf-8')

# Resumo por turma
resumo_turma.to_csv('resumo_turmas.csv', index=False, encoding='utf-8')

print('\nArquivos salvos:')
print(' alunos_tratados.csv — dataset completo (10 alunos × 12 colunas)')
print(' resumo_turmas.csv — resumo por turma (2 linhas × 8 colunas)')