import streamlit as st
import google.generativeai as genai

# [중요] 발급받은 API 키를 여기에 넣어주세요
GOOGLE_API_KEY = "AIzaSyB9YhBjWPaBayGYuBRKhdwt4veSRzyaNlA"

try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"API 키 설정 에러: {e}")

def generate_message(name, status, week, memo):
    # 업데이트 후에는 이 최신 모델이 가장 잘 작동합니다
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    당신은 친절하고 전문적인 학원 상담 실장입니다.
    아래 내용을 바탕으로 학부모님께 보낼 정중하고 깔끔한 상담 문자를 작성해주세요.

    [학생 정보]
    - 이름: {name}
    - 구분: {status}
    - 기간: {week}
    
    [상담/특이사항 메모]
    {memo}

    문자 내용은 바로 복사해서 보낼 수 있도록 핵심 내용과 인사를 포함해줘.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"오류 발생: {str(e)}"

st.set_page_config(page_title="학습매니저", page_icon="🧑‍🏫")
st.title("🧑‍🏫 학습매니저")

with st.container():
    col1, col2 = st.columns([2, 1])
    with col1:
        name = st.text_input("학생 이름", placeholder="예: 김철수")
    with col2:
        status = st.radio("구분", ["재원생", "신규생"], horizontal=True)

    week = st.selectbox("주차", ["1주차", "2주차", "3주차", "4주차", "월말 평가"])
    memo = st.text_area("상담 메모", height=150)

    if st.button("저장 및 변환", type="primary"):
        if not name or not memo:
            st.warning("이름과 메모를 입력해주세요.")
        else:
            with st.spinner("문자 생성 중..."):
                result = generate_message(name, status, week, memo)
            st.success("완료!")
            st.code(result, language=None)
