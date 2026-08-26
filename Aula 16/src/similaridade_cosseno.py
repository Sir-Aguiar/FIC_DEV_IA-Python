import numpy as np

def similaridade_coseno(v1: np.ndarray, v2: np.ndarray) -> float:
  produto_interno = np.dot(v1, v2)
  
  # Calcula a norma dos vetores
  norma_v1 = np.linalg.norm(v1)
  norma_v2 = np.linalg.norm(v2)

  # Se a norma dos vetores for 0, a similaridade é 0
  if norma_v1 == 0 or norma_v2 == 0:
    return 0.0
  
  # Calcula a similaridade do cosseno
  return float(produto_interno / (norma_v1 * norma_v2))

# Simulando embeddings de dimensão 4 (normalmente 384 ou 768)

emb_contrato   = np.array([0.82, 0.15, 0.91, 0.33])  # 'O contrato foi assinado'

emb_acordo     = np.array([0.79, 0.18, 0.88, 0.31])  # 'O acordo foi firmado'

emb_culinaria  = np.array([0.12, 0.95, 0.08, 0.77])  # 'Receita de bolo de cenoura'

sim_juridico = similaridade_coseno(emb_contrato, emb_acordo)
sim_diferente = similaridade_coseno(emb_contrato, emb_culinaria)

print(f'Similaridade contrato vs acordo:    {sim_juridico:.4f}')   # ~0.99
print(f'Similaridade contrato vs culinaria: {sim_diferente:.4f}')  # ~0.20

# Interpretação:
# 1.0  = vetores idênticos (mesmo texto)
# >0.8 = muito similares (mesmo assunto)
# >0.5 = relacionados
# <0.3 = sem relação semântica aparente
