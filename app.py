import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# 1. 기본 설정 및 비밀키 확인
# ---------------------------------------------------------
st.set_page_config(page_title="학습매니저", page_icon="🧑‍🏫")

# 비밀키(Secrets)가 잘 들어있는지 확인합니다.
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("🚨 설정 오류: Secrets에 'GOOGLE_API_KEY'가 없습니다.")
    st.stop()

if "gcp_service_account" not in st.secrets:
    st.error("🚨 설정 오류: Secrets에 'gcp_service_account'가 없습니다.")
    st.stop()

# ---------------------------------------------------------
# 2. 제미나이(AI) 연결 (최신 모델 적용)
# ---------------------------------------------------------
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # 404 오류 방지를 위해 'gemini-1.5-flash' 사용
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"AI 모델 연결 실패: {e}")

# ---------------------------------------------------------
# 3. 구글 시트 연결 함수
# ---------------------------------------------------------
def get_google_sheet():
    try:
        # 인증 범위 설정
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        
        # 인증 정보 로드
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes,
        )
        
        # 구글 시트 권한 획득
        gc = gspread.authorize(credentials)
        
        # 시트 주소(URL) 가져오기
        sheet_url = st.secrets.get("sheet_url")
        if not sheet_url:
            st.error("Secrets에 'sheet_url'이 설정되지 않았습니다.")
            return None
            
        # 시트 열기
        sh = gc.open_by_url(sheet_url)
        return sh.sheet1  # 첫 번째 시트를 반환
        
    except Exception as e:
        st.error(f"구글 시트 연결 중 오류가 발생했습니다: {e}")
        return None

# ---------------------------------------------------------
# 4. AI 상담 문구 생성 함수
# ---------------------------------------------------------
def generate_ai_message(name, memo):
    # 프롬프트(명령어) 설정
    prompt = f"""
    당신은 꼼꼼하고 다정한 학원 수학 선생님입니다.
    아래 내용을 바탕으로 학부모님께 보낼 정중한 문자를 써주세요.
    
    학생 이름: {name}
    메모 내용: {memo}
    
    [조건]
    1. 예의 바르고 신뢰감 있게 작성할 것.
    2. 전체 길이는 3~4문장으로 요약할 것.
    3. 첫 인사와 끝 인사를 포함할 것.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 변환 에러: {e}"

# ---------------------------------------------------------
# 5. 화면 구성 (UI)
# ---------------------------------------------------------
st.title("🧑‍🏫 학습매니저")
st.caption("선생님을 위한 AI 상담 비서")

with st.form("main_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("학생 이름", placeholder="예: 김철수")
    with col2:
        # 가로로 배치하여 공간 절약
        student_type = st.radio("구분", ["재원생", "신규생"], horizontal=True)
    
    # 주차 선택 (1주차 ~ 12주차)
    week_options = [f"{i}주차" for i in range(1, 13)]
    week_select = st.selectbox("진행 주차", week_options)
    
    # 선생님 메모 입력창
    teacher_memo = st.text_area(
        "상담 메모", 
        height=150, 
        placeholder="학생의 학습 태도, 특이사항 등을 적어주세요."
    )
    
    # 제출 버튼
    submit_btn = st.form_submit_button("저장 및 AI 변환 시작 ✨")

# ---------------------------------------------------------
# 6. 실행 로직 (버튼 클릭 시)
# ---------------------------------------------------------
if submit_btn:
    # 1. 입력값 검증
    if not student_name:
        st.warning("⚠️ 학생 이름을 입력해주세요.")
    elif not teacher_memo:
        st.warning("⚠️ 상담 메모 내용을 입력해주세요.")
    else:
        # 2
