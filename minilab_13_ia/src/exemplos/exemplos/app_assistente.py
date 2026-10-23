# ============================================================
# Aula 13 – Construindo um Assistente de Documentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# App Streamlit: interface do assistente com citação de fonte
# Seção 7 – A Interface com Streamlit
# Requisitos: pip install streamlit openai chromadb pymupdf python-dotenv
# Execução: streamlit run app_assistente.py
# ============================================================
"""Interface web do assistente de documentos.

A tela existe para tornar visível aquilo que a Seção 6 exige: de qual
documento e de qual página veio cada resposta. Por isso o painel de
fontes não é opcional nem escondido em um menu — ele acompanha toda
resposta, inclusive as recusas, mostrando o que foi consultado.
"""

import os
import tempfile

import streamlit as st

from exemplo02 import AssistenteDocumentos

st.set_page_config(
    page_title="Assistente de Documentos",
    page_icon="📄",
    layout="wide",
)


@st.cache_resource
def obter_assistente() -> AssistenteDocumentos:
    """Cria o assistente uma única vez por sessão do servidor.

    Sem o cache, cada interação reexecutaria o script inteiro e
    reconstruiria o índice vetorial do zero, reprocessando o PDF e
    gastando créditos de embedding a cada pergunta.
    """
    return AssistenteDocumentos()


assistente = obter_assistente()

if "historico" not in st.session_state:
    st.session_state.historico = []
if "acervo" not in st.session_state:
    st.session_state.acervo = []

# ----------------------------------------------------------------------
# Barra lateral — carga do acervo
# ----------------------------------------------------------------------
with st.sidebar:
    st.header("Acervo")

    arquivos = st.file_uploader(
        "Documentos em PDF",
        type=["pdf"],
        accept_multiple_files=True,
        help="Use PDFs de texto. Documentos digitalizados exigem OCR (Aula 06).",
    )

    if arquivos and st.button("Indexar documentos", type="primary"):
        for arquivo in arquivos:
            if arquivo.name in st.session_state.acervo:
                continue
            with st.spinner(f"Indexando {arquivo.name}..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(arquivo.read())
                    caminho_tmp = tmp.name
                try:
                    info = assistente.carregar_documento(caminho_tmp, arquivo.name)
                    st.session_state.acervo.append(arquivo.name)
                    st.success(
                        f"{arquivo.name}: {info['total_trechos']} trechos "
                        f"de {info['total_paginas']} páginas"
                    )
                except ValueError as erro:
                    st.error(f"{arquivo.name}: {erro}")
                finally:
                    os.unlink(caminho_tmp)

    if st.session_state.acervo:
        st.divider()
        st.caption("Documentos indexados")
        for nome in st.session_state.acervo:
            st.write(f"- {nome}")

        if st.button("Limpar acervo"):
            st.cache_resource.clear()
            st.session_state.historico = []
            st.session_state.acervo = []
            st.rerun()

    st.divider()
    st.caption(
        "O assistente responde apenas com base nos documentos indexados. "
        "Quando a informação não está no acervo, ele recusa a pergunta."
    )


# ----------------------------------------------------------------------
# Exibição das fontes
# ----------------------------------------------------------------------
def mostrar_fontes(resultado: dict) -> None:
    """Exibe documento, página e trecho de origem de cada resposta."""
    fontes = resultado.get("fontes", [])

    if not fontes:
        st.warning("Nenhum trecho do acervo atingiu a similaridade mínima.")
        return

    rotulo = (
        "Fontes desta resposta"
        if resultado["fundamentada"]
        else "Trechos consultados (nenhum responde à pergunta)"
    )
    with st.expander(f"{rotulo} — {len(fontes)} trecho(s)"):
        for fonte in fontes:
            st.markdown(
                f"**{fonte['documento']} — página {fonte['pagina']}** "
                f"· similaridade {fonte['similaridade']}"
            )
            st.text(fonte["texto"])
            st.divider()


# ----------------------------------------------------------------------
# Área principal — conversa
# ----------------------------------------------------------------------
st.title("Assistente de Documentos")
st.caption("Perguntas em linguagem natural sobre editais, contratos e manuais.")

if not st.session_state.acervo:
    st.info("Envie ao menos um PDF na barra lateral para começar.")
    st.markdown(
        """
**Exemplos de perguntas para um edital:**

- Qual o prazo para envio das propostas?
- Quais são os requisitos de habilitação técnica?
- Qual o valor estimado da contratação?
- O órgão aceita participação de consórcio?
"""
    )
else:
    for item in st.session_state.historico:
        with st.chat_message("user"):
            st.write(item["pergunta"])
        with st.chat_message("assistant"):
            st.write(item["resposta"])
            mostrar_fontes(item)

    pergunta = st.chat_input("Digite sua pergunta sobre os documentos...")

    if pergunta:
        with st.chat_message("user"):
            st.write(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("Consultando o acervo..."):
                resultado = assistente.responder(
                    pergunta, historico=st.session_state.historico
                )
            st.write(resultado["resposta"])
            mostrar_fontes(resultado)

        st.session_state.historico.append(resultado)
