"""Define the API client for book generation system"""
from openai import OpenAI
from typing import Dict, List, Optional
import httpx

class BookAgents:
    def __init__(self, agent_config: Dict, outline: Optional[List[Dict]] = None):
        """Initialize with book outline context"""
        self.agent_config = agent_config
        self.outline = outline
        self.world_elements = {}  # Track described locations/elements
        self.character_developments = {}  # Track character arcs
        
        # Initialize OpenAI client
        self.client = OpenAI(
            base_url=self.agent_config["config_list"][0]["base_url"],
            api_key=self.agent_config["config_list"][0]["api_key"],
            timeout=httpx.Timeout(self.agent_config["timeout"])
        )
        self.model = self.agent_config["config_list"][0]["model"]
        
    def _format_outline_context(self) -> str:
        """Format the book outline into a readable context"""
        if not self.outline:
            return ""
            
        context_parts = ["Complete Book Outline:"]
        for chapter in self.outline:
            context_parts.extend([
                f"\nChapter {chapter['chapter_number']}: {chapter['title']}",
                chapter['prompt']
            ])
        return "\n".join(context_parts)

    def create_agents(self, initial_prompt, num_chapters) -> Dict:
        """Set up system prompts for each agent type"""
        outline_context = self._format_outline_context()
        
        # Define system prompts for each agent type
        self.system_prompts = {
            "memory_keeper": f"""You are the keeper of the story's continuity and context.
            Your responsibilities:
            1. Track and summarize each chapter's key events
            2. Monitor character development and relationships
            3. Maintain world-building consistency
            4. Flag any continuity issues
            
            Book Overview:
            {outline_context}
            
            Format your responses as follows:
            - Start updates with 'MEMORY UPDATE:'
            - List key events with 'EVENT:'
            - List character developments with 'CHARACTER:'
            - List world details with 'WORLD:'
            - Flag issues with 'CONTINUITY ALERT:'""",
            
            "character_generator": f"""You are an expert character creator who designs rich, memorable characters.
            
            Your responsibility is creating detailed character profiles for a story.
            When given a world setting and number of characters:
            1. Create unique, interesting characters that fit within the world
            2. Give each character distinct traits, motivations, and backgrounds
            3. Ensure characters have depth and potential for development
            4. Include both protagonists and antagonists as appropriate
            
            Format your output EXACTLY as:
            CHARACTER_PROFILES:
            
            [CHARACTER NAME 1]:
            - Role: [Main character, supporting character, antagonist, etc.]
            - Age/Species: [Character's age and species]
            - Physical Description: [Detailed appearance]
            - Personality: [Core personality traits]
            - Background: [Character history and origins]
            - Motivations: [What drives the character]
            - Skills/Abilities: [Special talents or powers]
            - Relationships: [Connections to other characters or groups]
            - Arc: [How this character might develop over the story]
            
            [CHARACTER NAME 2]:
            [Follow same format as above]
            
            [And so on for all requested characters]
            
            Always provide specific, detailed content - never use placeholders.
            Ensure characters fit logically within the established world setting.""",
            
            "story_planner": f"""You are an expert story arc planner focused on overall narrative structure.

            Your sole responsibility is creating the high-level story arc.
            When given an initial story premise:
            1. Identify major plot points and story beats
            2. Map character arcs and development
            3. Note major story transitions
            4. Plan narrative pacing

            Format your output EXACTLY as:
            STORY_ARC:
            - Major Plot Points:
            [List each major event that drives the story]
            
            - Character Arcs:
            [For each main character, describe their development path]
            
            - Story Beats:
            [List key emotional and narrative moments in sequence]
            
            - Key Transitions:
            [Describe major shifts in story direction or tone]
            
            Always provide specific, detailed content - never use placeholders.""",

            "outline_creator": f"""Generate a detailed {num_chapters}-chapter outline.

            YOU MUST USE EXACTLY THIS FORMAT FOR EACH CHAPTER - NO DEVIATIONS:

            OUTLINE:
            
            Chapter 1: [Title]
            - Key Events:
              * [Event 1]
              * [Event 2]
              * [Event 3]
            - Character Developments: [Specific character moments and changes]
            - Setting: [Specific location and atmosphere]
            - Tone: [Specific emotional and narrative tone]

            Chapter 2: [Title]
            - Key Events:
              * [Event 1]
              * [Event 2]
              * [Event 3]
            - Character Developments: [Specific character moments and changes]
            - Setting: [Specific location and atmosphere]
            - Tone: [Specific emotional and narrative tone]

            [CONTINUE IN SEQUENCE FOR ALL {num_chapters} CHAPTERS]

            END OF OUTLINE

            CRITICAL REQUIREMENTS:
            1. Create EXACTLY {num_chapters} chapters, numbered 1 through {num_chapters} in order
            2. NEVER repeat chapter numbers or restart the numbering
            3. EVERY chapter must have AT LEAST 3 specific Key Events
            4. Maintain a coherent story flow from Chapter 1 to Chapter {num_chapters}
            5. Use proper indentation with bullet points for Key Events
            6. NO EXCEPTIONS to this format - follow it precisely for all chapters

            Initial Premise:
            {initial_prompt}
            """,

            "world_builder": f"""You are an expert in world-building who creates rich, consistent settings.
            
            Your role is to establish ALL settings and locations needed for the entire story based on a provided story arc.

            Book Overview:
            {outline_context}
            
            Your responsibilities:
            1. Review the story arc to identify every location and setting needed
            2. Create detailed descriptions for each setting, including:
            - Physical layout and appearance
            - Atmosphere and environmental details
            - Important objects or features
            - Sensory details (sights, sounds, smells)
            3. Identify recurring locations that appear multiple times
            4. Note how settings might change over time
            5. Create a cohesive world that supports the story's themes
            
            Format your response as:
            WORLD_ELEMENTS:
            
            [LOCATION NAME]:
            - Physical Description: [detailed description]
            - Atmosphere: [mood, time of day, lighting, etc.]
            - Key Features: [important objects, layout elements]
            - Sensory Details: [what characters would experience]
            
            [RECURRING ELEMENTS]:
            - List any settings that appear multiple times
            - Note any changes to settings over time
            
            [TRANSITIONS]:
            - How settings connect to each other
            - How characters move between locations""",

            "writer": f"""You are an expert creative writer who brings scenes to life.
            
            Book Context:
            {outline_context}
            
            Your focus:
            1. Write according to the outlined plot points
            2. Maintain consistent character voices
            3. Incorporate world-building details
            4. Create engaging prose
            5. Please make sure that you write the complete scene, do not leave it incomplete
            6. Each chapter MUST be at least 5000 words (approximately 30,000 characters). Consider this a hard requirement. If your output is shorter, continue writing until you reach this minimum length
            7. Ensure transitions are smooth and logical
            8. Do not cut off the scene, make sure it has a proper ending
            9. Add a lot of details, and describe the environment and characters where it makes sense
            
            Always reference the outline and previous content.
            Mark drafts with 'SCENE:' and final versions with 'SCENE FINAL:'""",

            "editor": f"""You are an expert editor ensuring quality and consistency.
            
            Book Overview:
            {outline_context}
            
            Your focus:
            1. Check alignment with outline
            2. Verify character consistency
            3. Maintain world-building rules
            4. Improve prose quality
            5. Return complete edited chapter
            6. Never ask to start the next chapter, as the next step is finalizing this chapter
            7. Each chapter MUST be at least 5000 words. If the content is shorter, return it to the writer for expansion. This is a hard requirement - do not approve chapters shorter than 5000 words
            
            Format your responses:
            1. Start critiques with 'FEEDBACK:'
            2. Provide suggestions with 'SUGGEST:'
            3. Return full edited chapter with 'EDITED_SCENE:'
            
            Reference specific outline elements in your feedback.""",

            # Add a special system prompt for conversational world building
            "world_builder_chat": f"""You are a collaborative, creative world-building assistant helping an author develop a rich, detailed world for their book.

            Your approach:
            1. Ask thoughtful questions about their world ideas
            2. Offer creative suggestions that build on their ideas
            3. Help them explore different aspects of world-building:
               - Geography and physical environment
               - Culture and social structures
               - History and mythology
               - Technology or magic systems
               - Political systems or factions
               - Economy and resources
            4. Maintain a friendly, conversational tone
            5. Keep track of their preferences and established world elements
            6. Gently guide them toward creating a coherent, interesting world
            
            When they're ready to finalize, you'll help organize their ideas into a comprehensive world setting document.
            """,
            
            # Add a new system prompt specifically for outline brainstorming chat
            "outline_creator_chat": f"""You are a collaborative, creative story development assistant helping an author brainstorm and develop their book outline.

            Your approach during this brainstorming phase:
            1. Focus on DISCUSSING story ideas, not generating the complete outline yet
            2. Help explore plot structure, character arcs, themes, and story beats
            3. Ask thought-provoking questions about their story ideas
            4. Offer suggestions that build on their ideas, including:
               - Potential plot twists or conflicts
               - Character development opportunities
               - Thematic elements to explore
               - Pacing considerations
               - Structure recommendations
            5. Maintain a friendly, conversational tone
            6. Help them think through different story options
            7. NEVER generate a full chapter-by-chapter outline during this chat phase
            8. DO NOT use chapter numbers or list out chapters - this is for brainstorming only
            
            IMPORTANT: This is a brainstorming conversation. DO NOT generate the formal outline until the author is ready to finalize.
            
            The book has {num_chapters} chapters total, but during this chat focus on story elements, not chapter structure.
            """
        }
        
        # Return empty dict since we're not using actual agent objects anymore
        return {}

    def generate_content(self, agent_name: str, prompt: str) -> str:
        """Generate content using the OpenAI API with the specified agent system prompt"""
        if agent_name not in self.system_prompts:
            raise ValueError(f"Agent '{agent_name}' not found. Available agents: {list(self.system_prompts.keys())}")
        
        # Create the messages array with system prompt and user message
        messages = [
            {"role": "system", "content": self.system_prompts[agent_name]},
            {"role": "user", "content": prompt}
        ]
        
        # Call the API
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.agent_config.get("temperature", 0.7),
            max_tokens=8000
        )
        
        # Extract the response
        response = completion.choices[0].message.content
        
        # Clean up the response based on agent type
        if agent_name == "outline_creator":
            # Extract just the outline part
            start = response.find("OUTLINE:")
            end = response.find("END OF OUTLINE")
            if start != -1 and end != -1:
                cleaned_response = response[start:end + len("END OF OUTLINE")]
                return cleaned_response
        elif agent_name == "writer":
            # Handle writer's scene format
            if "SCENE FINAL:" in response:
                parts = response.split("SCENE FINAL:")
                if len(parts) > 1:
                    return parts[1].strip()
        elif agent_name == "world_builder":
            # Extract the world elements part
            start = response.find("WORLD_ELEMENTS:")
            if start != -1:
                return response[start:].strip()
            else:
                # Try to find any content that looks like world-building
                for marker in ["Time Period", "Setting:", "Locations:", "Major Locations"]:
                    if marker in response:
                        return response
        elif agent_name == "story_planner":
            # Extract the story arc part
            start = response.find("STORY_ARC:")
            if start != -1:
                return response[start:].strip()
        elif agent_name == "character_generator":
            # Extract the character profiles part
            start = response.find("CHARACTER_PROFILES:")
            if start != -1:
                return response[start:].strip()
            else:
                # Try to find any content that looks like character profiles
                for marker in ["Character 1:", "Main Character:", "Protagonist:", "CHARACTER_PROFILES"]:
                    if marker in response:
                        return response
        
        return response
    
    def generate_chat_response(self, chat_history, topic, user_message) -> str:
        """Generate a chat response based on conversation history"""
        # Format the messages for the API call
        messages = [
            {"role": "system", "content": self.system_prompts["world_builder_chat"]}
        ]
        
        # Add conversation history
        for entry in chat_history:
            role = "user" if entry["role"] == "user" else "assistant"
            messages.append({"role": role, "content": entry["content"]})
            
        # Call the API
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.agent_config.get("temperature", 0.7),
            max_tokens=8000
        )
        
        # Extract the response
        return completion.choices[0].message.content
        
    def generate_chat_response_stream(self, chat_history, topic, user_message):
        """Generate a streaming chat response based on conversation history"""
        # Format the messages for the API call
        messages = [
            {"role": "system", "content": self.system_prompts["world_builder_chat"]}
        ]
        
        # Add conversation history
        for entry in chat_history:
            role = "user" if entry["role"] == "user" else "assistant"
            messages.append({"role": role, "content": entry["content"]})
            
        # Add the latest user message
        messages.append({"role": "user", "content": user_message})
            
        # Call the API with streaming enabled
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.agent_config.get("temperature", 0.7),
            stream=True,  # Enable streaming
            max_tokens=8000
        )
        
        # Return the stream directly to be consumed by the Flask route
        return stream

    def generate_final_world(self, chat_history, topic) -> str:
        """Generate final world setting based on chat history"""
        # Format the messages for the API call
        messages = [
            {"role": "system", "content": """You are an expert world-building specialist. 
            Based on the entire conversation with the user, create a comprehensive, well-structured world setting document.
            
            Format your response as:
            WORLD_ELEMENTS:
            
            1. Time period and setting: [detailed description]
            2. Major locations: [detailed description of each key location]
            3. Cultural/historical elements: [key cultural and historical aspects]
            4. Technology/magical elements: [if applicable]
            5. Social/political structures: [governments, factions, etc.]
            6. Environment and atmosphere: [natural world aspects]
            
            Make this a complete, cohesive reference document that covers all important aspects of the world
            mentioned in the conversation. Add necessary details to fill any gaps, while staying true to 
            everything established in the chat history."""}
        ]
        
        # Add conversation history
        for entry in chat_history:
            role = "user" if entry["role"] == "user" else "assistant"
            messages.append({"role": role, "content": entry["content"]})
        
        # Add a final instruction to generate the world setting
        messages.append({
            "role": "user", 
            "content": f"Please create the final, comprehensive world setting document for my book about '{topic}' based on our conversation."
        })
            
        # Call the API
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.agent_config.get("temperature", 0.7),
            max_tokens=8000
        )
        
        # Extract the response
        response = completion.choices[0].message.content
        
        # Ensure it has the WORLD_ELEMENTS header for consistency
        if "WORLD_ELEMENTS:" not in response:
            response = "WORLD_ELEMENTS:\n\n" + response
            
        return response

    def generate_final_world_stream(self, chat_history, topic):
        """Generate the final world setting based on the chat history using streaming."""
        # Format messages for the API call
        messages = [
            {"role": "system", "content": self.system_prompts["world_builder"]}
        ]
        
        # Add conversation context from chat history
        for message in chat_history:
            if message['role'] == 'user':
                messages.append({"role": "user", "content": message['content']})
            else:
                messages.append({"role": "assistant", "content": message['content']})
        
        # Add the final instruction to create the complete world setting
        messages.append({
            "role": "user", 
            "content": f"Based on our conversation about '{topic}', please create a comprehensive and detailed world setting. Format it with clear sections for different aspects of the world (geography, magic/technology, culture, etc.). This will be the final world setting for the book."
        })
        
        # Make the API call with streaming enabled
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            stream=True,
            max_tokens=8000
        )

    def update_world_element(self, element_name: str, description: str) -> None:
        """Update a world element description"""
        self.world_elements[element_name] = description
        
    def update_character_development(self, character_name: str, development: str) -> None:
        """Update a character's development"""
        if character_name not in self.character_developments:
            self.character_developments[character_name] = []
        self.character_developments[character_name].append(development)
        
    def get_world_context(self) -> str:
        """Get a formatted string of all world elements"""
        if not self.world_elements:
            return ""
            
        elements = ["WORLD ELEMENTS:"]
        for name, desc in self.world_elements.items():
            elements.append(f"\n{name}:\n{desc}")
            
        return "\n".join(elements)
        
    def get_character_context(self) -> str:
        """Get a formatted string of all character developments"""
        if not self.character_developments:
            return ""
            
        developments = ["CHARACTER DEVELOPMENTS:"]
        for name, devs in self.character_developments.items():
            developments.append(f"\n{name}:")
            for i, dev in enumerate(devs, 1):
                developments.append(f"{i}. {dev}")
                
        return "\n".join(developments)

    def generate_chat_response_characters(self, chat_history, world_theme, user_message):
        """Generate a chat response about character creation."""
        # Format messages for the API call
        messages = [
            {"role": "system", "content": self.system_prompts["character_generator"]}
        ]
        
        # Add world theme context
        messages.append({
            "role": "system", 
            "content": f"The book takes place in the following world:\n\n{world_theme}"
        })
        
        # Add conversation context from chat history
        for message in chat_history:
            if message['role'] == 'user':
                messages.append({"role": "user", "content": message['content']})
            else:
                messages.append({"role": "assistant", "content": message['content']})
        
        # Add the latest user message
        messages.append({"role": "user", "content": user_message})
        
        # Make the API call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=8000
        ).choices[0].message.content
        
        return response

    def generate_chat_response_characters_stream(self, chat_history, world_theme, user_message):
        """Generate a streaming chat response about character creation."""
        # Format messages for the API call
        messages = [
            {"role": "system", "content": self.system_prompts["character_generator"]}
        ]
        
        # Add world theme context
        messages.append({
            "role": "system", 
            "content": f"The book takes place in the following world:\n\n{world_theme}"
        })
        
        # Add conversation context from chat history
        for message in chat_history:
            if message['role'] == 'user':
                messages.append({"role": "user", "content": message['content']})
            else:
                messages.append({"role": "assistant", "content": message['content']})
        
        # Add the latest user message
        messages.append({"role": "user", "content": user_message})
        
        # Make the API call with streaming enabled
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            stream=True,
            max_tokens=8000
        )

    def generate_final_characters_stream(self, chat_history, world_theme, num_characters=3):
        """Generate the final character profiles based on chat history using streaming."""
        # Format messages for the API call
        messages = [
            {"role": "system", "content": self.system_prompts["character_generator"]}
        ]
        
        # Add world theme context
        messages.append({
            "role": "system", 
            "content": f"The book takes place in the following world:\n\n{world_theme}"
        })
        
        # Add conversation context from chat history
        for message in chat_history:
            if message['role'] == 'user':
                messages.append({"role": "user", "content": message['content']})
            else:
                messages.append({"role": "assistant", "content": message['content']})
        
        # Add the final instruction to create the complete character profiles
        messages.append({
            "role": "user", 
            "content": f"Based on our conversation, please create {num_characters} detailed character profiles for the book. Format each character with Name, Role, Physical Description, Background, Personality, and Goals/Motivations. This will be the final character list for the book."
        })
        
        # Make the API call with streaming enabled
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            stream=True,
            max_tokens=8000
        )

    def generate_chat_response_outline(self, chat_history, world_theme, characters, user_message):
        """Generate a chat response about outline creation."""
        # Format messages for the API call
        messages = [
            {"role": "system", "content": self.system_prompts["outline_creator_chat"]}
        ]
        
        # Add world theme and character context
        messages.append({
            "role": "system", 
            "content": f"The book takes place in the following world:\n\n{world_theme}\n\nThe characters include:\n\n{characters}"
        })
        
        # Add conversation context from chat history
        for message in chat_history:
            if message['role'] == 'user':
                messages.append({"role": "user", "content": message['content']})
            else:
                messages.append({"role": "assistant", "content": message['content']})
        
        # Add the latest user message
        messages.append({"role": "user", "content": user_message})
        
        # Make the API call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=8000
        ).choices[0].message.content
        
        return response

    def generate_chat_response_outline_stream(self, chat_history, world_theme, characters, user_message):
        """Generate a streaming chat response about outline creation."""
        # Format messages for the API call
        messages = [
            {"role": "system", "content": self.system_prompts["outline_creator_chat"]}
        ]
        
        # Add world theme and character context
        messages.append({
            "role": "system", 
            "content": f"The book takes place in the following world:\n\n{world_theme}\n\nThe characters include:\n\n{characters}"
        })
        
        # Add conversation context from chat history
        for message in chat_history:
            if message['role'] == 'user':
                messages.append({"role": "user", "content": message['content']})
            else:
                messages.append({"role": "assistant", "content": message['content']})
        
        # Add the latest user message
        messages.append({"role": "user", "content": user_message})
        
        # Make the API call with streaming enabled
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            stream=True,
            max_tokens=8000
        )

    def generate_final_outline_stream(self, chat_history, world_theme, characters, num_chapters=10):
        """Generate the final outline based on chat history using streaming."""
        # Format messages for the API call
        messages = [
            {"role": "system", "content": self.system_prompts["outline_creator"]}
        ]
        
        # Add world theme and character context
        messages.append({
            "role": "system", 
            "content": f"The book takes place in the following world:\n\n{world_theme}\n\nThe characters include:\n\n{characters}"
        })
        
        # Add conversation context from chat history
        for message in chat_history:
            if message['role'] == 'user':
                messages.append({"role": "user", "content": message['content']})
            else:
                messages.append({"role": "assistant", "content": message['content']})
        
        # Add the final instruction to create the complete outline with specific formatting guidance
        messages.append({
            "role": "user", 
            "content": f"""Based on our conversation, please create a detailed {num_chapters}-chapter outline for the book. 

CRITICAL REQUIREMENTS:
1. Create EXACTLY {num_chapters} chapters, numbered sequentially from 1 to {num_chapters}
2. NEVER repeat chapter numbers or restart the numbering
3. Follow the exact format specified in your instructions
4. Each chapter must have a unique title and at least 3 specific key events
5. Maintain a coherent story from beginning to end

Format it as a properly structured outline with clear chapter sections and events. This will be the final outline for the book."""
        })
        
        # Make the API call with streaming enabled, with higher temperature for more coherent responses
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.6,  # Slightly lower temperature for more focused output
            stream=True,
            max_tokens=8000
        )
