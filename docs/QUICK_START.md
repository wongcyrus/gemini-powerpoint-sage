# Quick Start Guide

Start with the smallest command that matches your goal.

## 1. Setup once

```bash
./setup.sh
gcloud auth application-default login
```

## 2. Choose one workflow

| If you want to... | Run this |
| --- | --- |
| Process one custom YAML file directly | `python main.py --config /path/to/config.yaml` |
| Process one built-in YAML template | `python main.py --style-config professional` |
| Process every configured style | `python main.py --styles` |

`python main.py` is the same as `python main.py --styles`.

## 3. Required inputs

Every presentation run needs a matching PPTX/PDF pair.

### Single-presentation YAML mode

Use a config file even for one deck:

```text
configs/
└── presentation.yaml

presentations/
├── presentation.pptx
└── presentation.pdf
```

### YAML-driven mode

Your YAML file points to an `input_folder` and `output_dir`, for example:

```yaml
input_folder: "notes"
output_dir: "notes/professional/generate"
language: "en,zh-CN"
style:
  visual_style: "Clean professional slides"
  speaker_style: "Clear executive presenter"
```

## 4. Most common commands

```bash
# One presentation via YAML
python main.py --config configs/presentation.yaml

# One configured style
python main.py --style-config cyberpunk

# One custom YAML file
python main.py --config /path/to/config.yaml

# All configured styles
python main.py --styles
```

## 5. What gets created

Typical outputs for one presentation/language pair:

```text
generate/
├── presentation_en_notes.pptx|pptm
├── presentation_en_visuals.pptx|pptm
├── presentation_en_progress.json
├── presentation_en_visuals/
└── presentation_en_speech/
```

The exact output root comes from the YAML:

- `output_dir` in YAML-driven mode
- otherwise the default `generate/` folder next to the PPTX named in the YAML

For non-English runs, translated visuals reuse the sibling English visual
folder when it already exists, then write the localized result into the
language-specific `*_visuals/` folder.

## 6. Pick the simplest path

1. Put processing inputs and options in YAML.
2. Use `--config` when you want to run one explicit YAML file.
3. Use `--style-config` only to choose one of the built-in template YAMLs.
4. Use `--styles` only when you really want every configured style to run.

## 7. Next references

- **Architecture trace:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **YAML config details:** [CONFIG_FILE_GUIDE.md](CONFIG_FILE_GUIDE.md)
- **Examples of styles:** [STYLE_EXAMPLES.md](STYLE_EXAMPLES.md)
- **Full docs index:** [README.md](README.md)
