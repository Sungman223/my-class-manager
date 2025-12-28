import streamlit as st
import pandas as pd
from datetime import datetime, timedelta # 날짜 계산용 기능 추가
import re

# -----------------------------------------------------------
# 1. 설정 및 2026년 주차 자동 생성
# -----------------------------------------------------------
st.set_page_config(page_title="학습매니저", layout="centered")

def generate_weeks():
    weeks = {}
    # 2026년의 첫 번째 일요일은 1월 4일입니다.
    curr_date = datetime(2026, 1, 4)
    
    for i in range(1, 54): # 1주차 ~ 53주차까지 넉넉하게 생성
        if curr_date.year > 2026: # 2026년 넘어가면 중단
            break
            
        end_date = curr_date + timedelta(days=6) # 토요일
        
        # 날짜 포맷: "1/4(일) ~ 1/10(토)"
        period = f"{curr_date.month}/{curr_date.day}(일) ~ {end_date.month}/{end_date.day}(토)"
        weeks[f"{i}주차"] = period
        
        # 다음 주 일요일로 이동
        curr_date += timedelta(days=7)
    return weeks

# 주차 정보 생성
WEEKS = generate_weeks()

# 기본 컬럼 정의
COLUMNS = [
    "이름", "반", "출신중", "배정고", "상담특이사항",
    "수강과목", "학습교재", 
    "주차", "기간", "작성일",
    "과제수행_개인", "과제수행_반평균", 
    "오답수_개인", "오답수_반평균", 
    "질문문항", "난이도", "총평"
]

# -----------------------------------------------------------
# 2. 데이터 저장/불러오기 (구글 시트 + CSV 자동 전환)
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
                st.stop()
                
            name = st.selectbox("학생 선택", student_list)
            
            student_records = df[df['이름'] == name]
            last_info = student_records.iloc[-1]
            user_class = last_info.get('반', '1B')
            subject = last_info.get('수강과목', '공통수학2')
            book = last_info.get('학습교재', '고쟁이')
            
            # 이전 주차 기록 보여주기
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
            
            note = st.text_area("상
