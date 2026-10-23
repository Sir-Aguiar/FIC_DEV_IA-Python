"""Extrai subseções do Regimento Interno da MTI.

Uso:
    python src/extractor.py caracterizacao objetivos conselho-administracao conselho-fiscal gestao-pessoas
    python src/extractor.py --list
    python src/extractor.py --all
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import pdfplumber

DATA_DIR = Path(__file__).resolve().parent / "data"
PDF_PADRAO = DATA_DIR / "regimento_interno_mti.pdf"
JSON_PADRAO = DATA_DIR / "subsecoes.json"

METADADOS_DOCUMENTO = {
    "titulo": "Regimento Interno da Empresa Mato-grossense de Tecnologia da Informação - MTI",
    "orgao": "MTI",
    "data_aprovacao": "2025-01-02",
    "idioma": "pt-BR",
    "arquivo": "regimento_interno_mti.pdf",
    "decreto": "Decreto nº 1.212, de 2 de janeiro de 2025",
}

INICIO_DOCUMENTO = "REGIMENTO INTERNO DA EMPRESA MATO-GROSSENSE"

SECOES: list[dict] = [
    {
        "id": "caracterizacao",
        "tipo": "capitulo",
        "numero": "I.I",
        "rotulo": "Título I, Capítulo I",
        "titulo": "Da caracterização",
        "parte": {"numero": "I", "titulo": "Da caracterização e objetivos"},
        "tema": "Natureza jurídica e origem histórica da MTI",
        "aliases": ["caracterizacao", "caracterização", "art-1", "art.1"],
        "inicio": "CAPITULO I DA CARACTERIZACAO",
        "fim": "ART.2 NOS TERMOS DO ARTIGO 5",
    },
    {
        "id": "objetivos",
        "tipo": "capitulo",
        "numero": "I.II",
        "rotulo": "Título I, Capítulo II",
        "titulo": "Dos objetivos",
        "parte": {"numero": "I", "titulo": "Da caracterização e objetivos"},
        "tema": "Objetivos e alcance dos serviços da MTI",
        "aliases": ["objetivos", "art-2", "art.2"],
        "inicio": "ART.2 NOS TERMOS DO ARTIGO 5",
        "fim": "TITULO II",
    },
    {
        "id": "conselho-administracao",
        "tipo": "secao",
        "numero": "III.I.I",
        "rotulo": "Título III, Capítulo I, Seção I",
        "titulo": "Do Conselho de Administração",
        "parte": {"numero": "III", "titulo": "Das competências"},
        "tema": "Competências do Conselho de Administração",
        "aliases": ["conselho-administracao", "conselho de administracao", "art-4"],
        "inicio": "SECAO I DO CONSELHO DE ADMINISTRACAO",
        "fim": "SECAO II DO CONSELHO FISCAL",
    },
    {
        "id": "conselho-fiscal",
        "tipo": "secao",
        "numero": "III.I.II",
        "rotulo": "Título III, Capítulo I, Seção II",
        "titulo": "Do Conselho Fiscal",
        "parte": {"numero": "III", "titulo": "Das competências"},
        "tema": "Competências do Conselho Fiscal",
        "aliases": ["conselho-fiscal", "conselho fiscal", "art-5"],
        "inicio": "SECAO II DO CONSELHO FISCAL",
        "fim": "SECAO III DA DIRETORIA EXECUTIVA",
    },
    {
        "id": "gestao-pessoas",
        "tipo": "secao",
        "numero": "III.V.IV",
        "rotulo": "Título III, Capítulo V, Seção IV",
        "titulo": "Da Unidade de Gestão de Pessoas",
        "parte": {"numero": "III", "titulo": "Das competências"},
        "tema": "Competências da Unidade de Gestão de Pessoas",
        "aliases": ["gestao-pessoas", "gestão de pessoas", "art-34"],
        "inicio": "ART.34 A UNIDADE DE GESTAO DE PESSOAS",
        "fim": "SUBSECAO I DA GERENCIA DE APLICACAO",
    },
]


def normalizar(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.upper()
    s = s.replace("º", "").replace("°", "").replace("ª", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def ler_pdf(caminho: Path) -> tuple[str, dict[int, int]]:
    """Lê o PDF em duas colunas e devolve texto + mapa de offsets por página."""
    blocos: list[str] = []
    offsets: dict[int, int] = {}
    tamanho = 0
    with pdfplumber.open(caminho) as pdf:
        for indice, pagina in enumerate(pdf.pages, 1):
            meio = pagina.width / 2
            topo, base = 70, pagina.height - 40
            esquerda = pagina.crop((0, topo, meio, base)).extract_text() or ""
            direita = pagina.crop((meio, topo, pagina.width, base)).extract_text() or ""
            marca = f"[[p={indice}]]"
            offsets[indice] = tamanho
            trecho = marca + "\n" + esquerda + "\n" + direita + "\n"
            blocos.append(trecho)
            tamanho += len(trecho)
    texto = "".join(blocos)
    pos = normalizar(texto).find(INICIO_DOCUMENTO)
    if pos >= 0:
        # encontra o ponto correspondente no texto original aproximando pelo prefixo
        bruto = texto
        m = re.search(
            r"REGIMENTO INTERNO DA EMPRESA MATO-GROSSENSE",
            bruto,
            flags=re.IGNORECASE,
        )
        if m:
            texto = bruto[m.start() :]
    return texto, offsets


def _mapa_normalizado(texto: str) -> tuple[str, list[int]]:
    """Texto sem acentos/caixa e índice de cada caractere no original."""
    n_chars: list[str] = []
    orig: list[int] = []
    for i, ch in enumerate(texto):
        n = unicodedata.normalize("NFD", ch)
        n = "".join(c for c in n if unicodedata.category(c) != "Mn")
        n = n.upper().replace("º", "").replace("°", "").replace("ª", "")
        if n.isspace():
            if n_chars and n_chars[-1] != " ":
                n_chars.append(" ")
                orig.append(i)
            continue
        for c in n:
            n_chars.append(c)
            orig.append(i)
    compactado: list[str] = []
    orig_c: list[int] = []
    prev_space = False
    for c, i in zip(n_chars, orig):
        space = c == " "
        if space and prev_space:
            continue
        compactado.append(c)
        orig_c.append(i)
        prev_space = space
    return "".join(compactado), orig_c


def recortar(texto: str, inicio: str, fim: str | None) -> str:
    n_texto, mapa = _mapa_normalizado(texto)
    n_inicio = normalizar(inicio)
    a = n_texto.find(n_inicio)
    if a < 0:
        raise RuntimeError(f"Marcador de início não encontrado: {inicio}")
    ini_orig = mapa[a]
    if not fim:
        return texto[ini_orig:]
    n_fim = normalizar(fim)
    b = n_texto.find(n_fim, a + len(n_inicio))
    if b < 0:
        return texto[ini_orig:]
    return texto[ini_orig : mapa[b]]


def pagina_do_trecho(texto_completo: str, trecho: str) -> tuple[int | None, int | None]:
    pos = texto_completo.find(trecho[:80]) if trecho else -1
    if pos < 0:
        return None, None
    pags = [int(m.group(1)) for m in re.finditer(r"\[\[p=(\d+)\]\]", texto_completo[: pos + len(trecho)])]
    if not pags:
        return None, None
    return pags[0], pags[-1]


RE_PAGINA = re.compile(r"^\[\[p=\d+\]\]$")
RE_ARTIGO = re.compile(r"^Art\.?\s*(\d+)[ºo°]?\s*(.*)$", re.IGNORECASE)
RE_INCISO = re.compile(r"^([IVXLCDM]{1,8})[-\s]+(.+)$")
RE_PARAGRAFO = re.compile(r"^§\s*(\d+)[ºo°]?\s*(.*)$")
RE_PARAGRAFO_UNICO = re.compile(r"^Par[áa]grafo [úu]nico[:\s]+(.*)$", re.IGNORECASE)
RE_ALINEA = re.compile(r"^([a-z])[)\.]\s+(.*)$")
RE_RUIDO = re.compile(
    r"GOVERNO DO ESTADO|Imprensa Oficial|C[oó]digo de Autenticidade|Di[áa]rio Oficial|P[áa]gina \d+",
    re.IGNORECASE,
)


def _compactar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def parse_artigos(corpo: str) -> list[dict]:
    artigos: list[dict] = []
    atual: dict | None = None
    inciso: dict | None = None
    alinea: dict | None = None

    def fechar_alinea():
        nonlocal alinea, inciso
        if alinea is not None and inciso is not None:
            alinea["texto"] = _compactar(alinea["texto"])
            inciso["itens"].append(alinea)
            alinea = None

    def fechar_inciso():
        nonlocal inciso, atual
        fechar_alinea()
        if inciso is not None and atual is not None:
            inciso["texto"] = _compactar(inciso["texto"])
            atual["alineas"].append(inciso)
            inciso = None

    def fechar_artigo():
        nonlocal atual
        fechar_inciso()
        if atual is not None:
            atual["texto"] = _compactar(atual["texto"])
            artigos.append(atual)
            atual = None

    for bruta in corpo.splitlines():
        linha = bruta.strip()
        if not linha or RE_PAGINA.match(linha) or RE_RUIDO.search(linha):
            continue

        m_art = RE_ARTIGO.match(linha)
        if m_art:
            fechar_artigo()
            atual = {
                "numero": int(m_art.group(1)),
                "bloco_tematico": None,
                "texto": m_art.group(2).strip(),
                "alineas": [],
            }
            continue

        m_par = RE_PARAGRAFO.match(linha)
        if m_par and atual is not None:
            fechar_inciso()
            atual["texto"] += " § " + m_par.group(1) + "º " + m_par.group(2).strip()
            continue

        m_uni = RE_PARAGRAFO_UNICO.match(linha)
        if m_uni and atual is not None:
            fechar_inciso()
            atual["texto"] += " Parágrafo único: " + m_uni.group(1).strip()
            continue

        m_inc = RE_INCISO.match(linha)
        if m_inc and atual is not None:
            fechar_inciso()
            inciso = {
                "marcador": m_inc.group(1),
                "texto": m_inc.group(2).strip(),
                "itens": [],
            }
            continue

        m_al = RE_ALINEA.match(linha)
        if m_al and inciso is not None:
            fechar_alinea()
            alinea = {"marcador": m_al.group(1), "texto": m_al.group(2).strip()}
            continue

        if atual is None:
            continue
        if alinea is not None:
            alinea["texto"] += " " + linha
        elif inciso is not None:
            inciso["texto"] += " " + linha
        else:
            atual["texto"] += " " + linha

    fechar_artigo()
    return artigos


def montar_texto_completo(artigos: list[dict], corpo: str) -> str:
    if not artigos:
        linhas = [
            ln.strip()
            for ln in corpo.splitlines()
            if ln.strip() and not RE_PAGINA.match(ln.strip()) and not RE_RUIDO.search(ln)
        ]
        return _compactar(" ".join(linhas))
    partes: list[str] = []
    for art in artigos:
        partes.append(f"Art. {art['numero']}º {art['texto']}")
        for inciso in art.get("alineas") or []:
            partes.append(f"{inciso['marcador']} - {inciso['texto']}")
            for item in inciso.get("itens") or []:
                partes.append(f"{item['marcador']}) {item['texto']}")
    return "\n".join(partes)


def montar_secao(meta: dict, recorte: str, texto_pdf: str) -> dict:
    artigos = parse_artigos(recorte)
    texto_completo = montar_texto_completo(artigos, recorte)
    p0, p1 = pagina_do_trecho(texto_pdf, recorte)
    return {
        "id": meta["id"],
        "tipo": meta["tipo"],
        "numero": meta["numero"],
        "rotulo": meta["rotulo"],
        "titulo": meta["titulo"],
        "parte": meta["parte"],
        "pagina_inicio": p0,
        "pagina_fim": p1,
        "tema": meta["tema"],
        "texto_completo": texto_completo,
        "paragrafos": artigos,
    }


def extrair(caminho_pdf: Path, ids: list[str]) -> dict:
    texto, _ = ler_pdf(caminho_pdf)
    por_id = {s["id"]: s for s in SECOES}
    secoes = []
    for sid in ids:
        meta = por_id[sid]
        recorte = recortar(texto, meta["inicio"], meta["fim"])
        secoes.append(montar_secao(meta, recorte, texto))
    return {
        "documento": {**METADADOS_DOCUMENTO, "arquivo": caminho_pdf.name},
        "secoes": secoes,
    }


def resolver_ids(pedidos: list[str]) -> list[str]:
    indice: dict[str, str] = {}
    for secao in SECOES:
        indice[normalizar(secao["id"])] = secao["id"]
        for alias in secao["aliases"]:
            indice[normalizar(alias)] = secao["id"]
    resolvidos: list[str] = []
    vistos: set[str] = set()
    desconhecidos: list[str] = []
    for pedido in pedidos:
        chave = normalizar(pedido.replace("_", "-"))
        sid = indice.get(chave)
        if not sid:
            desconhecidos.append(pedido)
            continue
        if sid not in vistos:
            resolvidos.append(sid)
            vistos.add(sid)
    if desconhecidos:
        disponiveis = ", ".join(s["id"] for s in SECOES)
        raise ValueError(
            "Subseção(ões) desconhecida(s): "
            + ", ".join(desconhecidos)
            + f"\nIDs válidos: {disponiveis}"
        )
    return resolvidos


def listar_secoes() -> None:
    print("Subseções disponíveis:")
    for secao in SECOES:
        print(f"  {secao['id']:28} {secao['rotulo']:40} {secao['titulo']}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extrai subseções do Regimento Interno da MTI para JSON."
    )
    parser.add_argument("subsecoes", nargs="*", help="IDs das subseções a extrair.")
    parser.add_argument("--list", action="store_true", help="Lista IDs disponíveis e sai.")
    parser.add_argument("--all", action="store_true", help="Extrai todas as subseções cadastradas.")
    parser.add_argument("--pdf", type=Path, default=PDF_PADRAO)
    parser.add_argument("--out", type=Path, default=JSON_PADRAO)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list:
        listar_secoes()
        return 0

    if args.all:
        ids = [s["id"] for s in SECOES]
    else:
        if not args.subsecoes:
            print("Informe as subseções a extrair. Use --list para ver os IDs.", file=sys.stderr)
            return 2
        try:
            ids = resolver_ids(args.subsecoes)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 2

    if not args.pdf.exists():
        print(f"PDF não encontrado: {args.pdf}", file=sys.stderr)
        return 1

    print(f"Lendo {args.pdf} ...")
    dados = extrair(args.pdf, ids)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Salvo em {args.out} ({len(dados['secoes'])} seção(ões)).")
    for secao in dados["secoes"]:
        n_par = len(secao["paragrafos"])
        print(
            f"  - {secao['id']}: {secao['titulo']} "
            f"(p. {secao['pagina_inicio']}-{secao['pagina_fim']}, {n_par} artigo(s))"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
