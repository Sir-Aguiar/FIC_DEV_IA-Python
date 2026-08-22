# historico.py
# Mini-lab Aula 11 — Persistência com SQLAlchemy
# Objetivo: cadastrar documentos processados e consultar histórico

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import (
    Column, DateTime, Float, Integer, String, Text,
    create_engine, func, text,
)
from sqlalchemy.orm import DeclarativeBase, Session

# Banco próprio deste mini-lab (não reutiliza data/pipeline.db da aula)
DATABASE_PATH = Path(__file__).resolve().parent / 'pipeline.db'
engine = create_engine(f'sqlite:///{DATABASE_PATH.as_posix()}', echo=False)


class Base(DeclarativeBase):
    pass


# ─── Modelo ──────────────────────────────────────────────────
class Documento(Base):
    __tablename__ = 'documentos'

    id            = Column(Integer, primary_key=True, autoincrement=True)
    nome          = Column(String(255), nullable=False)
    origem        = Column(String(50),  nullable=False)
    tipo          = Column(String(20),  nullable=False)   # pdf, docx, txt
    status        = Column(String(20),  nullable=False, default='pendente')
    num_tokens    = Column(Integer,     nullable=True)
    score_ia      = Column(Float,       nullable=True)
    observacao    = Column(Text,        nullable=True)
    tentativas    = Column(Integer,     nullable=False, default=0)
    criado_em     = Column(DateTime,    default=datetime.now)
    processado_em = Column(DateTime,    nullable=True)

    def __repr__(self) -> str:
        return (
            f'<Documento id={self.id} nome={self.nome!r}'
            f' status={self.status!r}>'
        )


class LogProcessamento(Base):
    __tablename__ = 'logs_processamento'

    id              = Column(Integer, primary_key=True, autoincrement=True)
    doc_id          = Column(Integer, nullable=False)
    status_anterior = Column(String(20), nullable=False)
    status_novo     = Column(String(20), nullable=False)
    timestamp       = Column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return (
            f'<LogProcessamento doc_id={self.doc_id} '
            f'{self.status_anterior!r} -> {self.status_novo!r}>'
        )


# Criar tabelas (idempotente)
Base.metadata.create_all(engine)


def _registrar_log(session: Session, doc: Documento, status_novo: str) -> None:
    """Registra a mudança de status do documento na tabela de logs."""
    session.add(LogProcessamento(
        doc_id=doc.id,
        status_anterior=doc.status,
        status_novo=status_novo,
    ))


# ─── Funções de domínio ──────────────────────────────────────
def cadastrar(nome: str, origem: str, tipo: str,
              num_tokens: int | None = None) -> Documento:
    """Cadastra um novo documento com status 'pendente'."""
    with Session(engine, expire_on_commit=False) as session:
        doc = Documento(
            nome=nome, origem=origem,
            tipo=tipo, num_tokens=num_tokens,
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)   # garante que doc.id está preenchido
        return doc


def processar(doc_id: int, score: float, obs: str | None = None) -> bool:
    """Marca documento como processado e registra score e timestamp."""
    with Session(engine) as session:
        doc = session.get(Documento, doc_id)
        if not doc:
            return False
        _registrar_log(session, doc, 'processado')
        doc.status        = 'processado'
        doc.score_ia      = score
        doc.observacao    = obs
        doc.processado_em = datetime.now()
        session.commit()
        return True


def marcar_erro(doc_id: int, motivo: str) -> bool:
    """Marca documento como 'erro' e registra o motivo."""
    with Session(engine) as session:
        doc = session.get(Documento, doc_id)
        if not doc:
            return False
        _registrar_log(session, doc, 'erro')
        doc.status     = 'erro'
        doc.observacao = motivo
        session.commit()
        return True


def incrementar_tentativa(doc_id: int) -> int | None:
    """Incrementa o contador de tentativas de processamento do documento."""
    with Session(engine) as session:
        doc = session.get(Documento, doc_id)
        if not doc:
            return None
        doc.tentativas = (doc.tentativas or 0) + 1
        session.commit()
        return doc.tentativas


def buscar_por_status(status: str) -> list[Documento]:
    """Retorna todos os documentos com o status informado."""
    with Session(engine, expire_on_commit=False) as session:
        return (session.query(Documento)
                .filter(Documento.status == status)
                .order_by(Documento.criado_em.desc())
                .all())


def historico_completo() -> list[Documento]:
    """Retorna todos os documentos em ordem cronológica inversa."""
    with Session(engine, expire_on_commit=False) as session:
        return (session.query(Documento)
                .order_by(Documento.criado_em.desc())
                .all())


def resumo_por_status() -> dict:
    """Retorna contagem de documentos agrupados por status."""
    with Session(engine) as session:
        resultados = (
            session.query(Documento.status, func.count(Documento.id))
            .group_by(Documento.status)
            .all()
        )
        return dict(resultados)


def top_por_score(n: int = 3) -> list[Documento]:
    """Retorna os N documentos com maior score_ia."""
    with Session(engine, expire_on_commit=False) as session:
        return (session.query(Documento)
                .filter(Documento.score_ia.isnot(None))
                .order_by(Documento.score_ia.desc())
                .limit(n)
                .all())


def resumo_por_origem() -> list[tuple]:
    """Média de score_ia e soma de num_tokens agrupados por origem."""
    with Session(engine) as session:
        return (
            session.query(
                Documento.origem,
                func.avg(Documento.score_ia),
                func.sum(Documento.num_tokens),
            )
            .group_by(Documento.origem)
            .order_by(Documento.origem)
            .all()
        )


def logs_de(doc_id: int) -> list[LogProcessamento]:
    """Retorna o histórico de mudanças de status de um documento."""
    with Session(engine, expire_on_commit=False) as session:
        return (session.query(LogProcessamento)
                .filter(LogProcessamento.doc_id == doc_id)
                .order_by(LogProcessamento.timestamp)
                .all())


# ─── Simulação do pipeline ───────────────────────────────────
def main() -> None:
    # Reinicia as tabelas deste script para a simulação bater com a saída esperada
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    sep = '=' * 55

    print(f'\n{sep}')
    print('  PIPELINE DE DOCUMENTOS — SIMULAÇÃO')
    print(sep)

    # 1. Cadastrar documentos
    print('\n[1] Cadastrando documentos...')
    lote = [
        ('relatorio_q1.pdf',    'upload', 'pdf',  1842),
        ('contrato_2024.pdf',   'email',  'pdf',   950),
        ('ata_reuniao.docx',    'drive',  'docx',  420),
        ('proposta_tecnica.pdf','upload', 'pdf',  2100),
        ('resumo_exec.txt',     'api',    'txt',   310),
        ('laudo_medico.pdf',    'upload', 'pdf',  3200),
        ('newsletter.txt',      'email',  'txt',   180),
        ('manual_usuario.pdf',  'drive',  'pdf',  5500),
    ]
    ids = []
    for nome, origem, tipo, tokens in lote:
        doc = cadastrar(nome, origem, tipo, tokens)
        ids.append(doc.id)
        print(f'   + #{doc.id:02d} {doc.nome}')

    # 2. Processar alguns documentos
    print('\n[2] Processando...')
    scores = [(ids[0], 0.92), (ids[1], 0.78), (ids[2], 0.85),
              (ids[4], 0.67), (ids[5], 0.95), (ids[6], 0.41)]
    for doc_id, score in scores:
        processar(doc_id, score)
        print(f'   ✓ #{doc_id:02d} processado — score: {score}')

    # 3. Marcar erros (com retentativas antes do erro definitivo)
    print('\n[3] Registrando erros...')
    for _ in range(2):
        tentativas = incrementar_tentativa(ids[3])
        print(f'   ↻ #{ids[3]:02d} tentativa {tentativas}')
    marcar_erro(ids[3], 'Arquivo corrompido — não foi possível extrair texto')
    print(f'   ✗ #{ids[3]:02d} marcado como erro')

    # ── Consultas analíticas ──────────────────────────────────
    print(f'\n{sep}')
    print('  HISTÓRICO E CONSULTAS')
    print(sep)

    # 4. Resumo por status
    print('\n[4] Resumo por status:')
    for status, total in sorted(resumo_por_status().items()):
        print(f'   {status:<12}: {total} documento(s)')

    # 5. Documentos pendentes
    pendentes = buscar_por_status('pendente')
    print(f'\n[5] Pendentes ({len(pendentes)}):')
    for d in pendentes:
        print(f'   #{d.id:02d} {d.nome:<30} {d.num_tokens:>5} tokens')

    # 6. Top 3 por score
    print('\n[6] Top 3 por score IA:')
    for i, d in enumerate(top_por_score(3), 1):
        print(f'   {i}. {d.nome:<30} score: {d.score_ia:.2f}')

    # 7. Documentos com erro
    erros = buscar_por_status('erro')
    print(f'\n[7] Erros ({len(erros)}):')
    for d in erros:
        print(f'   #{d.id:02d} {d.nome}')
        print(f'       Motivo: {d.observacao}')

    # 8. Histórico completo com SQL direto
    print(f'\n[8] Histórico completo (SQL direto):')
    with engine.connect() as conn:
        resultado = conn.execute(text(
            'SELECT id, nome, status, score_ia, num_tokens '
            'FROM documentos ORDER BY id'
        ))
        print(f'   {"ID":<4} {"NOME":<30} {"STATUS":<12} {"SCORE":>6} {"TOKENS":>7}')
        print(f'   {"-"*4} {"-"*30} {"-"*12} {"-"*6} {"-"*7}')
        for row in resultado:
            score = f'{row.score_ia:.2f}' if row.score_ia else '  —   '
            print(f'   {row.id:<4} {row.nome:<30} {row.status:<12} {score:>6} {row.num_tokens or 0:>7}')

    # ── Desafios extras ───────────────────────────────────────
    print(f'\n{sep}')
    print('  DESAFIOS EXTRAS')
    print(sep)

    print('\n[9] Média de score e soma de tokens por origem:')
    print(f'   {"ORIGEM":<10} {"MÉDIA SCORE":>12} {"SOMA TOKENS":>12}')
    for origem, media, soma in resumo_por_origem():
        media_fmt = f'{media:.2f}' if media is not None else '—'
        print(f'   {origem:<10} {media_fmt:>12} {int(soma or 0):>12}')

    print('\n[10] Logs de mudança de status:')
    with Session(engine, expire_on_commit=False) as session:
        logs = (session.query(LogProcessamento)
                .order_by(LogProcessamento.timestamp, LogProcessamento.id)
                .all())
        for log in logs:
            print(
                f'   #{log.doc_id:02d} {log.status_anterior} -> {log.status_novo}'
                f'  ({log.timestamp:%H:%M:%S})'
            )

    print('\n[11] Banco em memória (existe só enquanto o processo roda):')
    engine_mem = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine_mem)
    with Session(engine_mem) as session:
        session.add(Documento(
            nome='teste_memoria.pdf', origem='teste', tipo='pdf', num_tokens=10,
        ))
        session.commit()
        total_mem = session.query(Documento).count()
        print(f'   {total_mem} documento(s) no banco :memory: (não gera arquivo)')

    print(f'\n{sep}')
    print(f'  Banco salvo em: {DATABASE_PATH.name}')
    print(f'{sep}\n')


if __name__ == '__main__':
    main()
