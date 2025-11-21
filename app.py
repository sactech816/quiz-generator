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

# --- CSS (デザイン) ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 900px; margin: 0 auto; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; border: none; padding: 0.5rem 1rem; transition: all 0.3s; }
    .stButton button:hover { transform: scale(1.02); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    
    /* タブの文字サイズ調整 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1rem; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

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
                <div style="width: 50px; height: 4px; background: #cbd5e1; margin: 1rem auto;"></div>
                <p style="color: #475569; margin-bottom: 2rem; line-height: 1.8;">{res_data.get('desc', '')}</p>
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
# モードB：作成モード
# ==========================================
else:
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
                <button onclick="startQuiz()" class="w-full bg-blue-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-blue-700 transition-transform transform hover:scale-105 shadow-lg">
                    診断をはじめる
                </button>
            </div>
            <div id="quiz-screen" class="hidden bg-white p-8 sm:p-10 rounded-2xl shadow-xl">
                <div class="text-center mb-8">
                    <p id="progress-text" class="text-sm text-slate-500">質問 1</p>
                    <div class="w-full bg-slate-200 rounded-full h-2.5 mt-2">
                        <div id="progress-bar" class="bg-blue-600 h-2.5 rounded-full transition-all duration-500 ease-out" style="width: 0%"></div>
                    </div>
                </div>
                <h2 id="question-text" class="text-xl font-bold mb-8 text-center min-h-[5rem] flex items-center justify-center"></h2>
                <div id="answers-container" class="grid grid-cols-1 gap-4"></div>
            </div>
            <div id="results-screen" class="hidden">
                {results_html}
            </div>
        </div>
        <script>
            const quizData = {quiz_data_json};
            let currentQuestionIndex = 0;
            let scores = {{ 'A': 0, 'B': 0, 'C': 0 }};
            function startQuiz() {{
                document.getElementById('start-screen').classList.add('hidden');
                document.getElementById('quiz-screen').classList.remove('hidden');
                document.getElementById('quiz-screen').classList.add('fade-in');
                displayQuestion();
            }}
            function displayQuestion() {{
                document.getElementById('answers-container').innerHTML = '';
                const currentQuestion = quizData[currentQuestionIndex];
                document.getElementById('question-text').textContent = currentQuestion.question;
                const progress = ((currentQuestionIndex + 1) / quizData.length) * 100;
                document.getElementById('progress-text').textContent = `質問 ${{currentQuestionIndex + 1}} / ${{quizData.length}}`;
                document.getElementById('progress-bar').style.width = `${{progress}}%`;
                currentQuestion.answers.forEach(answer => {{
                    const button = document.createElement('button');
                    button.textContent = answer.text;
                    button.className = 'w-full bg-white border border-slate-300 text-slate-700 font-semibold py-4 px-4 rounded-lg hover:bg-blue-50 hover:border-blue-500 transition-all duration-200 text-left';
                    button.onclick = () => selectAnswer(answer.type);
                    document.getElementById('answers-container').appendChild(button);
                }});
            }}
            function selectAnswer(type) {{
                if (scores[type] !== undefined) {{ scores[type]++; }}
                currentQuestionIndex++;
                if (currentQuestionIndex < quizData.length) {{
                    setTimeout(() => {{ displayQuestion(); }}, 300);
                }} else {{
                    showResults();
                }}
            }}
            function showResults() {{
                document.getElementById('quiz-screen').classList.add('hidden');
                document.getElementById('results-screen').classList.remove('hidden');
                let maxType = 'A';
                let maxCount = 0;
                for (const [type, count] of Object.entries(scores)) {{
                    if (count > maxCount) {{ maxCount = count; maxType = type; }}
                }}
                document.getElementById(`result-${{maxType}}`).classList.remove('hidden');
                document.getElementById(`result-${{maxType}}`).classList.add('fade-in');
            }}
        </script>
    </body>
    </html>
    """

    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <h1 style="font-size: 3rem; font-weight: 800; background: -webkit-linear-gradient(45deg, #2563eb, #db2777); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            AI Diagnosis Maker
        </h1>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
        else:
            st.warning("APIキー設定が必要です")
            st.stop()
        
        st.header("🧠 AIアシスタント")
        remaining = AI_LIMIT - st.session_state.ai_count
        if remaining > 0:
            st.caption(f"残り生成回数: {remaining} 回")
        
        theme = st.text_area("テーマ", "例：30代女性向けの辛口婚活診断")
        if st.button("AIで構成案を作成", type="primary", disabled=(remaining <= 0)):
            try:
                client = openai.OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Output JSON only."},
                        {"role": "user", "content": f"テーマ: {theme} で診断を作成。JSON形式。質問5問。"}
                    ],
                    response_format={"type": "json_object"}
                )
                data = json.loads(response.choices[0].message.content)
                
                st.session_state['page_title'] = data.get('page_title', '')
                st.session_state['main_heading'] = data.get('main_heading', '')
                st.session_state['intro_text'] = data.get('intro_text', '')
                
                if 'results' in data:
                    for t in ['A', 'B', 'C']:
                        if t in data['results']:
                            st.session_state[f'res_title_{t}'] = data['results'][t].get('title', '')
                            st.session_state[f'res_desc_{t}'] = data['results'][t].get('desc', '')
                            st.session_state[f'res_btn_{t}'] = data['results'][t].get('btn', '')
                
                if 'questions' in data:
                    for i, qd in enumerate(data['questions']):
                        idx = i + 1
                        st.session_state[f'q_text_{idx}'] = qd.get('question', '')
                        for j, ans in enumerate(qd.get('answers', [])):
                            adx = j + 1
                            st.session_state[f'q{idx}_a{adx}_text'] = ans.get('text', '')
                            st.session_state[f'q{idx}_a{adx}_type'] = ans.get('type', 'A')
                
                st.session_state.ai_count += 1
                st.rerun()
            except Exception as e:
                st.error(e)

    # 編集フォーム (初期化)
    init_state('page_title', '')
    init_state('main_heading', '')
    init_state('intro_text', '')
    
    with st.form("editor"):
        st.subheader("診断コンテンツ編集")
        page_title = st.text_input("タブ名", key='page_title')
        main_heading = st.text_input("タイトル", key='main_heading')
        intro_text = st.text_area("導入文", key='intro_text')
        
        # --- 結果設定ループ (ここが抜けていました！) ---
        st.markdown("---")
        results_obj = {}
        tabs = st.tabs(["タイプA", "タイプB", "タイプC"])
        for i, t in enumerate(['A', 'B', 'C']):
            init_state(f'res_title_{t}', '')
            init_state(f'res_desc_{t}', '')
            init_state(f'res_btn_{t}', '')
            init_state(f'res_link_{t}', '')
            
            with tabs[i]:
                rt = st.text_input("結果タイトル", key=f'res_title_{t}')
                rd = st.text_area("説明文", key=f'res_desc_{t}')
                rb = st.text_input("ボタン文字", key=f'res_btn_{t}')
                rl = st.text_input("リンクURL", key=f'res_link_{t}')
                results_obj[t] = {'title': rt, 'desc': rd, 'btn': rb, 'link': rl}

        # --- 質問設定ループ (ここが抜けていました！) ---
        st.markdown("---")
        questions_obj = []
        for q in range(1, 6):
            init_state(f'q_text_{q}', '')
            with st.expander(f"Q{q}. 質問文"):
                qt = st.text_input("文", key=f'q_text_{q}')
                ans_list = []
                for a in range(1, 5):
                    init_state(f'q{q}_a{a}_text', '')
                    init_state(f'q{q}_a{a}_type', 'A')
                    
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        at = st.text_input(f"選択肢{a}", key=f'q{q}_a{a}_text')
                    with c2:
                        aty = st.selectbox("加点", ["A", "B", "C"], key=f'q{q}_a{a}_type')
                    ans_list.append({'text': at, 'type': aty})
                
                if qt:
                    questions_obj.append({'question': qt, 'answers': ans_list})

        st.markdown("---")
        st.write("#### 📤 公開設定")
        st.info("メールアドレスを入力してください。公開URLが送信されます。")
        user_email = st.text_input("メールアドレス (必須)", placeholder="example@gmail.com")
        
        col_pub, col_dl = st.columns(2)
        with col_pub:
            submit_pub = st.form_submit_button("🌐 無料でWeb公開 (URL発行)", type="primary")
        with col_dl:
            submit_dl = st.form_submit_button("💾 HTMLデータをダウンロード (有料想定)")

    # データ整形と処理
    if submit_pub or submit_dl:
        if not user_email:
            st.error("メールアドレスを入力してください")
        elif len(questions_obj) < 1:
            st.error("質問が入力されていません")
        else:
            save_data = {
                'page_title': page_title,
                'main_heading': main_heading,
                'intro_text': intro_text,
                'results': results_obj,
                'questions': questions_obj
            }
            
            try:
                # DB保存
                res = supabase.table("quizzes").insert({
                    "email": user_email,
                    "title": main_heading,
                    "content": save_data
                }).execute()
                new_id = res.data[0]['id']
                
                # 分岐A: Web公開
                if submit_pub:
                    base_url = "https://shindan-quiz-maker.streamlit.app"
                    public_url = f"{base_url}/?id={new_id}"
                    
                    if send_email(user_email, public_url, main_heading):
                        st.success("公開しました！メールアドレスにURLを送信しました。")
                        st.balloons()
                    else:
                        st.error("メール送信に失敗しました")

                # 分岐B: HTMLダウンロード
                if submit_dl:
                    results_html_str = ""
                    for type_char, data in results_obj.items():
                        results_html_str += f"<div id='result-{type_char}' class='hidden p-8 bg-white rounded-2xl shadow-xl'><p class='text-center text-blue-600 font-bold mb-2'>診断結果</p><h2 class='text-2xl font-bold text-center mb-4'>{data['title']}</h2><p class='mb-6 text-slate-600'>{data['desc']}</p><a href='{data['link']}' class='block w-full text-center bg-blue-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-blue-700 transition-transform transform hover:scale-105 shadow-lg'>→ {data['btn']}</a></div>"
                    
                    final_html = html_template_str.format(
                        page_title=page_title, 
                        main_heading=main_heading, 
                        intro_text=intro_text, 
                        results_html=results_html_str, 
                        quiz_data_json=json.dumps(questions_obj, ensure_ascii=False)
                    )
                    
                    st.success("データを作成しました！")
                    st.download_button("📥 HTMLファイルをダウンロード", final_html, "diagnosis.html", "text/html")
                    st.info("※決済機能を追加すれば、ここを有料化できます")

            except Exception as e:
                st.error(f"保存エラー: {e}")
