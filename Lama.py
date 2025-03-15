import streamlit as st
import sqlite3
from datetime import datetime

# SQLite 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    # 대화 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS conversations 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user_input TEXT, ai_response TEXT)''')
    # 자동차 번호 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS car_numbers 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, car_number TEXT)''')
    conn.commit()
    conn.close()

# 대화 저장 함수
def save_conversation(user_input, ai_response):
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO conversations (timestamp, user_input, ai_response) VALUES (?, ?, ?)", 
              (timestamp, user_input, ai_response))
    conn.commit()
    conn.close()

# 대화 불러오기 함수
def load_conversations():
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, user_input, ai_response FROM conversations")
    data = c.fetchall()
    conn.close()
    return data

# 자동차 번호 업로드 함수
def upload_car_numbers(car_list):
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    for car_number in car_list:
        c.execute("INSERT INTO car_numbers (car_number) VALUES (?)", (car_number,))
    conn.commit()
    conn.close()

# 자동차 번호 조회 함수
def get_car_numbers():
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    c.execute("SELECT car_number FROM car_numbers")
    data = c.fetchall()
    conn.close()
    return [row[0] for row in data]

# LLaMA 대체 함수 (실제 LLaMA 대신 간단한 응답)
def get_llama_response(user_input):
    if "자동차 번호" in user_input:
        car_numbers = get_car_numbers()
        if car_numbers:
            return f"저장된 자동차 번호: {', '.join(car_numbers)}"
        else:
            return "저장된 자동차 번호가 없습니다."
    return f"당신이 말한 것: {user_input}"

# Streamlit 앱
st.title("LLaMA와 대화하기 (SQLite 저장)")

# 데이터베이스 초기화
init_db()

# 사용자 입력
user_input = st.text_input("하고 싶은 말:")

if user_input:
    # LLaMA 응답 (여기서는 대체 함수 사용)
    ai_response = get_llama_response(user_input)
    st.write(f"AI: {ai_response}")
    
    # 대화 저장
    save_conversation(user_input, ai_response)

# 저장된 대화 보기
if st.button("저장된 대화 보기"):
    conversations = load_conversations()
    if conversations:
        for timestamp, user, ai in conversations:
            st.write(f"[{timestamp}] 사용자: {user} | AI: {ai}")
    else:
        st.write("저장된 대화가 없습니다.")

# 자동차 번호 업로드 (예시로 100개 추가)
if st.button("자동차 번호 100개 업로드"):
    car_numbers = [f"12가 {i:04d}" for i in range(1, 101)]  # 예: "12가 0001" ~ "12가 0100"
    upload_car_numbers(car_numbers)
    st.success("자동차 번호 100개가 업로드되었습니다!")
