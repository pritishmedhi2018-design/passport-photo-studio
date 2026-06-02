import streamlit as st
from streamlit_cropper import st_cropper

from PIL import Image
import io
import pandas as pd

from modules.bg_removal import remove_background
from modules.layout_generator import (
    generate_layout,
    create_preview
)

from modules.pricing import calculate_total

from modules.database import (
    create_database,
    save_order,
    get_total_orders,
    get_total_revenue,
    get_today_orders,
    get_today_revenue
)

# -----------------------------------
# DATABASE INIT
# -----------------------------------

create_database()

# -----------------------------------
# PAGE CONFIG
# -----------------------------------

st.set_page_config(
    page_title="Passport Photo Studio",
    page_icon="📸",
    layout="wide"
)

# -----------------------------------
# SESSION STATE
# -----------------------------------

if "processed_photos" not in st.session_state:
    st.session_state.processed_photos = []

# -----------------------------------
# CACHE BG REMOVAL
# -----------------------------------

@st.cache_data(show_spinner=False)
def cached_bg_remove(file_bytes):

    file_obj = io.BytesIO(file_bytes)

    return remove_background(file_obj)

# -----------------------------------
# HEADER
# -----------------------------------

st.title("📸 Smart Passport Photo Studio")

st.caption(
    """
    AI Background Removal • Crop • Zoom • Rotate •
    Passport Photo Sheet Generator • Billing System
    """
)

# ===================================
# SETTINGS - NOW IN MAIN AREA
# ===================================
st.header("⚙️ Photo Settings")

col_set1, col_set2, col_set3 = st.columns(3)

with col_set1:
    photo_type = st.selectbox(
        "Photo Type",
        ["Passport", "ID Card"],
        key="photo_type"
    )
    remove_bg = st.radio(
        "Remove Background",
        ["Yes", "No"],
        key="remove_bg"
    )

with col_set2:
    crop_option = st.radio(
        "Crop Option",
        [
            "No Crop",
            "Manual Crop",
            "Passport Crop"
        ],
        key="crop_option"
    )
    bg_option = st.selectbox(
        "Background Color",
        [
            "Original",
            "White",
            "Blue",
            "Red",
            "Light Grey",
            "Green"
        ],
        key="bg_option"
    )

with col_set3:
    photos_per_row = st.selectbox(
        "Photos Per Row",
        [6, 7],
        key="photos_per_row"
    )

st.divider()

# -----------------------------------
# SIDEBAR - Only Statistics Now
# -----------------------------------
with st.sidebar:
    st.header("📊 Statistics")
    st.metric("Total Orders", get_total_orders())
    st.metric("Today's Orders", get_today_orders())
    st.metric("Total Revenue", f"₹{get_total_revenue()}")
    st.metric("Today's Revenue", f"₹{get_today_revenue()}")
# -----------------------------------
# FILE UPLOAD
# -----------------------------------

uploaded_files = st.file_uploader(
    "Upload Photo(s)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

# -----------------------------------
# NO FILE
# -----------------------------------

if not uploaded_files:

    st.info(
        "Upload one or more photos to begin."
    )

    st.stop()

# -----------------------------------
# PROCESS STORAGE
# -----------------------------------

processed_photos = []

copies = []

# -----------------------------------
# PHOTO PROCESSING SECTION START
# -----------------------------------

for idx, uploaded_file in enumerate(uploaded_files):

    st.divider()

    st.subheader(
        f"Photo {idx + 1}"
    )

    file_bytes = uploaded_file.getvalue()

    try:
        if remove_bg == "Yes":
            with st.spinner(
                "Removing background..."
            ):
                image = cached_bg_remove(
                    file_bytes
                )
        else:
            image = Image.open(
                io.BytesIO(file_bytes)
            ).convert("RGBA")
    
    except Exception:
        image = Image.open(
            io.BytesIO(file_bytes)
        ).convert("RGBA")

    # --------------------------------
    # BACKGROUND CHANGE
    # --------------------------------

    if bg_option != "Original":

        colors = {
    "White": (255, 255, 255),
    "Blue": (135, 206, 235),
    "Red": (255, 0, 0),
    "Light Grey": (220, 220, 220),
    "Green": (0, 150, 0)
        }

        bg = Image.new(
            "RGBA",
            image.size,
            colors[bg_option]
        )

        bg.paste(
            image,
            (0, 0),
            image
        )

        image = bg

    # --------------------------------
    # PREVIEW + EDITING
    # --------------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.write("Photo Editor")

    if image.mode == "RGBA":
        image = image.convert("RGB")

    if crop_option == "Manual Crop":

        cropped_img = st_cropper(
    image,
    realtime_update=True,
    box_color="#0000FF",
    aspect_ratio=(35, 45) if photo_type == "Passport" else (25, 35),
    return_type="image"
)

    else:

        cropped_img = image

    with col2:

        st.write("Adjust Photo")

    zoom = st.slider(
        "Zoom %",
        50,
        200,
        100,
        key=f"zoom_{idx}"
    )

    rotation = st.slider(
        "Rotate",
        -180,
        180,
        0,
        key=f"rot_{idx}"
    )

    brightness = st.slider(
        "Brightness",
        50,
        200,
        100,
        key=f"bright_{idx}"
    )

    # --------------------------------
    # ZOOM
    # --------------------------------

    scale = zoom / 100
    w, h = cropped_img.size
    from PIL import ImageOps
    
    cropped_img = cropped_img.resize(
        (
            int(w * scale),
            int(h * scale)
        ),
        Image.LANCZOS
    )

    cropped_img = ImageOps.fit(
        cropped_img,
        (w, h),
        Image.LANCZOS
    )

    # --------------------------------
    # ROTATE
    # --------------------------------
 
     
    cropped_img = cropped_img.rotate(
        rotation,
        expand=True,
        fillcolor="white"
    )

    # --------------------------------
    # BRIGHTNESS
    # --------------------------------

    from PIL import ImageEnhance

    enhancer = ImageEnhance.Brightness(
        cropped_img
    )

    cropped_img = enhancer.enhance(
        brightness / 100
    )

    # --------------------------------
    # PREVIEW
    # --------------------------------

    st.image(
        cropped_img,
        caption=f"Edited Photo {idx+1}",
        use_container_width=True
    )

    qty = st.number_input(
        f"Copies for Photo {idx+1}",
        min_value=3,
        value=3,
        step=1,
        key=f"copies_{idx}"
    )

    processed_photos.append(
        cropped_img.convert("RGB")
    )

    copies.append(qty)

# --------------------------------
# BILLING SECTION
# --------------------------------
# 
    st.divider()
    st.header("Billing")
    total_photos = sum(copies)
    total_amount = calculate_total(
        total_photos
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Photos",
        total_photos
    )

    c2.metric(
        "Rate",
        "₹5"
    )

    c3.metric(
        "Amount",
        f"₹{total_amount}"
    )

    st.divider()

    generate_btn = st.button(
        "Generate A4 Sheet",
        use_container_width=True
    )

    if not generate_btn:
        st.stop()

    # --------------------------------
# GENERATE SHEET
# --------------------------------

with st.spinner(
    "Generating print sheet..."
):

    sheet = generate_layout(
        photos=processed_photos,
        copies=copies,
        photos_per_row=photos_per_row,
        photo_type=photo_type
    )

preview = create_preview(
    sheet
)

# --------------------------------
# PREVIEW
# --------------------------------

st.header(
    "A4 Print Preview"
)

st.image(
    preview,
    use_container_width=True
)

# --------------------------------
# ORDER SUMMARY
# --------------------------------

st.divider()

st.subheader(
    "Order Summary"
)

summary_df = pd.DataFrame(
    {
        "Item": [
            "Photo Type",
            "Layout",
            "Total Photos",
            "Rate",
            "Amount"
        ],
        "Value": [
            photo_type,
            f"{photos_per_row} per row",
            total_photos,
            "₹5",
            f"₹{total_amount}"
        ]
    }
)

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True
)

# --------------------------------
# SAVE ORDER
# --------------------------------

try:

    save_order(
        photo_type,
        photos_per_row,
        total_photos,
        total_amount
    )

except Exception as e:

    st.warning(
        f"Database Error: {e}"
    )

# --------------------------------
# PNG DOWNLOAD
# --------------------------------

png_buffer = io.BytesIO()

sheet.save(
    png_buffer,
    format="PNG",
    dpi=(300, 300)
)

png_buffer.seek(0)

# --------------------------------
# PDF DOWNLOAD
# --------------------------------

pdf_buffer = io.BytesIO()

sheet.convert("RGB").save(
    pdf_buffer,
    format="PDF",
    resolution=300.0
)

pdf_buffer.seek(0)

# -----------------------------------
# PHOTO PROCESSING SECTION START
# -----------------------------------

for idx, uploaded_file in enumerate(uploaded_files):

    st.divider()

    st.subheader(
        f"Photo {idx + 1}"
    )

    file_bytes = uploaded_file.getvalue()

try:
    if remove_bg == "Yes":
        with st.spinner(
            "Removing background..."
        ):
            image = cached_bg_remove(
                file_bytes
            )
    else:
        image = Image.open(
            io.BytesIO(file_bytes)
        ).convert("RGBA")
    
except Exception:
    
        image = Image.open(
            io.BytesIO(file_bytes)
            ).convert("RGBA")

# --------------------------------
# DOWNLOADS
# --------------------------------

st.divider()

col1, col2 = st.columns(2)

with col1:

    st.download_button(
        label="⬇ Download PNG",
        data=png_buffer.getvalue(),
        file_name="passport_sheet.png",
        mime="image/png",
        use_container_width=True
    )

with col2:

    st.download_button(
        label="⬇ Download PDF",
        data=pdf_buffer.getvalue(),
        file_name="passport_sheet.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# --------------------------------
# SUCCESS MESSAGE
# --------------------------------

st.success(
    f"""
    Sheet Generated Successfully!

    Photo Type : {photo_type}

    Layout : {photos_per_row} Photos Per Row

    Total Photos : {total_photos}

    Amount : ₹{total_amount}
    """
)

# --------------------------------
# FOOTER
# --------------------------------

st.divider()

st.caption(
    """
    Smart Passport Photo Studio

    Features:
    • AI Background Removal
    • Crop / Zoom / Rotate
    • Passport & ID Card Sizes
    • A4 Sheet Generator
    • SQLite Billing
    • PNG & PDF Download
    """
)