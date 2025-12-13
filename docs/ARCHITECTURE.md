# Gemini Powerpoint Sage - Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                           CLI Layer                                 │
│                          main.py (24 lines)                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ • Entry point                                                │  │
│  │ • Setup logging                                              │  │
│  │ • Delegate to application.CLI                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Application Layer                              │
│                    application/cli.py                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ • Parse arguments                                            │  │
│  │ • Load configuration                                         │  │
│  │ • Initialize services                                        │  │
│  │ • Orchestrate processing                                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Configuration Layer                            │
│                      config/ (251 lines total)                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ • config.py - Configuration dataclass                       │  │
│  │ • config_loader.py - YAML/JSON loading                      │  │
│  │ • constants.py - Model names, patterns                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────┐
│                         Service Layer                               │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │         PresentationProcessor (1261 lines)                   │  │
│  │  ┌────────────────────────────────────────────────────────┐ │  │
│  │  │ • Orchestrate all processing phases                    │ │  │
│  │  │ • Load presentation & PDF                              │ │  │
│  │  │ • Generate/load global context                         │ │  │
│  │  │ • Process slides (notes, visuals, videos)              │ │  │
│  │  │ • Handle multi-language workflows                      │ │  │
│  │  │ • Save enhanced presentations                          │ │  │
│  │  └────────────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │           AgentManager                                       │  │
│  │  • Centralized agent initialization                          │  │
│  │  • Lazy loading of agents                                    │  │
│  │  • Agent registry and getters                                │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │           NotesGenerator                                     │  │
│  │  • Generate speaker notes via supervisor                     │  │
│  │  • Translation mode detection                                │  │
│  │  • Fallback handling                                         │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │           TranslationService                                 │  │
│  │  • Translate speaker notes                                   │  │
│  │  • Translate slide visuals                                   │  │
│  │  • Language name mapping                                     │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │           VisualGenerator                                    │  │
│  │  • Generate enhanced slide visuals                           │  │
│  │  • Manage style consistency                                  │  │
│  │  │ • Skip logic for existing visuals                        │  │
│  │  • Embed visuals in presentation                             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │           VideoService                                       │  │
│  │  • Generate video prompts                                    │  │
│  │  • MCP agent integration                                     │  │
│  │  • Artifact extraction                                       │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │           ContextService                                     │  │
│  │  • Manage global context                                     │  │
│  │  • Handle rolling context                                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │           FileService                                        │  │
│  │  • File I/O operations                                       │  │
│  │  • Path management                                           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │           RefinementProcessor                                │  │
│  │  • Refine notes for TTS                                      │  │
│  │  • Remove markdown formatting                                │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │           PromptRewriter                                     │  │
│  │  • Rewrite prompts for agents                                │  │
│  │  • Style adaptation                                          │  │
│  └─────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                    │                              │
                    ▼                              ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│       Tool Factory Layer      │   │      Utility Layer            │
│  tools/agent_tools.py         │   │                               │
│  tools/veo_mcp_tools.py       │   │  utils/image_utils.py         │
│  ┌─────────────────────────┐ │   │  ┌─────────────────────────┐ │
│  │ • create_analyst_tool()  │ │   │  │ • Image registry        │ │
│  │ • create_writer_tool()   │ │   │  │ • PIL ↔ Part conversion │ │
│  │ • create_auditor_tool()  │ │   │  └─────────────────────────┘ │
│  │ • Track writer output    │ │   │                               │
│  │ • Video MCP tools        │ │   │  utils/progress_utils.py      │
│  └─────────────────────────┘ │   │  ┌─────────────────────────┐ │
└──────────────────────────────┘   │  │ • Load/save progress    │ │
                                    │  │ • Create slide keys     │ │
                                    │  │ • Check retry mode      │ │
                                    │  └─────────────────────────┘ │
                                    │                               │
                                    │  utils/agent_utils.py         │
                                    │  ┌─────────────────────────┐ │
                                    │  │ • run_stateless_agent() │ │
                                    │  │ • run_visual_agent()    │ │
                                    │  │ • Session management    │ │
                                    │  └─────────────────────────┘ │
                                    │                               │
                                    │  utils/error_handling.py      │
                                    │  ┌─────────────────────────┐ │
                                    │  │ • Retry strategies      │ │
                                    │  │ • @with_retry decorator │ │
                                    │  │ • Custom exceptions     │ │
                                    │  └─────────────────────────┘ │
                                    │                               │
                                    │  utils/pptx_utils.py          │
                                    │  ┌─────────────────────────┐ │
                                    │  │ • PPTX operations       │ │
                                    │  │ • Slide manipulation    │ │
                                    │  └─────────────────────────┘ │
                                    │                               │
                                    │  utils/cli_utils.py           │
                                    │  ┌─────────────────────────┐ │
                                    │  │ • CLI helpers           │ │
                                    │  │ • Argument parsing      │ │
                                    │  └─────────────────────────┘ │
                                    └──────────────────────────────┘
                                                  │
                                                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                          Agent Layer                                │
│                         agents/ (unchanged)                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ • supervisor_agent   - Orchestrates workflow                │  │
│  │ • analyst_agent      - Analyzes slide images                │  │
│  │ • writer_agent       - Writes speaker notes                 │  │
│  │ • auditor_agent      - Audits existing notes                │  │
│  │ • overviewer_agent   - Generates global context             │  │
│  │ • designer_agent     - Generates enhanced visuals           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

## Agent Interaction Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION PROCESSOR                             │
│                              (3 Phases)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
         ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
         │   PHASE 1:      │ │   PHASE 2:      │ │   PHASE 3:      │
         │ Generate Notes  │ │Generate Visuals │ │Generate Videos  │
         └─────────────────┘ └─────────────────┘ └─────────────────┘
                    │                 │                 │
                    ▼                 ▼                 ▼
         ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
         │  OVERVIEWER     │ │    DESIGNER     │ │ VIDEO GENERATOR │
         │ (Global Context)│ │ (Visual Gen.)   │ │ (Video Prompts) │
         └─────────────────┘ └─────────────────┘ └─────────────────┘
                    │
                    ▼
         ┌─────────────────────────────────────────────────────────┐
         │              SUPERVISOR WORKFLOW                        │
         │                 (Per Slide)                            │
         │                                                         │
         │  1. AUDITOR ──→ 2. ANALYST ──→ 3. WRITER               │
         │     │              │              │                    │
         │     ▼              ▼              ▼                    │
         │  Quality       Content        Speaker                  │
         │  Check         Analysis       Notes                    │
         │                                                         │
         │  Alternative Path: TRANSLATOR (Translation Mode)       │
         └─────────────────────────────────────────────────────────┘
                                      │
                                      ▼
         ┌─────────────────────────────────────────────────────────┐
         │              PROMPT REWRITER (META-AGENT)               │
         │                 (Agent Creation Time)                   │
         │                                                         │
         │  Base Prompts + Style Guidelines → Rewritten Prompts   │
         │                                                         │
         │  • Designer: Visual style integration                   │
         │  • Writer: Speaker style integration                    │
         │  • Translator: Speaker style integration                │
         │  • Title Generator: Speaker style integration           │
         └─────────────────────────────────────────────────────────┘
```

## Detailed Agent Relationships

```
                    ┌─────────────────────────────────────────┐
                    │           AGENT ECOSYSTEM               │
                    └─────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  OVERVIEWER     │         │   SUPERVISOR    │         │  PROMPT         │
│                 │         │                 │         │  REWRITER       │
│ • Analyzes ALL  │         │ • Orchestrates  │         │  (META-AGENT)   │
│   slides at once│         │   workflow      │         │                 │
│ • Creates global│         │ • Makes         │         │ • Rewrites      │
│   context       │         │   decisions     │         │   prompts with  │
│ • Defines       │         │ • Coordinates   │         │   style         │
│   narrative arc │         │   other agents  │         │ • LLM-powered   │
└─────────────────┘         └─────────────────┘         │ • Creation time │
        │                             │                 │ • Fallback safe │
        │                             ▼                 └─────────────────┘
        │                   ┌─────────────────┐                     │
        │                   │    AUDITOR      │                     │
        │                   │                 │                     │
        │                   │ • Quality check │                     │
        │                   │ • Language      │                     │
        │                   │   validation    │                     │
        │                   │ • USEFUL/       │                     │
        │                   │   USELESS       │                     │
        │                   └─────────────────┘                     │
        │                             │                             │
        │                             ▼                             │
        │                   ┌─────────────────┐                     │
        │                   │    ANALYST      │                     │
        │                   │                 │                     │
        │                   │ • Slide vision  │                     │
        │                   │ • Content       │                     │
        │                   │   extraction    │                     │
        │                   │ • Visual        │                     │
        │                   │   analysis      │                     │
        │                   └─────────────────┘                     │
        │                             │                             │
        │                             ▼                             │
        └─────────────────────────────┼─────────────────────────────┘
                                      ▼                             │
                            ┌─────────────────┐                     │
                            │     WRITER      │◄────────────────────┘
                            │                 │    Style Integration
                            │ • Speaker notes │    (at creation time)
                            │ • Language      │
                            │   enforcement   │
                            │ • Style         │
                            │   application   │
                            └─────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
         ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
         │   TRANSLATOR    │ │    DESIGNER     │ │ IMAGE           │
         │                 │ │                 │ │ TRANSLATOR      │
         │ • Style-aware   │ │ • Visual        │ │                 │
         │   translation   │ │   generation    │ │ • Visual        │
         │ • Cultural      │ │ • Style         │ │   analysis      │
         │   adaptation    │ │   integration   │ │ • Translation   │
         │ • Bypasses      │ │ • Layout        │ │   specs         │
         │   supervisor    │ │   optimization  │ │ • Works with    │
         │   in trans mode │ │                 │ │   Designer      │
         └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Module Dependencies

```
main.py
  └── application.cli
       ├── config.config_loader
       │    ├── config.config
       │    └── config.constants
       ├── services.presentation_processor
       │    ├── services.agent_manager
       │    │    └── agents.*
       │    ├── services.notes_generator
       │    ├── services.translation_service
       │    ├── services.visual_generator
       │    ├── services.video_service
       │    ├── services.context_service
       │    ├── services.file_service
       │    ├── services.refinement_processor
       │    ├── services.prompt_rewriter
       │    ├── utils.progress_utils
       │    ├── utils.image_utils
       │    ├── utils.agent_utils
       │    ├── utils.pptx_utils
       │    ├── utils.error_handling
       │    ├── pymupdf
       │    └── pptx
       └── application.logging_setup
```

## Agent Workflow Details

### Phase 1: Speaker Notes Generation

**Per-Slide Supervisor Workflow (Strict 5-Step Process):**

```
1. AUDIT EXISTING NOTES
   ├─ Supervisor calls: note_auditor(existing_notes, slide_position)
   ├─ Auditor evaluates quality and language correctness
   └─ Returns: "USEFUL" or "USELESS" with reasoning

2. DECISION POINT
   ├─ If "USEFUL" → Return existing notes immediately (END)
   └─ If "USELESS" → Continue to step 3

3. ANALYZE SLIDE CONTENT  
   ├─ Supervisor calls: call_analyst(image_id)
   ├─ Analyst examines slide image for content
   └─ Returns: Structured analysis (topic, details, visuals, intent)

4. GENERATE SPEAKER NOTES
   ├─ Supervisor calls: speech_writer(analysis, context, theme, global_context)
   ├─ Writer creates notes using all context + style
   └─ Returns: Natural speaker script

5. RETURN FINAL RESPONSE
   ├─ Supervisor outputs exact text from writer
   └─ No modification or commentary added
```

**Translation Mode Alternative:**
```
Non-English + English Notes Available:
├─ Bypass supervisor workflow entirely
├─ Use styled Translator agent directly
├─ Apply speaker style during translation
└─ 2-3x faster than full generation
```

### Phase 2: Visual Generation

**Visual Processing Decision Tree:**

```
English Language:
├─ Designer generates visuals directly
├─ Uses slide image + speaker notes + visual style
└─ Outputs enhanced slide image (PNG)

Non-English Language:
├─ Check for existing English visuals
├─ If found:
│   ├─ Image Translator analyzes English visual
│   ├─ Provides translation specifications
│   ├─ Designer regenerates with translated content
│   └─ Maintains layout and style consistency
└─ If not found:
    ├─ Generate directly in target language
    └─ Designer uses language-specific prompts
```

### Phase 3: Video Generation (Optional)

**Video Processing Flow:**

```
For Each Successful Slide:
├─ Extract video prompt from speaker notes
├─ Video Generator creates professional video concept
├─ MCP integration with Veo 3.1 (if available)
├─ Generate 8-10 second promotional video
└─ Save video prompts and artifacts
```

## Agent Communication Patterns

### Tool Factory Pattern
```python
# Supervisor uses tools created by AgentToolFactory
tools = [
    factory.create_analyst_tool(),    # Wraps analyst agent
    factory.create_writer_tool(),     # Wraps writer agent  
    factory.create_auditor_tool(),    # Wraps auditor agent
]
supervisor_agent.tools = tools
```

### Fallback Mechanisms
```python
# Writer output capture for supervisor fallback
self._last_writer_output = result  # Captured in tool factory
if supervisor_returns_empty:
    return self.tool_factory.last_writer_output  # Fallback
```

### Style Integration Points
```python
# Prompt Rewriter integrates styles at agent creation
rewriter = PromptRewriter(visual_style, speaker_style)
designer_prompt = rewriter.rewrite_designer_prompt(base_prompt)
writer_prompt = rewriter.rewrite_writer_prompt(base_prompt)
translator_prompt = rewriter.rewrite_translator_prompt(base_prompt)
title_gen_prompt = rewriter.rewrite_title_generator_prompt(base_prompt)
```

### Prompt Rewriter Execution Timeline
```
System Startup
    ↓
YAML Config Loading (visual_style + speaker_style)
    ↓
Agent Factory Initialization
    ↓
Prompt Rewriter Agent Creation
    ↓
For Each Styled Agent:
    ├─ Load Base Prompt
    ├─ Call Prompt Rewriter Agent (LLM)
    ├─ Receive Rewritten Prompt
    ├─ Create Agent with Styled Prompt
    └─ Agent Ready for Content Processing
    ↓
All Agents Created and Style-Integrated
    ↓
Begin Presentation Processing (Phases 1-3)
```

**Key Insight**: The Prompt Rewriter operates **before** any content processing begins, ensuring all agents are style-aware from the start.

## Key Design Principles

### 1. Separation of Concerns
- **Entry Point** (main.py): Application entry
- **Application** (application/): CLI and logging
- **Config** (config/): Configuration management
- **Services** (services/): Business logic
- **Tools** (tools/): Agent tool creation
- **Utils** (utils/): Reusable utilities
- **Agents** (agents/): AI agent definitions
- **Core** (core/): Domain models and interfaces

### 2. Dependency Injection
```python
processor = PresentationProcessor(
    config=config,
    supervisor_agent=supervisor_agent,
    analyst_agent=analyst_agent,
    # ... inject dependencies
)
```

### 3. Single Responsibility
Each module has one clear purpose:
- `image_utils.py`: Image handling only
- `progress_utils.py`: Progress tracking only
- `visual_generator.py`: Visual generation only

### 4. Open/Closed Principle
Easy to extend without modification:
```python
# Add new tool type
factory.create_summarizer_tool()

# Add new storage backend
processor = PresentationProcessor(
    progress_tracker=DatabaseProgressTracker()
)
```

### 5. Interface Segregation
Small, focused interfaces:
```python
# VisualGenerator has focused interface
generator.generate_visual(...)
generator.add_visual_to_presentation(...)
generator.reset_style_context()
```

## Architecture Benefits

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  main.py     │  │ application/ │  │  config/     │
│  (24 lines)  │  │  CLI & logs  │  │  (251 lines) │
│  ✅ Entry    │  │  ✅ Interface│  │  ✅ Config   │
└──────────────┘  └──────────────┘  └──────────────┘
       │                 │                  │
       └─────────────────┴──────────────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
┌───────────▼─────┐       ┌───────────▼─────┐
│  services/      │       │  agents/         │
│  10 services    │       │  14 agents       │
│  ✅ Business    │       │  ✅ AI logic     │
└─────────────────┘       └──────────────────┘
            │                         │
            └────────────┬────────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
┌───────────▼─────┐       ┌───────────▼─────┐
│  tools/         │       │  utils/          │
│  Agent tools    │       │  Utilities       │
│  ✅ Tool factory│       │  ✅ Reusable     │
└─────────────────┘       └──────────────────┘

✅ Easy to test (109 tests)
✅ Easy to maintain
✅ Easy to reuse
✅ Easy to extend
✅ Multi-language support
```

## Architecture Quality Metrics

| Metric | Status | Notes |
|--------|--------|-------|
| Main file size | 24 lines | Minimal entry point |
| Service modules | 10 services | Focused responsibilities |
| Testable components | 109 tests | Comprehensive test coverage |
| Coupling | Low | Loose coupling via dependency injection |
| Cohesion | High | Clear, focused responsibilities |
| Code duplication | Low | DRY principle applied throughout |
| Extensibility | High | Plugin-ready architecture |
| Multi-language support | Yes | English baseline + translations |
