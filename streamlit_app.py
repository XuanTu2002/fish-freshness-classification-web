import streamlit as st
import requests
from PIL import Image
import io
import json
from datetime import datetime
import time

# ========== CẤU HÌNH ==========
st.set_page_config(
    page_title="Fish Freshness AI",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# CSS cho màu sắc xanh đại dương + responsive
st.markdown("""
<style>
    :root {
        --ocean-blue: #0066cc;
        --ocean-dark: #004d99;
        --white: #ffffff;
        --light-gray: #f0f4f8;
    }
    
    * {
        margin: 0;
        padding: 0;
    }
    
    .main {
        background: linear-gradient(135deg, #e8f1f9 0%, #f5f8fc 100%);
        padding: 0;
    }
    
    .stButton>button {
        background-color: var(--ocean-blue);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton>button:hover {
        background-color: var(--ocean-dark);
        box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3);
    }
    
    .big-button {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .freshness-box {
        border-radius: 1.5rem;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        color: white;
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    .freshness-high {
        background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
    }
    
    .freshness-medium {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
    }
    
    .freshness-low {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
    }
    
    .confidence-bar {
        background: #ecf0f1;
        border-radius: 1rem;
        height: 2rem;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--ocean-blue), #0099ff);
        border-radius: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        transition: width 0.5s ease;
    }
    
    .history-item {
        background: white;
        border-left: 4px solid var(--ocean-blue);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .scanning-frame {
        border: 3px solid var(--ocean-blue);
        border-radius: 1rem;
        box-shadow: 0 0 20px rgba(0, 102, 204, 0.4);
        padding: 1rem;
        position: relative;
        background: #f5f8fc;
    }
    
    @media (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }
        .freshness-box {
            padding: 1.5rem;
            font-size: 1.2rem;
        }
        .stButton>button {
            padding: 0.6rem 1rem;
            font-size: 0.9rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ========== KHỞI TẠO SESSION STATE ==========
if 'page' not in st.session_state:
    st.session_state.page = "home"

if 'history' not in st.session_state:
    st.session_state.history = []

if 'current_result' not in st.session_state:
    st.session_state.current_result = None

if 'uploaded_image' not in st.session_state:
    st.session_state.uploaded_image = None

# ========== URL API ==========
API_URL = "https://lucasclarke-fish-freshness-classification.hf.space/predict"

# ========== DỮ LIỆU GỢI Ý ==========
COOKING_SUGGESTIONS = {
    "Highly Fresh": [
        "🍡 Hấp nhẹ với nước dùng gà",
        "🔥 Nướng mù tạt",
        "🍲 Nấu cá kho tộ (1-2 ngày)",
        "🥄 Ăn sống (sashimi) - an toàn nhất"
    ],
    "Fresh": [
        "🍲 Kho cá với gừng",
        "🔥 Chiên xù cả con",
        "🥘 Kho với dứa hoặc mơ",
        "🍜 Nấu canh chua"
    ],
    "Not Fresh": [
        "🍲 Kho cá 3-4 ngày",
        "🔥 Chiên xù (tiêu diệt vi khuẩn)",
        "🧂 Cơm cá muối",
        "⚠️ Kiểm tra kỹ trước khi nấu"
    ]
}

SHOP_LOCATION = "Chợ Hàng Dương, Hà Nội"  # Hardcoded vị trí

# ========== HÀM HELPER ==========
def add_to_history(label, confidence, location):
    """Thêm vào lịch sử quét"""
    history_item = {
        "timestamp": datetime.now().isoformat(),
        "label": label,
        "confidence": confidence,
        "location": location
    }
    st.session_state.history.insert(0, history_item)
    if len(st.session_state.history) > 50:  # Giới hạn 50 items
        st.session_state.history = st.session_state.history[:50]

def render_scanning_animation():
    """Hiệu ứng radar quét"""
    placeholder = st.empty()
    for i in range(3):
        with placeholder.container():
            st.markdown(f"""
            <div style="text-align: center; font-size: 2rem;">
                🔍 {'.' * (i + 1)} Quét AI...
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.3)
    placeholder.empty()

def render_freshness_box(label, confidence):
    """Hiển thị hộp chỉ số độ tươi"""
    if label == "Highly Fresh":
        class_name = "freshness-high"
        emoji = "✨"
        vi_label = "RẤT TƯƠI"
    elif label == "Fresh":
        class_name = "freshness-medium"
        emoji = "👍"
        vi_label = "TƯƠI"
    else:
        class_name = "freshness-low"
        emoji = "⚠️"
        vi_label = "KHÔNG TƯƠI"
    
    st.markdown(f"""
    <div class="freshness-box {class_name}">
        {emoji} {vi_label} {emoji}
    </div>
    """, unsafe_allow_html=True)
    
    # Thanh tin cậy
    st.markdown(f"""
    <div class="confidence-bar">
        <div class="confidence-fill" style="width: {confidence*100}%">
            {confidence:.1%}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    return f"{vi_label} - Độ tin cậy: {confidence:.1%}"

# ========== TRANG HOME ==========
def page_home():
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem;">
        <h1 style="color: #0066cc; font-size: 2.5rem; margin-bottom: 1rem;">🐟 Fish Freshness AI</h1>
        <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem;">
            Kiểm tra độ tươi của cá chỉ trong 3 giây
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Nút lớn Quét cá ngay
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📷 QUÉT CÁ NGAY", use_container_width=True, key="scan_btn"):
            st.session_state.page = "analysis"
            st.rerun()
    
    st.divider()
    
    # Lịch sử quét
    st.subheader("📜 Lịch sử quét gần nhất")
    
    if st.session_state.history:
        for idx, item in enumerate(st.session_state.history[:10]):
            dt = datetime.fromisoformat(item['timestamp'])
            time_str = dt.strftime("%H:%M %d/%m")
            
            freshness_color = {
                "Highly Fresh": "🟢",
                "Fresh": "🟡",
                "Not Fresh": "🔴"
            }.get(item['label'], "⚪")
            
            st.markdown(f"""
            <div class="history-item">
                <strong>{freshness_color} {item['label']}</strong> - 
                Độ tin cậy: {item['confidence']:.1%} | 
                {time_str} | 
                📍 {item['location']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Chưa có lịch sử quét. Hãy quét cá đầu tiên!")

# ========== TRANG ANALYSIS ==========
def page_analysis():
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h2 style="color: #0066cc;">📸 Tải ảnh con cá</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        uploaded_file = st.file_uploader(
            "Chọn file ảnh",
            type=["jpg", "jpeg", "png"],
            key="file_uploader"
        )
    
    if uploaded_file is not None:
        st.session_state.uploaded_image = uploaded_file
        
        image = Image.open(uploaded_file)
        # Resize để fit 224x224 (chuẩn input model)
        image_resized = image.resize((224, 224), Image.Resampling.LANCZOS)
        
        # Hiển thị ảnh đã resize
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(image_resized, use_column_width=True, caption='Ảnh sẽ được phân tích (224×224px)')
        
        st.divider()
        
        # Nút dự đoán
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 DỰ ĐOÁN NGAY", use_container_width=True):
                with st.spinner(''):
                    render_scanning_animation()
                    
                    try:
                        img_bytes = uploaded_file.getvalue()
                        files = {"file": ("image.jpg", img_bytes, "image/jpeg")}
                        response = requests.post(API_URL, files=files, timeout=30)
                        
                        if response.status_code == 200:
                            res = response.json()
                            st.session_state.current_result = res
                            st.session_state.page = "result"
                            st.rerun()
                        else:
                            st.error(f"❌ Lỗi API (Mã {response.status_code})")
                    except Exception as e:
                        st.error(f"❌ Lỗi kết nối: {str(e)}")
        
        # Nút quay lại
        st.divider()
        if st.button("⬅️ Quay lại", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

# ========== TRANG RESULT ==========
def page_result():
    if not st.session_state.current_result:
        st.session_state.page = "home"
        st.rerun()
        return
    
    result = st.session_state.current_result
    label = result['label']
    confidence = result['confidence']
    
    # Thêm vào lịch sử
    add_to_history(label, confidence, SHOP_LOCATION)
    
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h2 style="color: #0066cc;">📊 Kết quả phân tích</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Hiển thị ảnh đã quét
    if st.session_state.uploaded_image:
        image = Image.open(st.session_state.uploaded_image)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(image, use_column_width=True, caption="Ảnh được phân tích")
    
    st.divider()
    
    # Chỉ số độ tươi
    st.markdown("### 🎯 Chỉ số độ tươi")
    result_text = render_freshness_box(label, confidence)
    
    st.divider()
    
    # Gợi ý chế biến
    st.markdown("### 🍳 Gợi ý chế biến")
    suggestions = COOKING_SUGGESTIONS.get(label, [])
    for suggestion in suggestions:
        st.markdown(f"- {suggestion}")
    
    st.divider()
    
    # Thông tin quét
    st.markdown(f"""
    <div style="background: #f5f8fc; padding: 1rem; border-radius: 0.5rem; font-size: 0.9rem; color: #666;">
        📍 <strong>Vị trí:</strong> {SHOP_LOCATION} | 
        🕐 <strong>Thời gian:</strong> {datetime.now().strftime("%H:%M %d/%m/%Y")}
    </div>
    """, unsafe_allow_html=True)
    
    # Nút tái quét
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Quét lại", use_container_width=True):
            st.session_state.page = "analysis"
            st.session_state.uploaded_image = None
            st.session_state.current_result = None
            st.rerun()
    
    with col2:
        if st.button("🏠 Về trang chủ", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
    
    with col3:
        if st.button("📤 Chia sẻ kết quả", use_container_width=True):
            st.info(f"📱 {label} - Độ tin cậy {confidence:.1%}\n📍 {SHOP_LOCATION}")

# ========== ĐIỀU HƯỚNG ==========
if st.session_state.page == "home":
    page_home()
elif st.session_state.page == "analysis":
    page_analysis()
elif st.session_state.page == "result":
    page_result()
