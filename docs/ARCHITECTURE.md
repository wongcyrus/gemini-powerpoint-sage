# Gemini Powerpoint Sage Architecture

This document traces the real runtime flow in the current codebase, from the CLI entry point down to slide-by-slide agent execution. It focuses on the paths implemented in:

- `main.py`
- `application/cli.py`
- `application/unified_processor.py`
- `services/presentation_processor.py`
- `services/visual_generator.py`
- `config/config.py`

## 1. Runtime entry points

The application has one executable entry point and several user-facing modes.

```mermaid
flowchart TD
    A[main.py] --> B[setup_logging]
    B --> C[CLI.run]
    C --> D[parse args + load .env]
    D --> E{mode}

    E -->|--style-config| F[UnifiedProcessor.process_single_style]
    E -->|--config| G[UnifiedProcessor.process_config]
    E -->|--styles or default| H[UnifiedProcessor.process_styles_directory]
    E -->|--tts-only| I[TTS CLI utility]
    E -->|--synthesize-video| J[Video synthesis service]
    E -->|--synthesize-style-videos| K[Style-driven video synthesis]
    E -->|--refine| L[RefineCommand]

    F --> M[Load YAML]
    G --> M
    H --> M
    M --> N[Create Config]
    N --> O[create_all_agents]
    O --> P[PresentationProcessor.process]
```

## 2. What each CLI mode actually does

| User command | Main handler | Purpose |
| --- | --- | --- |
| `python main.py --style-config cyberpunk` | `UnifiedProcessor.process_single_style()` | Batch process all PPTX/PDF pairs from one YAML config. |
| `python main.py --config /path/to/config.yaml` | `UnifiedProcessor.process_config()` | Run one custom YAML file directly. |
| `python main.py --styles` or `python main.py` | `UnifiedProcessor.process_styles_directory()` | Process every `styles/config.*.yaml` file. |
| `python main.py --tts-only --progress-file progress.json` | `CLI._handle_tts_only()` | Generate audio from an existing progress JSON. |
| `python main.py --synthesize-video ...` | `CLI._handle_video_synthesis()` | Combine generated visuals and audio into a video. |

## 2.5 YAML config resolution rules

`ConfigFileLoader.load_from_file()` now resolves relative paths before processing starts:

1. Config files under `styles/` resolve relative paths from the repository root.
2. Config files outside `styles/` resolve relative paths from the config file's own folder.

That keeps built-in style configs working while also making `--config /full/path/to/file.yaml` reliable, while preserving YAML as the only processing source of truth.

## 3. End-to-end processing for one presentation

Once a single presentation reaches `PresentationProcessor`, the runtime becomes a fixed multi-phase pipeline.

```mermaid
flowchart TD
    A[Load PPTX twice<br/>notes copy + visuals copy] --> B[Open matching PDF]
    B --> C[Load progress JSON]
    C --> D{language == en?}
    D -->|no| E[Load English notes / global context if available]
    D -->|yes| F[Continue]
    E --> F
    F --> G[Get global context]
    G --> H[Configure supervisor tools]
    H --> I[Create supervisor session]
    I --> J[Phase 1: generate speaker notes]
    J --> K[Phase 1.5: generate TTS audio]
    K --> L[Phase 2: generate or translate visuals]
    L --> M[Phase 3: plan video moments optional]
    M --> N[Save notes PPTM/PPTX]
    N --> O{all visuals generated?}
    O -->|yes| P[Save visuals PPTM/PPTX]
    O -->|no| Q[Skip visuals output file]
```

## 4. Phase-by-phase trace

### Phase 0: global context

`PresentationProcessor._get_global_context()` resolves presentation-wide context in this order:

1. Reuse cached context from the progress file.
2. If the target language is not English, try translating the English global context.
3. Otherwise render every PDF page to an image and call the overviewer agent once.

That global context is then reused for every slide in the same run.

### Phase 1: speaker notes

`PresentationProcessor._phase_generate_notes()` loops through each slide and keeps small rolling context:

- current slide image from the PDF
- existing slide notes
- summary of the previous slide
- last three generated speaker-note blocks
- progress status for skip/retry behavior

Each slide is routed through `_process_slide_notes()`.

```mermaid
sequenceDiagram
    participant PP as PresentationProcessor
    participant Sup as Supervisor agent
    participant Aud as Auditor tool
    participant Ana as Analyst tool
    participant Wri as Writer tool
    participant Tr as Translator tool

    PP->>PP: Build supervisor prompt
    alt Non-English and English note already exists
        PP->>Tr: Translate English note
        Tr-->>PP: Translated note
    else Generate or reuse note
        PP->>Sup: Run slide workflow
        Sup->>Aud: Check existing notes
        alt Existing notes are useful
            Aud-->>Sup: Reuse notes
        else Need regeneration
            Sup->>Ana: Analyze slide image
            Ana-->>Sup: Structured slide analysis
            Sup->>Wri: Generate speaker notes
            Wri-->>Sup: Final notes
        end
        Sup-->>PP: Final note text
    end
    PP->>PP: Save progress + update both PPTX copies
```

### Phase 1.5: TTS

If TTS is enabled, `PresentationProcessor._phase_generate_tts()` converts successful slide notes into `SlideData` objects, sends them to the batch TTS orchestrator, then writes audio metadata back into the same progress JSON.

### Phase 2: visuals

`PresentationProcessor._phase_generate_visuals()` uses one of two branches:

For non-English runs, translated visuals are first looked up in the sibling
`*_en_visuals/` directory under the same presentation output root, then the
localized `*_visuals/` folder is used as the target for the translated result.

```mermaid
flowchart TD
    A[Phase 2 start] --> B{target language == en?}
    B -->|yes| C[Generate visuals directly]
    B -->|no| D{English visuals available?}
    D -->|yes| E[Translate English visuals]
    D -->|no| F[Generate visuals in target language]

    C --> G[VisualGenerator.generate_visual]
    E --> H[image_translator_agent]
    F --> G
    G --> I[Save slide_N_reimagined.png]
    H --> I
    I --> J[Replace slide contents in visuals deck]
```

`VisualGenerator.generate_visual()` itself is a three-tier fallback chain:

1. primary designer agent
2. secondary Gemini image model
3. direct Imagen generation

### Phase 3: video planning + Veo generation

If `generate_videos` is enabled, `_phase_generate_videos()` asks the planner agent to pick a few high-value moments, saves a `video_plan.json` sidecar, and generates Veo clips for those moments into the `*_videos/` folder. Later synthesis inserts each clip before the matching slide segment in the final combined video. The slide deck itself is not modified.

The planner prefers:

1. an intro moment
2. a section transition if the deck has one
3. a conclusion moment

It does not create a video for every slide.

## 5. Responsibility map

| Component | Responsibility |
| --- | --- |
| `CLI` | Parse mode, enforce mutually exclusive inputs, dispatch to the correct handler. |
| `UnifiedProcessor` | Convert CLI/YAML input into `Config` + agents + `PresentationProcessor`. |
| `Config` | Resolve style, language, output folders, and artifact naming. |
| `InputScanner` | Discover PPTX/PDF pairs for YAML-driven processing. |
| `PresentationProcessor` | Orchestrate the full presentation pipeline and progress tracking. |
| `AgentToolFactory` | Expose analyst/writer/auditor/translator tools to the supervisor agent. |
| `VisualGenerator` | Generate slide images and replace slide contents in the visuals deck. |
| `TTSOrchestrator` | Batch audio generation from successful notes. |

## 6. Output model

For each presentation/language pair, the processor may create:

- `*_notes.pptx|pptm`
- `*_visuals.pptx|pptm`
- `*_progress.json`
- `*_visuals/` image directory
- `*_speech/` audio directory
- `*_videos/` video plan sidecar artifacts and Veo clip files

The exact output root depends on `Config._get_output_dir()`:

- single-file mode defaults to `generate/` next to the PPTX
- non-`professional` styles get a nested style folder
- YAML-driven runs usually honor the config file's `output_dir`

## 7. Main design takeaway

The system is best understood as:

1. **CLI routing**
2. **file discovery / config resolution**
3. **agent creation**
4. **one presentation pipeline**
5. **per-slide supervisor workflow**

If you are tracing bugs, start from the mode-specific CLI branch first, then follow the `UnifiedProcessor -> Config -> PresentationProcessor` path.
