import streamlit as st
import google.generativeai as genai

# ---------------------------------------------------------
# [중요] 여기에 본인의 구글 API 키를 입력하세요
# 따옴표 안에 키를 붙여넣으시면 됩니다.
GOOGLE_API_KEY = "AIzaSyB9YhBjWPaBayGYuBRKhdwt4veSRzyaNlA"
# ---------------------------------------------------------

# API 설정
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"API 키 설정 중 오류가 발생했습니다: {e}")

def generate_message(name, status, week, memo):
    """Gemini를 이용해 상담 내용을 문자로 변환하는 함수"""
    
    # 모델 이름을 'gemini-1.5-flash-latest'로 지정 (오류 해결 포인트!)
    # 만약 그래도 안 되면 'gemini-pro'로 변경해보세요.
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    # 프롬프트(명령어) 구성
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

# 입력 폼
with st.container():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        name = st.text_input("학생 이름", placeholder="예: 김철수")
    with col2:
        status = st.radio("구분", ["재원생", "신규생"], horizontal=True)

    week = st.selectbox("주차", ["1주차", "2주차", "3주차", "4주차", "월말 평가"])
    
    memo = st.text_area("상담 메모", height=150, placeholder="학생의 학습 태도, 특이사항, 진도 등을 자유롭게 적어주세요.")

    # 버튼 클릭 시 동작
    if st.button("저장 및 변환", type="primary"):
        if not GOOGLE_API_KEY or GOOGLE_API_KEY == "여기에_발급받은_API_KEY를_넣으세요":
            st.error("⚠️ 코드 상단에 Google API Key를 먼저 입력해주세요!")
        elif not name:
            st.warning("학생 이름을 입력해주세요.")
        elif not memo:
            st.warning("상담 메모를 입력해주세요.")
        else:
            # 로딩 표시
            with st.spinner(f"{name} 학생의 상담 일지를 분석 중입니다..."):
                result_text = generate_message(name, status, week, memo)
            
            # 성공 메시지
            st.success(f"{name} 학생 저장 완료!")
            
            # 결과 보여주기
            st.subheader("결과 확인")
            st.caption("문자 복사용")
            st.code(result_text, language=None) # 복사하기 편한 코드 블록 형태
