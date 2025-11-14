from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import streamlit as st

from generation_service import run_generation
from model_presets import POPULAR_MODELS
from ui.theme import card, render_sidebar_logo, set_page


set_page("Generate | AI Book Writer")
render_sidebar_logo("Tune your settings, then generate the book draft.")

st.title("Generate your book")
st.caption("Provide one idea to create outlines and draft chapters.")

if "progress_log" not in st.session_state:
    st.session_state["progress_log"] = []
if "result" not in st.session_state:
    st.session_state["result"] = None


with st.sidebar:
    st.header("Settings")
    provider_choice = st.selectbox(
        "LLM Provider",
        ("Local endpoint", "OpenRouter"),
        index=1 if os.getenv("OPENROUTER_API_KEY") else 0,
    )

    use_openrouter = provider_choice == "OpenRouter"

    if use_openrouter:
        if not os.getenv("OPENROUTER_API_KEY"):
            st.warning("OPENROUTER_API_KEY is not set. Set it to use OpenRouter.")
        model_options = ["Custom model..."] + list(POPULAR_MODELS.keys())
        selected = st.selectbox("Choose a model preset", options=model_options)
        if selected == "Custom model...":
            model_override = st.text_input(
                "Custom model ID",
                value=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
                help="Use the full provider/model name, e.g. openai/gpt-4o-mini",
            ).strip()
        else:
            preset = POPULAR_MODELS[selected]
            model_override = preset["id"]
            description = preset.get("description")
            if description:
                st.caption(description)
        endpoint_input: Optional[str] = None
    else:
        endpoint_input = st.text_input(
            "Local LLM Endpoint",
            value=os.getenv("LOCAL_LLM_URL", "http://localhost:1234/v1"),
            help="URL of your local OpenAI-compatible server (e.g., LM Studio, Ollama)",
        ).strip()
        model_override = st.text_input(
            "Model ID",
            value=os.getenv("LOCAL_LLM_MODEL", "Mistral-Nemo-Instruct-2407"),
        ).strip()

    num_chapters = st.slider("Number of chapters", min_value=1, max_value=40, value=10)
    generate_book = st.checkbox("Generate full chapter drafts", value=False)

    st.divider()
    st.caption("Tip: You can switch providers or adjust chapters at any time.")


with st.form("generation_form"):
    prompt = st.text_area(
        "Your story idea",
        placeholder=(
            "Describe the world, characters, plot, genre, tone, and any specific "
            "requirements for your story..."
        ),
        height=220,
    )
    submitted = st.form_submit_button(
        "Generate",
        type="primary",
        use_container_width=True,
    )


log_area = st.empty()

if submitted:
    st.session_state["progress_log"] = []

    status_widget = getattr(st, "status", None)
    status_container = (
        status_widget("Preparing generation...", expanded=True)
        if callable(status_widget)
        else None
    )

    def update_progress(message: str) -> None:
        st.session_state["progress_log"].append(message)
        log_area.write("\n".join(st.session_state["progress_log"][-10:]))
        if status_container is not None:
            status_container.update(label=message)

    sanitized_endpoint = (endpoint_input or "").strip() or None

    try:
        with st.spinner("Working... This may take a few minutes"):
            st.session_state["result"] = run_generation(
                initial_prompt=prompt,
                num_chapters=num_chapters,
                local_url=sanitized_endpoint,
                use_openrouter=use_openrouter,
                model=model_override or None,
                generate_book=generate_book,
                progress_callback=update_progress,
            )
        if status_container is not None:
            status_container.update(state="complete", label="Generation complete.")
        st.success("Generation complete.")
    except Exception as exc:
        if status_container is not None:
            status_container.update(state="error", label=f"Generation failed: {exc}")
        st.session_state["result"] = None
        st.error(f"Generation failed: {exc}")


result = st.session_state.get("result")
if result:
    outline_tab, chapters_tab, logs_tab = st.tabs(["Outline", "Chapters", "Logs"])

    with outline_tab:
        outline = result.get("outline", [])
        if outline:
            st.caption(f"Chapters: {len(outline)}")
            for chapter in outline:
                title = f"Chapter {chapter['chapter_number']}: {chapter['title']}"
                card(title, "Outline", chapter["prompt"])

        else:
            st.info("No outline was returned.")

        outline_path = result.get("outline_path")
        if outline_path:
            try:
                p = Path(outline_path)
                content = p.read_text(encoding="utf-8")
                download_cols = st.columns([1, 1])
                with download_cols[0]:
                    st.download_button(
                        "Download outline",
                        data=content,
                        file_name=p.name,
                        mime="text/plain",
                        use_container_width=True,
                    )
                with download_cols[1]:
                    st.caption(f"Saved to: {p}")
            except OSError:
                st.warning("Outline file could not be read.")

    with chapters_tab:
        chapters = result.get("chapters", [])
        if not chapters:
            st.info("Generate full chapters to see downloads here.")
        for index, chapter_file in enumerate(chapters, start=1):
            p = Path(chapter_file)
            try:
                content = p.read_text(encoding="utf-8")
            except OSError:
                st.warning(f"Could not read {p}.")
                continue

            with st.expander(f"Chapter {index}: {p.stem.replace('_', ' ').title()}"):
                st.write(content)
                download_cols = st.columns([1, 1])
                with download_cols[0]:
                    st.download_button(
                        "Download chapter",
                        data=content,
                        file_name=p.name,
                        mime="text/plain",
                        use_container_width=True,
                    )
                with download_cols[1]:
                    st.caption(f"Saved to: {p}")

    with logs_tab:
        logs = st.session_state.get("progress_log", [])
        if logs:
            st.code("\n".join(logs[-200:]), language="text")
        else:
            st.caption("Logs will appear here while generation is running.")
