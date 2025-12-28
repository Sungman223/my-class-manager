import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys

# ===========================================================
# 1. 페이지 설정
# ===========================================================
st.set_page_config(page_title="학습매니저", layout="centered")

# ===========================================================
# 2. Gemini 안전 초기화
# ===========================================================
GEMINI_READY = False
genai = None

try:
    import google.generativeai as genai
    if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        GEMINI_READY = True
except Exception:
    GEMINI_READY = False


def refine_text_with_ai(text: str) -> str:
    if not text:
        return ""

    if not GEMINI_READY:
        return "⚠️ Gemini API 키가 설정되지 않아 AI 기능을 사용할 수 없습니다."

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        너는 학원 선생님의 비서야.
        아래 상담 메모를 학부모님께 보내기 좋은
        정중하고 전문적인 문체로 다듬어줘.
        내용은 절대 바꾸지 마.

        [상담 메모]
        {text}
        """
        res = model.generate_content(prompt)
        return res.text
    except Exception as e:
        return f"⚠️ Gemini 오류: {e}"


# ===========================================================
# 3. 주차 생성
# ===========================================================
def generate_weeks_2026():
    weeks = {}
    curr = datetime(2026, 1, 4)  # 1주차 일요일
    for i in range(1, 54):
        if curr.year != 2026:
            break
        end = curr + timedelta(days=6)
        weeks[f"{i}주차"] = f"{curr.month}/{curr.day}(일) ~ {end.month}/{end.day}(토)"
        curr += timedelta(days=7)
    return weeks


WEEKS = generate_weeks_2026()

COLUMNS = [
    "이름", "반", "출신중", "배정고", "상담특이사항",
    "수강과목", "학
