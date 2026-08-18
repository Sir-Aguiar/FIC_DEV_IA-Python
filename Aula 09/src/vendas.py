from pathlib import Path
import pandas as pd

CAMINHO_VENDAS = Path(__file__).parent / "assets" / "vendas.csv"

df = pd.read_csv(
    CAMINHO_VENDAS,
    sep=";",  # separador (padrão: vírgula)
    encoding="utf-8",
    nrows=1000,  # ler apenas as primeiras N linhas
    usecols=["Data", "Produto", "Valor", "Cliente"],  # apenas estas colunas
)

cols = df.columns.tolist()

df["Valor"] = df["Valor"].astype(float)

valor_total_vendas = df["Valor"].sum().round(2)
vendas_por_dia = df.groupby("Data")["Valor"].sum()

print("="*50)
print("Valor total de vendas: R$", valor_total_vendas)
print("="*50)

print("Vendas por dia")

print(vendas_por_dia)

print("=" * 50)

