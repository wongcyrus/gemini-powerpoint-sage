# Prompt Rewriter Agent

## Overview

The Prompt Rewriter Agent is an LLM-powered system that intelligently combines base agent prompts with visual and speaker style guidelines. Instead of simply appending styles to prompts, it deeply integrates them throughout the instructions for better adherence and more consistent results.

## Problem Solved

Previously, styles were appended to the end of agent prompts, which often resulted in:
- Styles being ignored or deprioritized by the agent
- Inconsistent application of style guidelines
- Styles feeling "tacked on" rather than integrated

## Solution

The new approach uses a dedicated LLM agent to rewrite prompts by:
1. Analyzing the base prompt structure
2. Identifying key sections where style should be emphasized
3. Weaving style requirements throughout the instructions
4. Adding concrete examples and checkpoints
5. Making style adherence feel natural and mandatory

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PromptRewriter Service                   │
│                                                             │
│  ┌──────────────┐         ┌─────────────────────┐         │
│  │ Visual Style │────────▶│                     │         │
│  └──────────────┘         │  Prompt Rewriter    │         │
│                           │      Agent          │         │
│  ┌──────────────┐         │   (LLM-Powered)     │         │
│  │Speaker Style │────────▶│                     │         │
│  └──────────────┘         └─────────────────────┘         │
│                                     │                       │
│                                     ▼                       │
│                           ┌─────────────────────┐         │
│                           │  Rewritten Prompts  │         │
│                           │  - Designer         │         │
│                           │  - Writer           │         │
│                           │  - Title Generator  │         │
│                           └─────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Prompt Rewriter Agent (`agents/prompt_rewriter.py`)

The core LLM agent that performs intelligent prompt rewriting.

**Key Features:**
- Deep integration of styles into prompts
- Contextual placement of style requirements
- Concrete examples and checkpoints
- Maintains original prompt structure

**Model:** `gemini-2.5-flash` (configurable via `MODEL_PROMPT_REWRITER` env var)

### 2. PromptRewriter Service (`services/prompt_rewriter.py`)

Service layer that manages the rewriting process.

**Methods:**
- `rewrite_designer_prompt(base_prompt)` - Rewrites designer prompts with visual style
- `rewrite_writer_prompt(base_prompt)` - Rewrites writer prompts with speaker style
- `rewrite_title_generator_prompt(base_prompt)` - Rewrites title generator prompts with speaker style

**Features:**
- Automatic fallback to simple concatenation if LLM fails
- Comprehensive logging of rewrite process
- Statistics and preview of rewritten prompts

### 3. Agent Factory Integration (`agents/agent_factory.py`)

Factory functions that create agents with rewritten prompts.

**Functions:**
- `create_designer_agent(visual_style)` - Creates designer with visual style
- `create_writer_agent(speaker_style)` - Creates writer with speaker style
- `create_title_generator_agent(speaker_style)` - Creates title generator with speaker style
- `create_all_agents(visual_style, speaker_style)` - Creates all agents with styles

## Usage

### Basic Usage

```python
from services.prompt_rewriter import PromptRewriter
from agents import prompt

# Define your styles
visual_style = """
Cyberpunk aesthetic with neon colors (electric blue, hot pink, purple).
Dark backgrounds with glowing elements.
Futuristic typography with sharp angles.
"""

speaker_style = """
Energetic tech evangelist.
Uses phrases like "game-changer", "revolutionary".
Speaks in short, punchy sentences.
"""

# Create rewriter
rewriter = PromptRewriter(
    visual_style=visual_style,
    speaker_style=speaker_style
)

# Rewrite prompts
designer_prompt = rewriter.rewrite_designer_prompt(prompt.DESIGNER_PROMPT)
writer_prompt = rewriter.rewrite_writer_prompt(prompt.WRITER_PROMPT)
```

### Using Agent Factory

```python
from agents.agent_factory import create_all_agents

# Create all agents with custom styles
agents = create_all_agents(
    visual_style="Minimalist design with pastel colors",
    speaker_style="Formal academic tone with technical precision"
)

# Access individual agents
designer = agents["designer"]
writer = agents["writer"]
title_generator = agents["title_generator"]
```

### Configuration

Set the model for prompt rewriting via environment variable:

```bash
export MODEL_PROMPT_REWRITER="gemini-2.5-flash"
```

Or in your `.env` file:

```
MODEL_PROMPT_REWRITER=gemini-2.5-flash
```

## Prompt Rewriting Strategy

The agent follows these principles when rewriting:

### For Visual Styles (Designer Agent)

1. **Color Integration**: Weaves color requirements into design sections
2. **Typography**: Adds font and text style requirements
3. **Layout**: Integrates spacing and composition guidelines
4. **Visual Elements**: Specifies icons, shapes, and decorative elements
5. **Consistency Checks**: Adds validation points for style adherence

### For Speaker Styles (Writer/Title Generator)

1. **Tone Integration**: Weaves tone requirements into writing guidelines
2. **Vocabulary**: Adds specific terminology and phrasing patterns
3. **Sentence Structure**: Specifies rhythm and complexity
4. **Voice Consistency**: Adds checkpoints for maintaining persona
5. **Example Phrases**: Provides concrete examples of the style

## Fallback Mechanism

If the LLM-based rewriting fails, the system automatically falls back to simple concatenation:

```python
def _fallback_designer_rewrite(self, base_prompt: str) -> str:
    """Fallback method for designer prompt rewriting."""
    return f"""{base_prompt}

╔══════════════════════════════════════════════════════════════════════════════╗
║                          MANDATORY VISUAL STYLE                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

{self.visual_style}

🎨 STYLE APPLICATION RULES:
...
"""
```

This ensures the system continues to work even if the rewriter agent encounters issues.

## Logging and Debugging

The rewriter provides comprehensive logging:

```
================================================================================
PROMPT REWRITER INITIALIZED (LLM-POWERED)
================================================================================
Visual Style: Cyberpunk aesthetic with neon colors...
Speaker Style: Energetic tech evangelist...
================================================================================

================================================================================
REWRITING DESIGNER PROMPT WITH LLM
================================================================================
Original prompt length: 1234 chars
Rewritten prompt length: 2456 chars
Style integration: 345 chars of style content
✓ Designer prompt rewritten successfully
================================================================================
```

Enable debug logging to see full rewritten prompts:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Testing

Run the test script to verify the implementation:

```bash
python test_prompt_rewriter.py
```

This will:
1. Create a rewriter with sample styles
2. Rewrite designer and writer prompts
3. Display statistics and previews
4. Verify the integration works correctly

## Benefits

1. **Better Style Adherence**: Styles are integrated throughout, not just appended
2. **More Natural**: Style requirements feel like part of the core instructions
3. **Flexible**: LLM can adapt integration strategy based on prompt structure
4. **Maintainable**: Base prompts remain clean and focused
5. **Robust**: Automatic fallback ensures reliability

## Future Enhancements

Potential improvements:
- Cache rewritten prompts to avoid redundant LLM calls
- Support for multiple style dimensions (e.g., color + layout separately)
- Style validation and consistency checking
- A/B testing framework for comparing rewrite strategies
- User feedback loop to improve rewriting quality

## Related Files

- `agents/prompt_rewriter.py` - Prompt rewriter agent
- `services/prompt_rewriter.py` - Rewriter service
- `agents/agent_factory.py` - Agent factory with rewriting
- `config/constants.py` - Model configuration
- `test_prompt_rewriter.py` - Test script
