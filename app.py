import streamlit as st
import google.generativeai as genai

# ---------------------------------------------------------
# [보안 설정] API 키를 코드에 직접 적지 않고 Secrets에서 가져옵니다.
# 이렇게 해야 GitHub에 코드를 올려도 키가 정지되지 않습니다.
# ---------------------------------------------------------
try:
    # Streamlit 사이트의 'Secrets'에 저장된 키를 불러옵니다.
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except FileNotFoundError:
    st.error("⚠️ API 키를 찾을 수 없습니다. Streamlit 설정(Secrets)에 키를 등록해주세요.")
    st.stop()
except Exception as e:
    st.error(f"⚠️ 연결 오류 발생: {e}")
    st.stop()


def generate_message(name, status, week, memo):
    """Gemini 1.5 Flash 모델을 이용해 상담 문자를 생성하는 함수"""
    
    # 최신 모델 사용
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

# ---------------------------------------------------------
# 화면 구성 (UI)
# ---------------------------------------------------------

st.set_page_config(page_title="학습매니저", page_icon="🧑‍🏫")

st.title("🧑‍🏫 학습매니저")

with st.container():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        name = st.text_input("학생 이름", placeholder="예: 이효승")
    with col2:
        status = st.radio("구분", ["재원생", "신규생"], horizontal=True)

    week = st.selectbox("주차", ["1주차", "2주차", "3주차", "4주차", "월말 평가"])
    
    memo = st.text_area("상담 메모", height=150, 
                        placeholder="학생의 학습 태도, 특이사항, 진도 등을 자유롭게 적어주세요.")

    if st.button("저장 및 변환", type="primary"):
        if not name:
            st.warning("학생 이름을 입력해주세요.")
        elif not memo:
            st.warning("상담 메모를 입력해주세요.")
        else:
            with st.spinner(f"{name} 학생의 상담 문자를 생성 중입니다..."):
                result_text = generate_message(name, status, week, memo)
            
            st.success("완료!")
            
            st.subheader("결과 확인")
            st.code(result_text, language=None)
