# ============================================================
# Aula 13 – Construindo um Assistente de Documentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 02: Assistente de documentos com resposta fundamentada
# Seção 5 – Geração Fundamentada e o Direito de Não Responder
# Requisitos: pip install openai chromadb pymupdf python-dotenv
# Execução: python exemplo02.py edital_exemplo.pdf
# ============================================================
"""Assistente de documentos com citação de fonte e recusa explícita.

O assistente responde apenas a partir dos trechos recuperados do
acervo. Quando nenhum trecho atinge a similaridade mínima, ele recusa
a pergunta antes de chamar o modelo — não há geração e, portanto, não
há como inventar. Toda resposta traz documento, página e trecho de
origem, e é registrada em um arquivo de auditoria.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from openai import OpenAI

from exemplo01 import dividir_em_trechos, extrair_paginas

load_dotenv()

MODELO_GERACAO = "gpt-5.6-luna"
MODELO_EMBEDDING = "text-embedding-3-small"

RECUSA_PADRAO = (
    "Não encontrei essa informação nos documentos carregados. "
    "Verifique se o documento correto foi enviado ou reformule a pergunta."
)

INSTRUCAO_SISTEMA = (
    "Você é um assistente de análise documental de um órgão público. "
    "Responda exclusivamente com base nos trechos fornecidos. "
    "Nunca complemente com conhecimento próprio."
)


class AssistenteDocumentos:
    """Consulta um acervo de PDFs com resposta rastreável até a página."""

    def __init__(
        self,
        modelo: str = MODELO_GERACAO,
        cliente: Optional[OpenAI] = None,
        parametros_geracao: Optional[Dict] = None,
        similaridade_minima: float = 0.25,
        arquivo_auditoria: str = "consultas.jsonl",
    ):
        # O cliente é injetável para permitir a troca de provedor sem
        # alterar a camada de recuperação (ver exemplo04.py).
        self.client = cliente or OpenAI()
        self.modelo = modelo
        # Modelos de raciocínio: o limite cobre também o raciocínio
        # interno, e o parâmetro chama-se max_completion_tokens.
        self.parametros_geracao = parametros_geracao or {
            "max_completion_tokens": 2000,
            "reasoning_effort": "low",
        }
        self.similaridade_minima = similaridade_minima
        self.arquivo_auditoria = arquivo_auditoria

        # Cliente em memória: o índice existe apenas durante a execução.
        # Para um acervo permanente, troque por chromadb.PersistentClient.
        self.chroma = chromadb.EphemeralClient()
        self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            model_name=MODELO_EMBEDDING
        )
        self.colecao = self.chroma.get_or_create_collection(
            name="acervo",
            embedding_function=self.embedding_fn,
            # Distância do cosseno: similaridade = 1 - distância.
            metadata={"hnsw:space": "cosine"},
        )
        self.documentos: Dict[str, Dict] = {}

    # ------------------------------------------------------------------
    # Ingestão
    # ------------------------------------------------------------------
    def carregar_documento(self, caminho_pdf: str, nome: Optional[str] = None) -> Dict:
        """Extrai, divide e indexa um PDF no acervo."""
        nome = nome or Path(caminho_pdf).name

        paginas = extrair_paginas(caminho_pdf)
        trechos = dividir_em_trechos(paginas)

        self.colecao.add(
            documents=[t["texto"] for t in trechos],
            metadatas=[
                {"documento": nome, "pagina": t["pagina"], "posicao": t["posicao"]}
                for t in trechos
            ],
            ids=[f"{nome}::{t['id']}" for t in trechos],
        )

        info = {
            "nome": nome,
            "caminho": caminho_pdf,
            "total_trechos": len(trechos),
            "total_paginas": max(p["pagina"] for p in paginas),
        }
        self.documentos[nome] = info
        return info

    # ------------------------------------------------------------------
    # Recuperação
    # ------------------------------------------------------------------
    def buscar_trechos(self, pergunta: str, k: int = 4) -> List[Dict]:
        """Recupera os trechos mais próximos e descarta os fracos."""
        if self.colecao.count() == 0:
            raise ValueError("Nenhum documento carregado no acervo.")

        resultado = self.colecao.query(
            query_texts=[pergunta],
            n_results=min(k, self.colecao.count()),
        )

        encontrados = []
        for texto, meta, distancia in zip(
            resultado["documents"][0],
            resultado["metadatas"][0],
            resultado["distances"][0],
        ):
            similaridade = 1 - distancia
            if similaridade >= self.similaridade_minima:
                encontrados.append(
                    {
                        "texto": texto,
                        "documento": meta["documento"],
                        "pagina": meta["pagina"],
                        "similaridade": round(similaridade, 3),
                    }
                )

        return encontrados

    # ------------------------------------------------------------------
    # Geração
    # ------------------------------------------------------------------
    def responder(self, pergunta: str, historico: Optional[List[Dict]] = None) -> Dict:
        """Responde à pergunta, ou recusa quando o acervo não a cobre."""
        trechos = self.buscar_trechos(pergunta)

        # Primeira barreira: sem trecho relevante, não há geração.
        if not trechos:
            return self._registrar(
                {
                    "pergunta": pergunta,
                    "resposta": RECUSA_PADRAO,
                    "fundamentada": False,
                    "motivo": "nenhum trecho acima da similaridade mínima",
                    "fontes": [],
                    "modelo": None,
                }
            )

        contexto = "\n\n".join(
            f"[Trecho {i} | documento: {t['documento']} | página: {t['pagina']}]\n{t['texto']}"
            for i, t in enumerate(trechos, 1)
        )

        conversa = ""
        if historico:
            for turno in historico[-3:]:
                conversa += (
                    f"\nPergunta anterior: {turno['pergunta']}"
                    f"\nResposta anterior: {turno['resposta'][:200]}\n"
                )

        prompt = f"""Responda à pergunta usando SOMENTE os trechos abaixo.

REGRAS OBRIGATÓRIAS
1. Cite a origem de cada informação no formato (documento, p. X).
2. Se os trechos não contiverem a resposta, escreva exatamente:
   "{RECUSA_PADRAO}"
3. Não use conhecimento externo ao documento, ainda que você o possua.
4. Não deduza valores, prazos ou obrigações que não estejam escritos.
{"HISTÓRICO DA CONVERSA:" + conversa if conversa else ""}
TRECHOS RECUPERADOS:
{contexto}

PERGUNTA: {pergunta}
"""

        resposta_api = self.client.chat.completions.create(
            model=self.modelo,
            messages=[
                {"role": "system", "content": INSTRUCAO_SISTEMA},
                {"role": "user", "content": prompt},
            ],
            **self.parametros_geracao,
        )

        escolha = resposta_api.choices[0]
        if escolha.finish_reason != "stop":
            raise RuntimeError(
                f"Resposta truncada (finish_reason={escolha.finish_reason}). "
                "Aumente max_completion_tokens ou reduza reasoning_effort."
            )

        texto = (escolha.message.content or "").strip()
        recusou = RECUSA_PADRAO[:40] in texto

        return self._registrar(
            {
                "pergunta": pergunta,
                "resposta": texto,
                "fundamentada": not recusou,
                "motivo": "recusa declarada pelo modelo" if recusou else "",
                "fontes": trechos,
                "modelo": self.modelo,
                "tokens_saida": resposta_api.usage.completion_tokens,
            }
        )

    # ------------------------------------------------------------------
    # Auditoria
    # ------------------------------------------------------------------
    def _registrar(self, resultado: Dict) -> Dict:
        """Grava a consulta em arquivo JSONL para conferência posterior."""
        resultado["momento"] = datetime.now().isoformat(timespec="seconds")
        with open(self.arquivo_auditoria, "a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(resultado, ensure_ascii=False) + "\n")
        return resultado


def main() -> None:
    caminho = sys.argv[1] if len(sys.argv) > 1 else "edital_exemplo.pdf"

    assistente = AssistenteDocumentos()
    info = assistente.carregar_documento(caminho)
    print(
        f"Indexado: {info['nome']} — "
        f"{info['total_trechos']} trechos de {info['total_paginas']} páginas\n"
    )

    perguntas = [
        "Qual o prazo para envio das propostas?",
        "A empresa pode participar em consórcio?",
        "Qual o percentual da multa por atraso na entrega?",
    ]

    for pergunta in perguntas:
        resultado = assistente.responder(pergunta)
        print(f"Pergunta: {pergunta}")
        print(f"Resposta: {resultado['resposta']}")
        if resultado["fontes"]:
            print("Fontes:")
            for fonte in resultado["fontes"]:
                amostra = fonte["texto"][:70].replace("\n", " ")
                print(
                    f"  - {fonte['documento']}, p. {fonte['pagina']} "
                    f"(similaridade {fonte['similaridade']}): {amostra}..."
                )
        else:
            print("Fontes: nenhuma acima do limiar de similaridade.")
        print("-" * 70)

    print(f"\nConsultas registradas em {assistente.arquivo_auditoria}")


if __name__ == "__main__":
    main()
