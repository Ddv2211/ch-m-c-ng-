import streamlit as st
import json
import re
import pandas as pd
import io
from PIL import Image
from google import genai

# --- Cấu hình Web ---
st.set_page_config(page_title="Sổ Chấm Công AI", layout="wide")
GEMINI_MODEL = "gemini-3.6-flash"

st.title("Sổ Chấm Công - Đọc Ảnh AI Tự Động")

# 1. Nhập API Key
api_key = st.text_input("Nhập Gemini API Key:", type="password", help="Lấy tại Google AI Studio")

# 2. Tải ảnh lên
uploaded_file = st.file_uploader("Chọn ảnh chấm công", type=["jpg", "png", "jpeg", "webp"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Ảnh đã tải lên", width=500)

    # 3. Nút xử lý AI
    if st.button("Đọc ảnh bằng Gemini", type="primary"):
        if not api_key:
            st.warning("Vui lòng nhập API Key!")
        else:
            with st.spinner("Đang đọc ảnh bằng Gemini..."):
                try:
                    client = genai.Client(api_key=api_key)
                    PROMPT = """Đây là ảnh chụp một bảng chấm công viết tay tiếng Việt. Các cột thường là: STT, Họ và tên, Sáng (Vào/Ra), Chiều (Vào/Ra), Tăng ca, Tổng thời gian, Ghi chú.
                    Hãy đọc kỹ toàn bộ các dòng có tên người (bỏ qua dòng trống) và trả về DUY NHẤT một mảng JSON, dùng cấu trúc sau:
                    [
                      {
                        "STT": 1,
                        "Họ Tên": "họ tên",
                        "Sáng Ra": "giờ ra sáng dạng HH:MM, rỗng nếu không có",
                        "Chiều Ra": "giờ ra chiều dạng HH:MM, rỗng nếu không có",
                        "Tăng Ca": "số giờ tăng ca viết trên bảng, rỗng nếu không có",
                        "Tổng TG": "tổng thời gian làm việc viết trên bảng, rỗng nếu không có",
                        "Ghi Chú": "nội dung ghi chú, rỗng nếu không có"
                      }
                    ]
                    Chỉ trả về mảng JSON, không dùng markdown code fence, không giải thích gì thêm."""

                    resp = client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=[image, PROMPT]
                    )
                    
                    # Làm sạch và Parse JSON
                    clean_text = re.sub(r"```json|```", "", resp.text).strip()
                    parsed_json = json.loads(clean_text)
                    
                    # Lưu dữ liệu vào session_state để tái sử dụng
                    st.session_state['df'] = pd.DataFrame(parsed_json)
                    st.success("✅ Đọc ảnh thành công!")

                except Exception as e:
                    st.error(f"Đã xảy ra lỗi: {e}")

# 4. Hiển thị bảng dữ liệu (Có thể sửa trực tiếp) và Nút xuất Excel
if 'df' in st.session_state:
    st.subheader("Dữ liệu chấm công (Nhấp đúp chuột vào ô bất kỳ để sửa)")
    
    # Bảng cho phép chỉnh sửa, thêm, xóa dòng trực tiếp
    edited_df = st.data_editor(st.session_state['df'], num_rows="dynamic", use_container_width=True)
    
    # 5. Xử lý xuất Excel trực tiếp trên Web
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        edited_df.to_excel(writer, index=False, sheet_name="Bảng Chấm Công")
    
    st.download_button(
        label="📥 Tải xuống Excel",
        data=buffer.getvalue(),
        file_name="Bang_Cham_Cong.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )