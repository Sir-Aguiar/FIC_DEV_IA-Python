from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import pytesseract

CAMINHO_IMAGEM = Path(__file__).parent / "assets" / "image.png"


def binarizar_adaptativo(img_cinza: np.ndarray) -> np.ndarray:
    """Binarização adaptativa: ideal para iluminação desigual.

    Diferente da binarização global (um único limiar para toda a imagem),
    a adaptativa calcula o limiar local em cada região,
    compensando sombras e gradientes de iluminação.
    """
    return cv2.adaptiveThreshold(
        img_cinza,
        255,  # valor máximo (branco)
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,  # peso gaussiano por vizinhança
        cv2.THRESH_BINARY,  # texto preto, fundo branco
        blockSize=31,  # tamanho da vizinhança (ímpar, ex: 11, 21, 31)
        C=10,  # constante subtraída da média (ajusta sensibilidade)
    )


def remover_ruido(img_bin: np.ndarray) -> np.ndarray:
    """Remove pequenos pontos de ruído com operações morfológicas.

    Opening = erosão seguida de dilatação: elimina manchas pequenas
    sem afetar as letras, que têm estrutura maior e mais regular.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    return cv2.morphologyEx(img_bin, cv2.MORPH_OPEN, kernel)


def corrigir_inclinacao(img: np.ndarray) -> np.ndarray:
    """Detecta e corrige a inclinação (deskew) de um documento escaneado.

    Usa a Transformada de Hough para detectar linhas horizontais e
    calcula o ângulo médio de inclinação para rotacionar a imagem.
    """
    coords = np.column_stack(np.where(img < 128))  # pixels escuros
    if len(coords) == 0:
        return img

    angulo = cv2.minAreaRect(coords)[-1]  # ângulo da caixa mínima

    # Ajuste do ângulo: cv2 retorna ângulos entre -90 e 0
    if angulo < -45:
        angulo = 90 + angulo

    # Só corrigir se a inclinação for significativa (> 0.5 grau)
    if abs(angulo) < 0.5:
        return img

    (h, w) = img.shape[:2]
    centro = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(centro, angulo, 1.0)
    rotacionada = cv2.warpAffine(
        img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    return rotacionada


def preprocessar_opencv(caminho_img: str) -> Image.Image:
    """Pipeline completo de pré-processamento com OpenCV.

    Args:
        caminho_img: Caminho para a imagem de entrada.

    Returns:
        Imagem PIL binarizada e corrigida, pronta para OCR.
    """
    # Carregar como array NumPy (escala de cinza)
    img = cv2.imread(caminho_img, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Imagem nao encontrada: {caminho_img}")

    # Denoising com filtro não-local (muito eficaz para ruído gaussiano)
    img = cv2.fastNlMeansDenoising(img, h=10)

    # Binarização adaptativa
    img_bin = binarizar_adaptativo(img)

    # Remoção de ruído morfológico
    img_limpa = remover_ruido(img_bin)

    # Correção de inclinação
    img_final = corrigir_inclinacao(img_limpa)

    # Converter de volta para PIL (pytesseract aceita ambos)
    return Image.fromarray(img_final)


# Passa a imagem em preto e branco gerada pelo OpenCV
img_tratada = preprocessar_opencv(CAMINHO_IMAGEM)

# Executa a leitura
config = "--oem 3 --psm 6 -l por"
texto = pytesseract.image_to_string(img_tratada, config=config)

print("--- Texto Extraído ---")
print(texto)
