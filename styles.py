import streamlit as st

def apply_portal_style():
    """
    【公開側】ポータル・プレイ画面用のデザイン
    - 白背景で清潔感を出す
    - Webサイトのようなカードデザイン
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
            padding-top: 2rem;
            padding-bottom: 5rem;
        }
        
        /* Streamlitのヘッダー・フッターを隠す */
        #MainMenu, footer, header {visibility: hidden;}
        
        /* ポータル用のカードデザイン */
        .portal-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            height: 100%;
            transition: 0.2s;
        }
        .portal-card:hover {
            transform: translateY(-3px);
            border-color: #3b82f6;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        }
        
        /* ボタン (白背景に合うデザイン) */
        .stButton button {
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            color: #334155;
            border-radius: 8px;
            font-weight: bold;
            padding: 0.6rem 1rem;
            transition: all 0.2s;
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
        .hero-box {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 40px 20px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 40px;
            border: 1px solid #bae6fd;
        }
        </style>
    """, unsafe_allow_html=True)

def apply_editor_style():
    """
    【制作側】エディタ画面用のデザイン
    - Streamlit標準のダークモードを活かす (目に優しい)
    - 余計な装飾はせず、機能性を重視
    """
    st.markdown("""
        <style>
        /* 余計なメニューだけ隠す */
        #MainMenu, footer, header {visibility: hidden;}
        
        /* 入力フォームを見やすく */
        .stTextInput input, .stTextArea textarea {
            font-family: "Inter", sans-serif;
        }
        
        /* エディタ内のカード枠線を目立たなくする */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #444;
        }
        </style>
    """, unsafe_allow_html=True)