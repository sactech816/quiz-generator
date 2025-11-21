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
        # Secretsから情報を取得
        sender_email = st.secrets["email"]["address"]
        sender_password = st.secrets["email"]["password"]
        
        subject = "【診断メーカー】作成された診断のURLをお届けします"
        body = f"""
        診断を作成いただきありがとうございます！
        
        以下のURLから、作成した診断にアクセスできます。
        
        ■タイトル: {quiz_title}
        ■URL: {quiz_url}
        
        このURLをコピーしてSNSなどでシェアしてください。
        --------------------------------------------------
        ※このメールは自動送信されています。
        """
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = to_email
        
        # Gmailのサーバーを使って送信
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
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
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
# モードA：閲覧モード (プレイ画面) - 変更なし
# ==========================================
if quiz_id:
    # (前回と同じコードのため省略せず記述します)
    st.markdown("""
        <style>
        .stApp { background-color: #f1f5f9; }
        .block-container { 
            padding-top: 2rem; padding-bottom: 2rem; max-width: 700px; margin: 0 auto;
        }
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
            if st.button("🔄 もう一度診断する", use_container_width=True):
                st.session_state[f"q_idx_{quiz_id}"] = 0
                st.session_state[f"scores_{quiz_id}"] = {'A': 0, 'B': 0, 'C': 0}
                st.session_state[f"finished_{quiz_id}"] = False
                st.rerun()
            if st.button("✨ 自分も診断を作る", type="primary", use_container_width=True):
                st.query_params.clear()
                st.rerun()
    except Exception as e:
        st.error(f"エラー: {e}")

# ==========================================
# モードB：作成モード
# ==========================================
else:
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
            # (AI生成処理は変更なしのため省略。以前のコードと同じロジックが入ります)
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
                # データ反映処理...
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

    # 編集フォーム (中身は変更なし)
    init_state('page_title', '')
    init_state('main_heading', '')
    init_state('intro_text', '')
    
    with st.form("editor"):
        # (入力欄の記述は省略、以前と同じ)
        st.subheader("診断コンテンツ編集")
        page_title = st.text_input("タブ名", key='page_title')
        main_heading = st.text_input("タイトル", key='main_heading')
        intro_text = st.text_area("導入文", key='intro_text')
        
        # ... (結果・質問のループ処理) ...
        # (ここも以前と同じコードを入れてください。長くなるため省略していますが、構造は変わりません)
        
        # ★★★ 変更点：ダウンロードボタン削除・メール必須化 ★★★
        st.markdown("---")
        st.write("#### 🌐 公開設定")
        st.info("入力されたメールアドレス宛に、診断URLをお送りします。（画面には表示されません）")
        user_email = st.text_input("メールアドレス (必須)", placeholder="example@gmail.com")
        
        # HTMLダウンロードボタンは削除しました
        # st.download_button(...) ← 削除
        
        submit = st.form_submit_button("保存してメールでURLを受け取る", type="primary", use_container_width=True)

    if submit:
        if not user_email:
            st.error("メールアドレスを入力してください")
        elif not supabase:
            st.error("データベースエラー")
        else:
            # データの保存処理... (省略、以前と同じ)
            # save_data = ...
            
            try:
                # DB保存
                # res = supabase.table("quizzes").insert(...).execute()
                # new_id = res.data[0]['id']
                
                # ダミーID（実際は上のコードで取得）
                new_id = "test-id" 
                
                base_url = "https://shindan-quiz-maker.streamlit.app"
                public_url = f"{base_url}/?id={new_id}"
                
                # ★★★ メール送信 ★★★
                if send_email(user_email, public_url, main_heading):
                    st.success(f"{user_email} 宛にURLを送信しました！メールをご確認ください。")
                    st.balloons()
                else:
                    st.error("メール送信に失敗しました。Gmailの設定を確認してください。")
                
            except Exception as e:
                st.error(f"保存エラー: {e}")
