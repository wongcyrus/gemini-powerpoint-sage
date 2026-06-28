# Quick Reference

## Fastest command choices

| Goal | Command |
| --- | --- |
| One YAML style | `python main.py --style-config cyberpunk` |
| One custom YAML file | `python main.py --config /path/to/config.yaml` |
| All YAML styles | `python main.py --styles` |

`python main.py` defaults to `--styles`.

## Processing rule

Put processing options such as `language`, `style`, `output_dir`, `retry_errors`, `skip_visuals`, `generate_videos`, `course_id`, and `region` in YAML.

## Video and audio utilities

```bash
# Generate TTS from an existing progress JSON
python main.py --tts-only --progress-file output/presentation_en_progress.json --language en

# Combine slide images + audio into a video
python main.py --synthesize-video \
  --slides-dir output/presentation_en_visuals \
  --video-output output/presentation.mp4

# Batch synthesize videos from one style config
python main.py --synthesize-style-videos --style-config professional
```

## Output shape

```text
generate/
├── presentation_en_notes.pptx|pptm
├── presentation_en_visuals.pptx|pptm
├── presentation_en_progress.json
├── presentation_en_visuals/
├── presentation_en_speech/
└── presentation_en_videos/
```

## Pick the right mode

1. `--style-config` for stable team workflows.
2. `--config` for one-off custom YAML workflows.
3. `--styles` for broad batch runs across every configured style.

## Useful file locations

```bash
ls styles/config.*.yaml     # discover available YAML styles
ls docs/                    # full documentation set
```

## Documentation

- **Quick start:** `docs/QUICK_START.md`
- **Architecture trace:** `docs/ARCHITECTURE.md`
- **Config guide:** `docs/CONFIG_FILE_GUIDE.md`
- **Styles:** `docs/STYLE_EXAMPLES.md`
- **Full index:** `docs/README.md`
