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

# ==========================================
# 1. デザイン定義 (CSS)
# ==========================================
def apply_portal_style():
    """ポータル画面・プレイ画面用の白ベースデザイン"""
    st.markdown("""
        <style>
        /* 全体: 白背景 */
        .stApp { background-color: #ffffff !important; color: #333333 !important; }
        
        /* コンテンツ幅調整 */
        .block-container { max-width: 1000px; padding-top: 1rem; padding-bottom: 5rem; }
        
        /* ヘッダー・フッター隠し */
        #MainMenu, footer, header {visibility: hidden;}
        
        /* ヒーローセクション */
        .hero-container {
            background: white; border-radius: 24px; padding: 3rem; margin-bottom: 2rem;
            box-shadow: 0 20px 40px -10px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;
            position: relative; overflow: hidden;
        }
        .hero-orb {
            position: absolute; width: 300px; height: 300px;
            background: radial-gradient(circle, rgba(59,130,246,0.2) 0%, rgba(255,255,255,0) 70%);
            top: -100px; right: -100px; border-radius: 50%; z-index: 0;
        }
        .hero-content { position: relative; z-index: 1; }

        /* カードデザイン */
        .quiz-card {
            background: white; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); height: 100%; transition: 0.2s;
            display: flex; flex-direction: column;
        }
        .quiz-card:hover { transform: translateY(-3px); border-color: #3b82f6; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
        .quiz-thumb { width: 100%; height: 140px; object-fit: cover; background-color: #f1f5f9; }
        .quiz-content { padding: 15px; flex-grow: 1; }
        .quiz-title { font-weight: bold; font-size: 1.1rem; margin-bottom: 5px; color: #1e293b; line-height: 1.4; }
        .quiz-desc { font-size: 0.85rem; color: #64748b; margin-bottom: 10px; height: 40px; overflow: hidden; }
        
        /* バッジ */
        .badge { display: inline-block; padding: 4px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; margin-bottom: 8px; }
        .badge-new { background: #dbeafe; color: #1e40af; }

        /* ボタン */
        .stButton button {
            background-color: #f8fafc; border: 1px solid #cbd5e1; color: #334155;
            border-radius: 8px; font-weight: bold; padding: 0.6rem 1rem; transition: all 0.2s; width: 100%;
        }
        .stButton button:hover { border-color: #3b82f6; color: #2563eb; background-color: #eff6ff; }
        .stButton button[kind="primary"] { background-color: #2563eb; color: white; border: none; }
        .stButton button[kind="primary"]:hover { background-color: #1d4ed8; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); }
        </style>
    """, unsafe_allow_html=True)

def apply_editor_style():
    """作成エディタ用のスタイル（Streamlit標準ダークモードを生かす）"""
    st.markdown("""
        <style>
        #MainMenu, footer, header {visibility: hidden;}
        .block-container { padding-top: 2rem; padding-bottom: 5rem; }
        .stTextInput input, .stTextArea textarea { font-family: "Inter", sans-serif; }
        </style>
    """, unsafe_allow_html=True)

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
    except:
        return False

# --- 初期設定 ---
if "stripe" in st.secrets: stripe.api_key = st.secrets["stripe"]["api_key"]
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

# ==========================================
# メイン処理
# ==========================================
query_params = st.query_params
quiz_id = query_params.get("id", None)
session_id = query_params.get("session_id", None)

# --- 🅰️ プレイ画面 ---
if quiz_id:
    apply_portal_style()
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
        
        st.markdown('<div style="text-align:center;margin-top:20px;">', unsafe_allow_html=True)
        if st.button("🏠 ポータルトップへ戻る"):
            st.query_params.clear()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
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
                if st.button("トップに戻る"): st.query_params.clear(); st.rerun()
                st.stop()
    except Exception as e: st.error(f"決済エラー: {e}")

# --- 🆑 ポータル & 作成画面 ---
else:
    if st.session_state.page_mode == 'home':
        apply_portal_style()
        
        # ナビゲーション
        c_logo, c_search, c_login = st.columns([2, 4, 2])
        with c_logo: st.markdown("### 💎 Diagnosis Portal")
        with c_search: st.text_input("🔍", label_visibility="collapsed", placeholder="キーワード検索...")
        with c_login:
            if st.button("＋ 作成する", type="primary", use_container_width=True):
                st.session_state.page_mode = 'create'; st.rerun()

        # ヒーロー
        st.markdown("""
        <div class="hero-container">
            <div class="hero-orb"></div>
            <div class="hero-content">
                <h1 style="font-size: 2.5rem; font-weight: 900; color: #1e293b; margin-bottom: 10px;">
                    あなたのビジネスを加速する<br>
                    <span style="background: linear-gradient(to right, #2563eb, #9333ea); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">診断コンテンツ</span>を作ろう。
                </h1>
                <p style="color: #64748b;">AIがたった1分で構成案を作成。集客・販促に使える高品質な診断ツールを今すぐ公開。</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # ギャラリー
        st.markdown("### 📚 新着の診断")
        if supabase:
            res = supabase.table("quizzes").select("*").eq("is_public", True).order("created_at", desc=True).limit(12).execute()
            if res.data:
                cols = st.columns(3)
                for i, q in enumerate(res.data):
                    with cols[i % 3]:
                        content = q.get('content', {})
                        keyword = content.get('image_keyword', 'abstract')
                        img_url = f"https://image.pollinations.ai/prompt/{keyword}?width=400&height=250&nologo=true"
                        
                        st.markdown(f"""
                        <div class="quiz-card">
                            <img src="{img_url}" class="quiz-thumb" loading="lazy">
                            <div class="quiz-content">
                                <span class="badge badge-new">NEW</span>
                                <div class="quiz-title">{q.get('title','無題')}</div>
                                <div class="quiz-desc">{content.get('intro_text','')[:40]}...</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        base = "https://shindan-quiz-maker.streamlit.app"
                        st.link_button("▶ 今すぐ診断する", f"{base}/?id={q['id']}", use_container_width=True)
                        st.write("") 
            else:
                st.info("まだ投稿がありません")

    elif st.session_state.page_mode == 'create':
        apply_editor_style()
        
        if st.button("← ポータルへ戻る"):
            st.session_state.page_mode = 'home'; st.rerun()
            
        st.title("📝 診断作成エディタ")
        
        with st.sidebar:
            if "OPENAI_API_KEY" in st.secrets: api_key = st.secrets["OPENAI_API_KEY"]
            else: st.error("APIキー設定なし"); st.stop()
            
            st.header("🧠 AIアシスタント")
            remaining = AI_LIMIT - st.session_state.ai_count
            if remaining > 0: st.caption(f"残り生成回数: {remaining} 回")
            theme = st.text_area("テーマ", "例：30代女性向けの辛口婚活診断")
            
            if st.button("AIで構成案を作成", type="primary", disabled=(remaining <= 0)):
                try:
                    msg = st.empty(); msg.info("AIが詳細な診断結果を執筆中...")
                    client = openai.OpenAI(api_key=api_key)
                    
                    prompt = f"""
                    あなたはプロの占い師兼キャリアコンサルタントです。テーマ: {theme}
                    以下のJSON形式で出力してください。
                    {{
                        "page_title": "タイトル", "main_heading": "大見出し", "intro_text": "導入文",
                        "image_keyword": "英単語1語(例: business)",
                        "results": {{
                            "A": {{ "title": "タイプA名", "desc": "詳細な解説(600文字程度)", "btn": "ボタン", "link":"" }},
                            "B": {{ "title": "タイプB名", "desc": "詳細な解説(600文字程度)", "btn": "ボタン", "link":"" }},
                            "C": {{ "title": "タイプC名", "desc": "詳細な解説(600文字程度)", "btn": "ボタン", "link":"" }}
                        }},
                        "questions": [
                            {{ "question": "質問文", "answers": [ {{ "text": "...", "type": "A" }}, {{ "text": "...", "type": "B" }}, {{ "text": "...", "type": "C" }}, {{ "text": "...", "type": "A" }} ] }}
                        ]
                    }}
                    質問は5問。JSONのみ出力。
                    """
                    
                    res = client.chat.completions.create(
                        model="gpt-4o-mini", 
                        messages=[{"role":"system","content":"Output JSON only"}, {"role":"user","content":prompt}], 
                        response_format={"type":"json_object"}
                    )
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
                            st.session_state[f'q_text_{i+1}'] = q.get('question','')
                            for j,a in enumerate(q.get('answers',[])):
                                st.session_state[f'q{i+1}_a{j+1}_text'] = a.get('text','')
                                st.session_state[f'q{i+1}_a{j+1}_type'] = a.get('type','A')
                    
                    st.session_state.ai_count += 1
                    msg.success("完了！"); time.sleep(0.5); st.rerun()
                except Exception as e: st.error(e)

        # 編集フォーム
        init_state('page_title',''); init_state('main_heading',''); init_state('intro_text',''); init_state('image_keyword','')
        
        with st.form("editor"):
            st.subheader("基本情報")
            page_title = st.text_input("タブ名", key='page_title')
            main_heading = st.text_input("タイトル", key='main_heading')
            intro_text = st.text_area("導入文", key='intro_text')
            image_keyword = st.text_input("サムネイル用英単語", key='image_keyword', help="AIがこの単語から画像を生成します")
            
            st.markdown("---")
            st.subheader("結果設定")
            res_obj = {}
            tabs = st.tabs(["Type A", "Type B", "Type C"])
            for i,t in enumerate(['A','B','C']):
                init_state(f'res_title_{t}',''); init_state(f'res_desc_{t}',''); init_state(f'res_btn_{t}',''); init_state(f'res_link_{t}','')
                with tabs[i]:
                    rt = st.text_input("名前", key=f'res_title_{t}')
                    rd = st.text_area("説明", key=f'res_desc_{t}', height=300)
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1: rb = st.text_input("ボタン名", key=f'res_btn_{t}')
                    with c_btn2: rl = st.text_input("リンクURL", key=f'res_link_{t}')
                    res_obj[t] = {'title':rt, 'desc':rd, 'btn':rb, 'link':rl}

            st.markdown("---")
            st.subheader("質問設定")
            q_obj = []
            for q in range(1,6):
                init_state(f'q_text_{q}','')
                with st.expander(f"Q{q}. 内容"):
                    qt = st.text_input("文", key=f'q_text_{q}')
                    ans_list = []
                    for a in range(1,5):
                        init_state(f'q{q}_a{a}_text',''); init_state(f'q{q}_a{a}_type','A')
                        c1, c2 = st.columns([3,1])
                        with c1: at = st.text_input(f"選択{a}", key=f'q{q}_a{a}_text')
                        with c2: aty = st.selectbox("加点", ["A","B","C"], key=f'q{q}_a{a}_type')
                        ans_list.append({'text':at, 'type':aty})
                    if qt: q_obj.append({'question':qt, 'answers':ans_list})

            st.markdown("---")
            st.info("URL送付用メールアドレス")
            email = st.text_input("Email", placeholder="mail@example.com")
            
            c1, c2 = st.columns(2)
            with c1: sub_free = st.form_submit_button("🌐 無料公開 (URL発行)", type="primary")
            with c2:
                is_pub = st.checkbox("ポータルに掲載")
                sub_paid = st.form_submit_button("💾 980円で購入 (DL)")
            
            if sub_free or sub_paid:
                if not email: st.error("Email必須")
                elif not q_obj: st.error("質問なし")
                else:
                    s_data = {
                        'page_title':page_title, 'main_heading':main_heading, 'intro_text':intro_text, 
                        'image_keyword':image_keyword,
                        'results':res_obj, 'questions':q_obj
                    }
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
