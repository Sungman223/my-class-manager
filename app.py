import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import google.generativeai as genai

# -----------------------------------------------------------
# 1. 설정 및 Gemini 연결
# -----------------------------------------------------------
st.set_page_config(page_title="학습매니저", layout="centered")

# Gemini API 설정 (Secrets에 키가 있을 때만 연결)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def refine_text_with_ai(text):
    """Gemini를 이용해 문장을 다듬는 함수"""
    if not text:
        return ""
    try:
        # 모델 설정 (flash 모델 사용)
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
    """2026년 주차 정보 생성"""
    weeks = {}
    curr_date = datetime(2026, 1, 4) # 시작일 설정
    for i in range(1, 54):
        if curr_date.year > 2026: break
        end_date = curr_date + timedelta(days=6)
        period = f"{curr_date.month}/{curr_date.day}(일) ~ {end_date.month}/{end_date.day}(토)"
        weeks[f"{i}주차"] = period
        curr_date += timedelta(days=7)
    return weeks

WEEKS = generate_weeks()

# 데이터 컬럼 정의
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
    """구글 시트 또는 로컬 CSV에서 데이터를 불러옵니다."""
    # 1. 구글 시트 연결 시도
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        try:
            from streamlit_gsheets import GSheetsConnection
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(worksheet="Sheet1")
            # 컬럼이 부족하면 채워줌
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            pass 
    
    # 2. 구글 시트 없으면 CSV 사용
    try:
        return pd.read_csv("student_records.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    """데이터를 저장합니다."""
    # 1. 구글 시트에 저장 시도
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        try:
            from streamlit_gsheets import GSheetsConnection
            conn = st.connection("gsheets", type=GSheetsConnection)
            conn.update(worksheet="Sheet1", data=df)
            return "구글 시트에 저장되었습니다!"
        except Exception as e:
            st.warning(f"구글 시트 저장 실패 (CSV로 저장 시도): {e}")
    
    # 2. 실패 시 로컬 CSV 저장
    df.to_csv("student_records.csv", index=False)
    return "CSV 파일로 저장되었습니다."

# -----------------------------------------------------------
# 3. 메인 화면 로직
# -----------------------------------------------------------
def main():
    st.title("👨‍🏫 학습매니저 (AI 탑재)")
    
    # [진단 도구]
    with st.expander("🛠️ 시스템 상태 확인"):
        st.write(f"Python 버전: {st.secrets.get('python_version', '알 수 없음')}")
