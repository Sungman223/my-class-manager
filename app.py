import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import google.generativeai as genai

# -----------------------------------------------------------
# 1. 설정 및 기본 데이터
# -----------------------------------------------------------
st.set_page_config(page_title="학습매니저 Pro", layout="wide")

# 주차 정보 생성 함수
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

# 데이터 컬럼 정의 (신규생/재원생 구분 포함)
COLUMNS = [
    "구분", "이름", "반", "출신중", "배정고", "상담특이사항",
    "수강과목", "학습교재", 
    "주차", "기간", "작성일",
    "과제수행_개인", "과제수행_반평균", 
    "오답수_개인", "오답수_반평균", 
    "AI_다듬은_멘트"
]

# -----------------------------------------------------------
# 2. 기능 로직 (AI 및 데이터)
# -----------------------------------------------------------
def init_gemini():
    """Gemini API 연결 확인"""
    if "GEMINI_API_KEY" in st.secrets:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            return True
        except:
            return False
    return False

def refine_text_with_ai(text, student_name, status):
    """
    AI 상담 문구 다듬기 (오류 수정됨)
    gemini-1.5-flash -> gemini-pro 로 변경하여 404 에러 방지
    """
    if not text: return ""
    try:
        # [수정] 가장 안정적인 모델인 gemini-pro 사용
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        너는 입시 학원의 베테랑 상담 실장이야.
        아래 '상담 메모'는 선생님이 급하게 작성한 내용이야.
        이 내용을 학부모님께 카톡이나 문자로 보낼 수 있도록,
        매우 정중하고 전문적이며, 신뢰감을 주는 '완성된 문장'으로 다듬어줘.
        
        - 학생 이름: {student_name}
        - 학생 상태: {status} (신규생이면 더 환영하는 느낌, 재원생이면 꼼꼼한 관리 느낌)
        - 상담 메모: {text}
        
        문장은 바로 복사해서 보낼 수 있게 '안녕하세요, OO 학부모님...'으로 시작해줘.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 호출 오류: {e}"

def load_data():
    """데이터 불러오기"""
    # 1. 구글 시트
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        try:
            from streamlit_gsheets import GSheetsConnection
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(worksheet="Sheet1")
            for col in COLUMNS:
                if col not in df.columns: df[col] = ""
            return df
        except:
            pass
    # 2. 로컬 CSV
    try:
        return pd.read_csv("student_records.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=COLUMNS)

def save_data_action(df):
    """데이터 저장하기"""
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        try:
            from streamlit_gsheets import GSheetsConnection
            conn = st.connection("gsheets", type=GSheetsConnection)
            conn.update(worksheet="Sheet1", data=df)
            return "구글 시트 저장 완료"
        except:
            pass
    df.to_csv("student_records.csv", index=False)
    return "CSV 저장 완료"

# -----------------------------------------------------------
#
