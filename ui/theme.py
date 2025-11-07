from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"

MENU_HELP_URL = "https://github.com/shuey/ai-book-writer/issues"
MENU_BUG_URL = "https://github.com/shuey/ai-book-writer/issues/new"
ABOUT_TEXT = "AI Book Writer - generate outlines and chapters from a single idea."


def set_page(title: str = "AI Book Writer") -> None:
    """Apply the global Streamlit page configuration and base styling."""
    st.set_page_config(
        page_title=title,
        page_icon=_resolve_page_icon(),
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get help": MENU_HELP_URL,
            "Report a bug": MENU_BUG_URL,
            "About": ABOUT_TEXT,
        },
    )
    inject_css()


def inject_css() -> None:
    """Inject lightweight CSS primitives shared across pages."""
    st.markdown(
        """
        <style>
        /* Global dark theme overrides */
        .stApp { background-color: #0a0a0a; }
        
        .block-container { 
            padding-top: 2rem; 
            padding-bottom: 4rem; 
            background-color: #0a0a0a;
        }
        
        .stTabs [role="tablist"] { 
            gap: 0.5rem; 
            background-color: #0a0a0a;
        }
        
        .stTabs [role="tab"] { 
            padding: 0.5rem 1rem; 
            background-color: #1a1a1a;
            border: 1px solid #333;
            color: #e0e0e0;
        }
        
        .stTabs [role="tab"]:hover {
            background-color: #2a2a2a;
            color: #ffffff;
        }
        
        .stTabs [role="tab"][aria-selected="true"] {
            background-color: #333333;
            color: #ffffff;
        }

        .card-box {
          border: 1px solid #333333;
          background: #1a1a1a;
          border-radius: 4px;
          padding: 1.25rem;
          margin-bottom: 1rem;
        }
        
        .card-box h4 { 
            margin: 0 0 0.5rem 0; 
            color: #ffffff;
            font-weight: 600;
        }
        
        .card-muted { 
            color: #888888; 
            font-size: 0.9rem; 
            margin-bottom: 0.75rem;
        }

        .pill {
          display: inline-block;
          padding: 0.25rem 0.6rem;
          border-radius: 2px;
          background: #333333;
          color: #e0e0e0;
          font-size: 0.8rem;
          border: 1px solid #555555;
        }

        .download-row button { 
            margin-right: 0.5rem; 
        }
        
        .sidebar-logo img { 
            border-radius: 2px; 
            border: 1px solid #333;
        }
        
        /* Streamlit component overrides */
        .stSelectbox > div > div {
            background-color: #1a1a1a;
            border: 1px solid #333333;
        }
        
        .stTextInput > div > div {
            background-color: #1a1a1a;
            border: 1px solid #333333;
        }
        
        .stTextArea > div > div {
            background-color: #1a1a1a;
            border: 1px solid #333333;
            color: #ffffff;
        }
        
        .stSlider > div {
            background-color: #1a1a1a;
        }
        
        .stCheckbox {
            color: #e0e0e0;
        }
        
        /* Primary button styling */
        .stButton > button {
            background-color: #333333;
            border: 1px solid #555555;
            color: #ffffff;
        }
        
        .stButton > button:hover {
            background-color: #444444;
            border-color: #666666;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #111111;
        }
        
        /* Divider styling */
        hr {
            border-color: #333333;
            margin: 1rem 0;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #1a1a1a;
            border: 1px solid #333333;
        }
        
        .streamlit-expanderContent {
            background-color: #0a0a0a;
            border: 1px solid #333333;
            border-top: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, subtitle: str | None = None, body: str | None = None) -> None:
    """Render a simple card with optional subtitle and body copy."""
    safe_title = html.escape(title, quote=False)
    subtitle_markup = ""
    if subtitle:
        subtitle_markup = (
            f'<div class="card-muted">{html.escape(subtitle, quote=False)}</div>'
        )
    body_markup = ""
    if body:
        safe_body = html.escape(body, quote=False).replace("\n", "<br />")
        body_markup = f"<div>{safe_body}</div>"
    st.markdown(
        f'<div class="card-box"><h4>{safe_title}</h4>{subtitle_markup}{body_markup}</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_logo(caption: str | None = "AI Book Writer") -> None:
    """Display the sidebar logo and optional caption if an asset exists."""
    if LOGO_PATH.exists():
        st.sidebar.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
        st.sidebar.image(str(LOGO_PATH), use_column_width=True)
        st.sidebar.markdown("</div>", unsafe_allow_html=True)
    if caption:
        st.sidebar.caption(caption)


def _resolve_page_icon() -> str:
    if LOGO_PATH.exists():
        return str(LOGO_PATH)
    return "\U0001f4d8"


__all__ = ["set_page", "inject_css", "card", "render_sidebar_logo"]
