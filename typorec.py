from spellchecker import SpellChecker
import language_tool_python
import re
from sympy import sympify


def texto(input_text):
    # Convert input_text to string
    input_text = str(input_text)
    math_pattern = re.compile(r"((?P<brackets>[()])|(?P<number>\-?\d*\.?\d+)|(?P<operator>[+\-\*\/]))")

    matches = math_pattern.findall(input_text)

    if matches:
        # If there are mathematical operations, evaluate and return the result
            result = evaluate_math_operation(input_text)
            return str(result)
    else:
        # If no mathematical operation, proceed with spell and grammar checking
        # Step 1: Spell Checking
        spell = SpellChecker()
        words = input_text.split()
        
        # Correct spellings, handling None values
        corrected_words = [spell.correction(word) if word is not None else '' for word in words]
        
        # Debug: Print the corrected words
        print("Corrected Words:", corrected_words)

        # Replace None values with empty string
        corrected_words = [word if word is not None else '' for word in corrected_words]

        corrected_text_spell = ' '.join(corrected_words)

        # Step 2: Grammar Checking
        #tool = language_tool_python.LanguageToolPublicAPI('en-US')
        
        # Debug: Print the corrected text after grammar checking
        #corrected_text_grammar = tool.correct(corrected_text_spell)
        #print("Corrected Text Grammar:", corrected_text_grammar)

        return corrected_text_spell

def evaluate_math_operation(input_text):
    input_text = str(input_text)
    math_pattern = re.compile(r"((?P<brackets>[()])|(?P<number>\-?\d*\.?\d+)|(?P<operator>[+\-\*\/]))")

    matches = math_pattern.findall(input_text)
    expression = ''.join(match[0] for match in matches)

    if expression:
        # If there is a mathematical expression, evaluate and return the result
        result = sympify(expression)
        return str(result)
    else:
        return None
import qrcode
from PIL import Image
from io import BytesIO 
def generate_qr_code(url):
    # Create a QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add data to the QR code
    qr.add_data(url)
    qr.make(fit=True)

    # Create an image from the QR code instance
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert PIL Image to bytes-like object
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()

    return img_bytes