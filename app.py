import streamlit as st
import sqlite3
from datetime import datetime, timedelta
from transformers import AutoModelForCausalLM, AutoTokenizer

# LLaMA 모델 초기화 (대신 GPT-Neo 사용)
@st.cache_resource
def load_model():
    model_name = "EleutherAI/gpt-neo-2.7B"  # LLaMA 대신 GPT-Neo 사용
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    return tokenizer, model

# SQLite 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS conversations 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user_input TEXT, ai_response TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS car_numbers 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, car_number TEXT)''')
    conn.commit()
    conn.close()

# 대화 저장
def save_conversation(user_input, ai_response):
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO conversations (timestamp, user_input, ai_response) VALUES (?, ?, ?)", 
              (timestamp, user_input, ai_response))
    conn.commit()
    conn.close()

# 대화 불러오기
def load_conversations(date_filter=None):
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    if date_filter:
        c.execute("SELECT timestamp, user_input, ai_response FROM conversations WHERE date(timestamp) = ?", (date_filter,))
    else:
        c.execute("SELECT timestamp, user_input, ai_response FROM conversations")
    data = c.fetchall()
    conn.close()
    return data

# 자동차 번호 업로드
def upload_car_numbers(car_list):
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    for car_number in car_list:
        c.execute("INSERT INTO car_numbers (car_number) VALUES (?)", (car_number,))
    conn.commit()
    conn.close()

# 자동차 번호 조회
def get_car_numbers():
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    c.execute("SELECT car_number FROM car_numbers")
    data = c.fetchall()
    conn.close()
    return [row[0] for row in data]

# AI 응답 생성
def get_ai_response(user_input, tokenizer, model):
    inputs = tokenizer(user_input, return_tensors="pt", truncation=True, max_length=512)
    outputs = model.generate(**inputs, max_length=100, num_return_sequences=1)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # 특수 요청 처리
    if "SQLite에 내정보를 저장해서 내일 알려줘" in user_input:
        save_conversation(user_input, response)
        return "내일 알려드릴게요! 내일 이 앱을 다시 열어주세요."
    
    elif "내일 알려줘" in user_input or "내정보 보여줘" in user_input:
        yesterday = (datetime.now() - timedelta(days=1)).date()
        conversations = load_conversations(yesterday)
        if conversations:
            context = "어제 저장된 정보: " + ", ".join([d[1] for d in conversations[:5]]) + ". 이에 대해 답변해줘."
            inputs = tokenizer(context, return_tensors="pt", truncation=True, max_length=512)
            outputs = model.generate(**inputs, max_length=100, num_return_sequences=1)
            return tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    elif "자동차 번호" in user_input:
        car_numbers = get_car_numbers()
        if car_numbers:
            context = f"저장된 자동차 번호: {', '.join(car_numbers[:5])}에 대해 설명해줘."
            inputs = tokenizer(context, return_tensors="pt", truncation=True, max_length=512)
            outputs = model.generate(**inputs, max_length=100, num_return_sequences=1)
            return tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return response

# Streamlit 앱
st.title("LLaMA와 대화하기 (SQLite 저장)")

init_db()
tokenizer, model = load_model()

user_input = st.text_input("하고 싶은 말:")

if user_input:
    ai_response = get_ai_response(user_input, tokenizer, model)
    st.write(f"AI: {ai_response}")
    save_conversation(user_input, ai_response)

if st.button("저장된 대화 보기"):
    conversations = load_conversations()
    if conversations:
        for timestamp, user, ai in conversations:
            st.write(f"[{timestamp}] 사용자: {user} | AI: {ai}")
    else:
        st.write("저장된 대화가 없습니다.")

if st.button("자동차 번호 100개 업로드"):
    car_numbers = [f"12가 {i:04d}" for i in range(1, 101)]
    upload_car_numbers(car_numbers)
    st.success("자동차 번호 100개 업로드 완료!")
