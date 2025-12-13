# Agent Relationships and Interactions

## Overview

This document provides a comprehensive view of how the 10 agents in the Gemini PowerPoint Sage system interact with each other, their dependencies, and the data flow between them.

## Agent Hierarchy and Dependencies

### Primary Orchestrator
- **Supervisor Agent**: The central coordinator that manages the workflow for each slide

### Context Providers  
- **Overviewer Agent**: Provides global presentation context to all other agents
- **Analyst Agent**: Provides slide-specific content analysis

### Content Generators
- **Writer Agent**: Generates speaker notes (primary content)
- **Designer Agent**: Generates visual content
- **Video Generator Agent**: Generates video prompts/content

### Quality Control
- **Auditor Agent**: Validates existing content quality

### Localization
- **Translator Agent**: Handles text translation with style preservation
- **Image Translator Agent**: Handles visual content translation

### Style Integration
- **Prompt Rewriter Agent**: Integrates styles into all other agents' prompts at creation time

## Interaction Matrix

| Agent | Calls → | Called by ← | Data Flow |
|-------|---------|-------------|-----------|
| **Supervisor** | Auditor, Analyst, Writer | PresentationProcessor | Orchestrates per-slide workflow |
| **Overviewer** | None | PresentationProcessor | Provides global context to Writer |
| **Analyst** | None | Supervisor (via tool) | Slide analysis → Writer |
| **Auditor** | None | Supervisor (via tool) | Quality assessment → Decision |
| **Writer** | None | Supervisor (via tool) | Analysis + Context → Speaker notes |
| **Designer** | None | VisualGenerator | Slide + Notes + Style → Visual |
| **Translator** | None | NotesGenerator | English notes → Translated notes |
| **Image Translator** | None | PresentationProcessor | English visual → Translation specs |
| **Video Generator** | None | PresentationProcessor | Notes + Image → Video prompts |
| **Prompt Rewriter** | None | Agent Factory | Base prompts + Style → Rewritten prompts |

## Data Flow Patterns

### 1. Global Context Flow
```
Overviewer Agent
    ↓ (Global Context)
Writer Agent (via Supervisor)
    ↓ (Consistent vocabulary/tone)
All generated speaker notes
```

### 2. Per-Slide Generation Flow
```
Supervisor Agent
    ↓ (Existing notes)
Auditor Agent
    ↓ (Quality decision)
Supervisor Agent
    ↓ (Image ID)
Analyst Agent  
    ↓ (Content analysis)
Supervisor Agent
    ↓ (Analysis + Context)
Writer Agent
    ↓ (Speaker notes)
Supervisor Agent (final output)
```

### 3. Translation Flow
```
English Notes (from previous run)
    ↓ (Direct translation)
Translator Agent (styled)
    ↓ (Translated notes)
Target Language Output
```

### 4. Visual Generation Flow
```
Slide Image + Speaker Notes
    ↓ (Generation request)
Designer Agent
    ↓ (Enhanced visual)
Visual Output (PNG)

OR (Translation path):

English Visual
    ↓ (Analysis request)
Image Translator Agent
    ↓ (Translation specs)
Designer Agent
    ↓ (Regenerated visual)
Translated Visual Output
```

## Prompt Rewriter - Meta-Agent Architecture

The **Prompt Rewriter Agent** has a unique role as a **meta-agent** that operates at a different level than content-processing agents:

### Meta-Agent Characteristics
- **Operates at Creation Time**: Modifies other agents before they process content
- **No Direct Content Processing**: Never sees presentation slides or speaker notes
- **Style Orchestrator**: Ensures consistent style application across all agents
- **LLM-Powered Integration**: Uses AI to intelligently weave styles into prompts

### Rewriting Process Flow
```
YAML Style Config
    ↓ (visual_style + speaker_style)
Agent Factory
    ↓ (agent creation request)
Prompt Rewriter Agent
    ↓ (LLM-powered rewriting)
Styled Agent Prompts
    ↓ (agent instantiation)
Style-Aware Agents
    ↓ (content processing)
Consistent Styled Output
```

### Integration Points
```python
# Agent Factory calls Prompt Rewriter for each styled agent:
rewriter = PromptRewriter(visual_style, speaker_style)

# Visual style integration:
designer = create_designer_agent(visual_style)
# → rewriter.rewrite_designer_prompt(DESIGNER_PROMPT)

# Speaker style integration:
writer = create_writer_agent(speaker_style)
translator = create_translator_agent(speaker_style)
title_gen = create_title_generator_agent(speaker_style)
# → rewriter.rewrite_writer_prompt(WRITER_PROMPT)
# → rewriter.rewrite_translator_prompt(TRANSLATOR_PROMPT)
# → rewriter.rewrite_title_generator_prompt(TITLE_GENERATOR_PROMPT)
```

### Fallback Architecture
```
LLM Rewriting (Primary)
    ↓ (if fails after 3 retries)
Simple Concatenation (Fallback)
    ↓ (always succeeds)
Styled Agent Created
```

**Benefits of Meta-Agent Design:**
- **Separation of Concerns**: Style integration separate from content processing
- **Consistency**: All agents get same style treatment
- **Flexibility**: Can modify style integration without changing content agents
- **Reliability**: Fallback ensures system always works
- **Maintainability**: Style logic centralized in one place

## Agent Communication Mechanisms

### 1. Tool Factory Pattern
The Supervisor doesn't call agents directly. Instead, it uses tools created by `AgentToolFactory`:

```python
# Tools wrap agent calls
async def call_analyst(image_id: str) -> str:
    return await run_stateless_agent(self.analyst_agent, prompt, images=[image])

async def speech_writer(analysis: str, ...) -> str:
    return await run_stateless_agent(self.writer_agent, prompt)

# Supervisor uses these as tools
supervisor_agent.tools = [call_analyst, speech_writer, note_auditor]
```

### 2. Direct Agent Calls
Some agents are called directly by services:

```python
# Overviewer called directly
global_context = await run_stateless_agent(
    self.overviewer_agent, prompt, images=all_images
)

# Designer called directly  
img_bytes = await run_visual_agent(
    self.designer_agent, prompt, images=[slide_image]
)
```

### 3. Session-Based Communication
The Supervisor uses persistent sessions for context:

```python
# Supervisor maintains conversation state
supervisor_runner = InMemoryRunner(agent=supervisor_agent)
for event in supervisor_runner.run(user_id, session_id, message):
    # Process supervisor response and tool calls
```

## Style Integration Relationships

### Prompt Rewriter Integration
The Prompt Rewriter affects multiple agents at creation time:

```python
# Style integration at agent creation
rewriter = PromptRewriter(visual_style=visual_style, speaker_style=speaker_style)

# Affected agents:
designer = create_designer_agent(visual_style)      # Visual style
writer = create_writer_agent(speaker_style)         # Speaker style  
translator = create_translator_agent(speaker_style) # Speaker style
title_gen = create_title_generator_agent(speaker_style) # Speaker style
```

### Style Consistency Chain
```
YAML Config (visual_style + speaker_style)
    ↓
Prompt Rewriter Agent
    ↓ (Rewritten prompts)
Agent Factory
    ↓ (Styled agents)
Content Generation
    ↓ (Consistent style)
Final Output
```

## Error Handling and Fallbacks

### Supervisor Fallback Chain
```
1. Supervisor executes normally
    ↓ (if empty response)
2. Check last_writer_output from tool factory
    ↓ (if available)
3. Use captured writer output
    ↓ (if still empty)
4. Retry with exponential backoff
    ↓ (if max retries exceeded)
5. Mark slide as error
```

### Translation Fallbacks
```
1. Translation Mode (English notes available)
    ↓ (if translation fails)
2. Generation Mode (full supervisor workflow)
    ↓ (if generation fails)
3. Error state with retry option
```

### Visual Generation Fallbacks
```
1. Translation Path (English visuals available)
    ↓ (if image translator fails)
2. Direct Generation Path
    ↓ (if designer fails)
3. Fallback to Imagen model
    ↓ (if still fails)
4. Skip visual for this slide
```

## Performance Optimization Relationships

### Caching Dependencies
```
Global Context (Overviewer)
    ↓ (cached in progress file)
Per-slide processing
    ↓ (uses cached context)
Faster subsequent runs
```

### Translation Mode Optimization
```
English Run (full generation)
    ↓ (saves English notes)
Non-English Run (translation mode)
    ↓ (bypasses Supervisor → Analyst → Writer chain)
2-3x faster processing
```

### Visual Translation Optimization
```
English Visuals (generated once)
    ↓ (reused for all languages)
Image Translator + Designer
    ↓ (faster than full generation)
Consistent visual design across languages
```

## Agent State Management

### Stateless Agents
Most agents are stateless and called independently:
- Overviewer, Analyst, Auditor, Writer, Designer, Translator, Image Translator, Video Generator

### Stateful Components
- **Supervisor**: Maintains conversation session
- **Tool Factory**: Tracks last writer output for fallbacks
- **Progress System**: Tracks completion state across all agents

## Concurrency and Parallelization

### Sequential Processing (Required)
- **Phase 1**: Notes generation (must complete before Phase 2)
- **Per-slide Supervisor workflow**: Strict sequential steps

### Parallel Processing (Possible)
- **Multiple slides**: Each slide processed independently in Phase 1
- **Phase 2 & 3**: Can run concurrently after Phase 1 completes
- **Multiple languages**: Each language processed independently

### Resource Sharing
- **Image Registry**: Shared temporary storage for slide images
- **Progress Files**: Language-specific, no conflicts
- **Agent Instances**: Reused across slides for efficiency

## Integration Points

### External Systems
- **Google Cloud AI**: All agents use Gemini models
- **MCP Servers**: Video Generator can integrate with Veo 3.1
- **File System**: Progress tracking, image storage, output files

### Configuration Systems
- **Model Config**: Defines which Gemini model each agent uses
- **Language Config**: Provides locale mappings for all agents
- **Style Config**: YAML files drive Prompt Rewriter integration

This relationship structure ensures robust, scalable, and maintainable presentation processing while providing flexibility for different use cases and languages.