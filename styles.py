import streamlit as st

def apply_portal_style():
    """公開画面用の白ベースデザイン"""
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff !important; color: #333333 !important; }
        .block-container { max-width: 1100px; padding-top: 1rem; padding-bottom: 5rem; }
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* カードデザイン */
        .quiz-card {
            background: white; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02); height: 380px; /* 高さ固定 */
            display: flex; flex-direction: column; transition: 0.2s; margin-bottom: 10px;
        }
        .quiz-card:hover {
            transform: translateY(-3px); border-color: #3b82f6;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        }
        .quiz-thumb-box { width: 100%; height: 160px; background-color: #f1f5f9; overflow: hidden; }
        .quiz-thumb { width: 100%; height: 100%; object-fit: cover; }
        .quiz-content { padding: 16px; flex-grow: 1; display:flex; flex-direction:column; }
        .quiz-title { font-weight: bold; font-size: 1.1rem; margin-bottom: 5px; color: #1e293b; line-height: 1.4; height: 3em; overflow: hidden; }
        .quiz-desc { font-size: 0.85rem; color: #64748b; margin-bottom: 10px; height: 4.5em; overflow: hidden; line-height: 1.5; }
        .badge-new { background: #dbeafe; color: #1e40af; padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: bold; margin-bottom: 6px; width: fit-content; }
        
        /* ボタン系 */
        .stButton button { background-color: #f8fafc; border: 1px solid #cbd5e1; color: #334155; border-radius: 8px; font-weight: bold; transition: 0.2s; }
        .stButton button:hover { border-color: #3b82f6; color: #2563eb; background-color: #eff6ff; }
        
        /* プライマリボタン */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
            color: white; border: none; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
        }
        .stButton button[kind="primary"]:hover {
            box-shadow: 0 8px 12px rgba(37, 99, 235, 0.3); transform: scale(1.01);
        }
        
        /* 削除ボタン (赤) */
        .delete-btn button {
            background-color: #fee2e2 !important; color: #991b1b !important; border: 1px solid #fecaca !important;
            padding: 0.3rem 0.5rem !important; font-size: 0.8rem !important;
        }
        .delete-btn button:hover { background-color: #fecaca !important; }
        </style>
    """, unsafe_allow_html=True)

def apply_editor_style():
    """エディタ用の黒ベースデザイン"""
    st.markdown("""
        <style>
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}
        .block-container { padding-top: 2rem; padding-bottom: 5rem; }
        .stTextInput input, .stTextArea textarea { font-family: "Inter", sans-serif; }
        </style>
    """, unsafe_allow_html=True)

# HTMLパーツ
HERO_HTML = """
<div style="background:white; border-radius:16px; padding:3rem; margin-bottom:2rem; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05); border:1px solid #e2e8f0; text-align:center;">
    <h1 style="font-size:2.5rem; font-weight:900; color:#1e293b; margin-bottom:10px;">診断クイズメーカー</h1>
    <p style="color:#64748b;">AIがたった1分で構成案を作成。集客・販促に使える高品質な診断ツールを今すぐ公開。</p>
</div>
"""

def get_card_html(title, desc, img_url):
    return f"""
    <div class="quiz-card">
        <div class="quiz-thumb-box">
            <img src="{img_url}" class="quiz-thumb" loading="lazy">
        </div>
        <div class="quiz-content">
            <span class="badge-new">NEW</span>
            <div class="quiz-title">{title}</div>
            <div class="quiz-desc">{desc}</div>
        </div>
    </div>
    """
