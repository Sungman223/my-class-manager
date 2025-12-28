import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
import google.generativeai as genai 
import streamlit as st
import google.generativeai as genai
# -----------------------------------------------------------
# 1. 설정 및 Gemini 연결
# -----------------------------------------------------------
st.set_page_config(page_title="학습매니저", layout="centered")

# Gemini API 설정
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def refine_text_with_ai(text):
    """Gemini를 이용해 문장을 다듬는 함수"""
    if not text:
        return ""
    try:
        # 모델 이름 확인 후 필요하면 수정하세요 (예: 'gemini-pro')
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        너는 학원 선생님의 비서야. 선생님이 급하게 적은 아래 '상담 메모'를 읽고,
        학부모님께 보낼 수 있는 '정중하고 전문적인 문체'로 다듬어줘.
        내용을 왜곡하지 말고 문장만 부드럽게 고쳐줘.
        
        [상담 메모]: {text}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 연결 오류: {e}"

def generate_weeks():
    weeks = {}
    curr_date = datetime(2026, 1, 4)
    for i in range(1, 54):
        if curr_date.year > 2026: break
        end_date = curr_date + timedelta(days=6)
        period = f"{curr_date.month}/{curr_date.day}(일) ~ {end_date.month}/{end_date.day}(토)"
        weeks[f"{i}주차"] = period
        curr_date += timedelta(days=7)
    return weeks

WEEKS = generate_weeks()

COLUMNS = [
    "이름", "반", "출신중", "배정고", "상담특이사항",
    "수강과목", "학습교재", 
    "주차", "기간", "작성일",
    "과제수행_개인", "과제수행_반평균", 
    "오답수_개인", "오답수_반평균", 
    "질문문항", "난이도", "총평"
]

# -----------------------------------------------------------
# 2. 데이터 저장/불러오기
# -----------------------------------------------------------
def load_data():
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        try:
            from streamlit_gsheets import GSheetsConnection
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(worksheet="Sheet1")
            if df.empty or len(df.columns) < len(COLUMNS):
                return pd.DataFrame(columns=COLUMNS)
            return df
        except Exception:
            pass 
    try:
        return pd.read_csv("student_records.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        try:
            from streamlit_gsheets import GSheetsConnection
            conn = st.connection("gsheets", type=GSheetsConnection)
            conn.update(worksheet="Sheet1", data=df)
            return "구글 시트에 저장되었습니다!"
        except Exception as e:
            return f"구글 시트 저장 실패 (CSV로 저장함): {e}"
    df.to_csv("student_records.csv", index=False)
    return "CSV 파일로 저장되었습니다."

# -----------------------------------------------------------
# 3. 메인 화면 로직 (진단 도구 포함)
# -----------------------------------------------------------
def main():
    st.title("👨‍🏫 학습매니저 (AI 탑재)")
    
    # --- 🛠️ 여기에 진단 도구를 합쳤습니다! ---
    with st.expander("🛠️ AI 모델 진단 (문제 해결용)"):
        st.info("AI가 작동하지 않을 때만 눌러보세요.")
        if st.button("사용 가능한 모델 리스트 확인"):
            try:
                models = [m.name for m in genai.list_models()]
                st.success("내 API 키로 쓸 수 있는 모델 목록:")
                st.write(models)
            except Exception as e:
                st.error(f"목록 불러오기 실패: {e}")
    # ---------------------------------------

    if "connections" not in st.secrets:
        st.warning("⚠️ 구글 시트 미연동 (CSV 모드)")
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Gemini API 키가 없습니다. Secrets에 추가해주세요.")

    tab1, tab2 = st.tabs(["📝 데이터 입력", "📊 리포트 생성"])
    df = load_data()

    # --- [탭 1] 데이터 입력 ---
    with tab1:
        st.header

