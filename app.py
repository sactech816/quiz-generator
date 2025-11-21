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

# ページ設定 (アイコン変更)
st.set_page_config(page_title="診断作成ツール", page_icon="📝", layout="wide")

# ==========================================
# 🎨 エディタ用デザインCSS (Pro版再現)
# ==========================================
st.markdown("""
    <style>
    /* 全体: Pro版のような白背景とフォント */
    .stApp {
        background-color: #f9fafb;
        color: #111827;
        font-family: 'Inter', sans-serif;
    }
    
    /* コンテンツ幅 */
    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 5rem;
        margin: 0 auto;
    }
    
    /* カード風コンテナ (st.container(border=True) のスタイル上書き) */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    
    /* 見出し */
    h1, h2, h3 {
        font-weight: 700 !important;
        color: #111827 !important;
    }
    h2 { font-size: 1.5rem !important; margin-bottom: 1rem !important; }
    h3 { font-size: 1.1rem !important; margin-top: 0 !important; }
    
    /* 入力フォーム */
    .stTextInput input, .stTextArea textarea {
        background-color: #fff;
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
        color: #374151;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
    }
    
    /* ボタン (Pro版の色使いを再現) */
    .stButton button {
        background-color: white;
        color: #374151;
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background-color: #f3f4f6;
        border-color: #9ca3af;
    }
    /* プライマリボタン (青) */
    .stButton button[kind="primary"] {
        background-color: #2563eb;
        color: white;
        border: none;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #1d4ed8;
    }
    
    /* エクスパンダー (質問などの開閉) */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-radius: 0.375rem;
        border: 1px solid #e2e8f0;
        font-weight: 600;
        color: #475569;
    }
    
    /* ヘッダー隠し */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- テンプレート定義 ---
HTML_TEMPLATE_RAW = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[[PAGE_TITLE]]</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Noto Sans JP', sans-serif; background-color: #f3f4f6; color: #1f2937; display: flex; flex-direction: column; min-height: 100vh; }
        .quiz-container-wrapper { flex-grow: 1; display: flex; justify-content: center; align-items: flex-start; padding: 2rem; }
        .quiz-container { max-width: 700px; width: 100%; padding: 2.5rem; background-color: white; border-radius: 0.75rem; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
        .question-card, .result-card { padding: 1.5rem; border: 1px solid #e5e7eb; border-radius: 0.5rem; margin-bottom: 1.5rem; }
        .option-button { display: block; width: 100%; text-align: left; padding: 1rem 1.25rem; margin-bottom: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.375rem; background-color: #f9fafb; transition: all 0.2s; cursor: pointer; }
        .option-button:hover { background-color: #eff6ff; border-color: #3b82f6; }
        .option-button.selected { background-color: #dbeafe; border-color: #3b82f6; font-weight: 600; }
        .next-button, .restart-button { padding: 0.85rem 2rem; border-radius: 0.375rem; font-weight: 600; transition: all 0.2s; text-align: center; display: inline-block; cursor: pointer; width: 100%; }
        .next-button { background-color: #2563eb; color: white; border: none; }
        .next-button:hover { background-color: #1d4ed8; }
        .next-button:disabled { background-color: #9ca3af; cursor: not-allowed; }
        .restart-button { background-color: #4b5563; color: white; margin-top: 1rem; border: none; }
        .progress-bar-container { width: 100%; background-color: #e5e7eb; border-radius: 99px; overflow: hidden; margin-bottom: 1.5rem; }
        .progress-bar { height: 0.5rem; background-color: #2563eb; width: 0%; transition: width 0.3s ease-in-out; }
        .hidden { display: none; }
        .result-title { font-size: 1.75rem; font-weight: 700; color: #1e3a8a; margin-bottom: 1rem; text-align: center; }
        .result-text { line-height: 1.8; color: #4b5563; }
        .flyer-link-button { background-color: #059669; color: white; text-decoration: none; display: block; padding: 1rem; border-radius: 0.375rem; text-align: center; font-weight: bold; transition: transform 0.2s; }
        .flyer-link-button:hover { transform: scale(1.02); }
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
        function loadData() {
            const d = document.getElementById('quiz-data');
            questions = Array.from(d.querySelectorAll('[data-container="questions"] [data-item="question"]')).map(q => ({
                text: q.querySelector('[data-key="text"]').textContent,
                options: Array.from(q.querySelectorAll('[data-key="option"]')).map(o => ({ text: o.textContent, points: JSON.parse(o.dataset.points||'{}') }))
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
            resultArea.innerHTML = `<div class="result-card">${r.html}</div><div class="mt-6 text-center"><button class="restart-button">もう一度診断する</button></div>`;
            resultArea.classList.remove('hidden');
            resultArea.querySelector('.restart-button').addEventListener('click', startQuiz);
        }
        function dispQ() {
            const q = questions[currentQuestionIndex];
            const pct = ((currentQuestionIndex)/questions.length)*100;
            quizArea.innerHTML = `
                <div class="progress-bar-container"><div class="progress-bar" style="width: ${pct}%"></div></div>
                <div class="question-card"><p class="text-lg font-bold mb-4 text-slate-700">Q${currentQuestionIndex+1}. ${q.text}</p>${q.options.map((o,i)=>`<button class="option-button" data-index="${i}">${o.text}</button>`).join('')}</div>
                <div class="mt-6"><button class="next-button" disabled>次の質問へ</button></div>
            `;
            const nBtn = quizArea.querySelector('.next-button');
            if(currentQuestionIndex===questions.length-1) nBtn.textContent="結果を見る";
            quizArea.querySelectorAll('.option-button').forEach(b => b.addEventListener('click', e => {
                quizArea.querySelectorAll('.option-button').forEach(btn=>btn.classList.remove('selected'));
                e.target.classList.add('selected');
                userAnswers[currentQuestionIndex] = q.options[e.target.dataset.index].points;
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

# --- ヘルパー関数 ---
def generate_html_content(data):
    html = HTML_TEMPLATE_RAW
    html = html.replace("[[PAGE_TITLE]]", data.get('page_title', '診断'))
    html = html.replace("[[MAIN_HEADING]]", data.get('main_heading', 'タイトル'))
    html = html.replace("[[INTRO_TEXT]]", data.get('intro_text', ''))
    
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
        r_html += f'<div data-item="result" data-id="{k}"><h2 data-key="title">{v["title"]}</h2><p data-key="description" class="result-text">{v["desc"]}</p>{b_html}</div>'
    html = html.replace("[[RESULTS_HTML]]", r_html)
    return html

# --- 設定読み込み ---
if "stripe" in st.secrets: stripe.api_key = st.secrets["stripe"]["api_key"]
@st.cache_resource
def init_supabase():
    if "supabase" in st.secrets: return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    return None
supabase = init_supabase()

def init_state(key, val):
    if key not in st.session_state: st.session_state[key] = val

init_state('ai_count', 0)
init_state('page_mode', 'home')
AI_LIMIT = 5

# --- メール送信 ---
def send_email(to_email, quiz_url, quiz_title):
    try:
        sender_email = st.secrets["email"]["address"]
        sender_password = st.secrets["email"]["password"]
        msg = MIMEText(f"タイトル: {quiz_title}\nURL: {quiz_url}\n\n作成ありがとうございます！")
        msg['Subject'] = "【診断メーカー】URLをお届けします"
        msg['From'] = sender_email
        msg['To'] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except: return False

# ==========================================
# メイン処理
# ==========================================
query_params = st.query_params
quiz_id = query_params.get("id", None)
session_id = query_params.get("session_id", None)

# --- 🅰️ プレイ画面 ---
if quiz_id:
    if not supabase: st.stop()
    try:
        res = supabase.table("quizzes").select("*").eq("id", quiz_id).execute()
        if not res.data:
            st.error("診断が見つかりません。")
            if st.button("トップへ戻る"): st.query_params.clear(); st.rerun()
            st.stop()
        
        data = res.data[0]['content']
        html_content = generate_html_content(data)
        components.html(html_content, height=800, scrolling=True)
        
        if st.button("ポータルトップへ戻る"): st.query_params.clear(); st.rerun()
    except Exception as e: st.error(e)

# --- 🅱️ 決済完了画面 ---
elif session_id:
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
                if st.button("トップに戻る"): st.query_params.clear(); st.rerun()
                st.stop()
    except Exception as e: st.error(f"決済エラー: {e}")

# --- 🆑 ポータル & 作成画面 ---
else:
    if st.session_state.page_mode == 'home':
        st.markdown("""
        <div style="text-align: center; margin: 40px 0;">
            <h1 style="color: #2563eb; font-size: 3rem; font-weight: 800;">Diagnosis Portal 🚀</h1>
            <p style="color: #4b5563; margin-top: 10px;">1時間で作る！あなただけの診断コンテンツ</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("✨ 新しい診断を作成する", type="primary", use_container_width=True):
                st.session_state.page_mode = 'create'; st.rerun()
        
        st.markdown("### 📚 新着ギャラリー")
        if supabase:
            res = supabase.table("quizzes").select("*").eq("is_public", True).order("created_at", desc=True).limit(12).execute()
            if res.data:
                cols = st.columns(3)
                for i, q in enumerate(res.data):
                    with cols[i%3]:
                        with st.container(border=True):
                            st.write(f"**{q.get('title','無題')}**")
                            base = "https://shindan-quiz-maker.streamlit.app"
                            st.link_button("▶ 遊んでみる", f"{base}/?id={q['id']}", use_container_width=True)

    elif st.session_state.page_mode == 'create':
        if st.button("← ポータルへ戻る"):
            st.session_state.page_mode = 'home'; st.rerun()
            
        st.markdown("<h2 style='text-align:center; margin-bottom:20px;'>📝 診断作成エディタ</h2>", unsafe_allow_html=True)
        
        # AIアシスタント
        with st.container(border=True):
            st.markdown("### 🧠 AIアシスタント (自動生成)")
            with st.sidebar: # スマホで見やすいようにAI設定はサイドバーに残すか、ここに持ってくるか
                pass # 今回はメインエリアに統合
            
            if "OPENAI_API_KEY" in st.secrets: api_key = st.secrets["OPENAI_API_KEY"]
            else: st.error("APIキー設定なし"); st.stop()
            
            c_ai1, c_ai2 = st.columns([3, 1])
            with c_ai1:
                theme = st.text_input("どんな診断を作りますか？", placeholder="例：30代女性向けの辛口婚活診断")
            with c_ai2:
                st.write("") # Spacer
                st.write("")
                if st.button("AIで構成案を作成 ⚡", type="primary"):
                    try:
                        msg = st.empty(); msg.info("思考中...")
                        client = openai.OpenAI(api_key=api_key)
                        prompt = f"""テーマ:{theme}。JSONのみ出力。format: {{ "page_title":"", "main_heading":"", "intro_text":"", "results":{{"A":{{"title":"","desc":"","btn":"","link":""}},"B":{{...}},"C":{{...}}}}, "questions":[ {{"question":"", "answers":[ {{"text":"","type":"A"}}, {{"text":"","type":"B"}}, {{"text":"","type":"C"}}, {{"text":"","type":"A"}} ]}} ] (5問) }}"""
                        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"system","content":"Output JSON only"},{"role":"user","content":prompt}], response_format={"type":"json_object"})
                        data = json.loads(res.choices[0].message.content)
                        st.session_state['page_title'] = data.get('page_title','')
                        st.session_state['main_heading'] = data.get('main_heading','')
                        st.session_state['intro_text'] = data.get('intro_text','')
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
                                st.session_state[f'q_text_{i+1}'] = q.get('question','')
                                for j,a in enumerate(q.get('answers',[])):
                                    st.session_state[f'q{i+1}_a{j+1}_text'] = a.get('text','')
                                    st.session_state[f'q{i+1}_a{j+1}_type'] = a.get('type','A')
                        msg.success("完了！"); time.sleep(0.5); st.rerun()
                    except Exception as e: st.error(e)

        # 編集フォーム
        init_state('page_title',''); init_state('main_heading',''); init_state('intro_text','')
        
        # 1. 基本設定
        with st.container(border=True):
            st.subheader("1. 基本設定")
            col1, col2 = st.columns(2)
            with col1: page_title = st.text_input("タブ名 (ページタイトル)", key='page_title')
            with col2: main_heading = st.text_input("診断タイトル (大見出し)", key='main_heading')
            intro_text = st.text_area("導入文", key='intro_text')

        # 2. 結果設定
        with st.container(border=True):
            st.subheader("2. 結果パターン (A / B / C)")
            res_obj = {}
            tabs = st.tabs(["Type A", "Type B", "Type C"])
            for i,t in enumerate(['A','B','C']):
                init_state(f'res_title_{t}',''); init_state(f'res_desc_{t}',''); init_state(f'res_btn_{t}',''); init_state(f'res_link_{t}','')
                with tabs[i]:
                    rt = st.text_input("結果タイプ名", key=f'res_title_{t}')
                    rd = st.text_area("詳細説明", key=f'res_desc_{t}')
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1: rb = st.text_input("ボタン文字", key=f'res_btn_{t}')
                    with c_btn2: rl = st.text_input("リンクURL", key=f'res_link_{t}')
                    res_obj[t] = {'title':rt, 'desc':rd, 'btn':rb, 'link':rl}

        # 3. 質問設定
        with st.container(border=True):
            st.subheader("3. 質問設定 (5問)")
            q_obj = []
            for q in range(1,6):
                init_state(f'q_text_{q}','')
                with st.expander(f"Q{q}. 質問内容を編集"):
                    qt = st.text_input("質問文", key=f'q_text_{q}')
                    ans_list = []
                    for a in range(1,5):
                        init_state(f'q{q}_a{a}_text',''); init_state(f'q{q}_a{a}_type','A')
                        c1, c2 = st.columns([3,1])
                        with c1: at = st.text_input(f"選択肢{a}", key=f'q{q}_a{a}_text')
                        with c2: aty = st.selectbox("加点", ["A","B","C"], key=f'q{q}_a{a}_type')
                        ans_list.append({'text':at, 'type':aty})
                    if qt: q_obj.append({'question':qt, 'answers':ans_list})

        # 4. 公開設定
        with st.container(border=True):
            st.subheader("4. 公開・ダウンロード")
            email = st.text_input("受取用メールアドレス (必須)", placeholder="mail@example.com")
            
            st.write("")
            c1, c2 = st.columns(2)
            with c1:
                st.info("無料でWeb公開し、URLを発行します。")
                sub_free = st.form_submit_button("🌐 公開する (無料)", type="primary")
            with c2:
                st.warning("HTMLファイルをダウンロードします（有料）。")
                is_pub = st.checkbox("ポータルにも掲載する", value=False)
                sub_paid = st.form_submit_button("💾 購入してDL (980円)")

        # 保存処理
        if sub_free or sub_paid:
            if not email: st.error("メールアドレスを入力してください")
            elif not q_obj: st.error("質問が入力されていません")
            else:
                s_data = {'page_title':page_title, 'main_heading':main_heading, 'intro_text':intro_text, 'results':res_obj, 'questions':q_obj}
                try:
                    is_p = True if sub_free else is_pub
                    res = supabase.table("quizzes").insert({"email":email, "title":main_heading, "content":s_data, "is_public":is_p}).execute()
                    new_id = res.data[0]['id']
                    base = "https://shindan-quiz-maker.streamlit.app"
                    
                    if sub_free:
                        if send_email(email, f"{base}/?id={new_id}", main_heading):
                            st.success("公開しました！メールを確認してください")
                            st.balloons(); time.sleep(2); st.session_state.page_mode='home'; st.rerun()
                        else: st.error("メール送信失敗")
                    
                    if sub_paid:
                        sess = stripe.checkout.Session.create(
                            payment_method_types=['card'],
                            line_items=[{'price_data':{'currency':'jpy','product_data':{'name':'診断データ'},'unit_amount':980},'quantity':1}],
                            mode='payment',
                            success_url=f"{base}/?session_id={{CHECKOUT_SESSION_ID}}",
                            cancel_url=f"{base}/",
                            metadata={'quiz_id':new_id}
                        )
                        st.link_button("決済へ進む", sess.url, type="primary")
                except Exception as e: st.error(e)
