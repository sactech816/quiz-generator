import streamlit as st
import json
import openai
import os

# ページ設定
st.set_page_config(page_title="AI診断LPジェネレーター", layout="wide")

# --- セッション状態の初期化 ---
def init_state(key, default_val):
    if key not in st.session_state:
        st.session_state[key] = default_val

# 基本情報
init_state('page_title', '【1分でわかる】〇〇診断')
init_state('main_heading', 'あなたの〇〇タイプ診断')
init_state('intro_text', '5つの質問に答えるだけで、あなたの現状と対策がわかります。')

# 結果データ (3パターン)
for i, t in enumerate(['A', 'B', 'C']):
    init_state(f'res_title_{t}', f'タイプ{t}')
    init_state(f'res_desc_{t}', 'あなたはこんな人です。')
    init_state(f'res_link_{t}', '#')
    init_state(f'res_btn_{t}', '詳細を見る')

# 質問データ (5問 x 4択)
for q in range(1, 6):
    init_state(f'q_text_{q}', '')
    for a in range(1, 5):
        init_state(f'q{q}_a{a}_text', '')
        def_type = ['A', 'B', 'C', 'A'][a-1]
        init_state(f'q{q}_a{a}_type', def_type)

# --- HTMLテンプレート ---
html_template = """
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

st.title("🤖 AI診断LPジェネレーター")
st.markdown("AIにテーマを伝えるだけで、質問から結果まで全自動で作成します。")

# === サイドバー：API設定 & AI生成 ===
with st.sidebar:
    # ▼▼▼ 修正箇所ここから ▼▼▼
    
    # APIキーは入力させず、Secretsから読み込む
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        st.error("管理者設定エラー：APIキーが設定されていません。")
        st.stop() # キーがない場合はここで止める
    
    st.header("✨ AIで自動生成")
    theme = st.text_area("どんな診断を作りますか？", "例：30代女性向けの婚活診断。辛口でアドバイスする。", height=100)
    
    if st.button("AIで構成案を作る", type="primary"):
        try:
            # プレースホルダー（メッセージ表示領域）を作成
            status_text = st.empty()
            progress_bar = st.progress(0)
            
            # ステップ1: 思考開始
            status_text.info("🧠 AIがテーマを分析しています...")
            progress_bar.progress(10)
            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""
            （プロンプトの中身は前回のままでOK）
            """
            
            # ステップ2: 生成実行 (ここが一番長い)
            status_text.info("🤔 質問と診断ロジックを構築中... (約15秒)")
            progress_bar.progress(30)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            # ステップ3: データ反映
            progress_bar.progress(80)
            status_text.info("🎨 画面に反映しています...")
            data = json.loads(response.choices[0].message.content)
            
            # ... (データの保存処理：st.session_stateへの代入などは前回のまま) ...
            # ここに前回の代入ロジックが入ります

            progress_bar.progress(100)
            status_text.success("✅ 完了しました！")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"エラー: {e}")

# === メインフォーム ===
with st.form("generator_form"):
    st.subheader("1. 基本情報")
    page_title = st.text_input("タイトル", key='page_title')
    main_heading = st.text_input("大見出し", key='main_heading')
    intro_text = st.text_area("導入文", key='intro_text', height=80)
    
    st.markdown("---")
    st.subheader("2. 結果設定 (A/B/C)")
    
    results_data = {}
    cols = st.columns(3)
    for i, type_char in enumerate(['A', 'B', 'C']):
        with cols[i]:
            st.markdown(f"**タイプ{type_char}**")
            r_title = st.text_input(f"結果名", key=f'res_title_{type_char}')
            r_desc = st.text_area(f"説明文", key=f'res_desc_{type_char}')
            r_link = st.text_input(f"リンクURL", key=f'res_link_{type_char}')
            r_btn = st.text_input(f"ボタン文字", key=f'res_btn_{type_char}')
            
            results_data[type_char] = {'title': r_title, 'desc': r_desc, 'link': r_link, 'btn': r_btn}

    st.markdown("---")
    st.subheader("3. 質問設定 (全5問)")
    
    questions_list = []
    for q_num in range(1, 6):
        with st.expander(f"質問 {q_num}", expanded=(q_num==1)):
            q_text = st.text_input("質問文", key=f'q_text_{q_num}')
            
            ans_objs = []
            c1, c2 = st.columns(2)
            c3, c4 = st.columns(2)
            cols_ans = [c1, c2, c3, c4]
            
            for a_idx in range(1, 5):
                with cols_ans[a_idx-1]:
                    a_txt = st.text_input(f"選択肢{a_idx}", key=f'q{q_num}_a{a_idx}_text')
                    a_typ = st.selectbox(f"加点", ["A", "B", "C"], key=f'q{q_num}_a{a_idx}_type')
                    ans_objs.append({"text": a_txt, "type": a_typ})

            if q_text:
                questions_list.append({"question": q_text, "answers": ans_objs})

    submitted = st.form_submit_button("✨ 診断LPを生成する")

if submitted:
    if len(questions_list) < 1:
        st.error("質問データがありません。")
    else:
        results_html_str = ""
        for type_char, data in results_data.items():
            results_html_str += f"<div id='result-{type_char}' class='hidden p-8 bg-white rounded-2xl shadow-xl'><p class='text-center text-blue-600 font-bold mb-2'>診断結果</p><h2 class='text-2xl font-bold text-center mb-4'>{data['title']}</h2><p class='mb-6 text-slate-600'>{data['desc']}</p><a href='{data['link']}' class='block w-full text-center bg-blue-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-blue-700 transition-transform transform hover:scale-105 shadow-lg'>→ {data['btn']}</a></div>"
        
        final_html = html_template.format(
            page_title=page_title, 
            main_heading=main_heading, 
            intro_text=intro_text, 
            results_html=results_html_str, 
            quiz_data_json=json.dumps(questions_list, ensure_ascii=False)
        )
        
        st.success("✅ 生成成功！")

        st.download_button("📥 HTMLをダウンロード", final_html, "my_diagnosis.html", "text/html")
