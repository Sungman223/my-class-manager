import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import json

# ---------------------------------------------------------
# 1. 기본 설정 및 비밀키(Secrets) 로드
# ---------------------------------------------------------
st.set_page_config(page_title="학습매니저", page_icon="🧑‍🏫")

# 비밀키 확인 (Secrets에 값이 없으면 에러 방지)
if "GOOGLE_API_KEY" not in st.secrets or "gcp_service_account" not in st.secrets:
    st.error("🚨 설정 오류: Streamlit Secrets에 API 키와 서비스 계정 정보가 없습니다.")
    st.stop()

# ---------------------------------------------------------
# 2. 제미나이(AI) 연결 설정 (핵심 수정 부분)
# ---------------------------------------------------------
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # 🌟 중요: 404 오류 해결을 위해 모델명을 'gemini-1.5-flash'로 변경했습니다.
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"AI 연결 중 오류 발생: {e}")

# ---------------------------------------------------------
# 3. 구글 시트 연결 함수
# ---------------------------------------------------------
def get_google_sheet():
    try:
        # Secrets에서 구글 인증 정보 가져오기
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
        ]
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes,
        )
        gc = gspread.authorize(credentials)
        
        # 시트 열기 (URL 방식이 가장 확실합니다)
        # secrets에 'sheet_url'을 저장해두셨다면 그것을 쓰고, 
        # 아니라면 아래 주석을 풀고 시트 URL을 직접 넣으셔도 됩니다.
        sheet_url = st.secrets.get("sheet_url") 
        if not sheet_url:
            st.error("Secrets에 'sheet_url'이 없습니다.")
            return None
            
        sh = gc.open_by_url(sheet_url)
        return sh.sheet1  # 첫 번째 시트 사용
    except Exception as e:
        st.error(f"구글 시트 연결 실패: {e}")
        return None

# ---------------------------------------------------------
# 4. AI 상담 문구 생성 함수
# ---------------------------------------------------------
def generate_ai_message(student_name, memo):
    prompt = f"""
    당신은 꼼꼼하고 다정한 학원 수학 선생님입니다.
    아래 '상담 메모'를 바탕으로 학부모님께 보낼 정중하고 신뢰감 있는 상담 문자를 작성해주세요.
    
    학생 이름: {student_name}
    상담 메모: {memo}
    
    조건:
    1. 문장은 자연스럽고 예의 바르게.
    2. 3~4문장 정도로 요약.
    3. 앞뒤 인사말 포함.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 변환 중 오류가 발생했습니다: {e}"

# ---------------------------------------------------------
# 5. 메인 화면 (UI)
# ---------------------------------------------------------
st.title("🧑‍🏫 학습매니저 (정상 작동)")
st.info("제미나이 1.5 Flash 모델과 구글 시트가 연결되어 있습니다.")

with st.form("consult_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("학생 이름", placeholder="예: 김철수")
    with col2:
        student_type = st.radio("구분", ["재원생", "신규생"], horizontal=True)
    
    week_select = st.selectbox("주차", [f"{i}주차" for i in range(1, 13)])
    teacher_memo = st.text_area("상담 메모 (선생님 작성)", height=150, placeholder="학생의 학습 태도, 진도 상황 등을 자유롭게 적어주세요.")
    
    submit_button = st.form_submit_button("저장 및 AI 변환 ✨")

# ---------------------------------------------------------
# 6. 버튼 클릭 시 실행 로직
# ---------------------------------------------------------
if submit_button:
    if not student_name or not teacher_memo:
        st.warning("학생 이름과 상담 메모를 모두 입력해주세요.")
    else:
        with st.spinner("AI가 문구를 다듬고 구글 시트에 저장 중입니다..."):
            # 1) 현재 시간
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 2) AI 문구 생성
            ai_result = generate_ai_message(student_name, teacher_memo)
            
            # 3) 구글 시트에 저장
            worksheet = get_google_sheet()
            if worksheet:
                # 행 추가: [날짜, 이름, 구분, 주차, 선생님메모, AI추천문구]
                new_row = [now, student_name, student_
