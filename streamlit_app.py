import streamlit as st
import requests
from PIL import Image
import io

# Cấu hình giao diện
st.set_page_config(page_title="Fish Freshness AI", layout="centered")
st.title("🐟 Phân loại độ tươi của cá (Swin Transformer)")

# URL API của bạn (Đã thêm /predict)
API_URL = "https://lucasclarke-fish-freshness-classification.hf.space/predict"

uploaded_file = st.file_uploader("Tải ảnh con cá lên...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Hiển thị ảnh đã chọn
    image = Image.open(uploaded_file)
    st.image(image, caption='Ảnh đầu vào', use_column_width=True)
    
    if st.button("Dự đoán ngay"):
        with st.spinner('Đang gửi dữ liệu đến AI model...'):
            try:
                # Chuyển file sang bytes để gửi qua API
                img_bytes = uploaded_file.getvalue()
                files = {"file": ("image.jpg", img_bytes, "image/jpeg")}
                
                # Gọi API
                response = requests.post(API_URL, files=files)
                
                if response.status_code == 200:
                    res = response.json()
                    label = res['label']
                    conf = res['confidence']
                    
                    # Hiển thị kết quả đẹp mắt
                    st.success(f"### Kết quả: {label}")
                    st.info(f"Độ tin cậy: {conf:.2%}")
                    
                    # Hiển thị biểu đồ xác suất (nếu có)
                    if 'all_probs' in res:
                        st.bar_chart(res['all_probs'])
                else:
                    st.error(f"Lỗi API (Mã lỗi: {response.status_code})")
                    
            except Exception as e:
                st.error(f"Không thể kết nối đến API: {e}")

st.divider()
