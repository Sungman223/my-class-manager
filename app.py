import streamlit as st
import pandas as pd
import time
from datetime import datetime
import google.generativeai as genai

# -----------------------------------------------------------
# 1. 화면 설정 (가장 먼저 실행되어야 함)
# -----------------------------------------------------------
st.set_page_config(page_title="학습매니저 재부팅", layout="centered")

# 화면이 멈췄는지 확인하기 위한 로딩 메시지
status_text = st.empty()
status_text.info("🚀 시스템을 시작하고 있습니다... (1/3)")
time.sleep(0.5)

# -----------------------------------------------------------
# 2. 기본 설정
# -----------------------------------------------------------
# 주차 정보 생성
def generate_weeks():
    weeks = {}
    curr = datetime(2026, 1, 4)
    for i in range(1, 54):
        end = curr + pd.Timedelta(days=6)
        period = f"{curr.month}/{curr.day} ~ {end.month}/{end.day}"
        weeks[f"{i}주차"] = period
        curr += pd.Timedelta(days=7)
    return weeks

WEEKS = generate_weeks()
COLUMNS = ["구분", "이름", "반", "과목", "주차", "상담내용", "AI조언", "작성일"]

# -----------------------------------------------------------
# 3. 기능 함수 (안전 모드)
# -----------------------------------------------------------
status_text.info("🤖 AI 기능을 연결하고 있습니다... (2/3)")

def get_ai_response(prompt):
    """AI 연결이 실패해도 앱이 죽지 않도록 방어"""
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ API 키가 설정되지 않았습니다."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 에러 발생: {str(e)}"

def load_csv():
    """CSV 파일만 사용 (멈춤 방지)"""
    try:
        return pd.read_csv("data.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=COLUMNS)

def save_csv(df):
    df.to_csv("data.csv", index=False)

# -----------------------------------------------------------
# 4. 메인 화면 그리기
# -----------------------------------------------------------
status_text.success("✅ 시스템 준비 완료! 화면을 불러옵니다. (3/3)")
time.sleep(0.5)
status_text.empty() # 로딩 메시지 삭제

def main():
    st.title("👨‍🏫 학습매니저 (복구 모드)")
    st.caption("현재 안전 모드로 실행 중입니다. (데이터는 CSV로 자동 저장됨)")

    # 데이터 로드
    df = load_csv()

    # 입력 탭과 조회 탭 분리
    tab1, tab2 = st.tabs(["📝 상담 입력", "📊 기록 확인"])

    with tab1:
        st.subheader("신규 상담 작성")
        with st.form("save_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("학생 이름", placeholder="예: 김철수")
            category = c2.radio("구분", ["재원생", "신규생"], horizontal=True)
            
            c3, c4 = st.columns(2)
            cls = c3.text_input("반 이름")
            week = c4.selectbox("주차", list(WEEKS.keys()))
            
            memo = st.text_area("상담 메모 (선생님 작성)", height=100)
            
            # AI 미리보기 버튼 (폼 안에 있으면 동작 안하므로 폼 제출 버튼으로 처리)
            submit = st.form_submit_button("저장 및 AI 변환")

            if submit:
                if not name:
                    st.error("이름을 입력해주세요!")
                else:
                    # AI 변환 시도
                    with st.spinner("AI가 문장을 다듬는 중..."):
                        ai_prompt = f"학부모님께 보낼 문자야. 정중하게 다듬어줘.\n학생: {name}\n상태: {category}\n내용: {memo}"
                        ai_result = get_ai_response(ai_prompt)
                    
                    # 데이터 저장
                    new_data = {
                        "구분": category, "이름": name, "반": cls, "과목": "수학",
                        "주차": week, "상담내용": memo, "AI조언": ai_result,
                        "작성일": datetime.now().strftime("%Y-%m-%d")
                    }
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                    save_csv(df)
                    
                    st.success(f"{name} 학생 상담이 저장되었습니다!")
                    st.info(f"💌 [AI 추천 문구]\n{ai_result}")

    with tab2:
        st.write(f"총 {len(df)}건의 상담 기록이 있습니다.")
        st.dataframe(df)

if __name__ == "__main__":
    main()
