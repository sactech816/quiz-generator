import streamlit as st
import json
import smtplib
from email.mime.text import MIMEText
from supabase import create_client

# HTMLテンプレート
HTML_TEMPLATE_RAW = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[[PAGE_TITLE]]</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --main-color: [[COLOR_MAIN]];
            --sub-color: #f3f4f6;
        }
        body { font-family: 'Noto Sans JP', sans-serif; background-color: var(--sub-color); color: #1f2937; display: flex; flex-direction: column; min-height: 100vh; }
        .quiz-container-wrapper { flex-grow: 1; display: flex; justify-content: center; align-items: flex-start; padding: 2rem; }
        .quiz-container { max-width: 700px; width: 100%; padding: 2.5rem; background-color: white; border-radius: 0.75rem; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
        .question-card, .result-card { padding: 1.5rem; border: 1px solid #e5e7eb; border-radius: 0.5rem; margin-bottom: 1.5rem; }
        
        .option-button { display: block; width: 100%; text-align: left; padding: 1rem 1.25rem; margin-bottom: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.375rem; background-color: #fff; transition: all 0.2s; cursor: pointer; }
        .option-button:hover { background-color: #eff6ff; border-color: var(--main-color); color: var(--main-color); }
        .option-button.selected { background-color: #dbeafe; border-color: var(--main-color); font-weight: 600; }
        
        .next-button, .restart-button { padding: 0.85rem 2rem; border-radius: 0.375rem; font-weight: 600; transition: all 0.2s; text-align: center; display: inline-block; cursor: pointer; width: 100%; border: none; color: white; background-color: var(--main-color); }
        .next-button:disabled { background-color: #9ca3af; cursor: not-allowed; }
        .restart-button { background-color: #4b5563; margin-top: 1rem; }
        
        .progress-bar-container { width: 100%; background-color: #e5e7eb; border-radius: 99px; overflow: hidden; margin-bottom: 1.5rem; }
        .progress-bar { height: 0.5rem; background-color: var(--main-color); width: 0%; transition: width 0.3s ease-in-out; }
        
        .hidden { display: none; }
        .result-title { font-size: 1.75rem; font-weight: 700; color: var(--main-color); margin-bottom: 1rem; text-align: center; }
        .result-text { line-height: 1.8; color: #4b5563; }
        
        .flyer-link-button { background-color: var(--main-color); color: white; text-decoration: none; display: block; padding: 1rem; border-radius: 0.375rem; text-align: center; font-weight: bold; transition: transform 0.2s; }
        .flyer-link-button:hover { transform: scale(1.02); }
        
        .line-section { background-color: #f0fdf4; border: 2px solid #22c55e; border-radius: 10px; padding: 20px; margin-top: 30px; text-align: center; }
        .line-title { color: #15803d; font-weight: bold; font-size: 1.1rem; margin-bottom: 10px; }
        .line-desc { font-size: 0.9rem; color: #333; margin-bottom: 15px; }
        .line-btn { background-color: #06c755; color: white; font-weight: bold; padding: 10px 30px; border-radius: 50px; text-decoration: none; display: inline-block; }
        .line-img { max-width: 150px; margin: 10px auto; display: block; }
    </style>
</head>
<body>
    <div id="quiz-data" style="display: none;">
        <div data-container="questions">[[QUESTIONS_HTML]]</div>
        <div data-container="results">[[RESULTS_HTML]]</div>
    </div>
    <div class="quiz-container-wrapper">
        <div class="quiz-container">
            <h1 class="text-2xl font-bold text-center mb-4 text-slate-800">[[MAIN_HEADING]]</h1>
            <p class="text-center text-gray-600 mb-8">[[INTRO_TEXT]]</p>
            <div id="quiz-area"></div>
            <div id="result-area" class="hidden"></div>
        </div>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', () => {
        let questions = [], results = [], currentQuestionIndex = 0, userAnswers = [];
        const quizArea = document.getElementById('quiz-area'), resultArea = document.getElementById('result-area');
        
        function shuffle(array) {
            for (let i = array.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }
            return array;
        }

        function loadData() {
            const d = document.getElementById('quiz-data');
            questions = Array.from(d.querySelectorAll('[data-container="questions"] [data-item="question"]')).map(q => ({
                text: q.querySelector('[data-key="text"]').textContent,
                options: shuffle(Array.from(q.querySelectorAll('[data-key="option"]')).map(o => ({ text: o.textContent, points: JSON.parse(o.dataset.points||'{}') })))
            }));
            results = Array.from(d.querySelectorAll('[data-container="results"] [data-item="result"]')).map(r => ({ id: r.dataset.id, html: r.innerHTML }));
        }
        function calcResult() {
            const s = {};
            userAnswers.forEach(a => { for(const t in a) s[t]=(s[t]||0)+a[t]; });
            let max=-1, rid=null;
            for(const r of results) { if((s[r.id]||0)>max) { max=s[r.id]; rid=r.id; } }
            return results.find(r => r.id===rid);
        }
        function showResult() {
            const r = calcResult();
            quizArea.classList.add('hidden');
            if(!r) return;
            resultArea.innerHTML = `<div class="result-card">${r.html}</div><div class="mt-6 text-center"><button class="restart-button" onclick="location.reload()">もう一度診断する</button></div>`;
            resultArea.classList.remove('hidden');
        }
        function dispQ() {
            const q = questions[currentQuestionIndex];
            const pct = ((currentQuestionIndex)/questions.length)*100;
            quizArea.innerHTML = `
                <div class="progress-bar-container"><div class="progress-bar" style="width: ${pct}%"></div></div>
                <div class="question-card"><p class="text-lg font-bold mb-4 text-slate-700">Q${currentQuestionIndex+1}. ${q.text}</p>${q.options.map((o,i)=>`<button class="option-button" data-i="${i}">${o.text}</button>`).join('')}</div>
                <div class="mt-6"><button class="next-button" disabled>次の質問へ</button></div>
            `;
            const nBtn = quizArea.querySelector('.next-button');
            if(currentQuestionIndex===questions.length-1) nBtn.textContent="結果を見る";
            quizArea.querySelectorAll('.option-button').forEach(b => b.addEventListener('click', e => {
                quizArea.querySelectorAll('.option-button').forEach(btn=>btn.classList.remove('selected'));
                e.target.classList.add('selected');
                userAnswers[currentQuestionIndex] = q.options[e.target.dataset.i].points;
                nBtn.disabled=false;
            }));
            nBtn.addEventListener('click', () => { if(userAnswers[currentQuestionIndex]==null)return; (currentQuestionIndex<questions.length-1)?(currentQuestionIndex++,dispQ()):showResult(); });
        }
        function startQuiz() { currentQuestionIndex=0; userAnswers=[]; resultArea.classList.add('hidden'); quizArea.classList.remove('hidden'); dispQ(); }
        loadData(); startQuiz();
    });
    </script>
</body>
</html>"""

def generate_html_content(data):
    html = HTML_TEMPLATE_RAW
    html = html.replace("[[PAGE_TITLE]]", data.get('page_title', '診断'))
    html = html.replace("[[MAIN_HEADING]]", data.get('main_heading', 'タイトル'))
    html = html.replace("[[INTRO_TEXT]]", data.get('intro_text', ''))
    # ★カラー設定を反映
    html = html.replace("[[COLOR_MAIN]]", data.get('color_main', '#2563eb'))
    
    q_html = ""
    for q in data.get('questions', []):
        o_html = ""
        for ans in q['answers']:
            pts = json.dumps({ans['type']: 1}, ensure_ascii=False).replace('"', '&quot;')
            o_html += f'<div data-key="option" data-points="{pts}">{ans["text"]}</div>'
        q_html += f'<div data-item="question"><p data-key="text">{q["question"]}</p><div data-key="options">{o_html}</div></div>'
    html = html.replace("[[QUESTIONS_HTML]]", q_html)
    
    r_html = ""
    for k, v in data.get('results', {}).items():
        b_html = ""
        if v.get('link') and v.get('btn'):
            b_html = f'<div class="mt-6 text-center"><a href="{v["link"]}" target="_blank" class="flyer-link-button">{v["btn"]} ➤</a></div>'
        
        # ★LINE誘導エリア
        line_html = ""
        if v.get('line_url'):
            img_tag = f'<img src="{v["line_img"]}" class="line-img">' if v.get('line_img') else ''
            line_html = f"""<div class="line-section"><p class="line-title">🎁 無料プレゼント！</p><p class="line-desc">{v.get('line_text', '公式LINE登録で詳細解説をプレゼント中！')}</p>{img_tag}<a href="{v['line_url']}" target="_blank" class="line-btn">LINEで受け取る</a></div>"""
        
        r_html += f'<div data-item="result" data-id="{k}"><h2 data-key="title">{v["title"]}</h2><p data-key="description" class="result-text">{v["desc"]}</p>{b_html}{line_html}</div>'
    
    html = html.replace("[[RESULTS_HTML]]", r_html)
    return html

def send_email(to_email, quiz_url, quiz_title):
    try:
        sender_email = st.secrets["email"]["address"]
        sender_password = st.secrets["email"]["password"]
        msg = MIMEText(f"診断URL: {quiz_url}\nタイトル: {quiz_title}")
        msg['Subject'] = "【診断クイズメーカー】URL発行のお知らせ"
        msg['From'] = sender_email
        msg['To'] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except: return False

@st.cache_resource
def init_supabase():
    if "supabase" in st.secrets:
        return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    return None

def delete_quiz(supabase, quiz_id):
    try:
        supabase.table("quizzes").delete().eq("id", quiz_id).execute()
        return True
    except: return False

def increment_views(supabase, quiz_id):
    try: supabase.rpc("increment_views", {"row_id": quiz_id}).execute()
    except: pass

def increment_likes(supabase, quiz_id):
    try:
        supabase.rpc("increment_likes", {"row_id": quiz_id}).execute()
        return True
    except: return False
