# Gemini Powerpoint Sage - Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                           CLI Layer                                 │
│                          main.py (124 lines)                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ • Parse arguments                                            │  │
│  │ • Set environment variables                                  │  │
│  │ • Delegate to process_presentation()                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Configuration Layer                            │
│                         config.py (109 lines)                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ • Validate input files                                       │  │
│  │ • Manage environment variables                               │  │
│  │ • Compute output paths                                       │  │
│  │ • Integrate course configuration                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────┐
│                         Service Layer                               │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │         PresentationProcessor (416 lines)                    │  │
│  │  ┌────────────────────────────────────────────────────────┐ │  │
│  │  │ • Load presentation & PDF                              │ │  │
│  │  │ • Generate/load global context                         │ │  │
│  │  │ • Configure supervisor tools                           │ │  │
│  │  │ • Process each slide sequentially                      │ │  │
│  │  │ • Save enhanced presentation                           │ │  │
│  │  └────────────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │           VisualGenerator (241 lines)                        │  │
│  │  ┌────────────────────────────────────────────────────────┐ │  │
│  │  │ • Generate enhanced slide visuals                      │ │  │
│  │  │ • Manage style consistency                             │ │  │
│  │  │ • Skip logic for existing visuals                      │ │  │
│  │  │ • Embed visuals in presentation                        │ │  │
│  │  └────────────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                    │                              │
                    ▼                              ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│       Tool Factory Layer      │   │      Utility Layer            │
│  tools/agent_tools.py         │   │                               │
│         (109 lines)            │   │  utils/image_utils.py         │
│  ┌─────────────────────────┐ │   │         (70 lines)             │
│  │ • create_analyst_tool()  │ │   │  ┌─────────────────────────┐ │
│  │ • create_writer_tool()   │ │   │  │ • Image registry        │ │
│  │ • create_auditor_tool()  │ │   │  │ • PIL ↔ Part conversion │ │
│  │ • Track writer output    │ │   │  └─────────────────────────┘ │
│  └─────────────────────────┘ │   │                               │
└──────────────────────────────┘   │  utils/progress_utils.py      │
                                    │         (98 lines)             │
                                    │  ┌─────────────────────────┐ │
                                    │  │ • Load/save progress    │ │
                                    │  │ • Create slide keys     │ │
                                    │  │ • Check retry mode      │ │
                                    │  └─────────────────────────┘ │
                                    │                               │
                                    │  utils/agent_utils.py         │
                                    │         (171 lines)            │
                                    │  ┌─────────────────────────┐ │
                                    │  │ • run_stateless_agent() │ │
                                    │  │ • run_visual_agent()    │ │
                                    │  │ • Session management    │ │
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
  ├── config.py
  └── services.presentation_processor
       ├── config.py
       ├── tools.agent_tools
       │    ├── utils.agent_utils
       │    └── utils.image_utils
       ├── services.visual_generator
       │    ├── utils.agent_utils
       │    └── pptx
       ├── utils.progress_utils
       ├── utils.image_utils
       ├── utils.agent_utils
       ├── pymupdf
       └── pptx
```

## Key Design Principles

### 1. Separation of Concerns
- **CLI** (main.py): User interface
- **Config** (config.py): Configuration management
- **Services**: Business logic
- **Tools**: Agent tool creation
- **Utils**: Reusable utilities
- **Agents**: AI agent definitions

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
│  main.py     │  │  config.py   │  │  services/   │
│  (124 lines) │  │  (109 lines) │  │  (657 lines) │
│  ✅ CLI only │  │  ✅ Config   │  │  ✅ Business │
└──────────────┘  └──────────────┘  └──────────────┘
       │                 │                  │
       └─────────────────┴──────────────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
┌───────────▼─────┐       ┌───────────▼─────┐
│  tools/         │       │  utils/          │
│  (109 lines)    │       │  (339 lines)     │
│  ✅ Tool factory│       │  ✅ Reusable     │
└─────────────────┘       └──────────────────┘

✅ Easy to test
✅ Easy to maintain
✅ Easy to reuse
✅ Easy to extend
```

## Architecture Quality Metrics

| Metric | Status | Notes |
|--------|--------|-------|
| Main file size | 124 lines | Focused CLI interface |
| Average module size | ~150 lines | Well-sized, maintainable modules |
| Testable components | 9 modules | Each with single responsibility |
| Coupling | Low | Loose coupling via dependency injection |
| Cohesion | High | Clear, focused responsibilities |
| Code duplication | Low | DRY principle applied throughout |
| Extensibility | High | Plugin-ready architecture |
