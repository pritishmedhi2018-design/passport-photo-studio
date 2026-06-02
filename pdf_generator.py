# pdf_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Image
from PIL import Image as PILImage
import tempfile


def save_as_pdf(a4_sheet, pdf_path):

    temp_img = tempfile.NamedTemporaryFile(
        suffix=".png",
        delete=False
    )

    a4_sheet.save(
        temp_img.name,
        format="PNG"
    )

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4
    )

    elements = []

    img = Image(
        temp_img.name,
        width=595,
        height=842
    )

    elements.append(img)

    doc.build(elements)

    return pdf_path