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

## Data Flow

```
┌─────────────┐
│ User Input  │ --pptx, --pdf, --course-id--> ┌──────────┐
│ (CLI Args)  │                                │  Config  │
└─────────────┘                                └────┬─────┘
                                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │ Presentation     │
                                          │ Processor        │
                                          └────┬─────────┬───┘
                                               │         │
                ┌──────────────────────────────┘         └───────────────┐
                │                                                        │
                ▼                                                        ▼
     ┌──────────────────┐                                    ┌──────────────────┐
     │ Agent Tools      │                                    │ Visual Generator │
     │ (via Factory)    │                                    │                  │
     └────┬─────────────┘                                    └────┬─────────────┘
          │                                                       │
          ▼                                                       ▼
     ┌─────────────────────┐                           ┌─────────────────────┐
     │ Agent Execution     │                           │ Enhanced Visuals    │
     │ (via agent_utils)   │                           │ (PNG files)         │
     └─────────────────────┘                           └─────────────────────┘
               │                                                     │
               └──────────────────┬──────────────────────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │ Enhanced PPTX    │
                        │ with Notes       │
                        └──────────────────┘
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
