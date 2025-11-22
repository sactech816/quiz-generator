import streamlit as st
import json
import openai
import os
import time
import stripe
import smtplib
import random
from email.mime.text import MIMEText
from supabase import create_client, Client
import streamlit.components.v1 as components

# 日本語文字化け防止
os.environ["PYTHONIOENCODING"] = "utf-8"

# ページ設定
st.set_page_config(page_title="診断クイズメーカー", page_icon="💎", layout="wide")

# ==========================================
# 1. デザイン定義 (CSS)
# ==========================================
def apply_portal_style():
    """公開画面用の白ベースデザイン"""
    st.markdown("""
        <style>
        /* 全体設定 */
        .stApp { background-color: #ffffff !important; color: #333333 !important; }
        .block-container { max-width: 1100px; padding-top: 1rem; padding-bottom: 5rem; }
        
        /* UI隠し */
        #MainMenu, footer, header {visibility: hidden !important;} 
        .stDeployButton {display:none !important;}
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stDecoration"] {display: none !important;}
        [data-testid="stStatusWidget"] {visibility: hidden !important;}
        
        /* --- カードデザイン --- */
        a.quiz-card-link {
            text-decoration: none !important;
            color: inherit !important;
            display: block !important;
        }
        a.quiz-card-link:hover { text-decoration: none !important; }

        /* カード本体 */
        .quiz-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            height: 420px; /* 高さを確保 */
            display: flex;
            flex-direction: column;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: all 0.2s ease-in-out;
            margin-bottom: 10px;
            cursor: pointer;
            position: relative;
        }
        
        .quiz-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
            border-color: #cbd5e1;
        }
        
        /* 画像エリア */
        .quiz-thumb-box {
            width: 100%;
            height: 180px; /* 画像高さ固定 */
            background-color: #f1f5f9;
            overflow: hidden;
            position: relative;
            flex-shrink: 0;
        }
        .quiz-thumb {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.5s ease;
        }
        .quiz-card:hover .quiz-thumb { transform: scale(1.05); }
        
        /* コンテンツエリア */
        .quiz-content {
            padding: 16px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }
        
        /* タイトル (2行制限) */
        .quiz-title { 
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 8px;
            color: #1e293b;
            line-height: 1.4;
            height: 2.8em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        
        /* 説明文 (3行制限) */
        .quiz-desc { 
            font-size: 0.85rem;
            color: #64748b;
            line-height: 1.5;
            height: 4.5em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            margin-bottom: auto; /* 下に余白を作る */
        }
        
        /* バッジ */
        .badge-new { 
            position: absolute; top: 10px; left: 10px; 
            background: rgba(255,255,255,0.9); color: #1e40af; 
            font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; z-index: 2;
        }
        .badge-stats {
            position: absolute; bottom: 5px; right: 5px;
            background: rgba(0,0,0,0.6); color: white;
            font-size: 0.7rem; padding: 2px 8px; border-radius: 12px; font-weight: bold; z-index: 2;
        }
        
        /* ボタン */
        .stButton button {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            color: #334155 !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            padding: 0.6rem 1rem !important;
            transition: all 0.2s !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        }
        .stButton button:hover {
            border-color: #94a3b8 !important;
            background-color: #f1f5f9 !important;
            color: #1e293b !important;
            transform: translateY(-1px);
        }
        
        /* プライマリボタン (青) */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important;
        }
        .stButton button[kind="primary"]:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%) !important;
            box-shadow: 0 6px 10px rgba(37, 99, 235, 0.3) !important;
            color: white !important;
        }
        
        /* セカンダリボタン (ピンク) */
        .stButton button[kind="secondary"] {
            background: #fff1f2 !important;
            color: #e11d48 !important;
            border: 1px solid #fecdd3 !important;
        }
        .stButton button[kind="secondary"]:hover {
            background: #ffe4e6 !important;
            border-color: #fda4af !important;
            color: #be123c !important;
        }

        /* リンクボタン (黒) */
        a[data-testid="stLinkButton"] {
            background-color: #1e293b !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: bold !important;
            text-align: center !important;
            border-radius: 8px !important;
            transition: all 0.2s !important;
            margin-top: 5px !important;
            display: block !important;
            padding: 0.6rem !important;
        }
        a[data-testid="stLinkButton"]:hover {
            background-color: #334155 !important;
            text-decoration: none !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        }
        
        /* 削除ボタン */
        .delete-btn button {
            background-color: #fee2e2 !important; color: #991b1b !important; border: 1px solid #fecaca !important;
            padding: 0.3rem 0.5rem !important; font-size: 0.8rem !important; margin-top: 5px; width: auto !important;
        }

        /* ヒーローエリア */
        .hero-container {
            background: white; border-radius: 16px; padding: 3rem; margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

def apply_editor_style():
    """エディタ用の黒ベースデザイン"""
    st.markdown("""
        <style>
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}
        .block-container { padding-top: 2rem; padding-bottom: 5rem; }
        .stApp {
            background-color: #0e1117 !important;
            color: #ffffff !important;
        }
        .stTextInput input, .stTextArea textarea, .stSelectbox select {
            background-color: #262730 !important;
            color: #ffffff !important;
            border: 1px solid #41444e !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #262730 !important;
            border: 1px solid #41444e !important;
        }
        </style>
    """, unsafe_allow_html=True)

# HTMLパーツ
HERO_HTML = """
<div class="hero-container">
    <h1 style="font-size:2.5rem; font-weight:900; color:#1e293b; margin-bottom:10px;">診断クイズメーカー</h1>
    <p style="color:#64748b;">AIがたった1分で構成案を作成。集客・販促に使える高品質な診断ツールを今すぐ公開。</p>
</div>
"""

# カードの中身（画像とテキストのみHTMLで描画）
def get_card_content_html(title, desc, img_url, views=0, likes=0):
    return f"""
    <div class="card-img-box">
        <span class="badge-new">NEW</span>
        <span class="badge-stats">👁️ {views} &nbsp; ❤️ {likes}</span>
        <img src="{img_url}" class="card-img" loading="lazy">
    </div>
    <div class="card-text-box">
        <div class="card-title">{title}</div>
        <div class="card-desc">{desc}</div>
    </div>
    """

# カスタムボタンHTML生成関数
def get_custom_button_html(url, text, color="blue", target="_top"):
    color_map = {
        "blue": "background-color: #2563eb; color: white;",
        "green": "background-color: #16a34a; color: white;",
        "red": "background-color: #dc2626; color: white;",
        "black": "background-color: #1e293b; color: white;"
    }
    style = color_map.get(color, color_map["blue"])
    
    return f"""
    <a href="{url}" target="{target}" style="
        display: block;
        width: 100%;
        padding: 0.75rem;
        text-align: center;
        text-decoration: none;
        border-radius: 8px;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: opacity 0.2s;
        {style}
    " onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
        {text}
    </a>
    """

# ==========================================
# 2. ロジック・関数定義
# ==========================================
HTML_TEMPLATE_RAW = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[[PAGE_TITLE]]</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --main-color: [[COLOR_MAIN]];
            --sub-color: #f3f4f6;
        }
        body { font-family: 'Noto Sans JP', sans-serif; background-color: var(--sub-color); color: #1f2937; display: flex; flex-direction: column; min-height: 100vh; }
        .quiz-container-wrapper { flex-grow: 1; display: flex; justify-content: center; align-items: flex-start; padding: 2rem; }
        .quiz-container { max-width: 700px; width: 100%; padding: 2.5rem; background-color: white; border-radius: 0.75rem; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
        .question-card, .result-card { padding: 1.5rem; border: 1px solid #e5e7eb; border-radius: 0.5rem; margin-bottom: 1.5rem; }
        
        .option-button { display: block; width: 100%; text-align: left; padding: 1rem 1.25rem; margin-bottom: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.375rem; background-color: #fff; transition: all 0.2s; cursor: pointer; }
        .option-button:hover { background-color: #eff6ff; border-color: var(--main-color); color: var(--main-color); }
        .option-button.selected { background-color: #dbeafe; border-color: var(--main-color); font-weight: 600; }
        
        .next-button, .restart-button { padding: 0.85rem 2rem; border-radius: 0.375rem; font-weight: 600; transition: all 0.2s; text-align: center; display: inline-block; cursor: pointer; width: 100%; border: none; color: white; background-color: var(--main-color); }
        .next-button:disabled { background-color: #9ca3af; cursor: not-allowed; }
        .restart-button { background-color: #4b5563; margin-top: 1rem; }
        
        .progress-bar-container { width: 100%; background-color: #e5e7eb; border-radius: 99px; overflow: hidden; margin-bottom: 1.5rem; }
        .progress-bar { height: 0.5rem; background-color: var(--main-color); width: 0%; transition: width 0.3s ease-in-out; }
        
        .hidden { display: none; }
        .result-title { font-size: 1.75rem; font-weight: 700; color: var(--main-color); margin-bottom: 1rem; text-align: center; }
        .result-text { line-height: 1.8; color: #4b5563; }
        
        .flyer-link-button { background-color: var(--main-color); color: white; text-decoration: none; display: block; padding: 1rem; border-radius: 0.375rem; text-align: center; font-weight: bold; transition: transform 0.2s; }
        .flyer-link-button:hover { transform: scale(1.02); }
        
        .line-section { background-color: #f0fdf4; border: 2px solid #22c55e; border-radius: 10px; padding: 20px; margin-top: 30px; text-align: center; }
        .line-title { color: #15803d; font-weight: bold; font-size: 1.1rem; margin-bottom: 10px; }
        .line-desc { font-size: 0.9rem; color: #333; margin-bottom: 15px; }
        .line-btn { background-color: #06c755; color: white; font-weight: bold; padding: 10px 30px; border-radius: 50px; text-decoration: none; display: inline-block; }
        .line-img { max-width: 150px; margin: 10px auto; display: block; }
    </style>
</head>
<body>
    <div id="quiz-data" style="display: none;">
        <div data-container="questions">[[QUESTIONS_HTML]]</div>
        <div data-container="results">[[RESULTS_HTML]]</div>
    </div>
    <div class="quiz-container-wrapper">
        <div class="quiz-container">
            <h1 class="text-2xl font-bold text-center mb-4 text-slate-800">[[MAIN_HEADING]]</h1>
            <p class="text-center text-gray-600 mb-8">[[INTRO_TEXT]]</p>
            <div id="quiz-area"></div>
            <div id="result-area" class="hidden"></div>
        </div>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', () => {
        let questions = [], results = [], currentQuestionIndex = 0, userAnswers = [];
        const quizArea = document.getElementById('quiz-area'), resultArea = document.getElementById('result-area');
        
        function shuffle(array) {
            for (let i = array.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }
            return array;
        }

        function loadData() {
            const d = document.getElementById('quiz-data');
            questions = Array.from(d.querySelectorAll('[data-container="questions"] [data-item="question"]')).map(q => ({
                text: q.querySelector('[data-key="text"]').textContent,
                options: shuffle(Array.from(q.querySelectorAll('[data-key="option"]')).map(o => ({ text: o.textContent, points: JSON.parse(o.dataset.points||'{}') })))
            }));
            results = Array.from(d.querySelectorAll('[data-container="results"] [data-item="result"]')).map(r => ({ id: r.dataset.id, html: r.innerHTML }));
        }
        function calcResult() {
            const s = {};
            userAnswers.forEach(a => { for(const t in a) s[t]=(s[t]||0)+a[t]; });
            let max=-1, rid=null;
            for(const r of results) { if((s[r.id]||0)>max) { max=s[r.id]; rid=r.id; } }
            return results.find(r => r.id===rid);
        }
        function showResult() {
            const r = calcResult();
            quizArea.classList.add('hidden');
            if(!r) return;
            resultArea.innerHTML = `<div class="result-card">${r.html}</div><div class="mt-6 text-center"><button class="restart-button" onclick="location.reload()">もう一度診断する</button></div>`;
            resultArea.classList.remove('hidden');
        }
        function dispQ() {
            const q = questions[currentQuestionIndex];
            const pct = ((currentQuestionIndex)/questions.length)*100;
            quizArea.innerHTML = `
                <div class="progress-bar-container"><div class="progress-bar" style="width: ${pct}%"></div></div>
                <div class="question-card"><p class="text-lg font-bold mb-4 text-slate-700">Q${currentQuestionIndex+1}. ${q.text}</p>${q.options.map((o,i)=>`<button class="option-button" data-i="${i}">${o.text}</button>`).join('')}</div>
                <div class="mt-6"><button class="next-button" disabled>次の質問へ</button></div>
            `;
            const nBtn = quizArea.querySelector('.next-button');
            if(currentQuestionIndex===questions.length-1) nBtn.textContent="結果を見る";
            quizArea.querySelectorAll('.option-button').forEach(b => b.addEventListener('click', e => {
                quizArea.querySelectorAll('.option-button').forEach(btn=>btn.classList.remove('selected'));
                e.target.classList.add('selected');
                userAnswers[currentQuestionIndex] = q.options[e.target.dataset.i].points;
                nBtn.disabled=false;
            }));
            nBtn.addEventListener('click', () => { if(userAnswers[currentQuestionIndex]==null)return; (currentQuestionIndex<questions.length-1)?(currentQuestionIndex++,dispQ()):showResult(); });
        }
        function startQuiz() { currentQuestionIndex=0; userAnswers=[]; resultArea.classList.add('hidden'); quizArea.classList.remove('hidden'); dispQ(); }
        loadData(); startQuiz();
    });
    </script>
</body>
</html>"""

def generate_html_content(data):
    html = HTML_TEMPLATE_RAW
    html = html.replace("[[PAGE_TITLE]]", data.get('page_title', '診断'))
    html = html.replace("[[MAIN_HEADING]]", data.get('main_heading', 'タイトル'))
    html = html.replace("[[INTRO_TEXT]]", data.get('intro_text', ''))
    html = html.replace("[[COLOR_MAIN]]", data.get('color_main', '#2563eb'))
    
    q_html = ""
    for q in data.get('questions', []):
        o_html = ""
        for ans in q['answers']:
            pts = json.dumps({ans['type']: 1}, ensure_ascii=False).replace('"', '&quot;')
            o_html += f'<div data-key="option" data-points="{pts}">{ans["text"]}</div>'
        q_html += f'<div data-item="question"><p data-key="text">{q["question"]}</p><div data-key="options">{o_html}</div></div>'
    html = html.replace("[[QUESTIONS_HTML]]", q_html)
    
    r_html = ""
    for k, v in data.get('results', {}).items():
        b_html = ""
        if v.get('link') and v.get('btn'):
            b_html = f'<div class="mt-6 text-center"><a href="{v["link"]}" target="_blank" class="flyer-link-button">{v["btn"]} ➤</a></div>'
        
        line_html = ""
        if v.get('line_url'):
            img_tag = f'<img src="{v["line_img"]}" class="line-img">' if v.get('line_img') else ''
            line_html = f"""<div class="line-section"><p class="line-title">🎁 無料プレゼント！</p><p class="line-desc">{v.get('line_text', '公式LINE登録で詳細解説をプレゼント中！')}</p>{img_tag}<a href="{v['line_url']}" target="_blank" class="line-btn">LINEで受け取る</a></div>"""
        
        r_html += f'<div data-item="result" data-id="{k}"><h2 data-key="title">{v["title"]}</h2><p data-key="description" class="result-text">{v["desc"]}</p>{b_html}{line_html}</div>'
    
    html = html.replace("[[RESULTS_HTML]]", r_html)
    return html

def send_email(to_email, quiz_url, quiz_title):
    try:
        sender_email = st.secrets["email"]["address"]
        sender_password = st.secrets["email"]["password"]
        msg = MIMEText(f"診断URL: {quiz_url}\nタイトル: {quiz_title}")
        msg['Subject'] = "【診断クイズメーカー】URL発行のお知らせ"
        msg['From'] = sender_email
        msg['To'] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except: return False

@st.cache_resource
def init_supabase():
    if "supabase" in st.secrets:
        return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    return None

def delete_quiz(supabase, quiz_id):
    try:
        supabase.table("quizzes").delete().eq("id", quiz_id).execute()
        return True
    except: return False

def increment_views(supabase, quiz_id):
    try: supabase.rpc("increment_views", {"row_id": quiz_id}).execute()
    except: pass

def increment_likes(supabase, quiz_id):
    try:
        supabase.rpc("increment_likes", {"row_id": quiz_id}).execute()
        return True
    except: return False

# ==========================================
# 3. アプリ本編
# ==========================================
# 設定読み込み
if "stripe" in st.secrets: stripe.api_key = st.secrets["stripe"]["api_key"]
supabase = init_supabase()

def init_state(key, val):
    if key not in st.session_state: st.session_state[key] = val

init_state('ai_count', 0)
init_state('page_mode', 'home')
init_state('is_admin', False)
init_state('draft_data', None)

AI_LIMIT = 5

query_params = st.query_params
quiz_id = query_params.get("id", None)
session_id = query_params.get("session_id", None)

# --- 管理者判定 ---
if query_params.get("admin") == "secret":
    st.session_state.is_admin = True
    st.toast("🔓 管理者モード")

# --- 🅰️ プレイ画面 ---
if quiz_id:
    apply_portal_style()
    if not supabase: st.stop()
    try:
        if f"viewed_{quiz_id}" not in st.session_state:
            increment_views(supabase, quiz_id)
            st.session_state[f"viewed_{quiz_id}"] = True

        res = supabase.table("quizzes").select("*").eq("id", quiz_id).execute()
        if not res.data:
            st.error("診断が見つかりません。")
            st.markdown(get_custom_button_html("/", "🏠 トップページに戻る", "blue"), unsafe_allow_html=True)
            st.stop()
        
        data = res.data[0]['content']
        html_content = generate_html_content(data)
        components.html(html_content, height=800, scrolling=True)
        
        c_like, c_back = st.columns([1, 1])
        with c_like:
            liked_key = f"liked_{quiz_id}"
            if st.session_state.get(liked_key, False):
                st.button("❤️ いいね済み", disabled=True, use_container_width=True)
            else:
                if st.button("🤍 この診断に「いいね」する", type="secondary", use_container_width=True):
                    increment_likes(supabase, quiz_id)
                    st.session_state[liked_key] = True
                    st.balloons()
                    st.rerun()
        with c_back:
            st.markdown(get_custom_button_html("/", "🏠 ポータルトップへ戻る", "blue", target="_self"), unsafe_allow_html=True)

    except Exception as e: st.error(e)

# --- 🅱️ 決済完了画面 ---
elif session_id:
    apply_portal_style()
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            paid_id = session.metadata.get('quiz_id')
            res = supabase.table("quizzes").select("*").eq("id", paid_id).execute()
            if res.data:
                data = res.data[0]['content']
                st.balloons()
                st.success("✅ お支払いが完了しました！")
                final_html = generate_html_content(data)
                st.download_button("📥 HTMLをダウンロード", final_html, "diagnosis.html", "text/html", type="primary")
                st.markdown(get_custom_button_html("/", "トップページに戻る", "blue", target="_self"), unsafe_allow_html=True)
                st.stop()
    except Exception as e: st.error(f"決済エラー: {e}")

# --- 🆑 ポータル & 作成画面 ---
else:
    if st.session_state.page_mode == 'home':
        apply_portal_style()
        c1, c2 = st.columns([1, 2])
        with c1: st.markdown("### 💎 診断クイズメーカー")
        with c2: st.text_input("search", label_visibility="collapsed", placeholder="🔍 キーワード検索...")
        st.write("") 
        st.markdown(HERO_HTML, unsafe_allow_html=True)
        st.markdown('<div class="big-create-btn">', unsafe_allow_html=True)
        if st.button("✨ 新しい診断を作成する", type="primary", use_container_width=True):
            st.session_state.page_mode = 'create'; st.rerun()
        st.markdown('</div><br>', unsafe_allow_html=True)
        st.markdown("### 📚 新着の診断")
        if supabase:
            res = supabase.table("quizzes").select("*").eq("is_public", True).order("created_at", desc=True).limit(15).execute()
            if res.data:
                cols = st.columns(3)
                for i, q in enumerate(res.data):
                    with cols[i % 3]:
                        content = q.get('content', {})
                        keyword = content.get('image_keyword', 'abstract')
                        seed = q['id'][-4:] 
                        img_url = f"https://image.pollinations.ai/prompt/{keyword}%20{seed}?width=350&height=180&nologo=true"
                        base = "https://shindan-quiz-maker.streamlit.app"
                        link_url = f"{base}/?id={q['id']}"
                        views = q.get('views', 0); likes = q.get('likes', 0)
                        with st.container(border=True):
                            st.markdown(get_card_content_html(q.get('title','無題'), content.get('intro_text',''), img_url, views, likes), unsafe_allow_html=True)
                            st.markdown(get_custom_button_html(link_url, "▶ 今すぐ診断する", "green"), unsafe_allow_html=True)
                            if st.session_state.is_admin:
                                st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                                if st.button("🗑️ 削除", key=f"del_{q['id']}"):
                                    if delete_quiz(supabase, q['id']): st.toast("削除しました"); time.sleep(1); st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                        st.write("") 
            else: st.info("まだ投稿がありません")

    elif st.session_state.page_mode == 'create':
        apply_editor_style()
        if st.button("← ポータルへ戻る"):
            st.session_state.page_mode = 'home'; st.rerun()
        st.title("📝 診断作成エディタ")
        
        with st.sidebar:
            if "OPENAI_API_KEY" in st.secrets: api_key = st.secrets["OPENAI_API_KEY"]
            else: st.error("APIキー設定なし"); st.stop()
            st.header("🧠 AIアシスタント")
            theme_placeholder = """【良い診断を作るヒント】\n1. ターゲット：誰向け？ (例: 30代婚活女性)\n2. テーマ：何を診断？ (例: 隠れた才能)\n3. トーン：辛口？優しく？\n\n(例)\n30代起業家向けに、向いているビジネスモデルを辛口で診断して。"""
            theme = st.text_area("テーマ・詳細設定", height=300, placeholder=theme_placeholder)
            st.caption("※AIの文章作成には10秒〜30秒ほどかかります。")
            
            if st.button("AIで構成案を作成", type="primary"):
                if not theme: st.warning("テーマを入力してください")
                else:
                    try:
                        msg = st.empty(); msg.info("AIが執筆中...")
                        client = openai.OpenAI(api_key=api_key)
                        prompt = f"""
                        あなたはプロの診断作家です。テーマ: {theme}
                        【絶対厳守】1.質問5問 2.選択肢4つ 3.結果3つ 4.JSONのみ
                        出力JSON: {{
                            "page_title": "", "main_heading": "", "intro_text": "", "image_keyword": "英単語1語",
                            "results": {{ "A": {{ "title": "", "desc": "600字", "btn": "", "link":"" }}, "B": {{...}}, "C": {{...}} }},
                            "questions": [ {{ "question": "", "answers": [ {{ "text": "", "type": "A" }}, {{ "text": "", "type": "B" }}, {{ "text": "", "type": "C" }}, {{ "text": "", "type": "A" }} ] }} ]
                        }}
                        """
                        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"system","content":"Output JSON only"}, {"role":"user","content":prompt}], response_format={"type":"json_object"})
                        data = json.loads(res.choices[0].message.content)
                        st.session_state['page_title'] = data.get('page_title','')
                        st.session_state['main_heading'] = data.get('main_heading','')
                        st.session_state['intro_text'] = data.get('intro_text','')
                        st.session_state['image_keyword'] = data.get('image_keyword', 'random')
                        if 'results' in data:
                            for t in ['A','B','C']:
                                if t in data['results']:
                                    r = data['results'][t]
                                    st.session_state[f'res_title_{t}'] = r.get('title','')
                                    st.session_state[f'res_desc_{t}'] = r.get('desc','')
                                    st.session_state[f'res_btn_{t}'] = r.get('btn','')
                                    st.session_state[f'res_link_{t}'] = r.get('link','')
                        if 'questions' in data:
                            for i,q in enumerate(data['questions']):
                                if i>=5: break
                                st.session_state[f'q_text_{i+1}'] = q.get('question','')
                                for j,a in enumerate(q.get('answers',[])):
                                    if j>=4: break
                                    st.session_state[f'q{i+1}_a{j+1}_text'] = a.get('text','')
                                    st.session_state[f'q{i+1}_a{j+1}_type'] = a.get('type','A')
                        msg.success("完了！"); time.sleep(0.5); st.rerun()
                    except Exception as e: st.error(e)

        init_state('page_title',''); init_state('main_heading',''); init_state('intro_text',''); init_state('image_keyword',''); init_state('color_main', '#2563eb')
        
        with st.form("editor"):
            st.subheader("1. 基本設定")
            c1, c2 = st.columns(2)
            with c1: page_title = st.text_input("タブ名", key='page_title')
            with c2: main_heading = st.text_input("タイトル", key='main_heading')
            intro_text = st.text_area("導入文", key='intro_text')
            image_keyword = st.text_input("ポータル掲載用画像テーマ (英単語)", key='image_keyword', help="例: business, cat, space")
            st.markdown("---"); st.subheader("2. デザイン設定")
            color_main = st.color_picker("メインカラー", key="color_main")
            st.markdown("---"); st.subheader("3. 結果ページ設定")
            res_obj = {}; tabs = st.tabs(["Type A", "Type B", "Type C"])
            for i,t in enumerate(['A','B','C']):
                init_state(f'res_title_{t}',''); init_state(f'res_desc_{t}',''); init_state(f'res_btn_{t}',''); init_state(f'res_link_{t}','')
                init_state(f'res_line_url_{t}',''); init_state(f'res_line_text_{t}',''); init_state(f'res_line_img_{t}','')
                with tabs[i]:
                    rt = st.text_input("結果名", key=f'res_title_{t}')
                    rd = st.text_area("説明文", key=f'res_desc_{t}', height=200)
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1: rb = st.text_input("ボタン名", key=f'res_btn_{t}')
                    with c_btn2: rl = st.text_input("URL", key=f'res_link_{t}')
                    with st.expander("🟩 LINE登録誘導を追加"):
                        line_u = st.text_input("LINE URL", key=f'res_line_url_{t}')
                        line_t = st.text_area("誘導文", key=f'res_line_text_{t}')
                        line_i = st.text_input("画像URL", key=f'res_line_img_{t}')
                    res_obj[t] = {'title':rt, 'desc':rd, 'btn':rb, 'link':rl, 'line_url':line_u, 'line_text':line_t, 'line_img':line_i}
            st.markdown("---"); st.subheader("4. 質問設定")
            q_obj = []
            for q in range(1,6):
                init_state(f'q_text_{q}','')
                with st.expander(f"Q{q}", expanded=(q==1)):
                    qt = st.text_input("質問文", key=f'q_text_{q}')
                    st.markdown("##### 選択肢")
                    ans_list = []
                    for a in range(1,5):
                        init_state(f'q{q}_a{a}_text',''); init_state(f'q{q}_a{a}_type','A')
                        c_opt1, c_opt2 = st.columns([3, 1])
                        with c_opt1: at = st.text_input(f"選択{a}", key=f'q{q}_a{a}_text')
                        with c_opt2: aty = st.selectbox("加点", ["A","B","C"], key=f'q{q}_a{a}_type', label_visibility="visible")
                        ans_list.append({'text':at, 'type':aty})
                    if qt: q_obj.append({'question':qt, 'answers':ans_list})
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("次へ：公開設定に進む", type="primary", use_container_width=True)

        if submitted:
            st.session_state.draft_data = {'page_title':page_title, 'main_heading':main_heading, 'intro_text':intro_text, 'image_keyword':image_keyword, 'color_main':color_main, 'results':res_obj, 'questions':q_obj}
        
        if st.session_state.draft_data:
            st.markdown("---"); st.subheader("5. 公開・販売設定")
            st.write("#### 💰 購入価格の設定")
            price = st.number_input("価格 (円)", 980, 98000, 980, 100)
            st.info("URL送付用メールアドレス (必須)")
            email = st.text_input("Email", placeholder="mail@example.com", label_visibility="collapsed")
            st.markdown("---"); st.subheader("📤 公開方法を選択")
            st.markdown("**① URL発行 (無料)**"); st.caption("※ポータルサイトに自動掲載されます。")
            sub_free = st.button("🌐 無料でWeb公開する", type="primary", use_container_width=True)
            st.write("")
            st.markdown("**② ファイルダウンロード (有料)**"); st.caption("※HTMLファイルをダウンロードします。")
            is_pub = st.checkbox("ポータルサイトにも掲載する", value=False)
            sub_paid = st.button(f"💾 {price}円で購入してダウンロード", use_container_width=True)
            
            if sub_free or sub_paid:
                draft = st.session_state.draft_data
                if not email: st.error("Emailを入力してください")
                elif not draft['questions']: st.error("質問データがありません")
                else:
                    try:
                        is_p = True if sub_free else is_pub
                        res = supabase.table("quizzes").insert({"email":email, "title":draft['main_heading'], "content":draft, "is_public":is_p, "price":price}).execute()
                        new_id = res.data[0]['id']
                        base = "https://shindan-quiz-maker.streamlit.app"
                        if sub_free:
                            if send_email(email, f"{base}/?id={new_id}", draft['main_heading']):
                                st.success("公開しました！メールを確認してください"); st.balloons(); time.sleep(2); st.session_state.draft_data = None; st.session_state.page_mode='home'; st.rerun()
                            else: st.error("メール送信失敗")
                        if sub_paid:
                            sess = stripe.checkout.Session.create(payment_method_types=['card'], line_items=[{'price_data':{'currency':'jpy','product_data':{'name':f"{draft['main_heading']}"},'unit_amount':price},'quantity':1}], mode='payment', success_url=f"{base}/?session_id={{CHECKOUT_SESSION_ID}}", cancel_url=f"{base}/", metadata={'quiz_id':new_id})
                            st.link_button("決済へ進む", sess.url, type="primary")
                    except Exception as e: st.error(f"保存エラー: {e}")
