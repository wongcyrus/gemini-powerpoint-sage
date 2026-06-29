# Configuration File Guide

YAML is the single source of truth for presentation processing.

Use the CLI only to choose **which YAML config to run**:

- `python main.py --style-config professional`
- `python main.py --config /path/to/config.yaml`
- `python main.py --styles`

## Quick start

### 1. Pick a config

```bash
ls styles/config.*.yaml
```

### 2. Run one built-in style config

```bash
python main.py --style-config cyberpunk
```

### 3. Or run one custom config

```bash
python main.py --config /path/to/config.yaml
```

## Processing rule

Put presentation inputs and processing behavior in YAML, not on the processing CLI.

That includes:

- `pptx`
- `pdf`
- `input_folder`
- `output_dir`
- `language`
- `style`
- `course_id`
- `skip_visuals`
- `generate_videos`
- `retry_errors`
- `region`
- `progress_file`

`generate_videos` now means "plan a few optional video moments" and generate
matching Veo clips for those moments. The run writes a sidecar `video_plan.json`,
saves the clips in the `*_videos/` folder, and inserts each clip before the
matching slide in the combined video. It still does not create a video for every
slide.

## Supported config shapes

Use **one** of these input styles.

### A. Single presentation config

```yaml
pptx: "presentations/lecture.pptx"
pdf: "presentations/lecture.pdf"
output_dir: "output/lecture"
language: "en,zh-CN"
region: "global"
retry_errors: false
skip_visuals: false
generate_videos: false
style:
  visual_style: |
    Clean professional slides
  speaker_style: |
    Clear executive presenter
```

Run it with:

```bash
python main.py --config configs/lecture.yaml
```

### B. Batch folder config

```yaml
input_folder: "notes"
output_dir: "notes/professional/generate"
language: "en,zh-CN,yue-HK"
course_id: "course123"
retry_errors: true
skip_visuals: false
generate_videos: false
region: "global"
style:
  visual_style: |
    Professional corporate presentation style
  speaker_style: |
    Senior business consultant persona
```

Run it with:

```bash
python main.py --style-config professional
```

## Path resolution rules

Relative paths are resolved automatically:

1. Configs inside `styles/` resolve relative paths from the repository root.
2. Configs outside `styles/` resolve relative paths from the config file's own folder.

So both of these work:

```yaml
# styles/config.professional.yaml
input_folder: "notes"
output_dir: "notes/professional/generate"
```

```yaml
# /tmp/demo/config.yaml
pptx: "presentations/demo.pptx"
pdf: "presentations/demo.pdf"
output_dir: "output"
```

## Creating a new config

```bash
cp styles/config.professional.yaml styles/config.mystyle.yaml
```

Then edit:

```yaml
input_folder: "notes"
output_dir: "notes/mystyle/generate"
language: "en"
retry_errors: false
skip_visuals: false
generate_videos: false
style:
  visual_style: |
    Your visual style here
  speaker_style: |
    Your speaker style here
```

Run it with:

```bash
python main.py --style-config mystyle
```

## Why this model

This YAML-first flow keeps:

1. inputs
2. languages
3. output locations
4. style prompts
5. retry and generation behavior

in one auditable file instead of splitting behavior between YAML and ad hoc CLI flags.

## Troubleshooting

### "Configuration file not found"

- Check the config path
- Use `--config /full/path/to/file.yaml` for external configs

### "Input folder not found"

- Confirm the path in YAML
- Remember relative paths resolve from the config location rules above

### "No valid PDF/PPTX pairs found"

- Each PPTX must have a matching PDF with the same basename

### "Invalid YAML"

- Check indentation
- Ensure `key: value` formatting is correct

## See also

- [QUICK_START.md](QUICK_START.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [STYLE_EXAMPLES.md](STYLE_EXAMPLES.md)
