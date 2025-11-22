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
# デザイン (CSS)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; color: #333333 !important; }
    .block-container { max-width: 1000px; padding-top: 1rem; padding-bottom: 5rem; }
    #MainMenu, footer, header {visibility: hidden;}
    
    /* カードデザイン (画像あり) */
    .quiz-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); height: 100%; transition: 0.2s; display: flex; flex-direction: column;
    }
    .quiz-card:hover { transform: translateY(-3px); border-color: #3b82f6; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    
    .quiz-thumb {
        width: 100%; height: 140px; object-fit: cover; background-color: #f1f5f9;
    }
    .quiz-content { padding: 15px; flex-grow: 1; }
    .quiz-title { font-weight: bold; font-size: 1.1rem; margin-bottom: 5px; color: #1e293b; line-height: 1.4; }
    .quiz-desc { font-size: 0.85rem; color: #64748b; margin-bottom: 10px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    
    /* ボタン */
    .stButton button { background-color: #f8fafc; border: 1px solid #cbd5e1; color: #334155; border-radius: 8px; font-weight: bold; transition: all 0.2s; }
    .stButton button:hover { border-color: #3b82f6; color: #2563eb; background-color: #eff6ff; }
    .stButton button[kind="primary"] { background-color: #2563eb; color: white; border: none; }
    .stButton button[kind="primary"]:hover { background-color: #1d4ed8; }
    </style>
""", unsafe_allow_html=True)

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

# --- HTML生成ヘルパー (省略版) ---
def generate_html_content(data):
    # (長くなるので簡略化していますが、実際は前回のHTML_TEMPLATE_RAWと同じものが入ります)
    # ※実際の運用では前回のHTMLコードをここに入れてください
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{data.get('page_title','')}</title><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-slate-100 text-slate-800 p-4"><div class="max-w-2xl mx-auto bg-white p-8 rounded-xl shadow"><h1 class="text-2xl font-bold mb-4">{data.get('main_heading','')}</h1><p>{data.get('intro_text','')}</p><div class="mt-8 p-4 bg-blue-50 rounded text-center"><p class="font-bold text-blue-600">診断スタート！</p></div></div></body></html>"""

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
        # 前回の完全版HTML生成関数があればそちらを使ってください
        # ここでは簡易表示
        st.markdown(f"<div style='text-align:center; padding:40px;'><h1>{data.get('main_heading')}</h1><p>本来はここに診断画面が表示されます(コード省略)</p></div>", unsafe_allow_html=True)
        
        if st.button("ポータルトップへ戻る"):
            st.query_params.clear()
            st.rerun()
    except Exception as e: st.error(e)

# --- 🅱️ 決済完了 ---
elif session_id:
    st.success("決済完了！(ダウンロード処理)")
    if st.button("トップに戻る"): st.query_params.clear(); st.rerun()

# --- 🆑 ポータル & 作成画面 ---
else:
    if st.session_state.page_mode == 'home':
        # ヒーローエリア
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 40px; border-radius: 20px; text-align: center; margin-bottom: 30px; border: 1px solid #bae6fd;">
            <h1 style="color: #0284c7; font-size: 2.5rem; font-weight: 800; margin-bottom: 10px;">Diagnosis Portal</h1>
            <p style="color: #475569;">1時間で作る！オリジナル診断サイト</p>
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
                        # ★サムネイル画像 (キーワードがない場合はランダム)
                        content = q.get('content', {})
                        keyword = content.get('image_keyword', 'abstract')
                        img_url = f"https://image.pollinations.ai/prompt/{keyword}?width=400&height=250&nologo=true"
                        
                        st.markdown(f"""
                        <div class="quiz-card">
                            <img src="{img_url}" class="quiz-thumb" loading="lazy">
                            <div class="quiz-content">
                                <div class="quiz-title">{q.get('title','無題')}</div>
                                <div class="quiz-desc">{content.get('intro_text','')[:30]}...</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        base = "https://shindan-quiz-maker.streamlit.app"
                        st.link_button("▶ 遊ぶ", f"{base}/?id={q['id']}", use_container_width=True)
                        st.write("") # スペース
            else:
                st.info("まだ投稿がありません")

    elif st.session_state.page_mode == 'create':
        if st.button("← ポータルへ戻る"):
            st.session_state.page_mode = 'home'; st.rerun()
            
        st.title("📝 診断作成エディタ")
        
        # フォーム変数初期化
        init_state('page_title','')
        init_state('main_heading','')
        init_state('intro_text','')
        init_state('image_keyword', '') # 画像キーワード用

        with st.sidebar:
            if "OPENAI_API_KEY" in st.secrets: api_key = st.secrets["OPENAI_API_KEY"]
            else: st.error("APIキー設定なし"); st.stop()
            
            st.header("🧠 AIアシスタント")
            theme = st.text_area("テーマ", "例：30代女性向けの辛口婚活診断")
            
if st.button("構成案を作成", type="primary"):
                try:
                    msg = st.empty(); msg.info("AIが詳細な診断結果を執筆中... (通常より少し時間がかかります)")
                    client = openai.OpenAI(api_key=api_key)
                    
                    # ★★★ ここが変更点です（指示を具体的にしました） ★★★
                    prompt = f"""
                    あなたはプロの占い師兼キャリアコンサルタントです。以下のテーマで、ユーザーが「当たってる！」「役に立つ！」と感動するような診断コンテンツを作成してください。
                    
                    テーマ: {theme}
                    
                    【重要】必ず以下のJSONフォーマットのみを出力してください。余計な解説は不要です。
                    {{
                        "page_title": "ブラウザのタブに表示する短いタイトル",
                        "main_heading": "診断のキャッチーな大見出し",
                        "intro_text": "ユーザーの興味を惹く導入文（150文字程度）",
                        "image_keyword": "この診断の雰囲気を表す英単語1語(例: business, forest, galaxy)",
                        "results": {{
                            "A": {{
                                "title": "タイプAの魅力的な名前",
                                "desc": "【超重要】このタイプの人への詳細な診断結果。性格の傾向、隠れた才能、注意点、具体的な開運/成功アドバイスなどを網羅し、読んだ人が満足するよう「600文字程度」で詳しく書いてください。",
                                "btn": "詳細ページへ（ボタンの文言）",
                                "link": ""
                            }},
                            "B": {{
                                "title": "タイプBの魅力的な名前",
                                "desc": "タイプAと同様に、性格、才能、アドバイスを含めて「600文字程度」で詳しく書いてください。",
                                "btn": "詳細ページへ",
                                "link": ""
                            }},
                            "C": {{
                                "title": "タイプCの魅力的な名前",
                                "desc": "タイプAと同様に、性格、才能、アドバイスを含めて「600文字程度」で詳しく書いてください。",
                                "btn": "詳細ページへ",
                                "link": ""
                            }}
                        }},
                        "questions": [
                            {{
                                "question": "ユーザーが迷うような深層心理を突く質問文",
                                "answers": [
                                    {{ "text": "選択肢1", "type": "A" }},
                                    {{ "text": "選択肢2", "type": "B" }},
                                    {{ "text": "選択肢3", "type": "C" }},
                                    {{ "text": "選択肢4", "type": "A" }}
                                ]
                            }}
                        ]
                    }}
                    質問は5つ作成してください。JSONのみ出力。
                    """
                    
                    res = client.chat.completions.create(
                        model="gpt-4o-mini", 
                        messages=[{"role":"system","content":"Output JSON only"}, {"role":"user","content":prompt}], 
                        response_format={"type":"json_object"}
                    )
                    data = json.loads(res.choices[0].message.content)
                    
                    # --- データ反映処理 (ここは変更なし) ---
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
                    
                    msg.success("完了！"); time.sleep(0.5); st.rerun()
                except Exception as e: st.error(e)
        with st.form("editor"):
            st.subheader("基本情報")
            page_title = st.text_input("タブ名", key='page_title')
            main_heading = st.text_input("タイトル", key='main_heading')
            intro_text = st.text_area("導入文", key='intro_text')
            
            # 画像キーワード（手動変更も可能にする）
            image_keyword = st.text_input("サムネイル用キーワード(英語)", key='image_keyword', help="この単語に基づいてAIが画像を生成します")
            
            # ... (質問・結果の入力欄は省略。前回と同じコードを使用) ...
            st.info("（ここに質問・結果設定フォームが入ります）")
            
            st.markdown("---")
            email = st.text_input("Email", placeholder="mail@example.com")
            sub_free = st.form_submit_button("🌐 無料公開", type="primary")
            
            if sub_free:
                # 保存データに image_keyword を含める
                s_data = {
                    'page_title': page_title,
                    'main_heading': main_heading,
                    'intro_text': intro_text,
                    'image_keyword': image_keyword, # 追加
                    'results': {}, # 本来は中身あり
                    'questions': [] # 本来は中身あり
                }
                try:
                    supabase.table("quizzes").insert({"email":email, "title":main_heading, "content":s_data, "is_public":True}).execute()
                    st.success("公開しました！")
                    time.sleep(2); st.session_state.page_mode='home'; st.rerun()
                except Exception as e: st.error(e)
