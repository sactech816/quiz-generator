import streamlit as st
import json
import openai
import os
import time
import smtplib
from email.mime.text import MIMEText
from supabase import create_client, Client

# 日本語文字化け防止
os.environ["PYTHONIOENCODING"] = "utf-8"

# ページ設定
st.set_page_config(page_title="診断クイズメーカー", page_icon="🔮", layout="wide")

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
    except Exception as e:
        st.error(f"メール送信エラー: {e}")
        return False

# --- Supabase接続 ---
@st.cache_resource
def init_supabase():
    if "supabase" in st.secrets:
        return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    return None

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"DB接続エラー: {e}")
    st.stop()

# --- セッション初期化 ---
def init_state(key, default_val):
    if key not in st.session_state:
        st.session_state[key] = default_val

# --- AI生成回数の管理 ---
init_state('ai_count', 0)
AI_LIMIT = 5

# --- モード判定 ---
query_params = st.query_params
quiz_id = query_params.get("id", None)

# ==========================================
# モードA：閲覧モード (プレイ画面)
# ==========================================
if quiz_id:
    # ★★★ プレイ画面専用のデザインCSS ★★★
    st.markdown("""
        <style>
        .stApp { background-color: #f1f5f9; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 700px; margin: 0 auto; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .stButton button { width: 100%; border-radius: 8px; font-weight: bold; border: none; padding: 0.5rem 1rem; transition: all 0.3s; }
        .stButton button:hover { transform: scale(1.02); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        </style>
    """, unsafe_allow_html=True)

    if not supabase:
        st.error("データベース設定がありません")
        st.stop()
    try:
        response = supabase.table("quizzes").select("*").eq("id", quiz_id).execute()
        if not response.data:
            st.error("診断が見つかりません。")
            if st.button("トップへ戻る"):
                st.query_params.clear()
                st.rerun()
            st.stop()
        data = response.data[0]
        content = data['content']
        
        if f"q_idx_{quiz_id}" not in st.session_state:
            st.session_state[f"q_idx_{quiz_id}"] = 0
            st.session_state[f"scores_{quiz_id}"] = {'A': 0, 'B': 0, 'C': 0}
            st.session_state[f"finished_{quiz_id}"] = False

        current_idx = st.session_state[f"q_idx_{quiz_id}"]
        questions = content.get('questions', [])
        
        if not st.session_state[f"finished_{quiz_id}"]:
            # 質問画面
            st.markdown(f"""
            <div style="background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; margin-bottom: 20px;">
                <h1 style="color: #1e293b; font-size: 1.8rem; margin-bottom: 1rem;">{content.get('main_heading', '診断')}</h1>
                <p style="color: #64748b; margin-bottom: 2rem;">{content.get('intro_text', '')}</p>
            </div>
            """, unsafe_allow_html=True)
            st.progress((current_idx / len(questions)))
            if current_idx < len(questions):
                q_data = questions[current_idx]
                st.markdown(f"""<div style="text-align: center; margin: 20px 0;"><p style="color: #2563eb; font-weight: bold;">QUESTION {current_idx + 1}</p><h2 style="font-size: 1.4rem; font-weight: bold; color: #334155;">{q_data['question']}</h2></div>""", unsafe_allow_html=True)
                for ans in q_data['answers']:
                    if st.button(ans['text'], key=f"ans_{current_idx}_{ans['text']}", use_container_width=True):
                        st.session_state[f"scores_{quiz_id}"][ans['type']] += 1
                        st.session_state[f"q_idx_{quiz_id}"] += 1
                        st.rerun()
            else:
                st.session_state[f"finished_{quiz_id}"] = True
                st.rerun()
        else:
            # 結果画面
            st.balloons()
            scores = st.session_state[f"scores_{quiz_id}"]
            max_type = max(scores, key=scores.get)
            res_data = content['results'].get(max_type, {})
            st.markdown(f"""
            <div style="background-color: white; padding: 2.5rem; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; border-top: 8px solid #2563eb; margin-top: 20px; margin-bottom: 30px;">
                <p style="color: #2563eb; font-weight: bold;">DIAGNOSIS RESULT</p>
                <h2 style="font-size: 2rem; font-weight: 800; margin: 1rem 0; color: #1e293b;">{res_data.get('title', 'タイプ' + max_type)}</h2>
                <p style="color: #475569; margin-bottom: 2rem;">{res_data.get('desc', '')}</p>
                <a href="{res_data.get('link', '#')}" target="_blank" style="display: inline-block; background: #2563eb; color: white; font-weight: bold; padding: 12px 30px; border-radius: 50px; text-decoration: none;">{res_data.get('btn', '詳細を見る')} ➤</a>
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 もう一度診断する", use_container_width=True):
                    st.session_state[f"q_idx_{quiz_id}"] = 0
                    st.session_state[f"scores_{quiz_id}"] = {'A': 0, 'B': 0, 'C': 0}
                    st.session_state[f"finished_{quiz_id}"] = False
                    st.rerun()
            with col2:
                if st.button("✨ 自分も診断を作る", type="primary", use_container_width=True):
                    st.query_params.clear()
                    st.rerun()
    except Exception as e:
        st.error(f"エラー: {e}")

# ==========================================
# モードB：作成モード (ジェネレーター画面)
# ==========================================
else:
    # ★★★ 作成モード用のCSS（標準に戻す） ★★★
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;} 
        footer {visibility: hidden;} 
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

    # HTMLテンプレート (ダウンロード用)
    html_template_str = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{page_title}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
            body {{ font-family: 'Noto Sans JP', sans-serif; }}
            .fade-in {{ animation: fadeIn 0.7s ease-in-out; }}
            @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(15px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        </style>
    </head>
    <body class="bg-slate-100 text-slate-800 flex items-center justify-center min-h-screen py-8">
        <div class="container mx-auto p-4 sm:p-6 max-w-2xl">
            <div id="start-screen" class="text-center bg-white p-8 sm:p-10 rounded-2xl shadow-xl fade-in">
                <h1 class="text-2xl sm:text-3xl font-bold text-slate-900 mb-4">{main_heading}</h1>
                <p class="text-slate-600 mb-8">{intro_text}</p>
                <button onclick="startQuiz()" class="w-full bg-blue
