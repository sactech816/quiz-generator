import streamlit as st
import json
import openai
import os
import time
from supabase import create_client, Client

# 日本語文字化け防止
os.environ["PYTHONIOENCODING"] = "utf-8"

# ページ設定
st.set_page_config(page_title="診断メーカー", layout="wide")

# --- Supabase接続設定 ---
@st.cache_resource
def init_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"データベース接続エラー: {e}")
    st.stop()

# --- セッション状態の初期化 ---
def init_state(key, default_val):
    if key not in st.session_state:
        st.session_state[key] = default_val

# --- モード判定（作成モード vs 閲覧モード）---
# URLに '?id=...' があるかどうかで判断する
query_params = st.query_params
quiz_id = query_params.get("id", None)

# ==========================================
# モードA：閲覧モード (クイズをプレイする画面)
# ==========================================
if quiz_id:
    try:
        # データベースからクイズ情報を取得
        response = supabase.table("quizzes").select("*").eq("id", quiz_id).execute()
        
        if not response.data:
            st.error("指定された診断が見つかりません。")
            if st.button("トップに戻る"):
                st.query_params.clear()
                st.rerun()
            st.stop()
            
        data = response.data[0]
        content = data['content'] # JSONの中身
        
        # 閲覧数（PV）のカウントアップ（簡易実装）
        # ※厳密なPV計測はロード時に行うが、ここではシンプルに
        
        # --- ここからプレイ画面 ---
        st.title(content.get('main_heading', '診断'))
        
        # 状態管理
        if f"q_idx_{quiz_id}" not in st.session_state:
            st.session_state[f"q_idx_{quiz_id}"] = 0
            st.session_state[f"scores_{quiz_id}"] = {'A': 0, 'B': 0, 'C': 0}
            st.session_state[f"finished_{quiz_id}"] = False

        current_idx = st.session_state[f"q_idx_{quiz_id}"]
        questions = content.get('questions', [])
        
        if not st.session_state[f"finished_{quiz_id}"]:
            # 導入文
            if current_idx == 0:
                st.markdown(content.get('intro_text', ''))
                st.markdown("---")

            # 質問表示
            if current_idx < len(questions):
                q_data = questions[current_idx]
                st.subheader(f"Q{current_idx + 1}. {q_data['question']}")
                
                for ans in q_data['answers']:
                    if st.button(ans['text'], key=f"ans_{current_idx}_{ans['text']}"):
                        # 加点
                        st.session_state[f"scores_{quiz_id}"][ans['type']] += 1
                        # 次へ
                        st.session_state[f"q_idx_{quiz_id}"] += 1
                        st.rerun()
            else:
                st.session_state[f"finished_{quiz_id}"] = True
                st.rerun()
        
        else:
            # 結果表示
            scores = st.session_state[f"scores_{quiz_id}"]
            max_type = max(scores, key=scores.get) # A, B, Cの中で一番多いもの
            
            res_data = content['results'].get(max_type, {})
            
            st.balloons()
            st.success("診断完了！")
            st.markdown(f"## あなたは... **{res_data.get('title', 'タイプ' + max_type)}**")
            st.info(res_data.get('desc', ''))
            
            link = res_data.get('link', '#')
            btn_text = res_data.get('btn', '詳細を見る')
            st.link_button(btn_text, link)
            
            if st.button("もう一度診断する"):
                st.session_state[f"q_idx_{quiz_id}"] = 0
                st.session_state[f"scores_{quiz_id}"] = {'A': 0, 'B': 0, 'C': 0}
                st.session_state[f"finished_{quiz_id}"] = False
                st.rerun()

            st.markdown("---")
            if st.button("自分も診断を作る"):
                st.query_params.clear()
                st.rerun()

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

# ==========================================
# モードB：作成モード (ジェネレーター画面)
# ==========================================
else:
    # 初期値設定
    init_state('page_title', '【1分でわかる】〇〇診断')
    init_state('main_heading', 'あなたの〇〇タイプ診断')
    init_state('intro_text', '5つの質問に答えるだけで、あなたの現状と対策がわかります。')
    
    for t in ['A', 'B', 'C']:
        init_state(f'res_title_{t}', f'タイプ{t}')
        init_state(f'res_desc_{t}', 'あなたはこんな人です。')
        init_state(f'res_link_{t}', '#')
        init_state(f'res_btn_{t}', '詳細を見る')
        
    for q in range(1, 6):
        init_state(f'q_text_{q}', '')
        for a in range(1, 5):
            init_state(f'q{q}_a{a}_text', '')
            def_type = ['A', 'B', 'C', 'A'][a-1]
            init_state(f'q{q}_a{a}_type', def_type)

    st.title("🛠️ 診断クイズメーカー")
    st.markdown("AIで作って、Webに公開しよう！")

    # --- サイドバー：AI生成 ---
    with st.sidebar:
        if "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
        else:
            st.error("APIキーが設定されていません")
            st.stop()
        
        st.header("✨ AIで自動生成")
        theme = st.text_area("テーマを入力", "例：起業家タイプ診断", height=100)
        
        if st.button("AIで構成案を作る", type="primary"):
            try:
                status = st.empty()
                status.info("AIが思考中...")
                client = openai.OpenAI(api_key=api_key)
                
                prompt = f"""
                テーマ: {theme}
                以下のJSON形式で診断を作成してください。
                {{
                    "page_title": "タイトル",
                    "main_heading": "大見出し",
                    "intro_text": "導入文",
                    "results": {{
                        "A": {{ "title": "...", "desc": "...", "btn": "..." }},
                        "B": {{ "title": "...", "desc": "...", "btn": "..." }},
                        "C": {{ "title": "...", "desc": "...", "btn": "..." }}
                    }},
                    "questions": [
                        {{
                            "question": "...",
                            "answers": [
                                {{ "text": "...", "type": "A" }},
                                {{ "text": "...", "type": "B" }},
                                {{ "text": "...", "type": "C" }},
                                {{ "text": "...", "type": "A" }}
                            ]
                        }}
                    ]
                }}
                質問は5問。
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
                            
                status.success("完了！")
                time.sleep(0.5)
                st.rerun()
                
            except Exception as e:
                st.error(f"エラー: {e}")

    # --- メインフォーム ---
    with st.form("editor"):
        st.subheader("基本設定")
        page_title = st.text_input("タイトル", key='page_title')
        main_heading = st.text_input("大見出し", key='main_heading')
        intro_text = st.text_area("導入文", key='intro_text')
        
        st.markdown("---")
        st.subheader("結果パターン (A/B/C)")
        c1, c2, c3 = st.columns(3)
        
        # データ収集用
        results_obj = {}
        
        for i, t in enumerate(['A', 'B', 'C']):
            with [c1, c2, c3][i]:
                st.markdown(f"**タイプ{t}**")
                rt = st.text_input("名前", key=f'res_title_{t}')
                rd = st.text_area("説明", key=f'res_desc_{t}')
                rb = st.text_input("ボタン", key=f'res_btn_{t}')
                rl = st.text_input("URL", key=f'res_link_{t}')
                results_obj[t] = {'title': rt, 'desc': rd, 'btn': rb, 'link': rl}

        st.markdown("---")
        st.subheader("質問 (5問)")
        
        questions_obj = []
        for q in range(1, 6):
            with st.expander(f"質問 {q}"):
                qt = st.text_input("文", key=f'q_text_{q}')
                ans_list = []
                cc1, cc2 = st.columns(2)
                cc3, cc4 = st.columns(2)
                for a, col in enumerate([cc1, cc2, cc3, cc4]):
                    idx = a + 1
                    at = st.text_input(f"選択肢{idx}", key=f'q{q}_a{idx}_text')
                    aty = st.selectbox("加点", ["A", "B", "C"], key=f'q{q}_a{idx}_type')
                    ans_list.append({'text': at, 'type': aty})
                
                if qt:
                    questions_obj.append({'question': qt, 'answers': ans_list})

        # 保存のためのメールアドレス入力
        st.markdown("---")
        st.subheader("公開設定")
        user_email = st.text_input("作成者のメールアドレス (公開には必須です)")
        
        submit = st.form_submit_button("🌐 保存して公開URLを発行する")

    if submit:
        if not user_email:
            st.error("メールアドレスを入力してください")
        elif len(questions_obj) < 1:
            st.error("質問がありません")
        else:
            # 保存するJSONデータ
            save_data = {
                'page_title': page_title,
                'main_heading': main_heading,
                'intro_text': intro_text,
                'results': results_obj,
                'questions': questions_obj
            }
            
            try:
                # Supabaseへ保存
                res = supabase.table("quizzes").insert({
                    "email": user_email,
                    "title": main_heading,
                    "content": save_data
                }).execute()
                
                # IDを取得してURLを表示
                new_id = res.data[0]['id']
                base_url = "https://keisho-quiz.streamlit.app" # ★ここを自分のURLに変える！
                public_url = f"{base_url}/?id={new_id}"
                
                st.success("公開しました！")
                st.code(public_url, language="text")
                st.link_button("👉 公開ページへ移動", public_url)
                
            except Exception as e:
                st.error(f"保存エラー: {e}")
