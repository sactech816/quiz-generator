import streamlit as st
import json
import openai
import os
import time
import smtplib
import stripe
from email.mime.text import MIMEText
from supabase import create_client, Client
import streamlit.components.v1 as components

# 日本語文字化け防止
os.environ["PYTHONIOENCODING"] = "utf-8"

# ページ設定
st.set_page_config(page_title="Diagnosis Portal", page_icon="💎", layout="wide")

# --- 設定読み込み ---
if "stripe" in st.secrets:
    stripe.api_key = st.secrets["stripe"]["api_key"]

@st.cache_resource
def init_supabase():
    if "supabase" in st.secrets:
        return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    return None
supabase = init_supabase()

def init_state(key, val):
    if key not in st.session_state: st.session_state[key] = val

init_state('ai_count', 0)
init_state('page_mode', 'home')
AI_LIMIT = 5

# --- メール送信関数 ---
def send_email(to_email, quiz_url, quiz_title):
    try:
        sender_email = st.secrets["email"]["address"]
        sender_password = st.secrets["email"]["password"]
        subject = "【診断メーカー】作成された診断のURLをお届けします"
        body = f"""
        診断を作成いただきありがとうございます！
        以下のURLから、作成した診断にアクセスできます。
        
        ■タイトル: {quiz_title}
        ■URL: {quiz_url}
        --------------------------------------------------
        ※このメールは自動送信されています。
        """
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except: return False

# ==========================================
# 🎨 デザイン: HTMLテンプレート生成関数
# ==========================================
def get_html_template(data, is_preview=False):
    page_title = data.get('page_title', '診断')
    main_heading = data.get('main_heading', 'タイトル')
    intro_text = data.get('intro_text', '')
    questions = data.get('questions', [])
    results = data.get('results', {})

    # 質問HTML
    questions_html = ""
    for q in questions:
        opts_html = ""
        for ans in q['answers']:
            points_json = json.dumps({ans['type']: 1}, ensure_ascii=False).replace('"', '&quot;')
            opts_html += f'<div data-key="option" data-points="{points_json}">{ans["text"]}</div>'
        questions_html += f'<div data-item="question"><p data-key="text">{q["question"]}</p><div data-key="options">{opts_html}</div></div>'

    # 結果HTML
    results_html = ""
    for key, val in results.items():
        btn_html = ""
        if val.get('link') and val.get('btn'):
            btn_html = f'<div class="mt-6 text-center"><a href="{val["link"]}" target="_blank" class="flyer-link-button">{val["btn"]} ➤</a></div>'
        results_html += f'<div data-item="result" data-id="{key}"><h2 data-key="title">{val["title"]}</h2><p data-key="description" class="result-text">{val["desc"]}</p>{btn_html}</div>'

    # CSS調整
    bg_color = "#f3f4f6" if is_preview else "#f3f4f6" # プレビュー時も同じ色にする

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Noto Sans JP', sans-serif; background-color: {bg_color}; color: #1f2937; display: flex; flex-direction: column; min-height: 100vh; }}
        .quiz-container-wrapper {{ flex-grow: 1; display: flex; justify-content: center; align-items: flex-start; padding: 2rem; }}
        .quiz-container {{ max-width: 700px; width: 100%; padding: 2.5rem; background-color: white; border-radius: 0.75rem; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }}
        .question-card, .result-card {{ padding: 1.5rem; border: 1px solid #e5e7eb; border-radius: 0.5rem; margin-bottom: 1.5rem; }}
        .option-button {{ display: block; width: 100%; text-align: left; padding: 1rem 1.25rem; margin-bottom: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.375rem; background-color: #f9fafb; transition: all 0.2s; cursor: pointer; }}
        .option-button:hover {{ background-color: #eff6ff; border-color: #3b82f6; }}
        .option-button.selected {{ background-color: #dbeafe; border-color: #3b82f6; font-weight: 600; }}
        .next-button, .restart-button {{ padding: 0.85rem 2rem; border-radius: 0.375rem; font-weight: 600; transition: all 0.2s; text-align: center; display: inline-block; cursor: pointer; width: 100%; }}
        .next-button {{ background-color: #2563eb; color: white; border: none; }}
        .next-button:hover {{ background-color: #1d4ed8; }}
        .next-button:disabled {{ background-color: #9ca3af; cursor: not-allowed; }}
        .restart-button {{ background-color: #4b5563; color: white; margin-top: 1rem; border: none; }}
        .progress-bar-container {{ width: 100%; background-color: #e5e7eb; border-radius: 99px; overflow: hidden; margin-bottom: 1.5rem; }}
        .progress-bar {{ height: 0.5rem; background-color: #2563eb; width: 0%; transition: width 0.3s ease-in-out; }}
        .hidden {{ display: none; }}
        .result-title {{ font-size: 1.75rem; font-weight: 700; color: #1e3a8a; margin-bottom: 1rem; text-align: center; }}
        .result-text {{ line-height: 1.8; color: #4b5563; }}
        .flyer-link-button {{ background-color: #059669; color: white; text-decoration: none; display: block; padding: 1rem; border-radius: 0.375rem; text-align: center; font-weight: bold; transition: transform 0.2s; }}
        .flyer-link-button:hover {{ transform: scale(1.02); }}
    </style>
</head>
<body>
    <div id="quiz-data" style="display: none;">
        <div data-container="questions">{questions_html}</div>
        <div data-container="results">{results_html}</div>
    </div>
    <div class="quiz-container-wrapper">
        <div class="quiz-container">
            <h1 class="text-2xl font-bold text-center mb-4 text-slate-800">{main_heading}</h1>
            <p class="text-center text-gray-600 mb-8">{intro_text}</p>
            <div id="quiz-area"></div>
            <div id="result-area" class="hidden"></div>
        </div>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', () => {{
        let questions = [], results = [], currentQuestionIndex = 0, userAnswers = [];
        const quizArea = document.getElementById('quiz-area'), resultArea = document.getElementById('result-area');
        function loadData() {{
            const d = document.getElementById('quiz-data');
            questions = Array.from
