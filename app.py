import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="학생 학습 관리", layout="centered")
DATA_FILE = "student_records.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        columns = ["이름", "반", "수강과목", "학습교재", "주차", "작성일", "과제수행_개인", "과제수행_반평균", "오답수_개인", "오답수_반평균", "질문문항", "난이도", "총평"]
        return pd.DataFrame(columns=columns)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def main():
    st.title("🎓 윈터스쿨 학습 매니저")
    tab1, tab2 = st.tabs(["📝 입력", "📊 리포트"])
    df = load_data()

    with tab1:
        st.header("데이터 입력")
        student_list = df['이름'].unique().tolist()
        student_option = st.radio("구분", ["기존 학생", "신규 등록"], horizontal=True)
        
        name, user_class, subject, book = "", "1B", "공통수학2", "고쟁이(내신+유형)"
        if student_option == "기존 학생":
            if student_list:
                name = st.selectbox("이름 선택", student_list)
                last_info = df[df['이름'] == name].iloc[-1]
                user_class, subject, book = last_info['반'], last_info['수강과목'], last_info['학습교재']
            else:
                student_option = "신규 등록"
        
        if student_option == "신규 등록":
            name = st.text_input("이름")
            user_class = st.text_input("반", value="1B")
            subject = st.text_input("과목", value="공통수학2")
            book = st.text_input("교재", value="고쟁이(내신+유형)")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            week = st.selectbox("주차", [f"{i}주차" for i in range(1, 10)])
            hw_score = st.text_input("과제 점수(개인)", placeholder="A, 90점")
            wrong_count = st.number_input("오답 수(개인)", min_value=0, step=1)
        with col2:
            hw_avg = st.text_input("과제 점수(반평균)", placeholder="B, 85점")
            wrong_avg = st.number_input("오답 수(반평균)", min_value=0, step=1, value=5)

        st.divider()
        q_list = st.text_area("질문 문항", placeholder="15번, 22번")
        difficulty = st.select_slider("난이도", ["최하", "하", "중", "상", "최상"], value="중")
        comment = st.text_area("총평", value="1. 과제수행이 훌륭합니다.\n2. 이해도가 좋습니다.", height=100)

        if st.button("저장하기", use_container_width=True):
            if name:
                new_data = {"이름": name, "반": user_class, "수강과목": subject, "학습교재": book, "주차": week, "작성일": datetime.today().strftime("%Y-%m-%d"), "과제수행_개인": hw_score, "과제수행_반평균": hw_avg, "오답수_개인": wrong_count, "오답수_반평균": wrong_avg, "질문문항": q_list, "난이도": difficulty, "총평": comment}
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                save_data(df)
                st.success("저장 완료!")
                st.rerun()

    with tab2:
        if not df.empty:
            view_name = st.selectbox("학생 확인", df['이름'].unique())
            records = df[df['이름'] == view_name]
            view_week = st.selectbox("주차 확인", records['주차'].unique())
            rec = records[records['주차'] == view_week].iloc[-1]
            
            st.markdown("---")
            st.subheader(f"📄 {rec['이름']} - {rec['주차']} 분석표")
            c1, c2, c3 = st.columns(3)
            c1.metric("반", rec['반']); c2.metric("과목", rec['수강과목']); c3.metric("교재", rec['학습교재'])
            
            st.markdown("##### 성취도")
            st.table(pd.DataFrame({"구분": ["학생", "반평균"], "과제": [rec['과제수행_개인'], rec['과제수행_반평균']], "오답": [rec['오답수_개인'], rec['오답수_반평균']]}).set_index("구분"))
            
            st.info(f"질문: {rec['질문문항']} (난이도: {rec['난이도']})")
            st.success(f"총평: \n{rec['총평']}")
            st.caption("캡처해서 보내세요.")
            st.markdown("---")
            with st.expander("엑셀 다운로드"):
                st.dataframe(df)
                st.download_button("CSV 다운로드", df.to_csv(index=False).encode('utf-8-sig'), "data.csv")

if __name__ == "__main__":
    main()