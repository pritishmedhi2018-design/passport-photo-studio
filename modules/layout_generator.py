from PIL import Image, ImageDraw, ImageOps


def generate_layout(
    photos,
    copies,
    photos_per_row=6,
    photo_type="Passport"
):

    # A4 @ 300 DPI
    A4_WIDTH = 2480
    A4_HEIGHT = 3508

    # Margins
    LEFT_MARGIN = 120
    RIGHT_MARGIN = 120
    TOP_MARGIN = 120
    BOTTOM_MARGIN = 120

    # Photo Size
    if photo_type == "Passport":

        PHOTO_W = 413      # 35 mm
        PHOTO_H = 531      # 45 mm

    else:

        PHOTO_W = 295      # 25 mm
        PHOTO_H = 413      # 35 mm

    # Layout Settings
    GAP_X = 25
    GAP_Y = 25

    BORDER = 1

    canvas = Image.new(
        "RGB",
        (A4_WIDTH, A4_HEIGHT),
        "white"
    )

    draw = ImageDraw.Draw(canvas)

    photo_list = []

    # -------------------------
    # Generate Copies
    # -------------------------

    for photo, qty in zip(
        photos,
        copies
    ):

        photo = photo.convert(
            "RGB"
        )

        # Fill complete photo area
        photo = ImageOps.fit(
    photo,
    (PHOTO_W, PHOTO_H),
    Image.LANCZOS
)

        for _ in range(
            int(qty)
        ):

            photo_list.append(
                photo.copy()
            )

    # -------------------------
    # Layout Width
    # -------------------------

    layout_width = (
        photos_per_row * PHOTO_W
    ) + (
        (photos_per_row - 1)
        * GAP_X
    )

    start_x = (
        A4_WIDTH
        - layout_width
    ) // 2

    if start_x < LEFT_MARGIN:

        start_x = LEFT_MARGIN

    x = start_x
    y = TOP_MARGIN

    current_col = 0

    # -------------------------
    # Place Photos
    # -------------------------

    for photo in photo_list:

        if (
            y + PHOTO_H
            > A4_HEIGHT
            - BOTTOM_MARGIN
        ):
            break

        draw.rectangle(
            (
                x - BORDER,
                y - BORDER,
                x + PHOTO_W + BORDER,
                y + PHOTO_H + BORDER
            ),
            outline="black",
            width=BORDER
        )

        canvas.paste(
            photo,
            (x, y)
        )

        current_col += 1

        if (
            current_col
            >= photos_per_row
        ):

            current_col = 0

            x = start_x

            y += (
                PHOTO_H
                + GAP_Y
            )

        else:

            x += (
                PHOTO_W
                + GAP_X
            )

    return canvas


def create_preview(
    sheet
):

    preview = sheet.copy()

    preview.thumbnail(
        (
            900,
            1200
        ),
        Image.LANCZOS
    )

    return preview