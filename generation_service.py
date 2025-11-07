from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agents import BookAgents
from book_generator import BookGenerator
from config import get_config
from outline_generator import OutlineGenerator

ProgressCallback = Callable[[str], None]


def run_generation(
    initial_prompt: str,
    num_chapters: int,
    local_url: Optional[str] = None,
    *,
    use_openrouter: Optional[bool] = None,
    model: Optional[str] = None,
    save_outline: bool = True,
    generate_book: bool = True,
    progress_callback: Optional[ProgressCallback] = None,
) -> Dict[str, Any]:
    """Run the complete generation workflow with optional callbacks."""

    def notify(message: str) -> None:
        if progress_callback:
            progress_callback(message)
        else:
            print(message)

    if not initial_prompt.strip():
        raise ValueError("Initial prompt cannot be empty.")

    if num_chapters <= 0:
        raise ValueError("Number of chapters must be positive.")

    cleaned_url: Optional[str]
    if isinstance(local_url, str):
        cleaned_url = local_url.strip() or None
    else:
        cleaned_url = local_url

    notify("Preparing configuration...")
    agent_config = get_config(
        local_url=cleaned_url,
        use_openrouter=use_openrouter,
        model=model,
    )

    notify("Creating agent team...")
    outline_agents = BookAgents(agent_config)
    agents = outline_agents.create_agents(initial_prompt, num_chapters)

    notify("Generating outline...")
    outline_gen = OutlineGenerator(agents, agent_config)
    outline = outline_gen.generate_outline(initial_prompt, num_chapters)

    if not outline:
        raise RuntimeError("Failed to generate outline. No chapters were returned.")

    notify(f"Outline generated with {len(outline)} chapters.")

    outline_path: Optional[Path] = None
    output_dir = Path("book_output")

    if save_outline:
        notify("Saving outline to disk...")
        output_dir.mkdir(parents=True, exist_ok=True)
        outline_path = output_dir / "outline.txt"
        with outline_path.open("w", encoding="utf-8") as file:
            for chapter in outline:
                file.write(f"Chapter {chapter['chapter_number']}: {chapter['title']}\n")
                file.write("-" * 50 + "\n")
                file.write(chapter["prompt"] + "\n\n")
        notify(f"Outline saved to {outline_path}.")

    chapters_generated: List[str] = []

    if generate_book:
        notify("Initializing chapter generation...")
        book_agents = BookAgents(agent_config, outline)
        agents_with_context = book_agents.create_agents(initial_prompt, num_chapters)
        book_gen = BookGenerator(agents_with_context, agent_config, outline)
        book_gen.generate_book(outline)
        chapters_generated = [
            str(path) for path in sorted(output_dir.glob("chapter_*.txt"))
        ]
        notify("Book generation complete.")
    else:
        notify("Chapter generation skipped as requested.")

    return {
        "outline": outline,
        "outline_path": str(outline_path) if outline_path else None,
        "output_dir": str(output_dir),
        "chapters": chapters_generated,
    }
