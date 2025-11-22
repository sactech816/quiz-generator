import streamlit as st
import json
import openai
import os
import time
import stripe
import streamlit.components.v1 as components

import styles
import logic

os.environ["PYTHONIOENCODING"] = "utf-8"
st.set_page_config(page_title="診断クイズメーカー", page_icon="💎", layout="wide")

if "stripe" in st.secrets: stripe.api_key = st.secrets["stripe"]["api_key"]
supabase = logic.init_supabase()

def init_state(key, val):
    if key not in st.session_state: st.session_state[key] = val

init_state('ai_count', 0)
init_state('page_mode', 'home')
init_state('is_admin', False)
AI_LIMIT = 5

query_params = st.query_params
quiz_id = query_params.get("id", None)
session_id = query_params.get("session_id", None)

# --- 管理者判定 ---
if query_params.get("admin") == "secret":
    st.session_state.is_admin = True
    st.toast("🔓 管理者モード")

# ==========================================
# 🅰️ プレイ画面 (Web公開)
# ==========================================
if quiz_id:
    styles.apply_portal_style()
    if not supabase: st.stop()
    try:
        # ★PVカウントアップ (初回ロード時のみ)
        if f"viewed_{quiz_id}" not in st.session_state:
            logic.increment_views(supabase, quiz_id)
            st.session_state[f"viewed_{quiz_id}"] = True

        res = supabase.table("quizzes").select("*").eq("id", quiz_id).execute()
        if not res.data:
            st.error("診断が見つかりません。")
            if st.button("トップへ戻る"): st.query_params.clear(); st.rerun()
            st.stop()
        
        data = res.data[0]['content']
        # HTML表示
        html_content = logic.generate_html_content(data)
        components.html(html_content, height=800, scrolling=True)
        
        # ★いいねボタンエリア
        c_like, c_back = st.columns([1, 1])
        with c_like:
            # 既にいいねしたかチェック
            liked_key = f"liked_{quiz_id}"
            if st.session_state.get(liked_key, False):
                st.button("❤️ いいね済み", disabled=True, use_container_width=True)
            else:
                if st.button("🤍 この診断に「いいね」する", use_container_width=True):
                    logic.increment_likes(supabase, quiz_id)
                    st.session_state[liked_key] = True
                    st.balloons()
                    st.rerun()
        
        with c_back:
            if st.button("🏠 ポータルトップへ戻る", use_container_width=True):
                st.query_params.clear()
                st.rerun()

    except Exception as e: st.error(e)

# --- 🅱️ 決済完了画面 ---
elif session_id:
    styles.apply_portal_style()
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            paid_id = session.metadata.get('quiz_id')
            res = supabase.table("quizzes").select("*").eq("id", paid_id).execute()
            if res.data:
                data = res.data[0]['content']
                st.balloons()
                st.success("✅ お支払いが完了しました！")
                final_html = logic.generate_html_content(data)
                st.download_button("📥 HTMLをダウンロード", final_html, "diagnosis.html", "text/html", type="primary")
                if st.button("トップに戻る"): st.query_params.clear(); st.rerun()
                st.stop()
    except Exception as e: st.error(f"決済エラー: {e}")

# --- 🆑 ポータル & 作成画面 ---
else:
    if st.session_state.page_mode == 'home':
        styles.apply_portal_style()
        
        c1, c2 = st.columns([1, 2])
        with c1: st.markdown("### 💎 診断クイズメーカー")
        with c2: st.text_input("search", label_visibility="collapsed", placeholder="🔍 キーワード検索...")
        st.write("") 

        st.markdown(styles.HERO_HTML, unsafe_allow_html=True)
        
        st.markdown('<div class="big-create-btn">', unsafe_allow_html=True)
        if st.button("✨ 新しい診断を作成する", type="primary", use_container_width=True):
            st.session_state.page_mode = 'create'; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.write("")

        # ギャラリー
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
                        
                        # ★統計情報を渡す
                        views = q.get('views', 0)
                        likes = q.get('likes', 0)
                        
                        with st.container(border=True):
                            st.markdown(
                                styles.get_card_content_html(q.get('title','無題'), content.get('intro_text',''), img_url, views, likes), 
                                unsafe_allow_html=True
                            )
                            
                            # 純正リンクボタン
                            st.link_button("▶ 今すぐ診断する", link_url, use_container_width=True)
                            
                            if st.session_state.is_admin:
                                st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                                if st.button("🗑️ 削除", key=f"del_{q['id']}"):
                                    if logic.delete_quiz(supabase, q['id']):
                                        st.toast("削除しました"); time.sleep(1); st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.write("") 
            else:
                st.info("まだ投稿がありません")

    # (作成画面は変更なしのため省略。前回のコードのままでOKです)
    elif st.session_state.page_mode == 'create':
        styles.apply_editor_style()
        if st.button("← ポータルへ戻る"):
            st.session_state.page_mode = 'home'; st.rerun()
        st.title("📝 診断作成エディタ")
        
        with st.sidebar:
            if "OPENAI_API_KEY" in st.secrets: api_key = st.secrets["OPENAI_API_KEY"]
            else: st.error("APIキー設定なし"); st.stop()
            st.header("🧠 AIアシスタント")
            theme = st.text_area("テーマ", "例：30代女性向けの辛口婚活診断")
            if st.button("AIで構成案を作成", type="primary"):
                try:
                    msg = st.empty(); msg.info("AIが執筆中...")
                    client = openai.OpenAI(api_key=api_key)
                    # (プロンプトなどは前回と同じ)
                    prompt = f"""テーマ: {theme} (詳細省略)"""
                    # ... (以下略、前回のcreateモードと同じコードを貼り付けてください) ...
                    # ※文字数制限のため省略していますが、前回のコードと全く同じで構いません
