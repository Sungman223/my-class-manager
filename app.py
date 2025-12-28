import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="학습매니저", page_icon="👩‍🏫")
st.title("👩‍🏫 학습매니저")

# 2. API 키 및 구글 시트 설정 (secrets에서 가져옴)
try:
    # Gemini API 설정
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 구글 시트 인증 설정
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # secrets에 저장된 구글 시트 인증 정보 로드
    credentials = Credentials.from_service_account_info(
        st.secrets["GOOGLE_SHEETS_CREDENTIALS"],
        scopes=scopes
    )
    gc = gspread.authorize(credentials)
    
    # 시트 열기 (URL 또는 시트 이름으로)
    # secrets에 SHEET_URL이 있다면 그것을 사용하고, 없다면 파일명으로 시도
    if "SHEET_URL" in st.secrets:
        sh = gc.open_by_url(st.secrets["SHEET_URL"])
    else:
        # 만약 URL이 없다면 아래 '학습매니저_데이터' 부분을 실제 시트 이름으로 바꿔주세요
        sh = gc.open("학습매니저_데이터") 
        
    worksheet = sh.sheet1

except Exception as e:
    st.error(f"설정 오류: secrets 설정이나 구글 시트 연결을 확인해주세요.\n{e}")
    st.stop()

# 3. 입력 폼 UI
with st.form("consultation_form"):
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("학생 이름", placeholder="이름을 입력하세요")
    with col2:
        student_type = st.radio("구분", ["재원생", "신규생"], horizontal=True)

    week = st.selectbox("주차", ["1주차", "2주차", "3주차", "4주차", "5주차"])
    
    memo = st.text_area("상담 메모", placeholder="학생의 특징이나 상담 내용을 적어주세요 (예: 기억력이 나쁨, 숙제 성실함 등)", height=150)

    submit_button = st.form_submit_button("저장 및 변환")

# 4. 저장 및 변환 로직
if submit_button:
    if not student_name or not memo:
        st.warning("학생 이름과 상담 메모를 모두 입력해주세요.")
    else:
        with st.spinner("AI가 상담 내용을 정리하고 있습니다..."):
            try:
                # [수정 포인트 1] 모델 이름 변경 (404 오류 해결 시도)
                # gemini-1.5-flash가 안 될 경우 gemini-pro로 자동 시도하도록 처리
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(
                        f"다음은 학생 상담 메모야. 이 내용을 바탕으로 학부모님께 보낼 정중하고 전문적인 상담 피드백 문구를 작성해줘.\n\n학생 이름: {student_name}\n메모: {memo}"
                    )
                except Exception:
                    # 1.5-flash가 안 되면 gemini-pro 사용
                    model = genai.GenerativeModel('gemini-pro')
                    response = model.generate_content(
                        f"다음은 학생 상담 메모야. 이 내용을 바탕으로 학부모님께 보낼 정중하고 전문적인 상담 피드백 문구를 작성해줘.\n\n학생 이름: {student_name}\n메모: {memo}"
                    )

                ai_result = response.text

                # [수정 포인트 2] 끊겨서 오류가 났던 리스트 문법 수정
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_row = [now, student_name, student_type, week, memo, ai_result]
                
                # 시트에 추가
                worksheet.append_row(new_row)

                st.success("저장 완료!")
                
                st.subheader("결과 확인")
                st.info(ai_result)

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
