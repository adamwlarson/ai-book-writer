from __future__ import annotations

import streamlit as st

from ui.theme import render_sidebar_logo, set_page


set_page("AI Book Writer")
render_sidebar_logo("Draft polished chapters from a single idea.")

st.title("AI Book Writer")
st.caption("Outline and chapters in minutes, ready to edit or share.")

page_link = getattr(st, "page_link", None)
if callable(page_link):
    page_link("pages/1_Generate.py", label="Start generating", icon="✨")
else:
    st.info("Open the '1_Generate' page from the sidebar to start.")

st.divider()

feature_cols = st.columns(3)
feature_cols[0].markdown(
    "**Outline-first approach**\n\nKeep a coherent structure before drafting prose."
)
feature_cols[1].markdown(
    "**Flexible models**\n\nSwitch between local endpoints and OpenRouter presets."
)
feature_cols[2].markdown(
    "**Download ready**\n\nExport outlines and chapters as soon as they finish."
)
