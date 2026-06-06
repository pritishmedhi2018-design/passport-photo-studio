import streamlit as st
from streamlit_cropper import st_cropper

from PIL import (
    Image,
    ImageOps,
    ImageEnhance,
    ImageStat
)

import io
import cv2
import numpy as np
import pandas as pd

from modules.bg_removal import remove_background
from modules.layout_generator import (
    generate_layout,
    create_preview,
    get_max_capacity
)

from modules.pricing import calculate_total

from modules.database import (
    create_database,
    save_order,
    get_total_orders,
    get_total_revenue,
    get_today_orders,
    get_today_revenue,
    get_orders,
    delete_order
)

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Passport Photo Studio",
    page_icon="📸",
    layout="wide"
)

create_database()

# ==========================================
# CACHE
# ==========================================

@st.cache_data(show_spinner=False)
def optimize_for_display(
    image,
    max_size=300
):
    img = image.copy()

    img.thumbnail(
        (max_size, max_size),
        Image.LANCZOS
    )

    return img


@st.cache_data(show_spinner=False)
def cached_bg_remove(file_bytes):

    return remove_background(
        io.BytesIO(file_bytes)
    )


# ==========================================
# FACE DETECTION
# ==========================================

@st.cache_resource
def load_face_detector():

    return cv2.CascadeClassifier(
        cv2.data.haarcascades +
        "haarcascade_frontalface_default.xml"
    )


def auto_face_crop(image):

    detector = load_face_detector()

    img_np = np.array(
        image.convert("RGB")
    )

    gray = cv2.cvtColor(
        img_np,
        cv2.COLOR_RGB2GRAY
    )

    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(100,100)
    )

    if len(faces) == 0:
        return image

    x,y,w,h = max(
        faces,
        key=lambda f:f[2]*f[3]
    )

    pad = int(h * 0.35)

    x1 = max(0,x-pad)
    y1 = max(0,y-pad)

    x2 = min(
        img_np.shape[1],
        x+w+pad
    )

    y2 = min(
        img_np.shape[0],
        y+h+pad
    )

    cropped = img_np[
        y1:y2,
        x1:x2
    ]

    return Image.fromarray(
        cropped
    )


# ==========================================
# IMAGE QUALITY
# ==========================================

def blur_score(image):

    gray = cv2.cvtColor(
        np.array(image),
        cv2.COLOR_RGB2GRAY
    )

    return cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()


# ==========================================
# BRIGHTNESS AUTO
# ==========================================

def auto_adjust_brightness(image):

    stat = ImageStat.Stat(image)

    mean = stat.mean[0]

    target = 130

    factor = (
        target / mean
        if mean > 0
        else 1
    )

    factor = max(
        0.7,
        min(
            factor,
            1.7
        )
    )

    return ImageEnhance.Brightness(
        image
    ).enhance(
        factor
    )

# ==========================================
# AUTO PASSPORT ENHANCE
# ==========================================

def auto_enhance(image):

    stat = ImageStat.Stat(
        image
    )

    mean = stat.mean[0]

    # Brightness correction

    if mean < 100:

        image = ImageEnhance.Brightness(
            image
        ).enhance(
            1.15
        )

    elif mean > 180:

        image = ImageEnhance.Brightness(
            image
        ).enhance(
            0.95
        )

    # Contrast enhancement

    image = ImageEnhance.Contrast(
        image
    ).enhance(
        1.12
    )

    # Sharpness enhancement

    image = ImageEnhance.Sharpness(
        image
    ).enhance(
        1.20
    )

    return image

    # ==========================================
# TABS
# ==========================================

tab1, tab2, tab3 = st.tabs(
    [
        "📸 Studio",
        "📋 Orders",
        "📊 Overview"
    ]
)

# ==========================================
# STUDIO TAB
# ==========================================

with tab1:

    st.title(
        "📸 Smart Passport Photo Studio"
    )

    st.caption(
        "Upload → Crop → Background → Edit → Print"
    )

    uploaded_files = st.file_uploader(
        "Upload Photos",
        type=["jpg","jpeg","png"],
        accept_multiple_files=True
    )

    if not uploaded_files:

        st.info(
            "Upload one or more photos to begin."
        )

        st.stop()

    st.divider()

    photo_data = []

    # ==========================================
    # PHOTO LOOP
    # ==========================================

    for idx, uploaded_file in enumerate(
        uploaded_files
    ):

        with st.expander(
            f"📷 Photo {idx+1} - {uploaded_file.name}",
            expanded=True
        ):

            file_bytes = uploaded_file.getvalue()

            original_image = Image.open(
                io.BytesIO(file_bytes)
            ).convert("RGB")

            st.subheader("⚙ Photo Settings")

            col1,col2=st.columns(2)

            with col1:

                size_name=st.selectbox(
                    "Photo Size",
                    [
                        "Passport",
                        "ID Card",
                        "1×1 inch",
                        "2×2 inch",
                        "Visa",
                        "Custom"
                    ],
                    key=f"size_{idx}"
                )

            with col2:

                copies=st.number_input(
                    "Copies",
                    1,
                    100,
                    8,
                    key=f"copies_{idx}"
                )

            if size_name=="Custom":

                width_mm=st.number_input(
                    "Width (mm)",
                    10,
                    100,
                    35,
                    key=f"width_{idx}"
                )

                height_mm=st.number_input(
                    "Height (mm)",
                    10,
                    100,
                    45,
                    key=f"height_{idx}"
                )

            else:

                size_map={
                    "Passport":(35,45),
                    "ID Card":(25,35),
                    "1×1 inch":(25,25),
                    "2×2 inch":(51,51),
                    "Visa":(35,45)
                }

                width_mm,height_mm=size_map[size_name]

            # ----------------------
            # ORIGINAL PREVIEW
            # ----------------------

            st.subheader(
                "1️⃣ Original Preview"
            )

            preview_img = optimize_for_display(
                original_image,
                max_size=350
            )

            st.image(
                preview_img
            )

            st.divider()

            # ----------------------
            # CROP SETTINGS
            # ----------------------

            st.subheader(
                "2️⃣ Crop & Rotate"
            )

            crop_mode = st.radio(
                "Crop Mode",
                [
                    "Auto Face Crop",
                    "Manual Crop",
                    "Original"
                ],
                horizontal=True,
                key=f"crop_{idx}"
            )

            working_image = original_image

            # AUTO FACE CROP

            if crop_mode == "Auto Face Crop":

                cropped = auto_face_crop(
                    original_image
                )

                st.image(
                    optimize_for_display(
                        cropped
                    ),
                    caption="Auto Crop Preview",
                    width=350
                )

                working_image = cropped

            # MANUAL CROP

            elif crop_mode == "Manual Crop":

                aspect_ratio = (
                    width_mm,
                    height_mm
                )

                cropped = st_cropper(
                    original_image,
                    realtime_update=True,
                    aspect_ratio=aspect_ratio,
                    box_color="#0000FF",
                    return_type="image",
                    key=f"cropper_{idx}"
                )

                working_image = cropped

                st.success(
                    "Manual crop selected."
                )

            else:

                    working_image = original_image

            # ----------------------
            # ROTATE
            # ----------------------

            st.subheader(
                "🔄 Rotate"
            )

            col_rot1, col_rot2 = st.columns([3,1])

            with col_rot1:

                slider_deg = st.slider(
                    "Rotation Slider",
                    min_value=-180,
                    max_value=180,
                    value=0,
                    key=f"slider_{idx}"
                )

            with col_rot2:

                manual_deg = st.number_input(
                    "Degree",
                    min_value=-180,
                    max_value=180,
                    value=slider_deg,
                    key=f"degree_{idx}"
                )

            rotation = manual_deg

            working_image = working_image.rotate(
                rotation,
                expand=True,
                fillcolor="white"
            )

            st.image(
                optimize_for_display(
                    working_image
                ),
                caption="Crop + Rotate Preview",
                width=300
            )
        # ----------------------
        # BACKGROUND REMOVAL
        # ----------------------

        st.subheader(
            "3️⃣ Background Removal"
            )

        final_image = working_image

        bg_color = "White"

        col_bg1, col_bg2 = st.columns(2)

        with col_bg1:

            bg_color = st.selectbox(
                    "Background Color",
                    [
                        "White",
                        "Blue",
                        "Red",
                        "Light Grey",
                        "Green"
                    ],
                    key=f"bg_color_{idx}"
                )

        with col_bg2:

            remove_now = st.checkbox(
                    "Apply Background Removal",
                    value=True,
                    key=f"remove_bg_{idx}"
                )

            if remove_now:

                with st.spinner(
                    "Removing Background..."
                ):

                    buffer = io.BytesIO()

                    working_image.save(
                        buffer,
                        format="PNG"
                    )
                    bg_removed = cached_bg_remove(
                        buffer.getvalue()
                    )
                    st.image(
                        bg_removed,
                        caption="Background Removed",
                        width=300
                    )

                if bg_removed.mode == "RGBA":

                    color_map = {
                        "White":"white",
                        "Blue":"#87CEEB",
                        "Red":"#FF4D4D",
                        "Light Grey":"#D3D3D3",
                        "Green":"#90EE90"
                    }

                    background = Image.new(
                        "RGB",
                        bg_removed.size,
                        color_map[bg_color]
                    )

                    background.paste(
                        bg_removed,
                        mask=bg_removed.split()[-1]
                    )

                    final_image = background

                else:

                    final_image = bg_removed.convert(
                        "RGB"
                    )

            st.divider()
            
            # ----------------------
            # PHOTO EDITING
            # ----------------------

            st.subheader(
            "4️⃣ Photo Editing"
            )

            edit_photo = st.radio(
                "Photo Editing Mode",
                [
                    "Keep Original",
                    "Auto Passport Enhance",
                    "Manual Editing"
                ],
                horizontal=True,
                key=f"edit_{idx}"
            )

            edited = final_image.copy()

            # ----------------------
            # AUTO ENHANCE
            # ----------------------

            if edit_photo == "Auto Passport Enhance":

                edited = auto_enhance(
                    edited
                )

            # ----------------------
            # MANUAL EDITING
            # ----------------------

            elif edit_photo == "Manual Editing":

                col1, col2 = st.columns(2)

                with col1:

                    brightness = st.slider(
                        "☀ Brightness",
                        50,
                        200,
                        100,
                        key=f"brightness_{idx}"
                    )

                    sharpness = st.slider(
                        "✨ Sharpness",
                        50,
                        300,
                        100,
                        key=f"sharpness_{idx}"
                    )

                with col2:

                    contrast = st.slider(
                        "🎚 Contrast",
                        50,
                        200,
                        100,
                        key=f"contrast_{idx}"
                    )

                edited = ImageEnhance.Brightness(
                    edited
                ).enhance(
                    brightness / 100
                )

                edited = ImageEnhance.Contrast(
                    edited
                ).enhance(
                    contrast / 100
                )

                edited = ImageEnhance.Sharpness(
                    edited
                ).enhance(
                    sharpness / 100
                )

            # ----------------------
            # FINAL PREVIEW
            # ----------------------

            st.divider()

            st.subheader(
                "5️⃣ Final Preview"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.image(
                    optimize_for_display(
                        working_image
                    ),
                    caption="Before",
                    width=300
                )

            with col2:

                st.image(
                    optimize_for_display(
                        edited
                    ),
                    caption="Final",
                    width=300
                )
                
                photo_data.append({
                    "image":edited.convert("RGB"),
                    "size_name":size_name,
                    "width_mm":width_mm,
                    "height_mm":height_mm,
                    "copies":copies
                })

# ==========================================
# BILLING SECTION
# ==========================================

st.divider()

st.header(
    "💰 Billing & Sheet Generation"
)

# Total photos from all uploaded images
total_photos = sum(
    item["copies"]
    for item in photo_data
)

# Maximum photos that fit on one sheet
max_capacity = get_max_capacity(
    photo_data
)

# Overflow check
if total_photos > max_capacity:

    st.error(
        f"Only {max_capacity} photos can fit on one A4 sheet."
    )

    st.stop()

# Calculate amount
total_amount = calculate_total(
    total_photos
)

# Metrics
col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Total Photos",
        total_photos
    )

with col2:

    st.metric(
        "Rate",
        "₹5 / Photo"
    )

with col3:

    st.metric(
        "Total Amount",
        f"₹{total_amount}"
    )

st.divider()

# ==========================================
# GENERATE BUTTON
# ==========================================

if st.button(
    "🚀 Generate Passport Sheet",
    width="stretch",
    type="primary"
):

    # No processed photos
    if len(photo_data) == 0:

        st.warning(
            "No photos available to generate."
        )

    else:

        with st.spinner(
            "Generating A4 Sheet..."
        ):

            sheet = generate_layout(
                photo_data
            )

            preview = create_preview(
                sheet
            )

        st.success(
            "✅ Passport Sheet Generated Successfully"
        )

        st.subheader(
            "📄 A4 Sheet Preview"
        )

        st.image(
            preview,
            width="stretch"
        )

        # ======================================
        # SAVE ORDER
        # ======================================

        save_order(
            "Mixed Layout",
            "-",
            total_photos,
            total_amount
        )

        # ======================================
        # JPG DOWNLOAD
        # ======================================

        jpg_buffer = io.BytesIO()

        sheet.save(
            jpg_buffer,
            format="JPEG",
            quality=95
        )

        jpg_buffer.seek(0)

        # ======================================
        # PDF DOWNLOAD
        # ======================================

        pdf_buffer = io.BytesIO()

        sheet.save(
            pdf_buffer,
            format="PDF",
            resolution=300
        )

        pdf_buffer.seek(0)

        col1,col2 = st.columns(2)

        with col1:

            st.download_button(
                "📥 Download JPG",
                jpg_buffer,
                file_name="passport_sheet.jpg",
                mime="image/jpeg",
                width="stretch"
            )

        with col2:

            st.download_button(
                "📥 Download PDF",
                pdf_buffer,
                file_name="passport_sheet.pdf",
                mime="application/pdf",
                width="stretch"
            )

        st.success(
            f"Order Saved Successfully | Amount ₹{total_amount}"
        )

        # ==========================================
# ORDERS TAB
# ==========================================

with tab2:

    st.title(
        "📋 Order History"
    )

    orders = get_orders()

    if not orders:

        st.info(
            "No orders found."
        )

    else:

        columns = [
            "ID",
            "Date & Time",
            "Photo Type",
            "Copies",
            "Total Photos",
            "Amount"
        ]

        df = pd.DataFrame(
            orders,
            columns=columns
        )

        st.dataframe(
            df,
            width="stretch",
            hide_index=True
        )

        st.divider()

        st.subheader(
            "🗑 Delete Order"
        )

        order_ids = df["ID"].tolist()

        selected_order = st.selectbox(
            "Select Order ID",
            order_ids
        )

        if st.button(
            "Delete Selected Order",
            type="secondary"
        ):

            success = delete_order(
                selected_order
            )

            if success:

                st.success(
                    f"Order #{selected_order} deleted."
                )

                st.rerun()

            else:

                st.error(
                    "Unable to delete order."
                )

        st.divider()

        st.subheader(
            "📊 Order Summary"
        )

        total_orders = len(df)

        total_photos = df[
            "Total Photos"
        ].sum()

        total_amount = df[
            "Amount"
        ].sum()

        col1,col2,col3 = st.columns(3)

        with col1:

            st.metric(
                "Orders",
                total_orders
            )

        with col2:

            st.metric(
                "Photos Printed",
                total_photos
            )

        with col3:

            st.metric(
                "Revenue",
                f"₹{total_amount:.0f}"
            )

            # ==========================================
# OVERVIEW TAB
# ==========================================

with tab3:

    st.title(
        "📊 Business Dashboard"
    )

    # ======================================
    # METRICS
    # ======================================

    total_orders = get_total_orders()

    total_revenue = get_total_revenue()

    today_orders = get_today_orders()

    today_revenue = get_today_revenue()

    col1,col2,col3,col4 = st.columns(4)

    with col1:

        st.metric(
            "📦 Total Orders",
            total_orders
        )

    with col2:

        st.metric(
            "💰 Total Revenue",
            f"₹{total_revenue:.0f}"
        )

    with col3:

        st.metric(
            "📅 Today's Orders",
            today_orders
        )

    with col4:

        st.metric(
            "🪙 Today's Revenue",
            f"₹{today_revenue:.0f}"
        )

    st.divider()

    # ======================================
    # LOAD DATA
    # ======================================

    orders = get_orders()

    if not orders:

        st.info(
            "No data available."
        )

    else:

        df = pd.DataFrame(
            orders,
            columns=[
                "ID",
                "Date",
                "Photo Type",
                "Layout",
                "Total Photos",
                "Amount"
            ]
        )

        # ==================================
        # REVENUE CHART
        # ==================================

        st.subheader(
            "💰 Revenue Per Order"
        )

        revenue_chart = df[
            ["ID","Amount"]
        ].set_index(
            "ID"
        )

        st.line_chart(
            revenue_chart
        )

        st.divider()

        # ==================================
        # PHOTO COUNT CHART
        # ==================================

        st.subheader(
            "📸 Photos Printed"
        )

        photo_chart = df[
            ["ID","Total Photos"]
        ].set_index(
            "ID"
        )

        st.bar_chart(
            photo_chart
        )

        st.divider()

        # ==================================
        # PHOTO TYPE ANALYSIS
        # ==================================

        st.subheader(
            "🪪 Photo Type Distribution"
        )

        type_counts = df[
            "Photo Type"
        ].value_counts()

        st.bar_chart(
            type_counts
        )

        st.divider()

        # ==================================
        # TOP PHOTO TYPE
        # ==================================

        top_type = type_counts.idxmax()

        st.success(
            f"🏆 Most Used Photo Type : {top_type}"
        )

        # ==================================
        # RECENT ORDERS
        # ==================================

        st.subheader(
            "🕒 Recent Orders"
        )

        st.dataframe(
            df.head(10),
            width="stretch",
            hide_index=True
        )
