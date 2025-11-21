import streamlit as st
import json
import openai
import os
import time
import smtplib
import stripe
from email.mime.text import MIMEText
from supabase import create_client, Client

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
# 🎨 デザイン: 添付ファイルのデザインを再現するHTMLテンプレート
# ==========================================
def get_html_template(data, is_preview=False):
    # データの展開
    page_title = data.get('page_title', '診断')
    main_heading = data.get('main_heading', 'タイトル')
    intro_text = data.get('intro_text', '')
    questions = data.get('questions', [])
    results = data.get('results', {})

    # 質問データのHTML化
    questions_html = ""
    for q in questions:
        opts_html = ""
        for ans in q['answers']:
            # ポイント設定 (A:1 などの形式)
            points_json = json.dumps({ans['type']: 1}, ensure_ascii=False).replace('"', '&quot;')
            opts_html += f'<div data-key="option" data-points="{points_json}">{ans["text"]}</div>'
        questions_html += f'<div data-item="question"><p data-key="text">{q["question"]}</p><div data-key="options">{opts_html}</div></div>'

    # 結果データのHTML化
    results_html = ""
    for key, val in results.items():
        # ボタンがある場合は追加
        btn_html = ""
        if val.get('link') and val.get('btn'):
            btn_html = f'<div class="mt-6 text-center"><a href="{val["link"]}" target="_blank" class="flyer-link-button">{val["btn"]} ➤</a></div>'
        
        results_html += f"""
        <div data-item="result" data-id="{key}">
            <h2 data-key="title">{val['title']}</h2>
            <p data-key="description" class="result-text">{val['desc']}</p>
            {btn_html}
        </div>
        """

    # テンプレート本体 (TailwindCSS + Custom CSS)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Noto Sans JP', sans-serif; background-color: #f3f4f6; color: #1f2937; display: flex; flex-direction: column; min-height: 100vh; }}
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
        
        /* Streamlit用調整 */
        {".stApp {background-color: #f3f4f6 !important;}" if is_preview else ""}
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
        
        function loadQuizDataFromDOM() {{
            const dataElem = document.getElementById('quiz-data');
            questions = Array.from(dataElem.querySelectorAll('[data-container="questions"] [data-item="question"]')).map(qElem => ({{
                text: qElem.querySelector('[data-key="text"]').textContent,
                options: Array.from(qElem.querySelectorAll('[data-key="option"]')).map(oElem => ({{
                    text: oElem.textContent,
                    points: JSON.parse(oElem.dataset.points || '{{}}')
                }}))
            }}));
            results = Array.from(dataElem.querySelectorAll('[data-container="results"] [data-item="result"]')).map(rElem => ({{
                id: rElem.dataset.id,
                html: rElem.innerHTML
            }}));
        }}

        function calculateResult() {{
            const scores = {{}};
            userAnswers.forEach(ans => {{ for (const t in ans) scores[t] = (scores[t] || 0) + ans[t]; }});
            let maxScore = -1, resultId = null;
            // デフォルトA,B,Cの順でチェック
            for (const r of results) {{ if ((scores[r.id] || 0) > maxScore) {{ maxScore = scores[r.id]; resultId = r.id; }} }}
            return results.find(r => r.id === resultId);
        }}

        function showResult() {{
            const rData = calculateResult();
            quizArea.classList.add('hidden');
            if (!rData) return;
            
            resultArea.innerHTML = `<div class="result-card">${{rData.html}}</div><div class="mt-6 text-center"><button class="restart-button">もう一度診断する</button></div>`;
            resultArea.classList.remove('hidden');
            resultArea.querySelector('.restart-button').addEventListener('click', startQuiz);
        }}

        function displayQuestion() {{
            const q = questions[currentQuestionIndex];
            quizArea.innerHTML = `
                <div class="progress-bar-container"><div class="progress-bar" style="width: ${{((currentQuestionIndex) / questions.length) * 100}}%"></div></div>
                <div class="question-card">
                    <p class="text-lg font-bold mb-4 text-slate-700">Q${{currentQuestionIndex + 1}}. ${{q.text}}</p>
                    ${{q.options.map((opt, i) => `<button class="option-button" data-index="${{i}}">${{opt.text}}</button>`).join('')}}
                </div>
                <div class="mt-6"><button class="next-button" disabled>次の質問へ</button></div>
            `;
            
            const nextBtn = quizArea.querySelector('.next-button');
            if (currentQuestionIndex === questions.length - 1) nextBtn.textContent = "結果を見る";

            quizArea.querySelectorAll('.option-button').forEach(btn => btn.addEventListener('click', e => {{
                quizArea.querySelectorAll('.option-button').forEach(b => b.classList.remove('selected'));
                e.target.classList.add('selected');
                userAnswers[currentQuestionIndex] = q.options[e.target.dataset.index].points;
                nextBtn.disabled = false;
                // 自動的に次へ進む挙動が好きならここ有効化
                // setTimeout(() => nextBtn.click(), 300);
            }}));

            nextBtn.addEventListener('click', () => {{
                if (userAnswers[currentQuestionIndex] == null) return;
                (currentQuestionIndex < questions.length - 1) ? (currentQuestionIndex++, displayQuestion()) : showResult();
            }});
        }}

        function startQuiz() {{ currentQuestionIndex = 0; userAnswers = []; resultArea.classList.add('hidden'); quizArea.classList.remove('hidden'); displayQuestion(); }}
        
        loadQuizDataFromDOM();
        startQuiz();
    }});
    </script>
</body>
</html>
"""

# ==========================================
# メイン処理
# ==========================================
quiz_id = query_params.get("id", None)
session_id = query_params.get("session_id", None)

# --- 🅰️ プレイ画面 (Web公開用) ---
if quiz_id:
    if not supabase: st.stop()
    try:
        res = supabase.table("quizzes").select("*").eq("id", quiz_id).execute()
        if not res.data:
            st.error("診断が見つかりません。")
            if st.button("トップへ戻る"): st.query_params.clear(); st.rerun()
            st.stop()
        
        data = res.data[0]['content']
        
        # HTMLを生成してiframeで表示 (これでデザインを完全再現)
        html_content = get_html_template(data, is_preview=True)
        st.components.v1.html(html_content, height=800, scrolling=True)
        
        # 戻るボタン（iframeの外に配置）
        if st.button("ポータルトップへ戻る"):
            st.query_params.clear()
            st.rerun()

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
                
                # ダウンロード用HTML生成
                final_html = get_html_template(data, is_preview=False)
                st.download_button("📥 HTMLをダウンロード", final_html, "diagnosis.html", "text/html", type="primary")
                
                if st.button("トップに戻る"): st.query_params.clear(); st.rerun()
                st.stop()
    except Exception as e: st.error(f"決済エラー: {e}")

# --- 🆑 ポータル & 作成画面 ---
else:
    # デザイン: ポータル全体を白基調に
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff; color: #333; }
        .block-container { max-width: 1000px; padding-top: 1rem; }
        #MainMenu, footer, header {visibility: hidden;}
        
        /* ポータルのカード */
        .portal-card {
            background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); transition: 0.2s; height: 100%;
        }
        .portal-card:hover { transform: translateY(-3px); border-color: #3b82f6; }
        
        /* ボタン */
        .stButton button { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; font-weight: bold; }
        .stButton button:hover { border-color: #3b82f6; color: #2563eb; }
        .stButton button[kind="primary"] { background-color: #2563eb; color: white; border: none; }
        .stButton button[kind="primary"]:hover { background-color: #1d4ed8; }
        </style>
    """, unsafe_allow_html=True)

    if st.session_state.page_mode == 'home':
        # 1. ヒーローエリア
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 40px; border-radius: 20px; text-align: center; margin-bottom: 30px; border: 1px solid #bae6fd;">
            <h1 style="color: #0284c7; font-size: 2.5rem; font-weight: 800; margin-bottom: 10px;">Diagnosis Portal</h1>
            <p style="color: #475569;">1時間で作る！オリジナル診断サイト</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. メニュー
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("✨ 作成する", type="primary", use_container_width=True):
                st.session_state.page_mode = 'create'; st.rerun()
        with c2: st.button("🔥 人気順", use_container_width=True)
        with c3: st.button("🆕 新着順", use_container_width=True)
        with c4: st.button("📖 使い方", use_container_width=True)
        
        # 3. 一覧
        st.markdown("### 📚 新着の診断")
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
            
        st.title("📝 診断作成エディタ")
        
        # AIサイドバー
        with st.sidebar:
            if "OPENAI_API_KEY" in st.secrets: api_key = st.secrets["OPENAI_API_KEY"]
            else: st.error("APIキー設定なし"); st.stop()
            
            st.header("🧠 AIアシスタント")
            theme = st.text_area("テーマ", "例：30代女性向けの辛口婚活診断")
            if st.button("構成案を作成", type="primary"):
                try:
                    msg = st.empty(); msg.info("思考中...")
                    client = openai.OpenAI(api_key=api_key)
                    prompt = f"""テーマ:{theme}。JSONのみ出力。format: {{ "page_title":"", "main_heading":"", "intro_text":"", "results":{{"A":{{"title":"","desc":"","btn":"","link":""}},"B":{{...}},"C":{{...}}}}, "questions":[ {{"question":"", "answers":[ {{"text":"","type":"A"}}, {{"text":"","type":"B"}}, {{"text":"","type":"C"}}, {{"text":"","type":"A"}} ]}} ] (5問) }}"""
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"system","content":"Output JSON only"},{"role":"user","content":prompt}], response_format={"type":"json_object"})
                    data = json.loads(res.choices[0].message.content)
                    # 反映
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

        # フォーム
        init_state('page_title',''); init_state('main_heading',''); init_state('intro_text','')
        with st.container(border=True):
            st.subheader("基本情報")
            with st.form("editor"):
                c1, c2 = st.columns(2)
                with c1: page_title = st.text_input("タブ名", key='page_title')
                with c2: main_heading = st.text_input("タイトル", key='main_heading')
                intro_text = st.text_area("導入文", key='intro_text')
                
                st.markdown("---")
                st.subheader("結果設定")
                res_obj = {}
                tabs = st.tabs(["Type A", "Type B", "Type C"])
                for i,t in enumerate(['A','B','C']):
                    init_state(f'res_title_{t}',''); init_state(f'res_desc_{t}',''); init_state(f'res_btn_{t}',''); init_state(f'res_link_{t}','')
                    with tabs[i]:
                        rt = st.text_input("名前", key=f'res_title_{t}')
                        rd = st.text_area("説明", key=f'res_desc_{t}')
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
