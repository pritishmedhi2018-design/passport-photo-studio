import streamlit as st
from streamlit_cropper import st_cropper
from PIL import Image, ImageOps, ImageEnhance
import io
import pandas as pd

from modules.bg_removal import remove_background
from modules.layout_generator import generate_layout, create_preview
from modules.pricing import calculate_total
from modules.database import (
    create_database, save_order, get_total_orders,
    get_total_revenue, get_today_orders, get_today_revenue, get_orders
)

# ====================== INITIALIZATION ======================
create_database()

st.set_page_config(
    page_title="Passport Photo Studio",
    page_icon="📸",
    layout="wide"
)

# ====================== CACHING ======================
@st.cache_data(show_spinner=False)
def cached_bg_remove(file_bytes):
    file_obj = io.BytesIO(file_bytes)
    return remove_background(file_obj)

# ====================== HEADER ======================
st.title("📸 Smart Passport Photo Studio")
st.caption("AI Background Removal • Smart Cropping • A4 Sheet Generator")

# ====================== TABS ======================
tab1, tab2, tab3 = st.tabs(["🖼️ Studio", "📊 Sales History", "📈 Overview"])

# ====================== STUDIO TAB ======================
with tab1:
    st.header("⚙️ Settings")

    col1, col2, col3 = st.columns(3)

    with col1:
        photo_type = st.selectbox("Photo Type", ["Passport", "ID Card"], key="photo_type")
        remove_bg = st.radio("Remove Background", ["Yes", "No"], key="remove_bg")

    with col2:
        crop_option = st.radio(
            "Crop Option",
            ["No Crop", "Free Crop", "Passport Crop"],
            key="crop_option"
        )
        bg_option = st.selectbox(
            "Background Color",
            ["Original", "White", "Blue", "Red", "Light Grey", "Green"],
            key="bg_option"
        )

    with col3:
        photos_per_row = st.selectbox("Photos Per Row", [6, 7], key="photos_per_row")

    st.divider()

    # ====================== SIDEBAR ======================
    with st.sidebar:
        st.header("📊 Quick Stats")
        st.metric("Total Orders", get_total_orders())
        st.metric("Today's Orders", get_today_orders())
        st.metric("Total Revenue", f"₹{get_total_revenue()}")
        st.metric("Today's Revenue", f"₹{get_today_revenue()}")

    # ====================== FILE UPLOAD ======================
    uploaded_files = st.file_uploader(
        "Upload Photo(s)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    if not uploaded_files:
        st.info("Upload one or more photos to begin.")
        st.stop()

    # ====================== PHOTO PROCESSING ======================
    processed_photos = []
    copies_list = []

    st.header("🖼️ Photo Processing")

    for idx, uploaded_file in enumerate(uploaded_files):
        st.divider()
        st.subheader(f"Photo {idx + 1}: {uploaded_file.name}")

        file_bytes = uploaded_file.getvalue()

        # Background Removal
        try:
            if remove_bg == "Yes":
                with st.spinner("Removing background..."):
                    image = cached_bg_remove(file_bytes)
            else:
                image = Image.open(io.BytesIO(file_bytes)).convert("RGBA")
        except Exception:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGBA")

        # Background Color
        if bg_option != "Original":
            colors = {
                "White": (255, 255, 255),
                "Blue": (135, 206, 235),
                "Red": (255, 0, 0),
                "Light Grey": (220, 220, 220),
                "Green": (0, 150, 0)
            }
            bg = Image.new("RGBA", image.size, colors[bg_option])
            bg.paste(image, (0, 0), image)
            image = bg

        if image.mode == "RGBA":
            image = image.convert("RGB")

        # ====================== CROPPING ======================
        if crop_option == "No Crop":
            cropped_img = image
        else:
            aspect_ratio = None
            if crop_option == "Passport Crop":
                aspect_ratio = (35, 45) if photo_type == "Passport" else (25, 35)

            cropped_img = st_cropper(
                image,
                realtime_update=True,
                box_color="#0000FF",
                aspect_ratio=aspect_ratio,
                return_type="image"
            )

        # Editing Controls
        col_a, col_b = st.columns(2)
        with col_a:
            zoom = st.slider("Zoom (%)", 50, 200, 100, key=f"zoom_{idx}")
            rotation = st.slider("Rotate (°)", -180, 180, 0, key=f"rot_{idx}")
        with col_b:
            brightness = st.slider("Brightness", 50, 200, 100, key=f"bright_{idx}")

        # Apply Transformations
        scale = zoom / 100.0
        w, h = cropped_img.size
        cropped_img = cropped_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        cropped_img = ImageOps.fit(cropped_img, (w, h), Image.LANCZOS)

        cropped_img = cropped_img.rotate(rotation, expand=True, fillcolor="white")

        enhancer = ImageEnhance.Brightness(cropped_img)
        cropped_img = enhancer.enhance(brightness / 100)

        st.image(cropped_img, caption=f"Final Preview {idx+1}", use_container_width=True)

        qty = st.number_input(
            f"Copies for Photo {idx+1}",
            min_value=1, value=4, step=1,
            key=f"copies_{idx}"
        )

        processed_photos.append(cropped_img.convert("RGB"))
        copies_list.append(qty)

    # ====================== BILLING & GENERATION ======================
    st.divider()
    st.header("💰 Billing & Print Generation")

    total_photos = sum(copies_list)
    total_amount = calculate_total(total_photos)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Photos", total_photos)
    c2.metric("Rate per Photo", "₹5")
    c3.metric("Total Amount", f"₹{total_amount}")

    generate_btn = st.button("Generate A4 Print Sheet", type="primary", use_container_width=True)

    if generate_btn and processed_photos:
        with st.spinner("Generating print sheet..."):
            sheet = generate_layout(
                photos=processed_photos,
                copies=copies_list,
                photos_per_row=photos_per_row,
                photo_type=photo_type
            )
            
            # Create preview (high-res)
            preview = create_preview(sheet)
            
            # Create smaller version for display to improve speed & fit
            preview_display = preview.copy()
            preview_display.thumbnail((1200, 1200), Image.LANCZOS)

        st.header("📄 A4 Print Preview")
        st.image(
            preview_display, 
            caption="A4 Sheet Preview (Resized for display)",
            use_container_width=True
        )

        # Order Summary
        summary_df = pd.DataFrame({
            "Item": ["Photo Type", "Layout", "Total Photos", "Rate", "Amount"],
            "Value": [photo_type, f"{photos_per_row} per row", total_photos, "₹5", f"₹{total_amount}"]
        })
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        # Save Order
        try:
            save_order(photo_type, photos_per_row, total_photos, total_amount)
            st.success("✅ Order saved successfully!")
        except Exception as e:
            st.error(f"Database Error: {e}")

        # Downloads (Full Resolution)
        png_buffer = io.BytesIO()
        sheet.save(png_buffer, format="PNG", dpi=(300, 300))
        png_buffer.seek(0)

        pdf_buffer = io.BytesIO()
        sheet.convert("RGB").save(pdf_buffer, format="PDF", resolution=300)
        pdf_buffer.seek(0)

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button("⬇ Download PNG (300 DPI)", 
                             png_buffer.getvalue(),
                             "passport_sheet.png", 
                             "image/png", 
                             use_container_width=True)
        with col_dl2:
            st.download_button("⬇ Download PDF", 
                             pdf_buffer.getvalue(),
                             "passport_sheet.pdf", 
                             "application/pdf", 
                             use_container_width=True)

# ====================== SALES HISTORY TAB ======================
with tab2:
    st.header("📊 Sales History")
    orders = get_orders()

    if orders:
        df = pd.DataFrame(orders, columns=[
            "ID", "Date & Time", "Photo Type", "Layout", "Total Photos", "Amount"
        ])
        
        st.dataframe(df, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        col1.metric("Total Orders", len(df))
        col2.metric("Total Revenue", f"₹{df['Amount'].sum():.2f}")

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Full Sales Report", 
                          csv, "sales_history.csv", "text/csv", use_container_width=True)
    else:
        st.info("No orders yet.")

# ====================== OVERVIEW TAB ======================
with tab3:
    st.header("📈 Business Overview")
    st.info("More detailed analytics can be added here later.")

# ====================== FOOTER ======================
st.divider()
st.caption("Smart Passport Photo Studio • AI Powered")
