# Google Cloud Project Rotation

## Overview

The project rotation feature allows you to distribute API calls across multiple Google Cloud projects to avoid hitting quota limits. This is particularly useful when processing large presentations with many slides.

## How It Works

The system automatically rotates through configured Google Cloud projects before each API-intensive operation:

- **Slide processing** (supervisor agent calls)
- **Visual generation** (image generation via Gemini/Imagen)
- **TTS generation** (text-to-speech synthesis)

Each operation uses a different project in round-robin fashion, distributing the load evenly across all configured projects.

## Configuration

### Single Project (Default)

```bash
# .env
GOOGLE_CLOUD_PROJECT=your-project-id
```

### Multiple Projects (Load Balancing)

```bash
# .env
GOOGLE_CLOUD_PROJECTS=project-id-1,project-id-2,project-id-3
```

**Note:** When `GOOGLE_CLOUD_PROJECTS` is set, it takes precedence over `GOOGLE_CLOUD_PROJECT`.

## Usage

No code changes are required. Simply configure the environment variable and the system will automatically rotate projects:

```bash
# Set multiple projects
export GOOGLE_CLOUD_PROJECTS=project-1,project-2,project-3

# Run your presentation processing
python main.py --pptx presentation.pptx
```

## Logging

The system logs project rotation information:

```
INFO - Google Cloud project rotation enabled: 3 projects configured
INFO - Starting with project: project-1
INFO - --- Processing Notes for Slide 1 (Project: project-1) ---
INFO - --- Processing Notes for Slide 2 (Project: project-2) ---
INFO - --- Processing Notes for Slide 3 (Project: project-3) ---
INFO - --- Processing Notes for Slide 4 (Project: project-1) ---
```

## Benefits

1. **Avoid Quota Limits**: Distribute API calls across multiple projects to stay within quota limits
2. **Automatic Load Balancing**: Round-robin rotation ensures even distribution
3. **Zero Code Changes**: Works transparently with existing code
4. **Thread-Safe**: Uses locking to ensure safe rotation in concurrent scenarios

## Implementation Details

The rotation is implemented in `utils/project_rotation.py` and integrated into:

- `services/presentation_processor.py` - Slide processing loop
- `services/visual_generator.py` - Visual generation
- `services/tts/tts_orchestrator.py` - TTS generation

Each rotation updates the `GOOGLE_CLOUD_PROJECT` environment variable, which is automatically picked up by Google Cloud client libraries.

**Lazy Initialization**: Projects are loaded from environment variables only when first accessed, ensuring compatibility with applications that load `.env` files at startup (like using `python-dotenv`).

## Best Practices

1. **Use 3-5 projects** for optimal load distribution
2. **Ensure all projects have the same APIs enabled** (Vertex AI, Imagen, TTS)
3. **Use the same service account** across all projects for consistent authentication
4. **Monitor quota usage** across all projects to ensure even distribution

## Troubleshooting

### Projects not rotating

Check that `GOOGLE_CLOUD_PROJECTS` is set correctly:

```bash
echo $GOOGLE_CLOUD_PROJECTS
```

### "No projects available for rotation" warning

This usually means the environment variable wasn't loaded when the module was imported. The system uses lazy initialization, so this should resolve automatically when the first rotation is attempted. If the issue persists:

1. Verify the environment variable is set: `echo $GOOGLE_CLOUD_PROJECTS`
2. Check your `.env` file contains the correct variable name
3. Ensure your application loads the `.env` file before using project rotation

### Authentication errors

Ensure your service account has access to all configured projects:

```bash
gcloud projects list
gcloud auth application-default login
```

### Quota still exceeded

If you're still hitting limits:
1. Add more projects to the rotation
2. Check quota limits in each project's Cloud Console
3. Request quota increases if needed
