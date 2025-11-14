"""Main class for generating books using AutoGen with improved iteration control"""

import autogen
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import os
import time
import re
import textwrap


@dataclass
class ChapterValidationResult:
    is_complete: bool
    final_text: Optional[str] = None
    missing_steps: List[str] = field(default_factory=list)
    memory_seen: bool = False


class BookGenerator:
    def __init__(
        self,
        agents: Dict[str, autogen.ConversableAgent],
        agent_config: Dict,
        outline: List[Dict],
    ):
        """Initialize with outline to maintain chapter count context"""
        self.agents = agents
        self.agent_config = agent_config
        self.output_dir = "book_output"
        self.chapters_memory: List[str] = []  # Store chapter summaries
        self.max_iterations = 4  # Allow additional revision loops
        self.outline = outline  # Store the outline
        self.min_chapter_words = int(os.getenv("MIN_CHAPTER_WORDS", "5000"))
        self.final_chapter_number = max(
            (ch.get("chapter_number", 0) for ch in outline), default=0
        )
        self.premature_ending_markers = [
            "The End",
            "Epilogue",
            "Afterword",
            "Acknowledgments",
            "Closing Credits",
        ]
        os.makedirs(self.output_dir, exist_ok=True)

    def _clean_chapter_content(self, content: str) -> str:
        """Clean up chapter content by removing artifacts and chapter numbers"""
        # Remove chapter number references
        content = re.sub(r"\*?\s*\(Chapter \d+.*?\)", "", content)
        content = re.sub(r"\*?\s*Chapter \d+.*?\n", "", content, count=1)

        # Clean up any remaining markdown artifacts
        content = content.replace("*", "")
        content = content.strip()

        return content

    def initiate_group_chat(self) -> autogen.GroupChat:
        """Create a new group chat for the agents with improved speaking order"""
        outline_context = "\n".join(
            [
                f"\nChapter {ch['chapter_number']}: {ch['title']}\n{ch['prompt']}"
                for ch in sorted(self.outline, key=lambda x: x["chapter_number"])
            ]
        )

        messages = [
            {"role": "system", "content": f"Complete Book Outline:\n{outline_context}"}
        ]

        writer_final = autogen.AssistantAgent(
            name="writer_final",
            system_message=self.agents["writer"].system_message,
            llm_config=self.agent_config,
        )

        return autogen.GroupChat(
            agents=[
                self.agents["user_proxy"],
                self.agents["memory_keeper"],
                self.agents["writer"],
                self.agents["editor"],
                writer_final,
            ],
            messages=messages,
            max_round=8,
            speaker_selection_method="round_robin",
        )

    def _get_sender(self, msg: Dict) -> str:
        """Helper to get sender from message regardless of format"""
        return msg.get("sender") or msg.get("name", "")

    def _verify_chapter_complete(
        self, messages: List[Dict], chapter_number: int
    ) -> ChapterValidationResult:
        """Verify that mandatory conversation steps are present."""
        sequence_flags = {
            "SCENE": False,
            "FEEDBACK": False,
            "EDITED_SCENE": False,
            "SCENE FINAL": False,
        }
        memory_seen = False
        final_text: Optional[str] = None

        for msg in messages:
            content = msg.get("content", "")

            if "MEMORY UPDATE:" in content:
                memory_seen = True

            if re.search(r"\bSCENE FINAL:", content):
                sequence_flags["SCENE FINAL"] = True
                final_text = content.split("SCENE FINAL:", 1)[1].strip()
            elif re.search(r"\bEDITED_SCENE:", content):
                sequence_flags["EDITED_SCENE"] = True
            elif re.search(r"\bFEEDBACK:", content):
                sequence_flags["FEEDBACK"] = True
            elif re.search(r"\bSCENE:", content) and not re.search(
                r"\bSCENE FINAL:", content
            ):
                sequence_flags["SCENE"] = True

        missing_steps = [step for step, done in sequence_flags.items() if not done]
        if missing_steps:
            print(f"Chapter {chapter_number} missing steps: {', '.join(missing_steps)}")
        is_complete = not missing_steps and bool(final_text)

        return ChapterValidationResult(
            is_complete=is_complete,
            final_text=final_text,
            missing_steps=missing_steps,
            memory_seen=memory_seen,
        )

    def _collect_content_issues(
        self, final_text: str, chapter_number: int
    ) -> Tuple[List[str], int]:
        """Identify minimum-length and premature-ending issues."""
        word_count = len(re.findall(r"\b\w+\b", final_text))
        issues: List[str] = []

        if word_count < self.min_chapter_words:
            issues.append(
                f"Word count {word_count:,} below minimum {self.min_chapter_words:,}."
            )

        if chapter_number != self.final_chapter_number:
            for marker_text in self.premature_ending_markers:
                if re.search(
                    rf"\b{re.escape(marker_text)}\b", final_text, re.IGNORECASE
                ):
                    issues.append(f"Detected premature ending phrase '{marker_text}'.")
                    break

        return issues, word_count

    def _build_revision_prompt(
        self,
        chapter_number: int,
        status: ChapterValidationResult,
        issues: List[str],
        word_count: int,
    ) -> str:
        """Construct an EXPAND instruction summarizing outstanding work."""
        lines = [f"EXPAND: Chapter {chapter_number}"]

        if status.missing_steps:
            lines.append("Missing required outputs: " + ", ".join(status.missing_steps))

        if not status.memory_seen:
            lines.append(
                "Memory Keeper: provide an updated MEMORY UPDATE before the writer revises."
            )

        if issues:
            lines.append("Quality issues detected:")
            lines.extend(f"- {issue}" for issue in issues)
        elif not status.missing_steps:
            lines.append(
                "The draft still needs additional depth before it can be finalized."
            )

        if word_count and word_count < self.min_chapter_words:
            lines.append(
                f"Current word count: {word_count:,} (minimum {self.min_chapter_words:,})."
            )

        lines.append("")
        lines.append(
            "Editor: respond with FEEDBACK and a complete EDITED_SCENE that addresses every listed issue."
        )
        lines.append(
            "Writer_final: only produce SCENE FINAL after applying the editor's updates and meeting the minimum length."
        )
        lines.append(
            "Avoid ending the story or using phrases like 'The End' until the actual final chapter."
        )

        return "\n".join(lines) + "\n"

    def _prepare_chapter_context(self, chapter_number: int, prompt: str) -> str:
        """Prepare context for chapter generation"""
        if chapter_number == 1:
            return f"Initial Chapter\nRequirements:\n{prompt}"

        context_parts = [
            "Previous Chapter Summaries:",
            *[
                f"Chapter {i+1}: {summary}"
                for i, summary in enumerate(self.chapters_memory)
            ],
            "\nCurrent Chapter Requirements:",
            prompt,
        ]
        return "\n".join(context_parts)

    def generate_chapter(self, chapter_number: int, prompt: str) -> None:
        """Generate a single chapter with quality gates and retries."""
        print(f"\nGenerating Chapter {chapter_number}...")

        try:
            groupchat = self.initiate_group_chat()
            manager = autogen.GroupChatManager(
                groupchat=groupchat, llm_config=self.agent_config
            )

            context = self._prepare_chapter_context(chapter_number, prompt)
            chapter_prompt = textwrap.dedent(
                f"""
                IMPORTANT: Wait for confirmation before proceeding.
                IMPORTANT: This is Chapter {chapter_number}. Do not proceed to next chapter until explicitly instructed.
                DO NOT END THE STORY HERE unless this is actually the final chapter ({self.final_chapter_number}).

                Current Task: Generate Chapter {chapter_number} content only.

                Chapter Outline:
                Title: {self.outline[chapter_number - 1]['title'] if self.outline else 'Unknown Title'}

                Chapter Requirements:
                {prompt}

                Previous Context for Reference:
                {context}

                Follow this exact sequence for Chapter {chapter_number} only:

                1. Memory Keeper: Share continuity context using "MEMORY UPDATE:"
                2. Writer: Deliver a complete draft labeled "SCENE:" (plan for enough material to exceed {self.min_chapter_words} words once finalized).
                3. Editor: Respond with "FEEDBACK:" plus a full "EDITED_SCENE:" revision.
                4. Writer Final: Publish the polished chapter with "SCENE FINAL:" after applying the editor's changes.

                The final SCENE FINAL must meet the minimum length and avoid premature endings such as "The End" unless this is the final chapter.
                """
            ).strip()

            self.agents["user_proxy"].initiate_chat(manager, message=chapter_prompt)

            attempts = 0
            while True:
                status = self._verify_chapter_complete(
                    groupchat.messages, chapter_number
                )
                issues: List[str] = []
                word_count = 0

                if status.final_text:
                    issues, word_count = self._collect_content_issues(
                        status.final_text, chapter_number
                    )

                if status.is_complete and not issues:
                    self._process_chapter_results(chapter_number, groupchat.messages)
                    chapter_file = os.path.join(
                        self.output_dir, f"chapter_{chapter_number:02d}.txt"
                    )
                    if not os.path.exists(chapter_file):
                        raise FileNotFoundError(
                            f"Chapter {chapter_number} file not created"
                        )

                    completion_msg = f"Chapter {chapter_number} is complete. Proceed with next chapter."
                    self.agents["user_proxy"].send(completion_msg, manager)
                    break

                if attempts >= self.max_iterations:
                    raise ValueError(
                        f"Chapter {chapter_number} generation incomplete after {self.max_iterations} revision attempts"
                    )

                revision_prompt = self._build_revision_prompt(
                    chapter_number, status, issues, word_count
                )
                attempts += 1
                self.agents["user_proxy"].send(revision_prompt, manager)

        except Exception as e:
            print(f"Error in chapter {chapter_number}: {str(e)}")
            self._handle_chapter_generation_failure(chapter_number, prompt)

    def _extract_final_scene(self, messages: List[Dict]) -> Optional[str]:
        """Extract chapter content with improved content detection"""
        for msg in reversed(messages):
            content = msg.get("content", "")
            sender = self._get_sender(msg)

            if sender in ["writer", "writer_final"]:
                # Handle complete scene content
                if "SCENE FINAL:" in content:
                    scene_text = content.split("SCENE FINAL:")[1].strip()
                    if scene_text:
                        return scene_text

                # Fallback to scene content
                if "SCENE:" in content:
                    scene_text = content.split("SCENE:")[1].strip()
                    if scene_text:
                        return scene_text

                # Handle raw content
                if len(content.strip()) > 100:  # Minimum content threshold
                    return content.strip()

        return None

    def _handle_chapter_generation_failure(
        self, chapter_number: int, prompt: str
    ) -> None:
        """Handle failed chapter generation with simplified retry"""
        print(f"Attempting simplified retry for Chapter {chapter_number}...")

        try:
            # Create a new group chat with just essential agents
            retry_groupchat = autogen.GroupChat(
                agents=[
                    self.agents["user_proxy"],
                    self.agents["story_planner"],
                    self.agents["writer"],
                ],
                messages=[],
                max_round=3,
            )

            manager = autogen.GroupChatManager(
                groupchat=retry_groupchat, llm_config=self.agent_config
            )

            retry_prompt = f"""Emergency chapter generation for Chapter {chapter_number}.
            
{prompt}

Please generate this chapter in two steps:
1. Story Planner: Create a basic outline (tag: PLAN)
2. Writer: Write the complete chapter (tag: SCENE FINAL)

Keep it simple and direct."""

            self.agents["user_proxy"].initiate_chat(manager, message=retry_prompt)

            # Save the retry results
            self._process_chapter_results(chapter_number, retry_groupchat.messages)

        except Exception as e:
            print(f"Error in retry attempt for Chapter {chapter_number}: {str(e)}")
            print("Unable to generate chapter content after retry")

    def _process_chapter_results(
        self, chapter_number: int, messages: List[Dict]
    ) -> None:
        """Process and save chapter results, updating memory"""
        try:
            # Extract the Memory Keeper's final summary
            memory_updates = []
            for msg in reversed(messages):
                sender = self._get_sender(msg)
                content = msg.get("content", "")

                if sender == "memory_keeper" and "MEMORY UPDATE:" in content:
                    update_start = content.find("MEMORY UPDATE:") + 14
                    memory_updates.append(content[update_start:].strip())
                    break

            # Add to memory even if no explicit update (use basic content summary)
            if memory_updates:
                self.chapters_memory.append(memory_updates[0])
            else:
                # Create basic memory from chapter content
                chapter_content = self._extract_final_scene(messages)
                if chapter_content:
                    basic_summary = (
                        f"Chapter {chapter_number} Summary: {chapter_content[:200]}..."
                    )
                    self.chapters_memory.append(basic_summary)

            # Extract and save the chapter content
            self._save_chapter(chapter_number, messages)

        except Exception as e:
            print(f"Error processing chapter results: {str(e)}")
            raise

    def _save_chapter(self, chapter_number: int, messages: List[Dict]) -> None:
        print(f"\nSaving Chapter {chapter_number}")
        try:
            chapter_content = self._extract_final_scene(messages)
            if not chapter_content:
                raise ValueError(f"No content found for Chapter {chapter_number}")

            chapter_content = self._clean_chapter_content(chapter_content)

            filename = os.path.join(
                self.output_dir, f"chapter_{chapter_number:02d}.txt"
            )

            # Create backup if file exists
            if os.path.exists(filename):
                backup_filename = f"{filename}.backup"
                import shutil

                shutil.copy2(filename, backup_filename)

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Chapter {chapter_number}\n\n{chapter_content}")

            # Verify file
            with open(filename, "r", encoding="utf-8") as f:
                saved_content = f.read()
                if len(saved_content.strip()) == 0:
                    raise IOError(f"File {filename} is empty")

            print(f"-> Saved to: {filename}")

        except Exception as e:
            print(f"Error saving chapter: {str(e)}")
            raise

    def generate_book(self, outline: List[Dict]) -> None:
        """Generate the book with strict chapter sequencing"""
        print("\nStarting Book Generation...")
        print(f"Total chapters: {len(outline)}")

        # Sort outline by chapter number
        sorted_outline = sorted(outline, key=lambda x: x["chapter_number"])

        for chapter in sorted_outline:
            chapter_number = chapter["chapter_number"]

            # Verify previous chapter exists and is valid
            if chapter_number > 1:
                prev_file = os.path.join(
                    self.output_dir, f"chapter_{chapter_number-1:02d}.txt"
                )
                if not os.path.exists(prev_file):
                    print(f"Previous chapter {chapter_number-1} not found. Stopping.")
                    break

                # Verify previous chapter content
                with open(prev_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not self._verify_chapter_content(content, chapter_number - 1):
                        print(
                            f"Previous chapter {chapter_number-1} content invalid. Stopping."
                        )
                        break

            # Generate current chapter
            print(f"\n{'='*20} Chapter {chapter_number} {'='*20}")
            self.generate_chapter(chapter_number, chapter["prompt"])

            # Verify current chapter
            chapter_file = os.path.join(
                self.output_dir, f"chapter_{chapter_number:02d}.txt"
            )
            if not os.path.exists(chapter_file):
                print(f"Failed to generate chapter {chapter_number}")
                break

            with open(chapter_file, "r", encoding="utf-8") as f:
                content = f.read()
                if not self._verify_chapter_content(content, chapter_number):
                    print(f"Chapter {chapter_number} content invalid")
                    break

            print(f"-> Chapter {chapter_number} complete")
            time.sleep(5)

    def _verify_chapter_content(self, content: str, chapter_number: int) -> bool:
        """Verify chapter content meets minimum quality requirements."""
        if not content:
            return False

        lines = [line for line in content.splitlines() if line.strip()]
        if not lines:
            return False

        header = lines[0]
        if not header.startswith(f"Chapter {chapter_number}"):
            print(f"Chapter {chapter_number} missing or misnumbered header.")
            return False

        body = "\n".join(lines[1:]).strip()
        if not body:
            return False

        issues, _ = self._collect_content_issues(body, chapter_number)
        if issues:
            print(f"Chapter {chapter_number} failed validation: {'; '.join(issues)}")
            return False

        return True
