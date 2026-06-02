from rembg import remove, new_session
from PIL import Image

session = new_session("u2netp")

def remove_background(uploaded_file):
    image = Image.open(uploaded_file).convert("RGBA")
    result = remove(image, session=session)
    return result