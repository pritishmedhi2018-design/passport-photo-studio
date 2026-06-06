from PIL import Image, ImageDraw, ImageOps

# ==========================================
# A4 SETTINGS (300 DPI)
# ==========================================

A4_WIDTH = 2480
A4_HEIGHT = 3508

LEFT_MARGIN = 140
RIGHT_MARGIN = 140

TOP_MARGIN = 140
BOTTOM_MARGIN = 140

GAP_X = 25
GAP_Y = 25

BORDER = 2

# ==========================================
# MM TO PIXELS
# ==========================================

def mm_to_pixels(mm, dpi=300):

    inches = mm / 25.4

    return int(inches * dpi)


# ==========================================
# CREATE SINGLE PHOTO TILE
# ==========================================

def create_photo_tile(
        image,
        width_mm,
        height_mm
):

    width_px = mm_to_pixels(width_mm)
    height_px = mm_to_pixels(height_mm)

    image = image.convert("RGB")

    image = ImageOps.fit(
        image,
        (width_px, height_px),
        Image.LANCZOS
    )

    return image


# ==========================================
# GENERATE LAYOUT
# ==========================================

def generate_layout(photo_data):

    canvas = Image.new(
        "RGB",
        (
            A4_WIDTH,
            A4_HEIGHT
        ),
        "white"
    )

    draw = ImageDraw.Draw(canvas)

    usable_width = (
        A4_WIDTH
        - LEFT_MARGIN
        - RIGHT_MARGIN
    )

    usable_height = (
        A4_HEIGHT
        - TOP_MARGIN
        - BOTTOM_MARGIN
    )

    x = LEFT_MARGIN
    y = TOP_MARGIN + 40

    row_height = 0

    total_placed = 0

    overflow = False

    # -----------------------------------
    # LOOP THROUGH ALL PHOTOS
    # -----------------------------------

    for item in photo_data:

        image = item["image"]

        width_mm = item["width_mm"]
        height_mm = item["height_mm"]

        copies = item["copies"]

        tile = create_photo_tile(
            image,
            width_mm,
            height_mm
        )

        photo_w, photo_h = tile.size

        # -----------------------------------
        # PLACE COPIES
        # -----------------------------------

        for _ in range(copies):

            # Next row
            if x + photo_w > A4_WIDTH - RIGHT_MARGIN:

                x = LEFT_MARGIN

                y += row_height + GAP_Y

                row_height = 0

            # Overflow check
            if y + photo_h > A4_HEIGHT - BOTTOM_MARGIN:

                overflow = True

                break

            # Border
            draw.rectangle(
                (
                x-3,
                y-3,
                x+photo_w+3,
                y+photo_h+3
                ),
                outline="black",
                width=2
                )

            # Paste image
            canvas.paste(
                tile,
                (
                    x,
                    y
                )
            )

            x += photo_w + GAP_X

            row_height = max(
                row_height,
                photo_h
            )

            total_placed += 1

        if overflow:

            break

    return canvas


# ==========================================
# PREVIEW
# ==========================================

def create_preview(sheet):

    preview = sheet.copy()

    preview.thumbnail(
        (
            1000,
            1400
        ),
        Image.LANCZOS
    )

    return preview


# ==========================================
# CAPACITY CHECK
# ==========================================

def get_max_capacity(photo_data):

    count = 0

    x = LEFT_MARGIN
    y = TOP_MARGIN

    row_height = 0

    for item in photo_data:

        width_px = mm_to_pixels(
            item["width_mm"]
        )

        height_px = mm_to_pixels(
            item["height_mm"]
        )

        copies = item["copies"]

        for _ in range(copies):

            if x + width_px > A4_WIDTH - RIGHT_MARGIN:

                x = LEFT_MARGIN

                y += row_height + GAP_Y

                row_height = 0

            if y + height_px > A4_HEIGHT - BOTTOM_MARGIN:

                return count

            x += width_px + GAP_X

            row_height = max(
                row_height,
                height_px
            )

            count += 1

    return count
