import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
import google.generativeai as genai # AI 기능 추가

# -----------------------------------------------------------
# 1. 설정 및 Gemini 연결
# -----------------------------------------------------------
st.set_page_config(page_title="학습매니저", layout="centered")

# Gemini API 설정 (Secrets에 키가 있을 때만 작동)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def refine_text_with_ai(text):
    """Gemini를 이용해 문장을 다듬는 함수"""
    if not text:
        return ""
    try:
        model = genai.GenerativeModel('gemini-pro')
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
# 3. 메인 화면 로직
# -----------------------------------------------------------
def main():
    st.title("👨‍🏫 학습매니저 (AI 탑재)")
    
    if "connections" not in st.secrets:
        st.warning("⚠️ 구글 시트 미연동 (CSV 모드)")
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Gemini API 키가 없습니다. Secrets에 추가해주세요.")

    tab1, tab2 = st.tabs(["📝 데이터 입력", "📊 리포트 생성"])
    df = load_data()

    # --- [탭 1] 데이터 입력 ---
    with tab1:
        st.header("학생 데이터 관리")
        
        student_list = df['이름'].unique().tolist()
        mode = st.radio("작업 선택", ["기존 학생 기록 추가", "신규 학생 등록"], horizontal=True)
        
        name, user_class, middle, high = "", "1B", "", ""
        subject, book = "공통수학2", "고쟁이(내신+유형)"
        
        # 세션 스테이트 초기화 (AI 변환 텍스트 저장용)
        if "refined_note" not in st.session_state:
            st.session_state["refined_note"] = ""

        if mode == "기존 학생 기록 추가":
            if not student_list:
                st.error("학생이 없습니다. 신규 등록을 먼저 해주세요.")
            else:
                name = st.selectbox("학생 선택", student_list)
                last_info = df[df['이름'] == name].iloc[-1]
                user_class = last_info.get('반', '1B')
                subject = last_info.get('수강과목', '공통수학2')
                book = last_info.get('학습교재', '고쟁이')

        else: # 신규 등록
            st.subheader("기본 정보")
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("학생 이름")
                middle = st.text_input("출신 중학교")
            with c2:
                user_class = st.text_input("배정 반", value="1B")
                high = st.text_input("배정 고등학교")

        st.divider()
        st.subheader("학습 및 상담 내용")

        # --- AI 다듬기 기능 구현부 ---
        raw_note = st.text_area("💡 상담 메모 (여기에 대충 적으세요)", placeholder="예: 숙제 덜해옴. 수업때 딴짓함. 어머니께 전화드리기.")
        
        if st.button("✨ AI로 문장 다듬기"):
            with st.spinner("AI가 문장을 다듬고 있습니다..."):
                st.session_state["refined_note"] = refine_text_with_ai(raw_note)
        
        # 최종 저장될 내용은 여기서 수정 가능
        final_note = st.text_area("✅ 최종 저장될 상담 내용", value=st.session_state["refined_note"], height=100)
        # ---------------------------

        col1, col2 = st.columns(2)
        with col1:
            week_key = st.selectbox("주차 선택", list(WEEKS.keys()))
            week_period = WEEKS[week_key]
            subject = st.text_input("수강과목", value=subject)
            book = st.text_input("학습교재", value=book)
        with col2:
            homework_p = st.number_input("과제수행(개인) %", 0, 100, 80)
            homework_c = st.number_input("과제수행(반평균) %", 0, 100, 75)
            wrong_p = st.number_input("오답수(개인)", 0, 100, 5)
            wrong_c = st.number_input("오답수(반평균)", 0, 100, 7)

        question = st.text_input("주요 질문 문항")
        difficulty = st.select_slider("난이도", ["쉬움", "보통", "어려움", "매우 어려움"], value="보통")
        review = st.text_area("금주 총평", placeholder="학부모 리포트에 들어갈 내용")

        if st.button("💾 데이터 저장", type="primary"):
            if not name:
                st.error("이름을 입력하세요.")
            else:
                new_record = {
                    "이름": name, "반": user_class, "출신중": middle, "배정고": high, 
                    "상담특이사항": final_note, # AI가 다듬은 내용 저장
                    "수강과목": subject, "학습교재": book,
                    "주차": week_key, "기간": week_period, 
                    "작성일": datetime.now().strftime("%Y-%m-%d"),
                    "과제수행_개인": homework_p, "과제수행_반평균": homework_c,
                    "오답수_개인": wrong_p, "오답수_반평균": wrong_c,
                    "질문문항": question, "난이도": difficulty, "총평": review
                }
                new_df = pd.DataFrame([new_record])
                updated_df = pd.concat([df, new_df], ignore_index=True)
                msg = save_data(updated_df)
                st.success(f"{name} 저장 완료! ({msg})")
                # 저장 후 입력칸 초기화
                st.session_state["refined_note"] = ""
                st.rerun()

    # --- [탭 2] 리포트 ---
    with tab2:
        st.header("학부모 리포트")
        if not df.empty:
            t_name = st.selectbox("학생 선택", df['이름'].unique(), key="report_name")
            t_data = df[df['이름'] == t_name].iloc[-1]
            
            rpt = f"""
[청솔학원 {t_data['이름']} 학습 리포트]
기간: {t_data['주차']}
과목: {t_data['수강과목']} / {t_data['학습교재']}
과제: {t_data['과제수행_개인']}% (반평균 {t_data['과제수행_반평균']}%)
특이사항: {t_data['상담특이사항']}
총평: {t_data['총평']}
            """
            st.text_area("복사하기", rpt, height=250)

if __name__ == "__main__":
    main()
