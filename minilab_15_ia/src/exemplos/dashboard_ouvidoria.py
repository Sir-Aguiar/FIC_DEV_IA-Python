# ============================================================
# Aula 14 – Análise de Sentimentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Dashboard Streamlit: painel de ouvidoria com ficha técnica
# Seção 6 – Painel de Acompanhamento
# Requisitos: pip install streamlit pandas
# Execução: streamlit run dashboard_ouvidoria.py
# ============================================================
#
# O painel não classifica nada e não chama nenhuma API: ele lê a tabela
# de rótulos gravada pelo exemplo02.py e refaz, em pandas, as mesmas
# contagens do exemplo03.py. Todo indicador aparece acompanhado do
# número de casos que o sustenta.

import os

import pandas as pd
import streamlit as st

BASE = os.path.dirname(os.path.abspath(__file__))
ROTULOS = os.path.join(BASE, "rotulos.csv")
GABARITO = os.path.join(BASE, "gabarito_manual.csv")

# Abaixo deste número de casos, o percentual não é exibido como indicador.
MINIMO_PARA_PERCENTUAL = 10

st.set_page_config(page_title="Ouvidoria — análise de sentimentos", layout="wide")
st.title("Ouvidoria Geral do Estado — análise de manifestações")


@st.cache_data
def carregar(caminho_ou_arquivo) -> pd.DataFrame:
    df = pd.read_csv(caminho_ou_arquivo)
    df["mes"] = df["data"].str.slice(0, 7)
    return df


def acuracia_medida(df: pd.DataFrame) -> str:
    """Compara com o conjunto rotulado à mão, quando ele existir."""
    if not os.path.exists(GABARITO):
        return "não medida"
    gab = pd.read_csv(GABARITO)
    junto = df.merge(gab, on="id", suffixes=("_modelo", "_humano"))
    if junto.empty:
        return "não medida"
    acertos = (junto["sentimento_modelo"] == junto["sentimento_humano"]).sum()
    return f"{100 * acertos / len(junto):.1f}% em {len(junto)} rótulos"


enviado = st.sidebar.file_uploader("Tabela de rótulos (CSV)", type=["csv"])
origem = enviado if enviado else ROTULOS

if not enviado and not os.path.exists(ROTULOS):
    st.warning("Execute antes o `exemplo02.py` para gerar `rotulos.csv`.")
    st.stop()

df = carregar(origem)
n = len(df)

# ── Ficha técnica: o que precede qualquer percentual ──────────────────
st.subheader("Ficha técnica")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Manifestações", n)
c2.metric("Período", f"{df['data'].min()} a {df['data'].max()}")
c3.metric("Classificador", ", ".join(sorted(df["modelo"].unique())))
c4.metric("Acurácia medida", acuracia_medida(df))

limitrofes = df[df["ambiguidade"] == "limitrofe"]
st.caption(
    f"Levantamento do tipo censo do período. {len(limitrofes)} manifestações "
    f"({100 * len(limitrofes) / n:.1f}%) foram marcadas como limítrofes pelo "
    f"classificador e devem ser revistas por servidor antes de qualquer decisão. "
    f"Percentuais calculados sobre estratos com menos de "
    f"{MINIMO_PARA_PERCENTUAL} casos não são exibidos."
)

# ── Distribuição por sentimento ───────────────────────────────────────
st.subheader("Distribuição por sentimento")
contagem = df["sentimento"].value_counts()
colunas = st.columns(len(contagem))
for coluna, (classe, quantidade) in zip(colunas, contagem.items()):
    coluna.metric(classe.capitalize(), f"{quantidade} de {n}",
                  f"{100 * quantidade / n:.1f}%", delta_color="off")

esquerda, direita = st.columns(2)

with esquerda:
    st.markdown("**Manifestações por tema**")
    st.bar_chart(df["tema"].value_counts(), horizontal=True)

with direita:
    st.markdown("**Manifestações por tipo**")
    st.bar_chart(df["tipo"].value_counts(), horizontal=True)

# ── Série mensal, sempre com o denominador ────────────────────────────
st.subheader("Evolução mensal")
serie = df.groupby("mes").agg(
    manifestacoes=("id", "count"),
    negativas=("sentimento", lambda s: (s == "negativo").sum()),
)
serie["percentual_negativas"] = (100 * serie["negativas"] / serie["manifestacoes"]).round(1)
serie["exibir_percentual"] = serie["manifestacoes"] >= MINIMO_PARA_PERCENTUAL

st.line_chart(serie["manifestacoes"])
st.dataframe(
    serie.rename(columns={
        "manifestacoes": "manifestações",
        "percentual_negativas": "% negativas",
        "exibir_percentual": "base suficiente",
    }),
    width="stretch",
)
st.caption(
    "O percentual de negativas oscila mais nos meses com poucos registros. "
    "A coluna de base suficiente indica quais meses reúnem casos bastantes "
    "para sustentar leitura; nos demais, use a contagem absoluta."
)

# ── Órgãos ────────────────────────────────────────────────────────────
st.subheader("Órgãos citados")
orgaos = df.groupby("orgao").agg(
    manifestacoes=("id", "count"),
    negativas=("sentimento", lambda s: (s == "negativo").sum()),
)
orgaos["percentual_negativas"] = (100 * orgaos["negativas"] / orgaos["manifestacoes"]).round(1)
orgaos = orgaos.sort_values("manifestacoes", ascending=False)
orgaos.loc[orgaos["manifestacoes"] < MINIMO_PARA_PERCENTUAL, "percentual_negativas"] = None

st.dataframe(
    orgaos.rename(columns={
        "manifestacoes": "manifestações",
        "percentual_negativas": "% negativas",
    }),
    width="stretch",
)
st.caption(
    "O percentual foi omitido nos órgãos com menos de "
    f"{MINIMO_PARA_PERCENTUAL} manifestações. Uma secretaria com duas "
    "manifestações negativas entre três registros não tem 66,7% de rejeição: "
    "tem três registros."
)

# ── Fila de revisão humana ────────────────────────────────────────────
st.subheader("Fila de revisão humana")
st.write(
    f"São {len(limitrofes)} manifestações em que o classificador reconheceu "
    "ambiguidade. A revisão começa por elas, porque é onde o rótulo tem maior "
    "chance de estar errado."
)
st.dataframe(
    limitrofes[["id", "orgao", "sentimento", "tipo", "trecho_determinante"]],
    width="stretch", hide_index=True,
)

with st.expander("Todas as manifestações classificadas"):
    st.dataframe(df, width="stretch", hide_index=True)
