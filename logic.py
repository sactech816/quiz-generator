import streamlit as st
import json
import smtplib
from email.mime.text import MIMEText
from supabase import create_client

# HTMLテンプレート (変更なし)
HTML_TEMPLATE_RAW = """<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>[[PAGE_TITLE]]</title><script src="https://cdn.tailwindcss.com"></script><style>@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');body{font-family:'Noto Sans JP',sans-serif;background-color:#f3f4f6;color:#1f2937;display:flex;flex-direction:column;min-height:100vh}.quiz-container{max-width:700px;width:100%;padding:2.5rem;background-color:white;border-radius:0.75rem;margin:2rem auto;box-shadow:0 10px 15px rgba(0,0,0,0.1)}.question-card,.result-card{padding:1.5rem;border:1px solid #e5e7eb;border-radius:0.5rem;margin-bottom:1.5rem}.option-button{display:block;width:100%;text-align:left;padding:1rem;margin-bottom:0.75rem;border:1px solid #d1d5db;border-radius:0.375rem;background:#f9fafb;transition:0.2s}.option-button:hover{background:#eff6ff;border-color:#3b82f6}.option-button.selected{background:#dbeafe;border-color:#3b82f6;font-weight:600}.next-button,.restart-button{padding:0.85rem 2rem;border-radius:0.375rem;font-weight:600;width:100%;background:#2563eb;color:white}.next-button:disabled{background:#9ca3af}.progress-bar-container{width:100%;background:#e5e7eb;border-radius:99px;height:0.5rem;margin-bottom:1.5rem}.progress-bar{height:100%;background:#2563eb;width:0%;transition:width 0.3s}.hidden{display:none}.flyer-link-button{background:#059669;color:white;display:block;padding:1rem;border-radius:0.375rem;text-align:center;font-weight:bold;text-decoration:none}</style></head><body><div id="quiz-data" style="display:none"><div data-container="questions">[[QUESTIONS_HTML]]</div><div data-container="results">[[RESULTS_HTML]]</div></div><div class="quiz-container"><h1 class="text-2xl font-bold text-center mb-4">[[MAIN_HEADING]]</h1><p class="text-center text-gray-600 mb-8">[[INTRO_TEXT]]</p><div id="quiz-area"></div><div id="result-area" class="hidden"></div></div><script>document.addEventListener('DOMContentLoaded',()=>{let q=[],r=[],idx=0,ans=[];const qa=document.getElementById('quiz-area'),ra=document.getElementById('result-area');function load(){const d=document.getElementById('quiz-data');q=Array.from(d.querySelectorAll('[data-container="questions"] [data-item="question"]')).map(e=>({text:e.querySelector('[data-key="text"]').textContent,opts:Array.from(e.querySelectorAll('[data-key="option"]')).map(o=>({text:o.textContent,pts:JSON.parse(o.dataset.points||'{}')}))}));r=Array.from(d.querySelectorAll('[data-container="results"] [data-item="result"]')).map(e=>({id:e.dataset.id,html:e.innerHTML}))}function calc(){const s={};ans.forEach(a=>{for(const k in a)s[k]=(s[k]||0)+a[k]});let m=-1,id=null;for(const x of r){if((s[x.id]||0)>m){m=s[x.id];id=x.id}}return r.find(x=>x.id===id)}function show(){const d=calc();qa.classList.add('hidden');ra.innerHTML=`<div class="result-card">${d.html}</div><div class="mt-6 text-center"><button class="restart-button" onclick="location.reload()">もう一度</button></div>`;ra.classList.remove('hidden')}function disp(){const d=q[idx];qa.innerHTML=`<div class="progress-bar-container"><div class="progress-bar" style="width:${((idx)/q.length)*100}%"></div></div><div class="question-card"><p class="text-lg font-bold mb-4">Q${idx+1}. ${d.text}</p>${d.opts.map((o,i)=>`<button class="option-button" data-i="${i}">${o.text}</button>`).join('')}</div><div class="mt-6"><button class="next-button" disabled>次へ</button></div>`;const btn=qa.querySelector('.next-button');if(idx===q.length-1)btn.textContent="結果を見る";qa.querySelectorAll('.option-button').forEach(b=>b.addEventListener('click',e=>{qa.querySelectorAll('.option-button').forEach(x=>x.classList.remove('selected'));e.target.classList.add('selected');ans[idx]=d.opts[e.target.dataset.i].pts;btn.disabled=false}));btn.addEventListener('click',()=>{if(ans[idx]==null)return;(idx<q.length-1)?(idx++,disp()):show()})}load();disp()})</script></body></html>"""

def generate_html_content(data):
    html = HTML_TEMPLATE_RAW
    html = html.replace("[[PAGE_TITLE]]", data.get('page_title', '診断'))
    html = html.replace("[[MAIN_HEADING]]", data.get('main_heading', 'タイトル'))
    html = html.replace("[[INTRO_TEXT]]", data.get('intro_text', ''))
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
        r_html += f'<div data-item="result" data-id="{k}"><h2 data-key="title">{v["title"]}</h2><p data-key="description" class="result-text">{v["desc"]}</p>{b_html}</div>'
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

# ★削除関数を追加
def delete_quiz(supabase, quiz_id):
    try:
        supabase.table("quizzes").delete().eq("id", quiz_id).execute()
        return True
    except:
        return False
