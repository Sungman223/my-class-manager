import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re

# -----------------------------------------------------------
# 1. 설정 및 2026년 주차 자동 생성
# -----------------------------------------------------------
st.set_page_config(page_title="학습매니저", layout="centered")

def generate_weeks():
    weeks = {}
    curr_date = datetime(2026, 1, 4)
    
    for i in range(1, 54):
        if curr_date.year > 2026:
            break
            
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
    st.title("👨‍🏫 학습매니저")
    
    if "connections" not in st.secrets:
        st.warning("⚠️ 구글 시트 미연동 상태 (CSV 임시 저장 모드)")

    tab1, tab2 = st.tabs(["📝 데이터 입력", "📊 학부모 전송 리포트"])
    df = load_data()

    # --- [탭 1] 데이터 입력 ---
    with tab1:
        st.header("학생 데이터 관리")
        
        student_list = df['이름'].unique().tolist()
        mode = st.radio("작업 선택", ["기존 학생 기록 추가", "신규 학생 등록"], horizontal=True)
        
        name, user_class, middle, high, note = "", "1B", "", "", ""
        subject, book = "공통수학2", "고쟁이(내신+유형)"
        
        if mode == "기존 학생 기록 추가":
            if not student_list:
                st.error("등록된 학생이 없습니다. 신규 등록을 먼저 해주세요.")
            else:
                name = st.selectbox("학생 선택", student_list)
                student_records = df[df['이름'] == name]
                last_info = student_records.iloc[-1]
                
                # 기존 정보 불러오기
                user_class = last_info.get('반', '1B')
                subject = last_info.get('수강과목', '공통수학2')
                book = last_info.get('학습교재', '고쟁이')
                
                with st.expander(f"📖 {name} 학생의 이전 기록 보기 (최근 5주)", expanded=True):
                    history_df = student_records[['주차', '과제수행_개인', '오답수_개인', '총평']].tail(5)
                    st.dataframe(history_df, use_container_width=True, hide_index=True)

        else: # 신규 학생 등록
            st.subheader("초도 상담 데이터 입력")
            col_new1, col_new2 = st.columns(2)
            with col_new1:
                name = st.text_input("학생 이름")
                middle = st.text_input("출신 중학교")
            with col_new2:
                user_class = st.text_input("배정 반", value="1B")
                high = st.text_input("배정 예정 고등학교")
            
            note = st.text_area("상담 내용") # 여기가 아까 에러났던 부분 (수정됨)

        st.divider()
        st.subheader("금주 학습 데이터 입력")
        
        col1, col2 = st.columns(2)
        with col1:
            week_key = st.selectbox("주차 선택", list(WEEKS.keys()))
            week_period = WEEKS[week_key]
            st.info(f"기간: {week_period}")
            
            subject = st.text_input("수강과목", value=subject)
            book = st.text_input("학습교재", value=book)
            
        with col2:
            homework_p = st.number_input("과제수행(개인) %", 0, 100, 80)
            homework_c = st.number_input("과제수행(반평균) %", 0, 100, 75)
            wrong_p = st.number_input("오답수(개인)", 0, 100, 5)
            wrong_c = st.number_input("오답수(반평균)", 0, 100, 7)

        question = st.text_input("주요 질문 문항")
        difficulty = st.select_slider("난이도 체감", options=["쉬움", "보통", "어려움", "매우 어려움"], value="보통")
        review = st.text_area("금주 총평 (학부모 전송용)")

        # 저장 버튼 로직
        if st.button("💾 데이터 저장", type="primary"):
            if not name:
                st.error("학생 이름을 입력해주세요.")
            else:
                new_record = {
                    "이름": name, "반": user_class, "출신중": middle, "배정고": high, "상담특이사항": note,
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
                st.success(f"{name} 학생 데이터 저장 완료! ({msg})")
                st.rerun()

    # --- [탭 2] 리포트 생성 (간단 예시) ---
    with tab2:
        st.header("학부모 전송 메시지 생성")
        if df.empty:
            st.info("데이터가 없습니다.")
        else:
            target_name = st.selectbox("학생 선택", df['이름'].unique())
            target_data = df[df['이름'] == target_name].iloc[-1]
            
            msg = f"""
[청솔학원 {target_data['이름']} 학생 학습 리포트]
- 기간: {target_data['주차']} ({target_data['기간']})
- 과목: {target_data['수강과목']}
- 과제 수행률: {target_data['과제수행_개인']}% (반평균 {target_data['과제수행_반평균']}%)
- 총평: {target_data['총평']}
            """
            st.text_area("카카오톡 복사 문구", msg, height=200)

if __name__ == "__main__":
    main()
