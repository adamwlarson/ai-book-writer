# AutoGen Book Generator

A Python-based system that uses AutoGen to generate complete books through collaborative AI agents. The system employs multiple specialized agents working together to create coherent, structured narratives from initial prompts.

## Features

- Multi-agent collaborative writing system
- Structured chapter generation with consistent formatting
- Maintains story continuity and character development
- Automated world-building and setting management
- Support for complex, multi-chapter narratives
- Built-in validation and error handling

## Architecture

The system uses several specialized agents:

- **Story Planner**: Creates high-level story arcs and plot points
- **World Builder**: Establishes and maintains consistent settings
- **Memory Keeper**: Tracks continuity and context
- **Writer**: Generates the actual prose
- **Editor**: Reviews and improves content
- **Outline Creator**: Creates detailed chapter outlines

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/autogen-book-generator.git
cd autogen-book-generator
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Interactive UI

Launch the Streamlit dashboard for a guided experience:

```bash
streamlit run streamlit_app.py
```

The UI lets you tweak the story prompt, choose the number of chapters, and decide whether to generate full chapters. Progress updates appear in real time, and you can download the outline and any generated chapters directly from the page.

1. Basic usage:
```python
from main import main

if __name__ == "__main__":
    main()
```

2. Custom initial prompt:
```python
from config import get_config
from agents import BookAgents
from book_generator import BookGenerator
from outline_generator import OutlineGenerator

# Get configuration
agent_config = get_config()

# Create agents
outline_agents = BookAgents(agent_config)
agents = outline_agents.create_agents()

# Generate outline
outline_gen = OutlineGenerator(agents, agent_config)
outline = outline_gen.generate_outline(your_prompt, num_chapters=25)

# Initialize book generator
book_agents = BookAgents(agent_config, outline)
agents_with_context = book_agents.create_agents()
book_gen = BookGenerator(agents_with_context, agent_config, outline)

# Generate book
book_gen.generate_book(outline)
```

## Configuration

The system can be configured through `config.py`. Key configurations include:

- LLM endpoint URL
- Number of chapters
- Agent parameters
- Output directory settings

### Choosing an LLM backend

The system reads environment variables via `config.get_config()` so you can switch providers without touching code.
By default it targets a local OpenAI-compatible endpoint at `http://localhost:1234/v1`, but it now understands OpenRouter as well.

**Local endpoint variables**
- `LOCAL_LLM_URL` sets the base URL (defaults to `http://localhost:1234/v1`)
- `LOCAL_LLM_MODEL` overrides the model name passed to the server
- `LOCAL_LLM_API_KEY` is only needed if your local server enforces auth

**OpenRouter variables**
- `OPENROUTER_API_KEY` (required) authenticates every request
- `OPENROUTER_MODEL` chooses the model id (defaults to `openai/gpt-4o-mini`)
  - You can use preset keys like `gpt-4o-mini`, `claude-3-haiku`, `llama-3.1-70b`, etc.
  - Or use full model IDs like `openai/gpt-4o-mini`, `anthropic/claude-3-haiku`, etc.
  - Check [OpenRouter's model list](https://openrouter.ai/models) for all available models
- `OPENROUTER_BASE_URL` lets you point to a custom OpenRouter gateway
- `OPENROUTER_HTTP_REFERER` and `OPENROUTER_APP_TITLE` add optional headers

Set `LLM_TIMEOUT` (seconds) if you need to override the default 600 second request timeout.

When `OPENROUTER_API_KEY` is present and you do not pass a `local_url`, `get_config()` automatically uses OpenRouter.
The Streamlit UI exposes the same choice with a provider selector; if you choose OpenRouter it will prompt for a model id and warn when the key is missing.

**Popular preset model options:**
- `gpt-4o-mini` - Fast, affordable model for everyday tasks
- `gpt-4o` - Advanced model for complex tasks  
- `claude-3-haiku` - Fast, intelligent model from Anthropic
- `claude-3-sonnet` - Balanced model for everyday use
- `claude-3-opus` - Most powerful Claude model
- `llama-3.1-70b` - Powerful open-source model
- `llama-3.1-405b` - Most powerful open-source model (free tier)
- `gemini-pro` - Google's flagship model
- `command-r-plus` - Great for reasoning and complex tasks

## Output Structure

Generated content is saved in the `book_output` directory:
```
book_output/
├── outline.txt
├── chapter_01.txt
├── chapter_02.txt
└── ...
```

## Requirements

- Python 3.8+
- AutoGen 0.2.0+
- Other dependencies listed in requirements.txt

## Development

To contribute to the project:

1. Fork the repository
2. Create a new branch for your feature
3. Install development dependencies:
```bash
pip install -r requirements.txt
```
4. Make your changes
5. Run tests:
```bash
pytest
```
6. Submit a pull request

## Error Handling

The system includes robust error handling:
- Validates chapter completeness
- Ensures proper formatting
- Maintains backup copies of generated content
- Implements retry logic for failed generations

## Limitations

- Requires significant computational resources
- Generation time increases with chapter count
- Quality depends on the underlying LLM model
- May require manual review for final polish

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built using the [AutoGen](https://github.com/microsoft/autogen) framework
- Inspired by collaborative writing systems
