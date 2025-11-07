"""Generate book outlines using AutoGen agents with improved error handling"""

import autogen
from typing import Dict, List
import re


class OutlineGenerator:
    def __init__(self, agents: Dict[str, autogen.ConversableAgent], agent_config: Dict):
        self.agents = agents
        self.agent_config = agent_config

    def generate_outline(
        self, initial_prompt: str, num_chapters: int = 25
    ) -> List[Dict]:
        """Generate a book outline based on initial prompt"""
        print("\nGenerating outline...")

        groupchat = autogen.GroupChat(
            agents=[
                self.agents["user_proxy"],
                self.agents["story_planner"],
                self.agents["world_builder"],
                self.agents["outline_creator"],
            ],
            messages=[],
            max_round=8,
            speaker_selection_method="round_robin",
        )

        manager = autogen.GroupChatManager(
            groupchat=groupchat, llm_config=self.agent_config
        )

        outline_prompt = f"""Let's create a {num_chapters}-chapter outline for a book with the following premise:

{initial_prompt}

Process:
1. Story Planner: Create a high-level story arc and major plot points
2. World Builder: Suggest key settings and world elements needed
3. Outline Creator: Generate a detailed outline with chapter titles and prompts

Start with Chapter 1 and number chapters sequentially.

Make sure there are at least 3 scenes in each chapter.

[Continue with remaining chapters]

Please output all chapters, do not leave out any chapters. Think through every chapter carefully, none should be to be determined later
It is of utmost importance that you detail out every chapter, do not combine chapters, or leave any out
There should be clear content for each chapter. There should be a total of {num_chapters} chapters.

End the outline with 'END OF OUTLINE'"""

        try:
            # Initiate the chat
            self.agents["user_proxy"].initiate_chat(manager, message=outline_prompt)

            # Extract the outline from the chat messages
            return self._process_outline_results(groupchat.messages, num_chapters)

        except Exception as e:
            print(f"Error generating outline: {str(e)}")
            # Try to salvage any outline content we can find
            return self._emergency_outline_processing(groupchat.messages, num_chapters)

    def _get_sender(self, msg: Dict) -> str:
        """Helper to get sender from message regardless of format"""
        return msg.get("sender") or msg.get("name", "")

    def _extract_outline_content(self, messages: List[Dict]) -> str:
        """Extract outline content from messages with better error handling"""
        print("Searching for outline content in messages...")

        # Look for content between "OUTLINE:" and "END OF OUTLINE"
        for msg in reversed(messages):
            content = msg.get("content", "")
            if "OUTLINE:" in content:
                # Extract content between OUTLINE: and END OF OUTLINE
                start_idx = content.find("OUTLINE:")
                end_idx = content.find("END OF OUTLINE")

                if start_idx != -1:
                    if end_idx != -1:
                        return content[start_idx:end_idx].strip()
                    else:
                        # If no END OF OUTLINE marker, take everything after OUTLINE:
                        return content[start_idx:].strip()

        # Fallback: look for content with chapter markers
        for msg in reversed(messages):
            content = msg.get("content", "")
            if "Chapter 1:" in content or "**Chapter 1:**" in content:
                return content

        return ""

    def _process_outline_results(
        self, messages: List[Dict], num_chapters: int
    ) -> List[Dict]:
        """Extract and process the outline with strict format requirements"""
        outline_content = self._extract_outline_content(messages)

        if not outline_content:
            print("No structured outline found, attempting emergency processing...")
            return self._emergency_outline_processing(messages, num_chapters)

        chapters = []
        chapter_sections = re.split(r"Chapter \d+:", outline_content)

        for i, section in enumerate(
            chapter_sections[1:], 1
        ):  # Skip first empty section
            try:
                # Extract required components
                title_match = re.search(
                    r"\*?\*?(?:Chapter\s+Title|Title):\*?\*?\s*(.+?)(?=\n|$)",
                    section,
                    re.IGNORECASE,
                )
                events_match = re.search(
                    r"\*?\*?Key Events:\*?\*?\s*(.*?)(?=\*?\*?Character Developments:|$)",
                    section,
                    re.DOTALL | re.IGNORECASE,
                )
                character_match = re.search(
                    r"\*?\*?Character Developments:\*?\*?\s*(.*?)(?=\*?\*?Setting:|$)",
                    section,
                    re.DOTALL | re.IGNORECASE,
                )
                setting_match = re.search(
                    r"\*?\*?Setting:\*?\*?\s*(.*?)(?=\*?\*?Tone:|$)",
                    section,
                    re.DOTALL | re.IGNORECASE,
                )
                tone_match = re.search(
                    r"\*?\*?Tone:\*?\*?\s*(.*?)(?=\*?\*?Chapter \d+:|$)",
                    section,
                    re.DOTALL | re.IGNORECASE,
                )

                # If no explicit title match, try to get it from the chapter header
                if not title_match:
                    title_match = re.search(
                        r"\*?\*?Chapter \d+:\s*(.+?)(?=\n|$)", section
                    )

                # Verify all components exist
                if not all(
                    [
                        title_match,
                        events_match,
                        character_match,
                        setting_match,
                        tone_match,
                    ]
                ):
                    print(f"Missing required components in Chapter {i}")
                    missing = []
                    if not title_match:
                        missing.append("Title")
                    if not events_match:
                        missing.append("Key Events")
                    if not character_match:
                        missing.append("Character Developments")
                    if not setting_match:
                        missing.append("Setting")
                    if not tone_match:
                        missing.append("Tone")
                    print(f"  Missing: {', '.join(missing)}")
                    continue

                # Format chapter content
                chapter_info = {
                    "chapter_number": i,
                    "title": title_match.group(1).strip(),
                    "prompt": "\n".join(
                        [
                            f"- Key Events: {events_match.group(1).strip()}",
                            f"- Character Developments: {character_match.group(1).strip()}",
                            f"- Setting: {setting_match.group(1).strip()}",
                            f"- Tone: {tone_match.group(1).strip()}",
                        ]
                    ),
                }

                # Verify events (at least 3)
                events_block = events_match.group(1)
                events = [
                    line.strip()
                    for line in re.findall(
                        r"^\s*-\s+(.+?)\s*$", events_block, re.MULTILINE
                    )
                    if line.strip()
                ]
                if len(events) < 3:
                    print(f"Chapter {i} has fewer than 3 events")
                    continue

                chapters.append(chapter_info)

            except Exception as e:
                print(f"Error processing Chapter {i}: {str(e)}")
                continue

        # If we don't have enough valid chapters, raise error to trigger retry
        if len(chapters) < num_chapters:
            raise ValueError(
                f"Only processed {len(chapters)} valid chapters out of {num_chapters} required"
            )

        return chapters

    def _verify_chapter_sequence(
        self, chapters: List[Dict], num_chapters: int
    ) -> List[Dict]:
        """Verify and fix chapter numbering"""
        # Sort chapters by their current number
        chapters.sort(key=lambda x: x["chapter_number"])

        # Renumber chapters sequentially starting from 1
        for i, chapter in enumerate(chapters, 1):
            chapter["chapter_number"] = i

        # Add placeholder chapters if needed
        while len(chapters) < num_chapters:
            next_num = len(chapters) + 1
            chapters.append(
                {
                    "chapter_number": next_num,
                    "title": f"Chapter {next_num}",
                    "prompt": "- Key events: [To be determined]\n- Character developments: [To be determined]\n- Setting: [To be determined]\n- Tone: [To be determined]",
                }
            )

        # Trim excess chapters if needed
        chapters = chapters[:num_chapters]

        return chapters

    def _emergency_outline_processing(
        self, messages: List[Dict], num_chapters: int
    ) -> List[Dict]:
        """Emergency processing when normal outline extraction fails"""
        print("Attempting emergency outline processing...")

        chapters = []
        current_chapter = None

        # Look through all messages for any chapter content
        for msg in messages:
            content = msg.get("content", "")
            lines = content.split("\n")

            for line in lines:
                # Look for chapter markers
                chapter_match = re.search(r"Chapter (\d+)", line)
                if chapter_match and "Key events:" in content:
                    if current_chapter:
                        chapters.append(current_chapter)

                    current_chapter = {
                        "chapter_number": int(chapter_match.group(1)),
                        "title": (
                            line.split(":")[-1].strip()
                            if ":" in line
                            else f"Chapter {chapter_match.group(1)}"
                        ),
                        "prompt": [],
                    }

                # Collect bullet points
                if current_chapter and line.strip().startswith("-"):
                    current_chapter["prompt"].append(line.strip())

            # Add the last chapter if it exists
            if current_chapter and current_chapter.get("prompt"):
                current_chapter["prompt"] = "\n".join(current_chapter["prompt"])
                chapters.append(current_chapter)
                current_chapter = None

        if not chapters:
            print("Emergency processing failed to find any chapters")
            # Create a basic outline structure
            chapters = [
                {
                    "chapter_number": i,
                    "title": f"Chapter {i}",
                    "prompt": "- Key events: [To be determined]\n- Character developments: [To be determined]\n- Setting: [To be determined]\n- Tone: [To be determined]",
                }
                for i in range(1, num_chapters + 1)
            ]

        # Ensure proper sequence and number of chapters
        return self._verify_chapter_sequence(chapters, num_chapters)
