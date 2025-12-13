# Documentation Index

Welcome to the Gemini Powerpoint Sage documentation!

## 📚 Getting Started

Start here if you're new to the project:

1. **[Quick Start Guide](QUICK_START.md)** - Get up and running in 3 steps
2. **[Configuration File Guide](CONFIG_FILE_GUIDE.md)** - Learn to use YAML configs
3. **[Style Examples](STYLE_EXAMPLES.md)** - Customize your presentation style

## 📖 User Guides

### Core Features
- **[Configuration File Guide](CONFIG_FILE_GUIDE.md)** - Manage settings with YAML files
- **[Style Examples](STYLE_EXAMPLES.md)** - Apply themes like Gundam, Cyberpunk, etc.
- **[Style Prompts Guide](STYLE_PROMPTS.md)** - Create detailed multi-line style prompts
- **[Folder Structure](FOLDER_STRUCTURE.md)** - Understand output organization
- **[Chinese Locale Support](CHINESE_LOCALE_SUPPORT.md)** - Traditional vs Simplified Chinese

### Reference
- **[User Quick Reference](../QUICK_REFERENCE.md)** - Command-line reference and tips
- **[Developer Reference](DEVELOPER_REFERENCE.md)** - Code patterns and APIs
- **[Testing Guide](TESTING_GUIDE.md)** - Test commands and validation

## 🏗️ Architecture & Development

For developers and contributors:

- **[Architecture](ARCHITECTURE.md)** - System architecture overview
- **[Agent Flow Detailed](AGENT_FLOW_DETAILED.md)** - Complete agent logic flow and relationships
- **[Agent Relationships](AGENT_RELATIONSHIPS.md)** - Agent interactions and dependencies
- **[Prompt Rewriter](PROMPT_REWRITER.md)** - Prompt rewriter system overview
- **[Prompt Rewriter Agent Details](PROMPT_REWRITER_AGENT_DETAILS.md)** - Detailed meta-agent analysis

## 🎯 Quick Links by Task

### I want to...

**Get started quickly**
→ [Quick Start Guide](QUICK_START.md)

**Use YAML configuration files**
→ [Configuration File Guide](CONFIG_FILE_GUIDE.md)

**Apply a custom style/theme to my presentation**
→ [Style Examples](STYLE_EXAMPLES.md) or [Style Prompts Guide](STYLE_PROMPTS.md)

**Process one specific style**
→ `python main.py --style-config cyberpunk`

**Process all styles at once**
→ `python main.py --styles`

**Understand the output folder structure**
→ [Folder Structure](FOLDER_STRUCTURE.md)

**Learn about the system architecture**
→ [Architecture](ARCHITECTURE.md)

## 📂 Documentation Structure

```
docs/
├── README.md                      # This file - documentation index
├── QUICK_START.md                 # Quick start guide
├── CONFIG_FILE_GUIDE.md           # Configuration file guide
├── STYLE_EXAMPLES.md              # Style gallery and customization
├── STYLE_PROMPTS.md               # Detailed style prompt guide
├── FOLDER_STRUCTURE.md            # Output folder structure
├── DEVELOPER_REFERENCE.md         # Developer reference
├── TESTING_GUIDE.md               # Testing guide
├── CHINESE_LOCALE_SUPPORT.md      # Chinese locale support
├── ARCHITECTURE.md                # System architecture overview
├── AGENT_FLOW_DETAILED.md         # Complete agent logic flow trace
├── AGENT_RELATIONSHIPS.md         # Agent interactions and dependencies
├── PROMPT_REWRITER.md             # Prompt rewriter system overview
└── PROMPT_REWRITER_AGENT_DETAILS.md # Detailed meta-agent analysis
```

## 🔄 Documentation Updates

This documentation is actively maintained. If you find any issues or have suggestions:

1. Check if the information is outdated
2. Refer to the main [README.md](../README.md) for the latest information
3. Open an issue or submit a pull request

## 📌 Version

Documentation last updated: December 2025
Compatible with: Gemini Powerpoint Sage v2.0+
