import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------------------------------------------------------
# 1. 설정 및 비밀키 확인
# ---------------------------------------------------------
st.set_page_config(page_title="학습매니저", page_icon="🧑‍🏫")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("설정 오류: Secrets에 GOOGLE_API_KEY가 없습니다.")
    st.stop()

if "gcp_service_account" not in st.secrets:
    st.error("설정 오류: Secrets에 gcp_service_account가 없습니다.")
    st.stop()

# ---------------------------------------------------------
# 2. AI 모델 연결 (gemini-1.5-flash)
# ---------------------------------------------------------
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"AI 연결 실패: {e}")

# ---------------------------------------------------------
# 3. 구글 시트 연결 함수
# ---------------------------------------------------------
def get_sheet():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scope
        )
        client = gspread.authorize(creds)
        
        sheet_url = st.secrets.get("sheet_url")
        if not sheet_url:
            st.error("Secrets에 sheet_url이 없습니다.")
            return None
            
        return client.open_by_url(sheet_url).sheet1
    except Exception as e:
        st.error(f"시트 연결 실패: {e}")
        return None

# ---------------------------------------------------------
# 4. AI 상담 문구 생성 함수
# ---------------------------------------------------------
def make_ai_msg(name, memo):
    prompt = f"""
    학원 수학 선생님입니다. 학부모님께 보낼 상담 문자를 써주세요.
    학생: {name}
    내용: {memo}
    조건: 예의바르게, 3~4문장 요약, 인사말 포함.
    """
    try:
        res = model.generate_content(prompt)
        return res.text
    except Exception as e:
        return f"오류 발생: {e}"

# ---------------------------------------------------------
# 5. 화면 구성 및 실행
# ---------------------------------------------------------
st.title("🧑‍🏫 학습매니저")

with st.form("form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("학생 이름", placeholder="예: 김철수")
    with col2:
        stype = st.radio("구분", ["재원생", "신규생"], horizontal=True)
    
    week = st.selectbox("주차", [f"{i}주차" for i in range(1, 13)])
    memo = st.text_area("상담 메모", height=100)
    
    # 버튼을 누르면 실행
    submit = st.form_submit_button("저장 및 변환")

if submit:
    if not name or not memo:
        st.warning("이름과 메모를 꼭 입력해주세요!")
    else:
        with st.spinner("처리 중입니다..."):
            # 1. 시간 구하기
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # 2. AI 문구 만들기
            ai_msg = make_ai_msg(name, memo)
            
            # 3. 구글 시트 저장
            sheet = get_sheet()
            if sheet:
                # 데이터를 한 줄로 정리
                row = [now, name, stype, week, memo, ai_msg]
                
                try:
                    sheet.append_row(row)
                    st.success(f"{name} 학생 저장 완료!")
                    
                    st.subheader("결과 확인")
                    st.text_area("문자 복사용", value=ai_msg, height=150)
                except Exception as e:
                    st.error(f"저장 중 오류: {e}")

# 코드 끝 (여기가 보이면 복사가 잘 된 것입니다)
