# Streamlit UI Style Guide — AI Book Writer

This guide shows how to give the app a clean, cohesive look using Streamlit’s theming, layout primitives, and a small amount of CSS. It’s tailored to this project’s structure:

- Entry UI: `streamlit_app.py`
- Main page: `pages/1_Generate.py`
- UI helpers: `ui/theme.py`
- Assets: `assets/`
- Theme config: `.streamlit/`


## 1) Establish a Global Theme

Use Streamlit’s config to set consistent typography and colors.

Create `.streamlit/config.toml` with a light, readable base theme:

```toml
[theme]
base = "light"
primaryColor = "#6F3FF5"       # Accent (buttons, sliders)
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F6F6FA"
textColor = "#1F2430"
font = "sans serif"
```

Tips:
- Keep contrast high for readability. Test both light and dark background variants.
- If you want a dark variant later, add a second TOML and toggle via environment.


## 2) Upgrade `ui/theme.py`

Centralize page config, icons, and optional CSS injection here so every page stays minimal.

Suggested implementation:

```python
# ui/theme.py
from __future__ import annotations
import streamlit as st


def set_page(title: str = "AI Book Writer") -> None:
    """Global page config used by all pages."""
    st.set_page_config(
        page_title=title,
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get help": "https://github.com/<your-org>/ai-book-writer/issues",
            "Report a bug": "https://github.com/<your-org>/ai-book-writer/issues/new",
            "About": "AI Book Writer — generate outlines and chapters from a single idea.",
        },
    )

    inject_css()


def inject_css() -> None:
    """Lightweight CSS for cards, spacing, and tag pills."""
    st.markdown(
        """
        <style>
        /* Tighter base layout */
        .block-container { padding-top: 2rem; padding-bottom: 4rem; }

        /* Card pattern */
        .card {
          border: 1px solid #E8E8EF;
          background: var(--secondary-background-color, #F6F6FA);
          border-radius: 12px;
          padding: 1rem 1.25rem;
          margin-bottom: 0.75rem;
        }
        .card h4 { margin: 0 0 .25rem 0; }
        .muted { color: #666C7A; font-size: 0.9rem; }

        /* Tag / pill */
        .pill { display: inline-block; padding: .2rem .5rem; border-radius: 999px; background:#EEE; }

        /* Download buttons alignment */
        .download-row button { margin-right: .5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, subtitle: str | None = None):
    """Simple card container you can reuse with `with card(...):`."""
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        st.markdown(f"<div class='card'><h4>{title}</h4>" + (f"<div class='muted'>{subtitle}</div>" if subtitle else "") + "</div>", unsafe_allow_html=True)
        with st.container():
            yield

    return _ctx()
```

Why this helps:
- `set_page` applies global look (title, icon, sidebar state, menu links) in one place.
- `inject_css` adds unobtrusive polish: subtle cards, spacing, and pills.
- Optional `card` helper avoids repeating markup for repeated sections (outline items, chapter blocks).


## 3) Polish the Home Screen (`streamlit_app.py`)

Make it feel like a welcoming landing page.

Recommended tweaks:
- Keep the hero area minimal with a short value prop.
- Prefer a prominent CTA using `st.page_link`.

Example:

```python
# streamlit_app.py
from ui.theme import set_page
import streamlit as st

set_page("AI Book Writer")

st.title("AI Book Writer")
st.caption("Generate structured outlines and chapters from a single idea.")

if callable(getattr(st, "page_link", None)):
    st.page_link("pages/1_Generate.py", label="Start Generating", icon="🎬")
else:
    st.info("Open the '1_Generate' page from the sidebar to start.")
```

Optional:
- Add a logo to the sidebar or top via `st.sidebar.image("assets/logo.png", use_container_width=True)`.
- Include a three‑bullet feature list under the title for clarity.


## 4) Streamline the Generate Page (`pages/1_Generate.py`)

Goal: keep the main column focused on the prompt and the primary action. Move advanced controls to the sidebar.

Layout suggestions:
- Put provider/model settings in the sidebar: `st.sidebar.selectbox`, `st.sidebar.text_input`.
- Keep the form’s CTA primary and full width: `st.form_submit_button(..., type="primary", use_container_width=True)`.
- Show progress and logs in a dedicated tab; show results in clean sections.

Tabs for result presentation:

```python
tabs = st.tabs(["Outline", "Chapters", "Logs"])
outline_tab, chapters_tab, logs_tab = tabs
```

Use them like this:

```python
# After generation succeeds
with outline_tab:
    st.subheader("Outline")
    st.caption(f"Chapters: {len(outline)}")
    for chapter in outline:
        with st.container():
            st.markdown(f"**Chapter {chapter['chapter_number']}: {chapter['title']}**")
            st.write(chapter["prompt"])  # summary

with chapters_tab:
    st.subheader("Chapters")
    for chapter_file in chapters:
        # render download UI per chapter

with logs_tab:
    # Stream or list recent messages
    st.write("\n".join(st.session_state.get("progress_log", [])[-200:]))
```

Progress UI options:
- Use `st.spinner("Working...")` (already present) for simple feedback.
- If on Streamlit ≥1.31, consider `st.status()` for richer progress with updateable label and state.
- For long runs, add a `st.progress` bar tied to outline/chapter steps (e.g., chapters completed / total).

Primary action button:

```python
submitted = st.form_submit_button("Generate", type="primary", use_container_width=True)
```

Downloads: group `st.download_button` calls in a row using `st.columns` so actions feel aligned.


## 5) Sidebar Organization

Use the sidebar for advanced or rarely‑changed controls so the main column stays focused.

Suggested grouping:
- Provider (Local / OpenRouter)
- Endpoint / Model ID (contextual to provider)
- Options: number of chapters, "Generate full chapter drafts"
- Help link and a short tip/policy note

Example snippet:

```python
with st.sidebar:
    st.header("Settings")
    provider_choice = st.selectbox("LLM Provider", ("Local endpoint", "OpenRouter"))
    if provider_choice == "OpenRouter":
        # model preset or custom id
    else:
        # endpoint + model id
    st.divider()
    st.caption("Tip: You can switch providers at any time.")
```


## 6) Results as Cards

Cards visually distinguish each chapter or outline item.

Using the CSS injected in `ui/theme.py` you can do:

```python
for chapter in outline:
    st.markdown(
        f"""
        <div class="card">
          <h4>Chapter {chapter['chapter_number']}: {chapter['title']}</h4>
          <div class="muted">Outline</div>
          <div>{chapter['prompt']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
```

Or with expanders when content is lengthy:

```python
with st.expander(f"Chapter {n}: {title}"):
    st.write(summary)
    st.download_button("Download", data=content, file_name=file_name)
```


## 7) Icons and Visual Language

Small touches go a long way:
- Use emoji icons on actions: "▶️ Generate", "📥 Download", "🧭 Outline", "📄 Chapter".
- Add a favicon via `page_icon` in `set_page` (already done in the example).
- If you have a logo, place it in `assets/` and show in the sidebar.


## 8) Accessibility & Typography

- Keep body text ≥ 15px for readability (Streamlit defaults are OK).
- Maintain sufficient color contrast, especially on buttons and pills.
- Avoid long unbroken paragraphs; use `st.markdown` with lists or `st.write` for chunking.


## 9) Performance & UX

- Debounce heavy UI updates (batch log lines; avoid updating the page per token).
- Use expanders or tabs to keep vertical length manageable.
- When generation finishes, scroll to results with a short note (`st.success("Generation complete.")`).


## 10) Quick Implementation Checklist

- [ ] Add `.streamlit/config.toml` theme
- [ ] Expand `ui/theme.py` to set `page_icon`, menu, and inject CSS
- [ ] Move advanced controls to the sidebar in `pages/1_Generate.py`
- [ ] Use `type="primary"` and `use_container_width=True` for the Generate button
- [ ] Present results in tabs (Outline / Chapters / Logs)
- [ ] Render outline/chapters as cards or expanders; align download buttons
- [ ] Add a logo in `assets/` and display it in sidebar


## 11) Optional Enhancements

- Use `st.tabs` on the home page to show a quick demo/FAQ.
- Add `st.toast("Saved to book_output/…")` after downloads.
- Provide a model preset description below the preset selector using `model_presets.POPULAR_MODELS[preset]["description"]`.
- If you have cover art, show a small thumbnail next to each chapter card.


## Notes for This Repo

- `ui/theme.py` currently sets `layout="wide"` only. The snippets above show how to centralize branding and polish there without touching business logic.
- `streamlit_app.py` has a minor syntax issue in the `st.page_link` line (an extra `?`/quote in the icon). Fixing that will restore the CTA.
- Keep UI code thin: business logic remains in `generation_service.py` and friends; UI files should mostly manage layout and interactions.


---

With these changes, the app reads as a focused tool: a clean landing page, a streamlined generate flow, and tidy, scannable results. Minimal CSS plus Streamlit’s built‑in primitives gets you 90% of the way there without heavy front‑end work.

