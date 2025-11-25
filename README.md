# Gemini Powerpoint Sage

This tool automatically generates or enhances speaker notes for PowerPoint presentations using a **Supervisor-led Multi-Agent System** powered by Google ADK.

It takes a PowerPoint (`.pptx`) and its corresponding PDF export (`.pdf`) as input. The PDF provides visual context for AI analysis, while the PPTX is updated with the generated speaker notes.

## Architecture
The system employs a sophisticated multi-agent approach, orchestrated in a two-pass system:

### Agents
1.  **Overviewer Agent (`gemini-3-pro-preview`, Pass 1):** This agent first analyzes *all* PDF slide images to generate a comprehensive `Global Context Guide`. This guide captures the overall narrative, key themes, vocabulary, and desired speaker persona for the entire presentation, ensuring consistency across all generated notes.
2.  **Supervisor Agent (`gemini-2.5-flash`, Pass 2 Orchestrator):** For each individual slide, the Supervisor directs the workflow. It decides whether to use existing notes (by consulting the Auditor), triggers the Analyst to understand the slide's content, and then requests the Writer to generate or refine speaker notes.
3.  **Auditor Agent (`gemini-2.5-flash`):** Evaluates the quality and usefulness of any existing speaker notes for a given slide.
4.  **Analyst Agent (`gemini-3-pro-preview`):** Analyzes the visual and textual content of a single slide image (from the PDF) to extract key topics, detailed information, visual descriptions, and the slide's intent.
5.  **Writer Agent (`gemini-2.5-flash`):** Crafts coherent, first-person speaker notes. It uses the insights from the Analyst, the `Global Context Guide` (from the Overviewer), and the `Previous Slide Summary` (from the Supervisor) to ensure smooth transitions and consistent tone.
6.  **Designer Agent (`gemini-3-pro-image-preview`):** Generates a new, high-fidelity, professional-looking slide image. It takes inspiration from the original slide (for branding like logos and colors) and critically, maintains style consistency by referencing the *previously generated slide image*. It converts speaker notes into concise on-slide text (Title + Bullet Points) and enhances any existing diagrams/charts.

### Additional Documentation

See the extended design rationale, sequence flows, and agent interface contracts in the full architecture guide: [ARCHITECTURE.md](docs/ARCHITECTURE.md).

### Workflow Diagram

```mermaid
graph TD
    A[User Input: PPTX, PDF] --> B(Extract All PDF Slide Images);

    subgraph Pass1[Pass 1: Global Context Generation]
        B --> C{Overviewer Agent};
        C --> D[Global Context Guide];
    end

    subgraph Pass2[Pass 2: Per-Slide Processing]
        D --> E{Supervisor Agent};
        E -- "Existing Notes" --> F{Auditor Agent};
        F -- "USEFUL" --> G[Use Existing Notes];
        F -- "USELESS / Needs Notes" --> E;
        
        E -- "Current Slide Image" --> H{Analyst Agent};
        H -- "Slide Analysis" --> I{Writer Agent};
        I -- "Speaker Notes" --> J[Update PPTX Notes];
        
        J -- "Notes & Current Slide" --> K{Designer Agent};
        K -- "Previous Generated Image" --> K;
        K -- "Reimagined Slide Image" --> L[Save PNG & Add to New PPTX];
        
        L -- "Updated Previous Image" --> K;
        I -- "Updated Previous Notes" --> E;
    end

    L --> M(Output: Enhanced PPTX);

    style C fill:#e6ffe6,stroke:#008000,stroke-width:2px;
    style E fill:#e6ffe6,stroke:#008000,stroke-width:2px;
    style I fill:#e6ffe6,stroke:#008000,stroke-width:2px;
    style K fill:#e6ffe6,stroke:#008000,stroke-width:2px;
    style M fill:#add8e6,stroke:#000080,stroke-width:2px;
```

## Setup

### Quick Setup (Recommended)

#### Linux/macOS
```bash
./setup.sh
```

#### Windows
```powershell
.\setup.ps1
```

The setup script will:
- Create a Python virtual environment at `.venv`
- Install all required dependencies from `requirements.txt`
- Configure the environment for use

### Manual Setup
1.  Create a virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    # or
    .\.venv\Scripts\Activate.ps1  # Windows
    ```
2.  Install the required Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Ensure you have valid Google Cloud credentials configured for your environment (e.g., via `gcloud auth application-default login` or by setting `GOOGLE_APPLICATION_CREDENTIALS`).

## Usage

### Linux/macOS
Run the `run.sh` script (it will automatically activate the virtual environment):

```bash
./run.sh --pptx /path/to/your/presentation.pptx --pdf /path/to/your/presentation.pdf
```

**Using an alternate GCP project (to avoid rate limits):**

```bash
export GOOGLE_CLOUD_PROJECT='your-other-project-id'
export GOOGLE_CLOUD_LOCATION='global'
./run.sh --pptx /path/to/file.pptx --pdf /path/to/file.pdf
```

### Windows
Run the `run.ps1` PowerShell script (it will automatically activate the virtual environment):

```powershell
.\run.ps1 --pptx "C:\path\to\your\presentation.pptx" --pdf "C:\path\to\your\presentation.pdf"
```

**Using an alternate GCP project (to avoid rate limits):**

```powershell
$env:GOOGLE_CLOUD_PROJECT = 'your-other-project-id'
$env:GOOGLE_CLOUD_LOCATION = 'global'
.\run.ps1 --pptx "path\to\file.pptx" --pdf "path\to\file.pdf"
```

**Arguments:**
*   `--pptx`: Path to the input PowerPoint (`.pptx`) file.
*   `--pdf`: Path to the corresponding PDF export of the presentation.
*   `--course-id` (Optional): A Firestore Course ID. If provided, the tool will attempt to fetch course details (like name or description) to provide more relevant thematic context to the agents.
*   `--progress-file` (Optional): Override the default progress tracking file location (default: `speaker_note_progress.json` in the same directory as the PPTX).
*   `--retry-errors` (Optional): Force regeneration of slides that were previously successful. By default, only slides with errors or missing notes are reprocessed.

## Technical Implementation Details

### Supervisor "Silent Finish" Fallback
A common issue in Agentic workflows is the "Silent Finish," where a Supervisor agent calls a tool (e.g., `speech_writer`), receives the correct text output, but then terminates the turn without explicitly repeating that text to the user.

To solve this, we implement a **Last Tool Output Fallback** pattern:
1.  The `speech_writer` tool function captures its generated text into a scoped variable (`last_writer_output`) every time it runs successfully.
2.  If the Supervisor loop finishes execution but produces **empty** final text, the system checks if `last_writer_output` contains data.
3.  If yes, the system infers that the Supervisor intended to return this content and uses the captured text as the final speaker note.

This ensures robustness against model unpredictability, especially with faster models like `gemini-2.5-flash`.

### Image Generation Skip Logic
*   **Stable Caching:** Generated images are named `slide_{index}_reimagined.png`.
*   **Skip Check:** Before calling the expensive Image Generation API, the system checks if this file already exists.
*   **Forced Retry:** The `--retry-errors` flag (or deleting the file) bypasses this check to force regeneration.
*   **Hash Removal:** We explicitly do *not* use the speaker note hash in the filename to allow for easier manual caching and to prevent minor text variations from triggering unnecessary image costs.

## Output
The tool will generate **two** PowerPoint files:
1. **`_with_notes.pptx`**: Contains the original slides with updated/generated speaker notes only.
2. **`_with_visuals.pptx`**: Contains the original slides with both speaker notes and AI-generated reimagined slide visuals (unless `--skip-visuals` is used).

Console output will show the progress, including agent decisions, analysis summaries, and generated notes.

### Progress Tracking
The tool automatically tracks progress in a JSON file (default: `speaker_note_progress.json` in the same directory as the input PPTX). This enables:

*   **Incremental processing**: If the tool is interrupted or fails on certain slides, you can re-run the same command and it will skip slides that were already successfully processed.
*   **Error retry**: Slides that failed or returned empty notes (status: `error`) are automatically retried on subsequent runs.
*   **Manual retry**: Use `--retry-errors` to force regeneration of all slides, including those previously successful.

The progress file stores each slide's:
- Slide index
- Original notes hash (to detect if notes change)
- Generated speaker note
- Status (`success` or `error`)

**Example progress file structure:**
```json
{
  "slides": {
    "slide_1_a1b2c3d4": {
      "slide_index": 1,
      "existing_notes_hash": "a1b2c3d4",
      "original_notes": "Introduction to security concepts",
      "note": "Welcome everyone. Today we'll explore...",
      "status": "success"
    }
  }
}
```

## Context Handling
*   **Rolling Context:** The Supervisor Agent maintains a "rolling context" by being aware of the previous slide's generated note. This helps in creating smooth transitions between slides.
*   **Presentation Theme:** The overall theme of the presentation is either a generic default or derived from the `--course-id` (if provided), helping agents align their output with the subject matter.

