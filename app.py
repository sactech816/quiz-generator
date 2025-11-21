import streamlit as st
import json
import openai
import os
import time
from supabase import create_client, Client

# 日本語文字化け防止
os.environ["PYTHONIOENCODING"] = "utf-8"

# ページ設定 (作成画面のために 'wide' に戻しました)
st.set_page_config(page_title="診断クイズメーカー", page_icon="🔮", layout="wide")

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
# モードA：閲覧モード (プレイ画面)
# ==========================================
if quiz_id:
    # ★★★ ここでけ「Webサイト風デザイン」を適用します ★★★
    st.markdown("""
        <style>
        /* 背景を薄いグレーに */
        .stApp { background-color: #f1f5f9; }
        
        /* スマホで見やすいように幅を制限して中央寄せ */
        .block-container { 
            padding-top: 2rem; 
            padding-bottom: 2rem; 
            max-width: 700px; 
            margin: 0 auto;
        }
        
        /* 余計なメニューを消す */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* ボタンデザイン */
        .stButton button {
            width: 100%;
            border-radius: 8px;
            font-weight: bold;
            border: none;
            padding: 0.5rem 1rem;
            transition: all 0.3s;
        }
        .stButton button:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    if not supabase:
        st.error("データベース設定がありません")
        st.stop()
        
    try:
        response = supabase.table("quizzes").select("*").eq("id", quiz_id).execute()
        
        if not response.data:
            st.error("診断が見つかりません。削除された可能性があります。")
            if st.button("トップへ戻る"):
                st.query_params.clear()
                st.rerun()
            st.stop()
            
        data = response.data[0]
        content = data['content']
        
        # 状態管理
        if f"q_idx_{quiz_id}" not in st.session_state:
            st.session_state[f"q_idx_{quiz_id}"] = 0
            st.session_state[f"scores_{quiz_id}"] = {'A': 0, 'B': 0, 'C': 0}
            st.session_state[f"finished_{quiz_id}"] = False

        current_idx = st.session_state[f"q_idx_{quiz_id}"]
        questions = content.get('questions', [])
        
        # --- プレイ画面 ---
        if not st.session_state[f"finished_{quiz_id}"]:
            st.markdown(f"""
            <div style="background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; margin-bottom: 20px;">
                <h1 style="color: #1e293b; font-size: 1.8rem; margin-bottom: 1rem;">{content.get('main_heading', '診断')}</h1>
                <p style="color: #64748b; margin-bottom: 2rem;">{content.get('intro_text', '')}</p>
            </div>
            """, unsafe_allow_html=True)

            progress = (current_idx / len(questions))
            st.progress(progress)
            
            if current_idx < len(questions):
                q_data = questions[current_idx]
                st.markdown(f"""
                <div style="text-align: center; margin: 20px 0;">
                    <p style="color: #2563eb; font-weight: bold;">QUESTION {current_idx + 1} / {len(questions)}</p>
                    <h2 style="font-size: 1.4rem; font-weight: bold; color: #334155;">{q_data['question']}</h2>
                </div>
                """, unsafe_allow_html=True)
                
                for ans in q_data['answers']:
                    if st.button(ans['text'], key=f"ans_{current_idx}_{ans['text']}", use_container_width=True):
                        st.session_state[f"scores_{quiz_id}"][ans['type']] += 1
                        st.session_state[f"q_idx_{quiz_id}"] += 1
                        st.rerun()
            else:
                st.session_state[f"finished_{quiz_id}"] = True
                st.rerun()
        
        # --- 結果画面 ---
        else:
            st.balloons()
            scores = st.session_state[f"scores_{quiz_id}"]
            max_type = max(scores, key=scores.get)
            res_data = content['results'].get(max_type, {})
            
            st.markdown(f"""
            <div style="background-color: white; padding: 2.5rem; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; border-top: 8px solid #2563eb; margin-top: 20px; margin-bottom: 30px;">
                <p style="color: #2563eb; font-weight: bold; letter-spacing: 0.1em;">DIAGNOSIS RESULT</p>
                <h2 style="font-size: 2rem; font-weight: 800; margin: 1rem 0; color: #1e293b;">{res_data.get('title', 'タイプ' + max_type)}</h2>
                <div style="width: 50px; height: 4px; background: #cbd5e1; margin: 1rem auto;"></div>
                <p style="color: #475569; line-height: 1.8; font-size: 1.05rem; margin-bottom: 2rem;">{res_data.get('desc', '')}</p>
                <a href="{res_data.get('link', '#')}" target="_blank" style="display: inline-block; background: linear-gradient(45deg, #2563eb, #1d4ed8); color: white; font-weight: bold; padding: 16px 32px; border-radius: 50px; text-decoration: none; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3); transition: transform 0.2s;">{res_data.get('btn', '詳細を見る')} ➤</a>
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
    # ★★★ 作成画面はデフォルトの見た目(黒背景など)に戻ります ★★★
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <h1 style="font-size: 3rem; font-weight: 800; background: -webkit-linear-gradient(45deg, #2563eb, #db2777); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            AI Diagnosis Maker
        </h1>
        <p style="color: #888;">AIの力で、世界に一つの診断コンテンツを作ろう。</p>
    </div>
    """, unsafe_allow_html=True)

    # --- サイドバー：AI生成 ---
    with st.sidebar:
        if "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
        else:
            st.warning("APIキーを設定してください")
            st.stop()
        
        st.header("🧠 AIアシスタント")
        
        # 残り回数の表示
        remaining = AI_LIMIT - st.session_state.ai_count
        if remaining > 0:
            st.caption(f"残り生成回数: {remaining} / {AI_LIMIT} 回")
        else:
            st.error("⚠️ 生成回数の上限に達しました")

        theme = st.text_area("テーマ", "例：30代女性向けの辛口婚活診断", height=100)
        
        generate_btn = st.button("AIで構成案を作成", type="primary", use_container_width=True, disabled=(remaining <= 0))
        
        if generate_btn:
            if remaining <= 0:
                st.error("回数制限を超えています。画面をリロードするとリセットされる場合があります。")
            else:
                try:
                    status = st.empty()
                    status.info("💡 AIがアイデアを練っています...")
                    client = openai.OpenAI(api_key=api_key)
                    
                    prompt = f"""
                    テーマ: {theme}
                    以下のJSON形式で診断を作成してください。
                    {{
                        "page_title": "ブラウザタイトル",
                        "main_heading": "ページ大見出し",
                        "intro_text": "導入文(100文字程度)",
                        "results": {{
                            "A": {{ "title": "タイプA名", "desc": "詳細な説明(200文字程度)", "btn": "ボタン名" }},
                            "B": {{ "title": "タイプB名", "desc": "詳細な説明(200文字程度)", "btn": "ボタン名" }},
                            "C": {{ "title": "タイプC名", "desc": "詳細な説明(200文字程度)", "btn": "ボタン名" }}
                        }},
                        "questions": [
                            {{
                                "question": "質問文",
                                "answers": [
                                    {{ "text": "選択肢1", "type": "A" }},
                                    {{ "text": "選択肢2", "type": "B" }},
                                    {{ "text": "選択肢3", "type": "C" }},
                                    {{ "text": "選択肢4", "type": "A" }}
                                ]
                            }}
                        ]
                    }}
                    質問は5問。JSONのみ出力。
                    """
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Output JSON only."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"}
                    )
                    
                    data = json.loads(response.choices[0].message.content)
                    
                    # データ反映
                    st.session_state['page_title'] = data.get('page_title', '')
                    st.session_state['main_heading'] = data.get('main_heading', '')
                    st.session_state['intro_text'] = data.get('intro_text', '')
                    
                    if 'results' in data:
                        for t in ['A', 'B', 'C']:
                            if t in data['results']:
                                res = data['results'][t]
                                st.session_state[f'res_title_{t}'] = res.get('title', '')
                                st.session_state[f'res_desc_{t}'] = res.get('desc', '')
                                st.session_state[f'res_btn_{t}'] = res.get('btn', '')
                    
                    if 'questions' in data:
                        for i, qd in enumerate(data['questions']):
                            idx = i + 1
                            if idx > 5: break
                            st.session_state[f'q_text_{idx}'] = qd.get('question', '')
                            for j, ans in enumerate(qd.get('answers', [])):
                                adx = j + 1
                                if adx > 4: break
                                st.session_state[f'q{idx}_a{adx}_text'] = ans.get('text', '')
                                st.session_state[f'q{idx}_a{adx}_type'] = ans.get('type', 'A')
                    
                    st.session_state.ai_count += 1
                    status.success(f"構成案が完成しました！(残り {remaining - 1}回)")
                    time.sleep(0.5)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"エラー: {e}")

    # --- 編集フォーム ---
    init_state('page_title', '')
    init_state('main_heading', '')
    init_state('intro_text', '')
    
    with st.form("editor"):
        st.caption("基本設定")
        c_basic1, c_basic2 = st.columns([1, 2])
        with c_basic1:
            page_title = st.text_input("タブ名", key='page_title')
        with c_basic2:
            main_heading = st.text_input("タイトル", key='main_heading')
        
        intro_text = st.text_area("導入文", key='intro_text', height=80)
        
        st.markdown("---")
        st.caption("診断結果パターン (A / B / C)")
        
        results_obj = {}
        tabs = st.tabs(["タイプA", "タイプB", "タイプC"])
        
        for i, t in enumerate(['A', 'B', 'C']):
            init_state(f'res_title_{t}', '')
            init_state(f'res_desc_{t}', '')
            init_state(f'res_btn_{t}', '')
            init_state(f'res_link_{t}', '')

            with tabs[i]:
                rt = st.text_input("結果タイトル", key=f'res_title_{t}')
                rd = st.text_area("説明文", key=f'res_desc_{t}', height=100)
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    rb = st.text_input("ボタン文字", key=f'res_btn_{t}')
                with c_btn2:
                    rl = st.text_input("リンクURL", key=f'res_link_{t}')
                results_obj[t] = {'title': rt, 'desc': rd, 'btn': rb, 'link': rl}

        st.markdown("---")
        st.caption("質問設定 (5問)")
        
        questions_obj = []
        for q in range(1, 6):
            init_state(f'q_text_{q}', '')
            with st.expander(f"Q{q}. 質問文を編集"):
                qt = st.text_input("質問文", key=f'q_text_{q}')
                ans_list = []
                for a in range(1, 5):
                    init_state(f'q{q}_a{a}_text', '')
                    init_state(f'q{q}_a{a}_type', 'A')
                    
                    c_ans1, c_ans2 = st.columns([3, 1])
                    with c_ans1:
                        at = st.text_input(f"選択肢{a}", key=f'q{q}_a{a}_text')
                    with c_ans2:
                        aty = st.selectbox("加点", ["A", "B", "C"], key=f'q{q}_a{a}_type')
                    ans_list.append({'text': at, 'type': aty})
                
                if qt:
                    questions_obj.append({'question': qt, 'answers': ans_list})

        st.markdown("---")
        st.write("#### 🌐 公開設定")
        st.info("メールアドレスを入力すると、この診断専用のURLが発行されます。")
        user_email = st.text_input("あなたのメールアドレス", placeholder="example@mail.com")
        
        submit = st.form_submit_button("保存して公開URLを発行する", type="primary", use_container_width=True)

    if submit:
        if not user_email:
            st.error("メールアドレスを入力してください")
        elif len(questions_obj) < 1:
            st.error("質問が入力されていません")
        elif not supabase:
            st.error("データベースに接続できませんでした")
        else:
            save_data = {
                'page_title': page_title,
                'main_heading': main_heading,
                'intro_text': intro_text,
                'results': results_obj,
                'questions': questions_obj
            }
            
            try:
                res = supabase.table("quizzes").insert({
                    "email": user_email,
                    "title": main_heading,
                    "content": save_data
                }).execute()
                
                new_id = res.data[0]['id']
                base_url = "https://shindan-quiz-maker.streamlit.app"
                public_url = f"{base_url}/?id={new_id}"
                
                st.success("公開に成功しました！")
                st.balloons()
                
                st.markdown(f"""
                <div style="background: #dcfce7; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; color: #166534;">
                    <p style="font-weight: bold; margin-bottom: 10px;">👇 あなたの診断URLはこちら</p>
                    <code style="font-size: 1.2rem; user-select: all;">{public_url}</code>
                </div>
                """, unsafe_allow_html=True)
                
                st.link_button("👉 今すぐ診断ページを見る", public_url, type="primary", use_container_width=True)
                
            except Exception as e:
                st.error(f"保存エラー: {e}")
