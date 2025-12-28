import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import google.generativeai as genai

# -----------------------------------------------------------
# 1. 기본 설정 및 유틸리티
# -----------------------------------------------------------
st.set_page_config(page_title="학습매니저", layout="centered")

def generate_weeks():
    """2026년 주차 정보 생성"""
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
    "오답수_개인", "오답수_반평균"
]

# -----------------------------------------------------------
# 2. AI 및 데이터 기능 (에러 방지 적용)
# -----------------------------------------------------------
def init_gemini():
    """Gemini API 연결 시도"""
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception:
        return None

def refine_text_with_ai(text):
    """AI 문장 다듬기"""
    if not text: return ""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"다음 상담 내용을 학부모님께 보낼 정중한 문체로 다듬어줘:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 연결 오류 (API 키 확인 필요): {e}"

def load_data():
    """데이터 불러오기 (구글시트 -> 없으면 빈 표)"""
    # 1. 구글 시트 시도
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        try:
            from streamlit_gsheets import GSheetsConnection
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(worksheet="Sheet1")
            # 컬럼 보정
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            pass # 실패하면 조용히 넘어감
    
    # 2. 로컬 CSV 시도
    try:
        return pd.read_csv("student_records.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=COLUMNS)

def save_data_logic(df):
    """데이터 저장 로직"""
    # 구글 시트 저장 시도
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        try:
            from streamlit_gsheets import GSheetsConnection
            conn = st.connection("gsheets", type=GSheetsConnection)
            conn.update(worksheet="Sheet1", data=df)
            return "구글 시트에 저장 성공!"
        except Exception as e:
            return f"구글 시트 저장 실패 (CSV로 저장됨): {e}"
    
    # 로컬 CSV 저장
    df.to_csv("student_records.csv", index=False)
    return "CSV 파일로 저장 성공!"

# -----------------------------------------------------------
# 3. 메인 화면 (UI)
# -----------------------------------------------------------
def main():
    st.title("👨‍🏫 학습매니저 (Safe Mode)")
    
    # 시스템 상태 체크
    gemini_connected = init_gemini()
    
    if not gemini_connected:
        st.warning("⚠️ Gemini API 키가 설정되지 않았습니다. AI 기능은 작동하지 않습니다.")
        
    df = load_data()
    
    tab1, tab2 = st.tabs(["📝 데이터 입력", "📊 저장된 데이터"])

    # --- 탭 1: 입력 ---
    with tab1:
        st.header("학생 상담 일지")
        with st.form("entry_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("이름")
            cls = c2.text_input("반")
            subject = c1.selectbox("과목", ["수학(상)", "수학(하)", "수1", "수2", "미적분", "확통"])
            week = c2.selectbox("주차", list(WEEKS.keys()))
            
            st.divider()
            c3, c4 = st.columns(2)
            task_p = c3.number_input("과제 점수", 0, 100, step=5)
            wrong_p = c4.number_input("오답 수", 0, 100, step=1)
            
            note = st.text_area("상담 메모")
            
            submit = st.form_submit_button("저장하기")
            
            if submit:
                new_row = {
                    "이름": name, "반": cls, "수강과목": subject,
                    "주차": week, "기간": WEEKS[week],
                    "과제수행_개인": task_p, "오답수_개인": wrong_p,
                    "상담특이사항": note,
                    "작성일": datetime.now().strftime("%Y-%m-%d")
                }
                new_df = pd.DataFrame([new_row])
                df = pd.concat([df, new_df], ignore_index=True)
                msg = save_data_logic(df)
                st.success(f"저장 완료: {msg}")

        # AI 도구 (Form 밖에서 작동)
        st.divider()
        st.subheader("🤖 AI 문장 다듬기")
        ai_txt = st.text_area("거친 문장을 입력하세요", height=100)
        if st.button("AI로 변환"):
            if gemini_connected:
                with st.spinner("변환 중..."):
                    res = refine_text_with_ai(ai_txt)
                    st.info(res)
            else:
                st.error("API 키가 없어서 실행할 수 없습니다.")

    # --- 탭 2: 조회 ---
    with tab2:
        st.dataframe(df)

if __name__ == "__main__":
    main()
