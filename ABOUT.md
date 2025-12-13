# About Gemini PowerPoint Sage

## 🎯 What It Does

**Gemini PowerPoint Sage** is an AI-powered presentation enhancement system that automatically generates or enhances speaker notes for PowerPoint presentations using Google's Gemini AI models. It transforms static slides into engaging presentations with professional speaker scripts and enhanced visuals.

## 🚀 Key Features

- **🤖 Multi-Agent AI System**: 10 specialized AI agents working together to analyze, write, and enhance presentations
- **🌍 Multi-Language Support**: Generate content in 16+ languages including English, Chinese (Simplified/Traditional), Japanese, Korean, Spanish, French, and more
- **🎨 Custom Styling**: Apply themed styles (Cyberpunk, Gundam, Star Wars, Professional) to both visuals and speaker voice
- **📁 Batch Processing**: Process entire folders of presentations automatically
- **🎬 Video Generation**: Create video prompts ready for Veo 3.1 integration
- **⚡ Translation Mode**: 2-3x faster processing by translating from English baseline
- **📊 Progress Tracking**: Resume interrupted processing with automatic progress saving

## 🏗️ Architecture

The system uses a sophisticated **Supervisor-led Multi-Agent Architecture** with three processing phases:

### Phase 1: Speaker Notes Generation
- **Overviewer Agent**: Analyzes entire presentation for global context
- **Supervisor Agent**: Orchestrates workflow for each slide
- **Auditor Agent**: Evaluates existing content quality
- **Analyst Agent**: Extracts insights from slide visuals
- **Writer Agent**: Generates natural, engaging speaker scripts
- **Translator Agent**: Provides style-aware translations

### Phase 2: Visual Enhancement
- **Designer Agent**: Creates professional slide designs with consistent styling
- **Image Translator Agent**: Adapts visuals for different languages and cultures

### Phase 3: Video Content (Optional)
- **Video Generator Agent**: Creates video prompts for promotional content
- **Prompt Rewriter Agent**: Integrates custom styles into all agent behaviors

## 🎭 Style System

Transform your presentations with themed styles:

- **🌌 Star Wars**: Epic space opera with Jedi Master narration
- **🤖 Gundam**: Mecha anime aesthetic with philosophical antagonist voice  
- **🌃 Cyberpunk**: Neon-soaked dystopian design with edgy tech-savvy narration
- **🎨 HK Comic**: Vibrant Hong Kong comic book style
- **📋 Professional**: Clean, corporate design with authoritative tone

Each style affects both visual design and speaker personality for cohesive presentations.

## 🛠️ Technology Stack

- **AI Models**: Google Gemini (2.5-flash, 3-pro-preview, 3-pro-image-preview)
- **Language**: Python 3.10+
- **Frameworks**: Google ADK (Agent Development Kit), FastMCP
- **Document Processing**: python-pptx, PyMuPDF, Pillow
- **Configuration**: YAML-driven with environment variable support

## 📈 Use Cases

### Education
- Transform lecture slides into engaging presentations
- Generate multilingual course materials
- Create consistent speaker notes across curriculum

### Business
- Enhance sales presentations with professional narration
- Standardize corporate presentation quality
- Localize presentations for global markets

### Content Creation
- Generate video-ready presentation scripts
- Create themed presentations for different audiences
- Batch process presentation libraries

## 🌟 What Makes It Special

### Intelligent Style Integration
Unlike simple template systems, Gemini PowerPoint Sage uses AI to deeply integrate styles throughout the content, making themed presentations feel natural and cohesive.

### Multi-Language Excellence
The system doesn't just translate—it adapts content culturally and linguistically while maintaining the chosen style and personality.

### Production Ready
Built for real-world use with robust error handling, progress tracking, and batch processing capabilities.

### Extensible Architecture
The multi-agent design makes it easy to add new capabilities, styles, or processing modes without disrupting existing functionality.

## 🎯 Perfect For

- **Educators** creating engaging course materials
- **Business professionals** standardizing presentation quality
- **Content creators** producing themed presentations
- **International organizations** needing multilingual content
- **Developers** interested in multi-agent AI systems

## 🚀 Getting Started

1. **Quick Setup**: Run `./setup.sh` (Linux/macOS) or `.\setup.ps1` (Windows)
2. **Configure**: Set up Google Cloud credentials and API access
3. **Process**: Choose from three modes:
   - Single file: `python main.py --pptx file.pptx --language en --style professional`
   - Single style: `python main.py --style-config cyberpunk`
   - All styles: `python main.py --styles`

## 📚 Documentation

Comprehensive documentation available in the `docs/` folder:
- [Quick Start Guide](docs/QUICK_START.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Agent Flow Details](docs/AGENT_FLOW_DETAILED.md)
- [Style Configuration](docs/STYLE_EXAMPLES.md)

## 🤝 Contributing

We welcome contributions! The multi-agent architecture makes it easy to:
- Add new AI agents for specialized tasks
- Create custom presentation styles
- Extend language support
- Improve processing capabilities

## 📄 License

See [LICENSE](LICENSE) file for details.

---

**Transform your presentations from static slides to engaging experiences with AI-powered enhancement.**