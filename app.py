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
st.set_page_config(page_title="Diagnosis Portal", page_icon="💎", layout="wide")

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

if query_params.get("admin") == "secret":
    st.session_state.is_admin = True
    st.toast("🔓 管理者モード")

# --- 🅰️ プレイ画面 ---
if quiz_id:
    styles.apply_portal_style()
    if not supabase: st.stop()
    try:
        if f"viewed_{quiz_id}" not in st.session_state:
            logic.increment_views(supabase, quiz_id)
            st.session_state[f"viewed_{quiz_id}"] = True

        res = supabase.table("quizzes").select("*").eq("id", quiz_id).execute()
        if not res.data:
            st.error("診断が見つかりません。")
            if st.button("トップへ戻る"): st.query_params.clear(); st.rerun()
            st.stop()
        
        data = res.data[0]['content']
        html_content = logic.generate_html_content(data)
        components.html(html_content, height=800, scrolling=True)
        
        c_like, c_back = st.columns([1, 1])
        with c_like:
            liked_key = f"liked_{quiz_id}"
            if st.session_state.get(liked_key, False):
                st.button("❤️ いいね済み", disabled=True, use_container_width=True)
            else:
                if st.button("🤍 この診断に「いいね」する", type="secondary", use_container_width=True):
                    logic.increment_likes(supabase, quiz_id)
                    st.session_state[liked_key] = True
                    st.balloons(); st.rerun()
        with c_back:
            if st.button("🏠 ポータルトップへ戻る", use_container_width=True):
                st.query_params.clear(); st.rerun()
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
        c1, c2 = st.columns([1, 2])
        with c1: st.markdown("### 💎 診断クイズメーカー")
        with c2: st.text_input("search", label_visibility="collapsed", placeholder="🔍 キーワード検索...")
        st.write("") 
        st.markdown(styles.HERO_HTML, unsafe_allow_html=True)
        st.markdown('<div class="big-create-btn">', unsafe_allow_html=True)
        if st.button("✨ 新しい診断を作成する", type="primary", use_container_width=True):
            st.session_state.page_mode = 'create'; st.rerun()
        st.markdown('</div><br>', unsafe_allow_html=True)
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
                        views = q.get('views', 0); likes = q.get('likes', 0)
                        with st.container(border=True):
                            st.markdown(styles.get_card_content_html(q.get('title','無題'), content.get('intro_text',''), img_url, views, likes), unsafe_allow_html=True)
                            st.link_button("▶ 今すぐ診断する", link_url, use_container_width=True)
                            if st.session_state.is_admin:
                                if st.button("削除", key=f"del_{q['id']}"):
                                    logic.delete_quiz(supabase, q['id']); st.rerun()
                        st.write("") 
            else: st.info("まだ投稿がありません")

    elif st.session_state.page_mode == 'create':
        styles.apply_editor_style()
        if st.button("← ポータルへ戻る"):
            st.session_state.page_mode = 'home'; st.rerun()
        st.title("📝 診断作成エディタ")
        
        # AIアシスタント (縦長＆ヒント付き)
        st.markdown("#### 🧠 AIアシスタント")
        st.caption("テーマを入力すると、AIが構成案（タイトル・質問・結果）を自動作成します。")
        with st.container(border=True):
            if "OPENAI_API_KEY" in st.secrets: api_key = st.secrets["OPENAI_API_KEY"]
            else: st.error("APIキー設定なし"); st.stop()
            
            theme = st.text_area("診断テーマ", height=150, placeholder="例：\n・30代女性向けの辛口婚活診断\n・自分に似合うアロマ診断\n・起業家タイプ診断 (厳しめ)")
            st.caption("💡 ヒント: 「ターゲット（誰向けか）」や「トーン（辛口/優しめ）」を指定すると精度が上がります。")
            
            if st.button("AIで構成案を作成", type="primary"):
                try:
                    msg = st.empty(); msg.info("AIが執筆中...")
                    client = openai.OpenAI(api_key=api_key)
                    prompt = f"""
                    あなたはプロの診断作家です。テーマ: {theme}
                    【絶対厳守】
                    1. 質問は「必ず5問」
                    2. 選択肢は「必ず4つ」
                    3. 結果は「必ず3つ（A, B, C）」
                    4. JSONのみ出力
                    出力JSON:
                    {{
                        "page_title": "", "main_heading": "", "intro_text": "", "image_keyword": "英単語1語",
                        "results": {{ "A": {{ "title": "", "desc": "600字", "btn": "", "link":"" }}, "B": {{...}}, "C": {{...}} }},
                        "questions": [ {{ "question": "", "answers": [ {{ "text": "", "type": "A" }}, {{ "text": "", "type": "B" }}, {{ "text": "", "type": "C" }}, {{ "text": "", "type": "A" }} ] }} ]
                    }}
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
                            if i>=5: break
                            st.session_state[f'q_text_{i+1}'] = q.get('question','')
                            for j,a in enumerate(q.get('answers',[])):
                                if j>=4: break
                                st.session_state[f'q{i+1}_a{j+1}_text'] = a.get('text','')
                                st.session_state[f'q{i+1}_a{j+1}_type'] = a.get('type','A')
                    msg.success("完了！"); time.sleep(0.5); st.rerun()
                except Exception as e: st.error(e)

        # フォーム
        init_state('page_title',''); init_state('main_heading',''); init_state('intro_text',''); init_state('image_keyword','')
        
        with st.form("editor"):
            st.subheader("1. 基本設定")
            c1, c2 = st.columns(2)
            with c1: page_title = st.text_input("タブ名", key='page_title')
            with c2: main_heading = st.text_input("タイトル", key='main_heading')
            intro_text = st.text_area("導入文", key='intro_text')
            image_keyword = st.text_input("ポータル掲載用画像テーマ (英単語)", key='image_keyword', help="AI画像生成に使われます")
            
            # ★カラー設定
            st.markdown("---")
            st.subheader("2. デザイン設定")
            color_main = st.color_picker("メインカラー", "#2563eb")

            # ★結果設定 (LINE含む)
            st.markdown("---")
            st.subheader("3. 結果ページ設定")
            res_obj = {}
            tabs = st.tabs(["Type A", "Type B", "Type C"])
            for i,t in enumerate(['A','B','C']):
                init_state(f'res_title_{t}',''); init_state(f'res_desc_{t}',''); init_state(f'res_btn_{t}',''); init_state(f'res_link_{t}','')
                # LINE用state
                init_state(f'res_line_url_{t}',''); init_state(f'res_line_text_{t}',''); init_state(f'res_line_img_{t}','')
                
                with tabs[i]:
                    rt = st.text_input("結果名", key=f'res_title_{t}')
                    rd = st.text_area("説明文", key=f'res_desc_{t}', height=200)
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1: rb = st.text_input("ボタン名", key=f'res_btn_{t}')
                    with c_btn2: rl = st.text_input("URL", key=f'res_link_{t}')
                    
                    # LINE設定エリア
                    with st.expander("LINE登録誘導を追加する"):
                        line_u = st.text_input("LINE公式アカウントURL", key=f'res_line_url_{t}')
                        line_t = st.text_area("誘導文 (例: 登録で特典プレゼント)", key=f'res_line_text_{t}')
                        line_i = st.text_input("画像URL (任意)", key=f'res_line_img_{t}')
                        
                    res_obj[t] = {
                        'title':rt, 'desc':rd, 'btn':rb, 'link':rl,
                        'line_url':line_u, 'line_text':line_t, 'line_img':line_i
                    }

            # ★質問設定 (インデント修正済み: 1つの枠に収める)
            st.markdown("---")
            st.subheader("4. 質問設定")
            q_obj = []
            for q in range(1,6):
                init_state(f'q_text_{q}','')
                with st.expander(f"Q{q} の内容を編集", expanded=(q==1)):
                    qt = st.text_input("質問文", key=f'q_text_{q}')
                    st.caption("選択肢設定")
                    ans_list = []
                    for a in range(1,5):
                        init_state(f'q{q}_a{a}_text',''); init_state(f'q{q}_a{a}_type','A')
                        c_opt1, c_opt2 = st.columns([3, 1])
                        with c_opt1:
                            at = st.text_input(f"選択肢{a}", key=f'q{q}_a{a}_text')
                        with c_opt2:
                            aty = st.selectbox("加点先", ["A","B","C"], key=f'q{q}_a{a}_type')
                        ans_list.append({'text':at, 'type':aty})
                    if qt: q_obj.append({'question':qt, 'answers':ans_list})

            st.markdown("---")
            st.write("#### 📤 公開・保存")
            price = st.number_input("販売価格 (円)", 980, 98000, 980, 100)
            email = st.text_input("Email (必須)", placeholder="mail@example.com")
            
            c1, c2 = st.columns(2)
            with c1: sub_free = st.form_submit_button("🌐 無料公開", type="primary")
            with c2: is_pub = st.checkbox("ポータル掲載"); sub_paid = st.form_submit_button(f"💾 {price}円で購入")
            
            if sub_free or sub_paid:
                if not email: st.error("Email必須")
                elif not q_obj: st.error("質問なし")
                else:
                    s_data = {
                        'page_title':page_title, 'main_heading':main_heading, 'intro_text':intro_text, 
                        'image_keyword':image_keyword, 'color_main':color_main, # 色を追加
                        'results':res_obj, 'questions':q_obj
                    }
                    try:
                        is_p = True if sub_free else is_pub
                        res = supabase.table("quizzes").insert({"email":email, "title":main_heading, "content":s_data, "is_public":is_p, "price":price}).execute()
                        new_id = res.data[0]['id']
                        base = "https://shindan-quiz-maker.streamlit.app"
                        if sub_free:
                            if logic.send_email(email, f"{base}/?id={new_id}", main_heading): st.success("完了！メールを確認してください"); st.balloons(); time.sleep(2); st.session_state.page_mode='home'; st.rerun()
                            else: st.error("メール送信失敗")
                        if sub_paid:
                            sess = stripe.checkout.Session.create(payment_method_types=['card'], line_items=[{'price_data':{'currency':'jpy','product_data':{'name':f'{main_heading}'},'unit_amount':price},'quantity':1}], mode='payment', success_url=f"{base}/?session_id={{CHECKOUT_SESSION_ID}}", cancel_url=f"{base}/", metadata={'quiz_id':new_id})
                            st.link_button("決済へ進む", sess.url, type="primary")
                    except Exception as e: st.error(e)
