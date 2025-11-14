"""Main script for running the book generation system"""

from generation_service import run_generation


def main() -> None:
    # Initial prompt for the book
    initial_prompt = """
    Create a story in my established writing style with these key elements:
    Its important that it has several key storylines that intersect and influence each other. The story should be set in a modern corporate environment, with a focus on technology and finance. The protagonist is a software engineer named Dane who has just completed a groundbreaking stock prediction algorithm. The algorithm predicts a catastrophic market crash, but Dane oversleeps and must rush to an important presentation to share his findings with executives. The tension arises from the questioning of whether his "error" might actually be correct.

    The piece is written in third-person limited perspective, following Dane's thoughts and experiences. The prose is direct and technical when describing the protagonist's work, but becomes more introspective during personal moments. The author employs a mix of dialogue and internal monologue, with particular attention to time progression and technical details around the algorithm and stock predictions.
    Story Arch:

    Setup: Dane completes a groundbreaking stock prediction algorithm late at night
    Initial Conflict: The algorithm predicts a catastrophic market crash
    Rising Action: Dane oversleeps and must rush to an important presentation
    Climax: The presentation to executives where he must explain his findings
    Tension Point: The questioning of whether his "error" might actually be correct

    Characters:

    Dane: The protagonist; a dedicated software engineer who prioritizes work over personal life. Wears grey polo shirts on Thursdays, tends to get lost in his work, and struggles with work-life balance. More comfortable with code than public speaking.
    Gary: Dane's nervous boss who seems caught between supporting Dane and managing upper management's expectations
    Jonathan Morego: Senior VP of Investor Relations who raises pointed questions about the validity of Dane's predictions
    Silence: Brief mention as an Uber driver
    C-Level Executives: Present as an audience during the presentation

    World Description:
    The story takes place in a contemporary corporate setting, likely a financial technology company. The world appears to be our modern one, with familiar elements like:

    Major tech companies (Tesla, Google, Apple, Microsoft)
    Stock market and financial systems
    Modern technology (neural networks, predictive analytics)
    Urban environment with rideshare services like Uber
    Corporate hierarchy and office culture

    The story creates tension between the familiar corporate world and the potential for an unprecedented financial catastrophe, blending elements of technical thriller with workplace drama. The setting feels grounded in reality but hints at potentially apocalyptic economic consequences.
    """

    num_chapters = 25

    result = run_generation(initial_prompt, num_chapters)
    outline = result["outline"]

    print("\nGenerated Outline:")
    for chapter in outline:
        print(f"\nChapter {chapter['chapter_number']}: {chapter['title']}")
        print("-" * 50)
        print(chapter["prompt"])

    if result["outline_path"]:
        print(f"\nOutline saved to: {result['outline_path']}")

    if result["chapters"]:
        print("\nGenerated Chapters:")
        for chapter_file in result["chapters"]:
            print(f"- {chapter_file}")
    else:
        print("\nChapter generation skipped or no chapters were produced.")


if __name__ == "__main__":
    main()
