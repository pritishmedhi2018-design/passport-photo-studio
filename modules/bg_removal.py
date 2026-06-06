from rembg import remove, new_session
from PIL import Image
import io

session = new_session("u2netp")

def remove_background(input_file):

    if isinstance(input_file, bytes):

        image = Image.open(
            io.BytesIO(input_file)
        ).convert("RGB")

    else:

        image = Image.open(
            input_file
        ).convert("RGB")

    # Resize for speed

    max_size = 1200

    w,h = image.size

    if max(w,h) > max_size:

        ratio = max_size / max(w,h)

        image = image.resize(
            (
                int(w*ratio),
                int(h*ratio)
            ),
            Image.LANCZOS
        )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    output = remove(
    buffer.getvalue(),
    session=session
    )
    
    output_image = Image.open(
        io.BytesIO(output)
)

    return output_image
