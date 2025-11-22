import streamlit as st

# ==========================================
# CSS定義
# ==========================================
def apply_portal_style():
    """
    【公開側】ポータル・プレイ画面用のデザイン
    - 白背景 (Light Mode強制)
    - 清潔感のあるWebサイト風
    """
    st.markdown("""
        <style>
        /* 強制ライトモード (白背景) */
        .stApp {
            background-color: #ffffff !important;
            color: #333333 !important;
        }
        
        /* コンテンツ幅を読みやすく調整 */
        .block-container {
            max-width: 1000px;
            padding-top: 1rem;
            padding-bottom: 5rem;
        }
        
        /* Streamlitのヘッダー・フッターを隠す */
        #MainMenu, footer, header {visibility: hidden;}
        
        /* ポータル用のカードデザイン */
        .quiz-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            height: 100%;
            transition: 0.2s;
            display: flex;
            flex-direction: column;
        }
        .quiz-card:hover {
            transform: translateY(-3px);
            border-color: #3b82f6;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        }
        
        .quiz-thumb {
            width: 100%;
            height: 150px;
            object-fit: cover;
            background-color: #f1f5f9;
        }
        
        .quiz-content {
            padding: 15px;
            flex-grow: 1;
        }
        
        .quiz-title {
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 5px;
            color: #1e293b;
            line-height: 1.4;
        }
        
        .quiz-desc {
            font-size: 0.85rem;
            color: #64748b;
            margin-bottom: 10px;
            height: 40px;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        
        /* バッジ */
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .badge-new { background: #dbeafe; color: #1e40af; }
        
        /* ボタン (白背景に合うデザイン) */
        .stButton button {
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            color: #334155;
            border-radius: 8px;
            font-weight: bold;
            padding: 0.6rem 1rem;
            transition: all 0.2s;
            width: 100%;
        }
        .stButton button:hover {
            border-color: #3b82f6;
            color: #2563eb;
            background-color: #eff6ff;
        }
        /* 強調ボタン (青) */
        .stButton button[kind="primary"] {
            background-color: #2563eb;
            color: white;
            border: none;
        }
        .stButton button[kind="primary"]:hover {
            background-color: #1d4ed8;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }
        
        /* ヒーローセクション (トップ画像の代わり) */
        .hero-container {
            background: white;
            border-radius: 24px;
            padding: 3rem;
            margin-bottom: 2rem;
            box-shadow: 0 20px 40px -10px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
            position: relative;
            overflow: hidden;
            text-align: center;
        }
        .hero-orb {
            position: absolute;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(59,130,246,0.2) 0%, rgba(255,255,255,0) 70%);
            top: -100px;
            right: -100px;
            border-radius: 50%;
            z-index: 0;
        }
        .hero-content {
            position: relative;
            z-index: 1;
        }
        </style>
    """, unsafe_allow_html=True)

def apply_editor_style():
    """
    【制作側】エディタ画面用のデザイン
    - Streamlit標準（ダークモード設定なら黒）をそのまま使う
    - 余計な要素だけ隠す
    """
    st.markdown("""
        <style>
        /* 余計なメニューだけ隠す */
        #MainMenu, footer, header {visibility: hidden;}
        
        /* 入力フォームを見やすく */
        .stTextInput input, .stTextArea textarea {
            font-family: "Inter", sans-serif;
        }
        
        /* コンテンツ幅 */
        .block-container {
            max-width: 1100px;
            padding-top: 2rem;
            padding-bottom: 5rem;
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# HTMLパーツ (アプリ内で呼び出すHTML)
# ==========================================
HERO_HTML = """
<div class="hero-container">
    <div class="hero-orb"></div>
    <div class="hero-content">
        <h1 style="font-size: 2.5rem; font-weight: 900; color: #1e293b; margin-bottom: 10px;">
            あなたのビジネスを加速する<br>
            <span style="background: linear-gradient(to right, #2563eb, #9333ea); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">診断コンテンツ</span>を作ろう。
        </h1>
        <p style="color: #64748b;">AIがたった1分で構成案を作成。集客・販促に使える高品質な診断ツールを今すぐ公開。</p>
    </div>
</div>
"""

def get_card_html(title, desc, img_url):
    """診断カードのHTMLを生成する"""
    return f"""
    <div class="quiz-card">
        <img src="{img_url}" class="quiz-thumb" loading="lazy">
        <div class="quiz-content">
            <span class="badge badge-new">NEW</span>
            <div class="quiz-title">{title}</div>
            <div class="quiz-desc">{desc}</div>
        </div>
    </div>
    """
