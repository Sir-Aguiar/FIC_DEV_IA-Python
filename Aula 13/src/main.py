# Baixar stopwords do NLTK (executar uma única vez, dentro do Python)
# import nltk
# nltk.download('stopwords')
# nltk.download('punkt')

# No Windows: informar ao pytesseract onde está o executável
# (no Linux/Mac geralmente detecta automaticamente)
from pathlib import Path
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

from PIL import Image, ImageFilter, ImageEnhance
import pytesseract


def preprocessar_pillow(caminho_img: str) -> Image.Image:
    """Aplica pré-processamento básico com Pillow para melhorar o OCR.

    Etapas: conversão para cinza, aumento de contraste,
    nitidez e redimensionamento para 300 DPI equivalente.

    Args:
        caminho_img: Caminho para a imagem de entrada.

    Returns:
        Imagem PIL processada, pronta para o OCR.
    """
    img = Image.open(caminho_img)

    # Passo 1: converter para escala de cinza
    # Elimina a cor — OCR funciona melhor em escala de cinza ou P&B
    img = img.convert("L")

    # Passo 2: aumentar contraste
    # Fator 2.0 = dobro do contraste original
    img = ImageEnhance.Contrast(img).enhance(2.0)

    # Passo 3: aumentar nitidez
    img = ImageEnhance.Sharpness(img).enhance(2.0)

    # Passo 4: filtro de nitidez adicional
    img = img.filter(ImageFilter.SHARPEN)

    # Passo 5: redimensionar para 300 DPI (se imagem for menor que 2000px)
    largura, altura = img.size

    if largura < 2000:
        fator = 2000 / largura
        nova_largura = int(largura * fator)
        nova_altura = int(altura * fator)
        img = img.resize((nova_largura, nova_altura), Image.LANCZOS)

    return img


IMAGE_PATH = Path(__file__).parent / "assets" / "image.png"

# Uso: OCR com pré-processamento Pillow
img_processada = preprocessar_pillow(IMAGE_PATH)

config = "--oem 3 --psm 6 -l por"
# --oem 3: motor LSTM (mais preciso)
# --psm 6: assume bloco uniforme de texto (ideal para documentos)
# -l por : idioma português

texto = pytesseract.image_to_string(img_processada, config=config)
print(texto[:500])
