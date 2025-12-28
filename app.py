import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(page_title="학습매니저", page_icon="👩‍🏫")
st.title("👩‍🏫 학습매니저")
st.caption("학생 상담 내용을 입력하면 AI가 학부모님께 보낼 피드백을 작성하고 구글 시트에 저장합니다.")

# 2. 비밀키 연결 및 설정 (캐싱을 사용하여 속도 향상)
@st.cache_resource
def connect_to_google_sheets():
    # 구글 시트 인증 범위 설정
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Secrets에서 인증 정보 불러오기
    credentials = Credentials.from_service_account_info(
        st.secrets["GOOGLE_SHEETS_CREDENTIALS"],
        scopes=scopes
    )
    gc = gspread.authorize(credentials)
    
    # Secrets에 있는 URL로 시트 열기
    return gc.open_by_url(st.secrets["SHEET_URL"])

# 초기화 및 연결 시도
try:
    # Gemini API 설정
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 구글 시트 연결
    sh = connect_to_google_sheets()
    worksheet = sh.sheet1  # 첫 번째 시트 사용
    
    st.success("✅ 시스템 연결 성공! 상담 내용을 입력해주세요.", icon="🟢")
    
except Exception as e:
    st.error(f"🚨 연결 오류 발생: {e}")
    st.info("Secrets 설정 이름이 [GOOGLE_SHEETS_CREDENTIALS]와 SHEET_URL 로 정확한지 확인해주세요.")
    st.stop()

# 3. 입력 폼 UI
with st.form("consultation_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("학생 이름", placeholder="예: 김철수")
    with col2:
        student_type = st.radio("구분", ["재원생", "신규생"], horizontal=True)

    week = st.selectbox("주차", ["1주차", "2주차", "3주차", "4주차", "5주차", "기타"])
    
    memo = st.text_area("상담 메모 (특이사항)", 
                       placeholder="예: 과제 수행도가 아주 좋음. 다만 계산 실수가 잦아 오답 노트 지도가 필요함.", 
                       height=150)

    submit_button = st.form_submit_button("💾 저장 및 AI 피드백 생성")

# 4. 저장 및 AI 처리 로직
if submit_button:
    if not student_name or not memo:
        st.warning("⚠️ 학생 이름과 상담 메모를 모두 입력해주세요.")
    else:
        status_area = st.empty() # 진행 상태 표시줄
        
        try:
            # (1) AI 피드백 생성
            status_area.info("🤖 AI가 상담 피드백을 작성 중입니다...")
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            당신은 베테랑 수학 학원 선생님입니다. 아래 학생 상담 메모를 바탕으로 학부모님께 보낼 '정중하고 전문적이며 신뢰감 있는' 상담 피드백 문자를 작성해주세요.
            
            - 학생 이름: {student_name}
            - 상담 내용: {memo}
            - 말투: 예의 바르고 격려하는 어조
            - 길이: 3~5문장 내외로 핵심만 간결하게
            """
            
            response = model.generate_content(prompt)
            ai_result = response.text

            # (2) 구글 시트에 저장
            status_area.info("📊 구글 시트에 기록 중입니다...")
            
            # 한국 시간(KST) 구하기
            kst_now = datetime.utcnow() + timedelta(hours=9)
            timestamp = kst_now.strftime("%Y-%m-%d %H:%M:%S")
            
            # 행 데이터 생성
            new_row = [timestamp, student_name, student_type, week, memo, ai_result]
            worksheet.append_row(new_row)

            # (3) 결과 출력
            status_area.success("🎉 저장 완료!")
            
            st.divider()
            st.subheader(f"📢 {student_name} 학생 학부모님 전송용 메시지")
            st.text_area("복사해서 사용하세요:", value=ai_result, height=200)
            
        except Exception as e:
            st.error(f"처리 중 오류가 발생했습니다: {e}")
