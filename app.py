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

# --- 🅰️ プレイ画面 ---
if quiz_id:
    styles.apply_portal_style()
    if not supabase: st.stop()
    try:
        res = supabase.table("quizzes").select("*").eq("id", quiz_id).execute()
        if not res.data:
            st.error("診断が見つかりません。")
            if st.button("トップへ戻る"): st.query_params.clear(); st.rerun()
            st.stop()
        
        data = res.data[0]['content']
        html_content = logic.generate_html_content(data)
        components.html(html_content, height=800, scrolling=True)
        
        st.markdown('<div style="text-align:center;margin-top:20px;">', unsafe_allow_html=True)
        if st.button("🏠 ポータルトップへ戻る"): st.query_params.clear(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e: st.error(e)

# --- 🅱️ 決済完了 ---
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

# --- 🆑 ポータル & 作成 ---
else:
    if st.session_state.page_mode == 'home':
        styles.apply_portal_style()
        
        # ナビ
        c1, c2 = st.columns([1, 2])
        with c1: st.markdown("### 💎 診断クイズメーカー")
        with c2: st.text_input("search", label_visibility="collapsed", placeholder="🔍 キーワード検索...")
        st.write("") 

        # ヒーロー
        st.markdown(styles.HERO_HTML, unsafe_allow_html=True)
        
        # 作成ボタン
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
                        # 画像
                        keyword = content.get('image_keyword', 'abstract')
                        seed = q['id'][-4:] 
                        img_url = f"https://image.pollinations.ai/prompt/{keyword}%20{seed}?width=350&height=180&nologo=true"
                        
                        # ★リンクURL
                        base = "https://shindan-quiz-maker.streamlit.app"
                        link_url = f"{base}/?id={q['id']}"
                        
                        # ★カード全体をクリック可能にするHTMLを表示
                        st.markdown(
                            styles.get_clickable_card_html(link_url, q.get('title','無題'), content.get('intro_text',''), img_url), 
                            unsafe_allow_html=True
                        )
                        
                        # 管理者削除ボタン
                        if st.session_state.is_admin:
                            st.markdown('<div class="delete-wrapper">', unsafe_allow_html=True)
                            st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                            if st.button("🗑️ 削除", key=f"del_{q['id']}"):
                                if logic.delete_quiz(supabase, q['id']):
                                    st.toast("削除しました", icon="🗑️")
                                    time.sleep(1); st.rerun()
                            st.markdown('</div></div>', unsafe_allow_html=True)
                        else:
                            st.write("") # レイアウト調整用の余白
            else:
                st.info("まだ投稿がありません")

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
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"system","content":"Output JSON only"}, {"role":"user","content":prompt}], response_format={"type":"json_object"})
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
                    msg.success("完了！"); time.sleep(0.5); st.rerun()
                except Exception as e: st.error(e)

        init_state('page_title',''); init_state('main_heading',''); init_state('intro_text',''); init_state('image_keyword','')
        
        with st.form("editor"):
            st.subheader("基本情報")
            page_title = st.text_input("タブ名", key='page_title')
            main_heading = st.text_input("タイトル", key='main_heading')
            intro_text = st.text_area("導入文", key='intro_text')
            image_keyword = st.text_input("サムネイル用英単語", key='image_keyword')
            
            st.markdown("---")
            st.subheader("結果設定")
            res_obj = {}
            tabs = st.tabs(["Type A", "Type B", "Type C"])
            for i,t in enumerate(['A','B','C']):
                init_state(f'res_title_{t}',''); init_state(f'res_desc_{t}',''); init_state(f'res_btn_{t}',''); init_state(f'res_link_{t}','')
                with tabs[i]:
                    rt = st.text_input("名前", key=f'res_title_{t}')
                    rd = st.text_area("説明", key=f'res_desc_{t}', height=200)
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
                    s_data = {'page_title':page_title, 'main_heading':main_heading, 'intro_text':intro_text, 'image_keyword':image_keyword, 'results':res_obj, 'questions':q_obj}
                    try:
                        is_p = True if sub_free else is_pub
                        res = supabase.table("quizzes").insert({"email":email, "title":main_heading, "content":s_data, "is_public":is_p}).execute()
                        new_id = res.data[0]['id']
                        base = "https://shindan-quiz-maker.streamlit.app"
                        
                        if sub_free:
                            if logic.send_email(email, f"{base}/?id={new_id}", main_heading):
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
