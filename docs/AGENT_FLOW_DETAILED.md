# Agent Flow and Relationships - Detailed Analysis

## Overview

The Gemini PowerPoint Sage system uses a sophisticated multi-agent architecture with a **Supervisor-led workflow** that orchestrates 10 specialized agents to process presentations. This document provides a complete trace of the logic flow and detailed explanation of each agent's role and relationships.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION PROCESSOR                             │
│                         (Main Orchestration Layer)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              THREE PHASES                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │   PHASE 1:      │  │   PHASE 2:      │  │      PHASE 3:               │ │
│  │ Generate Notes  │  │Generate Visuals │  │   Generate Videos           │ │
│  │                 │  │                 │  │    (Optional)               │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AGENT ECOSYSTEM                                  │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│  │  OVERVIEWER     │    │   SUPERVISOR    │    │     TRANSLATOR          │ │
│  │   (Pass 0)      │    │  (Orchestrator) │    │   (Translation Mode)    │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘ │
│           │                       │                         │              │
│           ▼                       ▼                         ▼              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│  │ Global Context  │    │   ANALYST       │    │  IMAGE TRANSLATOR       │ │
│  │   Generation    │    │ (Slide Vision)  │    │  (Visual Translation)   │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘ │
│                                  │                                         │
│                                  ▼                                         │
│                         ┌─────────────────┐                               │
│                         │    AUDITOR      │                               │
│                         │ (Quality Check) │                               │
│                         └─────────────────┘                               │
│                                  │                                         │
│                                  ▼                                         │
│                         ┌─────────────────┐                               │
│                         │     WRITER      │                               │
│                         │ (Content Gen.)  │                               │
│                         └─────────────────┘                               │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│  │    DESIGNER     │    │VIDEO GENERATOR  │    │    PROMPT REWRITER      │ │
│  │ (Visual Gen.)   │    │ (Video Prompts) │    │  (Style Integration)    │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Complete Logic Flow Trace

### Entry Point: `main.py` → `application/cli.py` → `application/unified_processor.py`

1. **CLI Processing**: Parse arguments and determine processing mode
2. **Agent Creation**: Use `agents/agent_factory.py` to create styled agents
3. **Processor Initialization**: Create `PresentationProcessor` with all agents

### Phase 0: Global Context Generation (Pre-Processing)

```python
# In PresentationProcessor._get_global_context()
async def _get_global_context(self, pdf_doc, limit: int, progress: Dict[str, Any]) -> str:
```

**Flow:**
1. **Check Cache**: Look for existing global context in progress file
2. **Translation Mode Check**: If non-English, try to translate from English global context
3. **Generation Mode**: Extract all slide images from PDF
4. **Overviewer Agent Call**: Send all images to overviewer for analysis

**Overviewer Agent Responsibility:**
- Analyzes ALL slides at once to understand presentation narrative
- Generates comprehensive context including themes, vocabulary, speaker persona
- Provides consistency foundation for individual slide processing

### Phase 1: Speaker Notes Generation (Per Slide)

```python
# In PresentationProcessor._phase_generate_notes()
for i in range(limit):
    slide_idx = i + 1
    # Process each slide through supervisor workflow
```

#### Supervisor Workflow (Per Slide)

The Supervisor agent orchestrates a **strict 5-step workflow** for each slide:

```python
# Supervisor tools configured in _configure_supervisor_tools():
tools = [
    self.tool_factory.create_analyst_tool(),      # Step 2
    self.tool_factory.create_writer_tool(...),    # Step 4  
    self.tool_factory.create_auditor_tool(...),   # Step 1
    self.tool_factory.create_translator_tool(),   # Fallback
]
```

**Step-by-Step Supervisor Flow:**

1. **AUDIT EXISTING NOTES**
   ```python
   # Supervisor calls: note_auditor(existing_notes, slide_position)
   async def note_auditor(existing_notes: str, slide_position: str = "") -> str:
   ```
   - **Auditor Agent** evaluates existing notes quality
   - Returns "USEFUL" or "USELESS" with reasoning
   - Validates language correctness (Chinese locale handling)
   - Checks slide position appropriateness (greetings/closings)

2. **DECISION POINT**
   - If Auditor says "USEFUL" → Return existing notes immediately
   - If Auditor says "USELESS" → Proceed to generation

3. **ANALYZE SLIDE CONTENT**
   ```python
   # Supervisor calls: call_analyst(image_id)
   async def call_analyst(image_id: str) -> str:
   ```
   - **Analyst Agent** examines slide image
   - Extracts topics, details, visuals, intent
   - Returns structured analysis for writer

4. **GENERATE SPEAKER NOTES**
   ```python
   # Supervisor calls: speech_writer(analysis, previous_context, theme, global_context, slide_position)
   async def speech_writer(...) -> str:
   ```
   - **Writer Agent** creates speaker notes
   - Uses analysis + global context + previous slide summary
   - Applies language enforcement and speaker style
   - Handles translation mode vs generation mode

5. **RETURN FINAL RESPONSE**
   - Supervisor outputs the exact text from writer
   - No modification or commentary added

#### Translation Mode vs Generation Mode

**Translation Mode** (Non-English with English notes available):
```python
if (language != "en" and english_notes and slide_idx in english_notes):
    # Direct translation using styled translator agent
    translated_note = await self._translate_notes(english_note, slide_idx)
```

**Generation Mode** (English or no English baseline):
```python
# Full supervisor workflow with language enforcement
prompt = f"SLIDE_ANALYSIS:\n{analysis}\n\n" + language_instruction
```

### Phase 2: Visual Generation

```python
# In PresentationProcessor._phase_generate_visuals()
for slide_info in slide_data:
    # Generate or translate visuals for each slide
```

**Visual Processing Flow:**

1. **Mode Detection**:
   - English: Generate visuals directly
   - Non-English: Check for English visuals to translate

2. **Translation Path** (Non-English with English visuals):
   ```python
   # Load English visual
   english_visual = Image.open(en_img_path)
   
   # Image Translator Agent analyzes and provides translation specs
   translation_spec = await run_stateless_agent(
       self.image_translator_agent, analysis_prompt, [english_visual]
   )
   
   # Designer Agent regenerates with translated content
   img_bytes = await run_visual_agent(
       self.designer_agent, design_prompt, images=[english_visual]
   )
   ```

3. **Generation Path** (English or fallback):
   ```python
   # Designer Agent generates new visual
   img_bytes = await self.visual_generator.generate_visual(
       slide_idx, slide_image, speaker_notes, self.retry_errors, self.config.language
   )
   ```

### Phase 3: Video Generation (Optional)

```python
# In PresentationProcessor._phase_generate_videos()
if self.config.generate_videos and self.video_generator_agent:
```

**Video Processing Flow:**

1. **Extract Video Prompt**: Analyze speaker notes for key visual concepts
2. **Video Agent Call**: Generate video using slide image + speaker notes
3. **Artifact Handling**: Parse response for video artifact IDs
4. **Save Prompts**: Store video prompts for reference

## Prompt Rewriter Agent - The Style Orchestrator

The **Prompt Rewriter Agent** is a unique meta-agent that operates at agent creation time to integrate styles into other agents' prompts. Unlike other agents that process presentation content, the Prompt Rewriter modifies how other agents behave.

### Prompt Rewriter Workflow

```python
# At agent creation time (in agent_factory.py):
rewriter = PromptRewriter(visual_style=visual_style, speaker_style=speaker_style)

# For each styled agent:
designer_prompt = rewriter.rewrite_designer_prompt(DESIGNER_PROMPT)
writer_prompt = rewriter.rewrite_writer_prompt(WRITER_PROMPT)
translator_prompt = rewriter.rewrite_translator_prompt(TRANSLATOR_PROMPT)
```

**Rewriting Strategy:**
1. **Deep Integration**: Weaves style throughout prompt, not just appending
2. **Contextual Placement**: Inserts style requirements where most relevant
3. **Concrete Examples**: Provides specific implementation guidance
4. **Language Enforcement**: Adds multilingual compliance rules
5. **Fallback Mechanism**: Simple concatenation if LLM rewriting fails

**Style Types Handled:**
- **Visual Style**: For Designer agent (colors, typography, layout)
- **Speaker Style**: For Writer, Translator, Title Generator (tone, vocabulary, persona)

**Key Features:**
- **LLM-Powered**: Uses Gemini model for intelligent prompt rewriting
- **Retry Logic**: 3 attempts with exponential backoff
- **Fallback Safety**: Concatenation method if LLM fails
- **Language Priority**: Ensures target language overrides style examples
- **Session Management**: Unique sessions to avoid conflicts

## Agent Detailed Specifications

### 1. Overviewer Agent
- **Model**: `gemini-3-pro-preview`
- **Purpose**: Global presentation analysis
- **Input**: All slide images at once
- **Output**: Global context guide (narrative, themes, vocabulary, persona)
- **When Called**: Once per presentation, before slide processing
- **Key Features**: 
  - Understands presentation flow and structure
  - Defines consistent vocabulary and tone
  - Provides narrative arc context

### 2. Supervisor Agent  
- **Model**: `gemini-2.5-flash`
- **Purpose**: Workflow orchestration
- **Input**: Slide context + existing notes
- **Output**: Final speaker notes
- **When Called**: Once per slide
- **Key Features**:
  - Enforces strict 5-step workflow
  - Makes audit/generation decisions
  - Coordinates other agents
  - Handles fallback mechanisms

### 3. Analyst Agent
- **Model**: `gemini-3-pro-preview` 
- **Purpose**: Slide content analysis
- **Input**: Single slide image
- **Output**: Structured analysis (topic, details, visuals, intent)
- **When Called**: Per slide, when auditor says "USELESS"
- **Key Features**:
  - Visual content interpretation
  - Text extraction and analysis
  - Intent recognition

### 4. Auditor Agent
- **Model**: `gemini-2.5-flash`
- **Purpose**: Quality control
- **Input**: Existing speaker notes + slide position
- **Output**: "USEFUL" or "USELESS" with reasoning
- **When Called**: First step for every slide
- **Key Features**:
  - Language validation (Chinese locale handling)
  - Content quality assessment
  - Slide position appropriateness check

### 5. Writer Agent
- **Model**: `gemini-2.5-flash`
- **Purpose**: Speaker notes generation
- **Input**: Analysis + context + theme + style
- **Output**: Natural speaker script
- **When Called**: Per slide, after analyst (if auditor says "USELESS")
- **Key Features**:
  - Style-aware content generation
  - Language enforcement
  - Context-aware transitions
  - Prompt rewriter integration

### 6. Designer Agent
- **Model**: `gemini-3-pro-image-preview`
- **Purpose**: Visual slide generation
- **Input**: Slide image + speaker notes + style
- **Output**: Enhanced slide image (PNG)
- **When Called**: Phase 2, per slide with successful notes
- **Key Features**:
  - Style-aware visual generation
  - Layout optimization
  - Consistent design application

### 7. Translator Agent
- **Model**: `gemini-2.5-flash`
- **Purpose**: Text translation with style preservation
- **Input**: English text + target language + style
- **Output**: Translated text with style applied
- **When Called**: Translation mode for speaker notes
- **Key Features**:
  - Style-aware translation
  - Cultural adaptation
  - Technical accuracy maintenance
  - Prompt rewriter integration

### 8. Image Translator Agent
- **Model**: `gemini-3-pro-image-preview`
- **Purpose**: Visual content translation
- **Input**: English slide visual + context
- **Output**: Translation specifications
- **When Called**: Phase 2, for non-English visual translation
- **Key Features**:
  - Text element identification
  - Cultural visual adaptation
  - Layout preservation guidance

### 9. Video Generator Agent
- **Model**: `gemini-2.5-flash`
- **Purpose**: Video prompt generation
- **Input**: Slide image + speaker notes
- **Output**: Video generation prompts/artifacts
- **When Called**: Phase 3, if video generation enabled
- **Key Features**:
  - MCP integration for Veo 3.1
  - Professional video concepts
  - Slide-appropriate timing

### 10. Prompt Rewriter Agent
- **Model**: `gemini-2.5-flash`
- **Purpose**: Style integration into agent prompts
- **Input**: Base prompt + style guidelines + style type
- **Output**: Rewritten prompt with deeply integrated style
- **When Called**: Agent creation time (via Agent Factory)
- **Key Features**:
  - Deep style integration (not just appending)
  - Visual style weaving for Designer
  - Speaker style weaving for Writer/Translator
  - Language enforcement for multilingual consistency
  - Fallback to concatenation if LLM fails

## Agent Relationships and Dependencies

### Primary Relationships

1. **Supervisor → Auditor → Analyst → Writer**
   - Sequential workflow for each slide
   - Supervisor orchestrates the entire flow
   - Each agent provides input for the next

2. **Overviewer → Writer**
   - Global context informs individual slide generation
   - Ensures consistency across presentation

3. **Translator ↔ Writer**
   - Translation mode bypasses analyst/auditor
   - Styled translator applies same style as writer

4. **Image Translator → Designer**
   - Visual translation workflow
   - Translator provides specs, Designer regenerates

### Tool Factory Relationships

```python
class AgentToolFactory:
    def __init__(self, analyst_agent, writer_agent, auditor_agent, 
                 translator_agent, image_translator_agent):
```

The Tool Factory creates callable functions that wrap agent interactions:
- `create_analyst_tool()` → `call_analyst(image_id)`
- `create_writer_tool()` → `speech_writer(...)`
- `create_auditor_tool()` → `note_auditor(...)`
- `create_translator_tool()` → `translator(...)`

### Style Integration via Prompt Rewriter

```python
# In agent_factory.py
rewriter = PromptRewriter(visual_style=visual_style, speaker_style=speaker_style)
instruction = rewriter.rewrite_designer_prompt(DESIGNER_PROMPT)
```

**Affected Agents:**
- **Designer**: Visual style integration
- **Writer**: Speaker style integration  
- **Translator**: Speaker style for translations
- **Title Generator**: Speaker style for titles

## Error Handling and Fallbacks

### Supervisor Fallback Mechanism
```python
# If supervisor returns empty response
last_output = self.tool_factory.last_writer_output
if last_output:
    return last_output, "success"
```

### Retry Strategy
```python
class RetryStrategy:
    def __init__(self, max_retries=3, base_delay=2.0, backoff_multiplier=2.0):
```

**Applied to:**
- Supervisor agent execution
- Visual generation
- Translation operations

### Translation Fallbacks
1. **Translation Mode**: English notes → Styled translation
2. **Fallback to Generation**: If translation fails → Full generation workflow
3. **Language Enforcement**: Multiple validation layers for Chinese locales

## Performance Optimizations

### Caching Mechanisms
- **Global Context**: Cached in progress file
- **English Notes**: Loaded once for translation mode
- **Generated Visuals**: Skip if already exists

### Parallel Processing
- **Phase Separation**: Notes → Visuals → Videos
- **Independent Slides**: Each slide processed independently
- **Batch Operations**: All slides in each phase

### Resource Management
- **Image Registry**: Temporary image storage with cleanup
- **Session Management**: Reused supervisor sessions
- **Memory Optimization**: Cleanup after each slide

## Configuration and Customization

### Model Configuration
```python
# config/constants.py
class ModelConfig:
    SUPERVISOR = "gemini-2.5-flash"
    ANALYST = "gemini-3-pro-preview"
    WRITER = "gemini-2.5-flash"
    # ... etc
```

### Style Configuration
```yaml
# styles/config.*.yaml
style:
  visual_style: |
    Detailed visual aesthetic description
  speaker_style: |
    Detailed speaker persona description
```

### Language Configuration
```python
# config/constants.py
class LanguageConfig:
    LOCALE_NAMES = {
        "en": "English",
        "zh-CN": "Simplified Chinese (简体中文)",
        # ... etc
    }
```

This comprehensive agent flow ensures consistent, high-quality presentation enhancement across multiple languages and styles while maintaining flexibility and robustness through sophisticated error handling and fallback mechanisms.