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

init_state('ai_count', 0)
init_state('page_mode', 'home') # home, create, play
AI_LIMIT = 5

# --- クエリパラメータ処理 (URLアクセス) ---
query_params = st.query_params
quiz_id = query_params.get("id", None)

# ==========================================
# モードA：プレイ画面 (URL直接アクセス時)
# ==========================================
if quiz_id:
    # ★★★ プレイ画面専用デザイン ★★★
    st.markdown("""
        <style>
        .stApp { background-color: #f1f5f9; }
        .block-container { padding-top: 2rem; max-width: 700px; margin: 0 auto; }
        #MainMenu, footer, header {visibility: hidden;}
        .stButton button { width: 100%; border-radius: 8px; font-weight: bold; border: none; padding: 0.5rem 1rem; transition: all 0.3s; }
        .stButton button:hover { transform: scale(1.02); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        </style>
    """, unsafe_allow_html=True)

    if not supabase:
        st.error("DB設定エラー")
        st.stop()
    try:
        # 閲覧数をカウントアップしたい場合はここにupdate処理を入れる
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
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 もう一度診断する", use_container_width=True):
                    st.session_state[f"q_idx_{quiz_id}"] = 0
                    st.session_state[f"scores_{quiz_id}"] = {'A': 0, 'B': 0, 'C': 0}
                    st.session_state[f"finished_{quiz_id}"] = False
                    st.rerun()
            with c2:
                if st.button("✨ 自分も診断を作る", type="primary", use_container_width=True):
                    st.query_params.clear()
                    st.rerun()
    except Exception as e:
        st.error(f"エラー: {e}")

# ==========================================
# モードB：ポータルサイト (HOME & CREATE)
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
            body {{ font-family: sans-serif; }}
            .fade-in {{ animation: fadeIn 0.7s ease-in-out; }}
            @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(15px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        </style>
    </head>
    <body class="bg-slate-100 text-slate-800 flex items-center justify-center min-h-screen py-8">
        <div class="container mx-auto p-4 max-w-2xl text-center">
            <div id="start-screen" class="bg-white p-10 rounded-2xl shadow-xl fade-in">
                <h1 class="text-3xl font-bold mb-4">{main_heading}</h1>
                <p class="mb-8">{intro_text}</p>
                <button onclick="alert('プレビュー版のためここまでです')" class="bg-blue-600 text-white font-bold py-3 px-6 rounded-lg">診断をはじめる</button>
            </div>
        </div>
    </body>
    </html>
    """

    # 画面切り替えロジック
    if st.session_state.page_mode == 'home':
        
        # --- 1. ポータルトップ画面 ---
        st.markdown("""
        <div style="text-align: center; padding: 40px 0;">
            <h1 style="font-size: 3.5rem; font-weight: 900; background: -webkit-linear-gradient(45deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px;">
                AI Diagnosis Portal
            </h1>
            <p style="font-size: 1.2rem; color: #64748b;">AIで作られた診断クイズが集まる場所。</p>
        </div>
        """, unsafe_allow_html=True)

        # 作成ボタン
        col_act1, col_act2, col_act3 = st.columns([1, 2, 1])
        with col_act2:
            if st.button("✨ 新しい診断を作る", type="primary", use_container_width=True):
                st.session_state.page_mode = 'create'
                st.rerun()

        st.markdown("---")
        st.subheader("🔥 新着診断ギャラリー")

        # データベースから「公開(is_public=True)」の診断を取得
        if supabase:
            try:
                res = supabase.table("quizzes").select("*").eq("is_public", True).order("created_at", desc=True).limit(12).execute()
                quizzes = res.data
                
                if not quizzes:
                    st.info("まだ投稿がありません。あなたが最初のクリエイターになりませんか？")
                else:
                    # 3列グリッドで表示
                    cols = st.columns(3)
                    for i, quiz in enumerate(quizzes):
                        with cols[i % 3]:
                            with st.container(border=True):
                                st.write(f"#### {quiz.get('title', '無題')}")
                                st.caption(f"作成者: {quiz.get('email', 'Guest')[:3]}***")
                                
                                # リンクボタン
                                base_url = "https://shindan-quiz-maker.streamlit.app" # あなたのURL
                                link = f"{base_url}/?id={quiz['id']}"
                                st.link_button("▶ 診断する", link, use_container_width=True)
                                
            except Exception as e:
                st.error(f"読み込みエラー: {e}")

    elif st.session_state.page_mode == 'create':
        
        # --- 2. 作成画面 (以前のエディタ) ---
        if st.button("← トップに戻る"):
            st.session_state.page_mode = 'home'
            st.rerun()
            
        st.title("🛠️ 診断作成エディタ")
        
        # サイドバー (AI)
        with st.sidebar:
            if "OPENAI_API_KEY" in st.secrets:
                api_key = st.secrets["OPENAI_API_KEY"]
            else:
                st.error("APIキー設定が必要です")
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

        # 編集フォーム
        init_state('page_title', '')
        init_state('main_heading', '')
        init_state('intro_text', '')
        
        with st.form("editor"):
            page_title = st.text_input("タブ名", key='page_title')
            main_heading = st.text_input("タイトル", key='main_heading')
            intro_text = st.text_area("導入文", key='intro_text')
            
            st.markdown("---")
            results_obj = {}
            for t in ['A', 'B', 'C']:
                init_state(f'res_title_{t}', '')
                init_state(f'res_desc_{t}', '')
                init_state(f'res_btn_{t}', '')
                init_state(f'res_link_{t}', '')
                with st.expander(f"タイプ{t} 設定"):
                    rt = st.text_input("名前", key=f'res_title_{t}')
                    rd = st.text_area("説明", key=f'res_desc_{t}')
                    rb = st.text_input("ボタン", key=f'res_btn_{t}')
                    rl = st.text_input("URL", key=f'res_link_{t}')
                    results_obj[t] = {'title': rt, 'desc': rd, 'btn': rb, 'link': rl}

            st.markdown("---")
            questions_obj = []
            for q in range(1, 6):
                init_state(f'q_text_{q}', '')
                with st.expander(f"Q{q}. 質問"):
                    qt = st.text_input("文", key=f'q_text_{q}')
                    ans_list = []
                    for a in range(1, 5):
                        init_state(f'q{q}_a{a}_text', '')
                        init_state(f'q{q}_a{a}_type', 'A')
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            at = st.text_input(f"選択{a}", key=f'q{q}_a{a}_text')
                        with c2:
                            aty = st.selectbox("加点", ["A", "B", "C"], key=f'q{q}_a{a}_type')
                        ans_list.append({'text': at, 'type': aty})
                    if qt:
                        questions_obj.append({'question': qt, 'answers': ans_list})

            st.markdown("---")
            st.write("#### 📤 保存と公開")
            user_email = st.text_input("メールアドレス (必須)", placeholder="example@gmail.com")
            
            # ★★★ ロジック分岐の核心 ★★★
            c_free, c_paid = st.columns(2)
            with c_free:
                st.info("【無料】URLを発行して、このポータルサイトに公開します。")
                submit_pub = st.form_submit_button("🌐 Web公開 (無料)", type="primary")
            
            with c_paid:
                st.warning("【有料】HTMLファイルをダウンロードします。ポータルへの掲載は任意です。")
                # 有料版だけ「掲載するかどうか」を選べる
                is_publish_paid = st.checkbox("ポータルにも掲載する", value=False)
                submit_dl = st.form_submit_button("💾 HTMLダウンロード (有料)")

        # 保存処理
        if submit_pub or submit_dl:
            if not user_email:
                st.error("メールアドレスを入力してください")
            elif len(questions_obj) < 1:
                st.error("質問がありません")
            else:
                save_data = {
                    'page_title': page_title,
                    'main_heading': main_heading,
                    'intro_text': intro_text,
                    'results': results_obj,
                    'questions': questions_obj
                }
                
                # 公開フラグの決定
                # 無料(URL発行) -> 強制的にTrue
                # 有料(ダウンロード) -> チェックボックスの値(デフォルトFalse)
                if submit_pub:
                    is_public_flag = True
                else:
                    is_public_flag = is_publish_paid
                
                try:
                    # DB保存 (is_publicフラグ付き)
                    res = supabase.table("quizzes").insert({
                        "email": user_email,
                        "title": main_heading,
                        "content": save_data,
                        "is_public": is_public_flag # ←ここがポイント
                    }).execute()
                    
                    new_id = res.data[0]['id']
                    
                    # 処理後の表示
                    if submit_pub:
                        base_url = "https://shindan-quiz-maker.streamlit.app"
                        public_url = f"{base_url}/?id={new_id}"
                        if send_email(user_email, public_url, main_heading):
                            st.success("公開しました！ポータルトップに掲載されました。")
                            st.balloons()
                            time.sleep(2)
                            st.session_state.page_mode = 'home' # トップに戻る
                            st.rerun()
                        else:
                            st.error("メール送信失敗")

                    if submit_dl:
                        # HTML生成 (省略版テンプレートを使用)
                        final_html = html_template_str.format(
                            page_title=page_title, 
                            main_heading=main_heading, 
                            intro_text=intro_text, 
                            results_html="", # 実際はここに生成ロジックが入る
                            quiz_data_json=json.dumps(questions_obj, ensure_ascii=False)
                        )
                        st.success("購入ありがとうございます！データをダウンロードできます。")
                        st.download_button("📥 HTMLダウンロード", final_html, "diagnosis.html", "text/html")
                        
                        if is_public_flag:
                            st.info("※ポータルサイトにも掲載されました。")
                        else:
                            st.info("※非公開設定で保存されました。ポータルには表示されません。")

                except Exception as e:
                    st.error(f"保存エラー: {e}")
