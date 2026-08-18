import pandas as pd
from pathlib import Path


CAMINHO_VENDAS = Path(__file__).parent / "assets" / "relatorio.xlsx"

df = pd.read_excel(CAMINHO_VENDAS, )

df["Total"] = df["Quantidade"] * df["Valor Unitário"]

total_categoria_vendido = df.groupby("Categoria")["Total"].sum()
total_vendas = df["Total"].sum()

print(df)
print(total_categoria_vendido)
print(total_vendas)