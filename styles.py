import streamlit as st

def apply_portal_style():
    """
    【公開側】ポータル・プレイ画面用のモダンデザイン
    """
    st.markdown("""
        <style>
        /* --- 1. 全体設定 --- */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');
        
        .stApp {
            background-color: #f8fafc !important; /* とても薄いグレー */
            color: #1e293b !important;
            font-family: 'Noto Sans JP', sans-serif;
        }
        
        .block-container {
            max-width: 1100px;
            padding-top: 1rem;
            padding-bottom: 5rem;
        }
        
        /* ヘッダー隠し */
        #MainMenu, footer, header {visibility: hidden;}

        /* --- 2. ヒーローセクション (トップの目立つ部分) --- */
        .hero-container {
            background: white;
            border-radius: 24px;
            padding: 3rem;
            margin-bottom: 2rem;
            box-shadow: 0 20px 40px -10px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
            position: relative;
            overflow: hidden;
        }
        
        /* 背景の装飾（ぼんやり光るオーブ） */
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

        /* --- 3. カードデザイン (診断一覧) --- */
        .quiz-card {
            background: white;
            border-radius: 16px;
            padding: 20px;
            height: 100%;
            border: 1px solid #f1f5f9;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .quiz-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
            border-color: #bfdbfe;
        }

        /* バッジ (NEWなど) */
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .badge-new { background: #dbeafe; color: #1e40af; }
        .badge-hot { background: #fee2e2; color: #991b1b; }

        /* --- 4. ボタンのカスタマイズ --- */
        .stButton button {
            width: 100%;
            border-radius: 12px;
            font-weight: 700;
            border: none;
            padding: 0.75rem 1rem;
            transition: 0.2s;
            background-color: #f1f5f9;
            color: #475569;
        }
        .stButton button:hover {
            background-color: #e2e8f0;
            color: #1e293b;
        }
        
        /* プライマリボタン (作成ボタンなど) */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }
        .stButton button[kind="primary"]:hover {
            box-shadow: 0 8px 16px rgba(37, 99, 235, 0.4);
            transform: scale(1.02);
        }

        /* --- 5. 入力フォーム --- */
        .stTextInput input {
            border-radius: 10px;
            border: 2px solid #e2e8f0;
            padding: 10px;
        }
        .stTextInput input:focus {
            border-color: #3b82f6;
        }
        </style>
    """, unsafe_allow_html=True)

def apply_editor_style():
    """作成エディタ用（機能重視）"""
    st.markdown("""
        <style>
        #MainMenu, footer, header {visibility: hidden;}
        .block-container { padding-top: 2rem; }
        .stTextInput input, .stTextArea textarea { font-family: "Inter", sans-serif; }
        </style>
    """, unsafe_allow_html=True)
