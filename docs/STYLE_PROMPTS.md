# Style Prompts Guide

This guide shows you how to create detailed, multi-line style prompts for maximum customization.

## 📝 YAML Multi-Line Syntax

YAML supports multi-line strings using the pipe (`|`) character:

```yaml
style: |
  Your detailed style description here
  Can span multiple lines
  With proper formatting
```

## 🎨 Style Prompt Template

Use this template for comprehensive style definitions:

```yaml
style: |
  [Style Name] - [Brief Description]
  
  Visual Design:
  - [Visual element 1]
  - [Visual element 2]
  - [Color scheme]
  - [Typography/shapes]
  
  Speaker Notes Tone:
  - [Language style]
  - [Terminology preferences]
  - [Example phrases]
```

## 🤖 Example: gundam Style

### Detailed Multi-Line Version

```yaml
style: |
  gundam Style - Mecha-inspired futuristic design
  
  Visual Design:
  - Towering mecha aesthetics with gleaming metallic armor
  - Glowing energy effects (blue/green accents)
  - Angular, geometric shapes and technical diagrams
  - Futuristic HUD-style elements
  - Military/tactical color schemes (grays, blues, blacks)
  - Technical schematics and blueprint-style graphics
  
  Speaker Notes Tone:
  - Strategic and tactical language
  - Military precision terminology
  - Technical mecha/engineering references
  - Heroic and determined tone
  - Use phrases like "Deploy", "Engage", "Strategic advantage"
  - Example: "Deploy this solution across all sectors" instead of "Use this solution"
```

### Simple Single-Line Version

```yaml
style: "gundam - Mecha-inspired, tactical language, futuristic visuals"
```

## 🌃 Example: Cyberpunk Style

### Detailed Version

```yaml
style: |
  Cyberpunk Style - Dystopian tech aesthetic
  
  Visual Design:
  - Neon colors (cyan, magenta, purple, hot pink)
  - Glitch effects and digital artifacts
  - Dark backgrounds with high contrast
  - Holographic and transparent UI elements
  - Urban dystopian imagery
  - Matrix-style code rain effects
  
  Speaker Notes Tone:
  - Edgy, tech-savvy language
  - Hacker/tech culture references
  - Slightly rebellious or disruptive tone
  - Use terms like "hack", "exploit", "system", "network"
  - Example: "Hack the system by..." instead of "Improve the system by..."
```

### Simple Version

```yaml
style: "Cyberpunk - Neon colors, edgy tech language, glitch aesthetics"
```

## ⚪ Example: Minimalist Style

### Detailed Version

```yaml
style: |
  Minimalist Style - Less is more
  
  Visual Design:
  - Clean lines and simple geometric shapes
  - Abundant whitespace
  - Monochromatic or limited color palette (2-3 colors max)
  - Sans-serif typography
  - No decorative elements
  - Focus on content hierarchy
  
  Speaker Notes Tone:
  - Clear, concise, no fluff
  - Direct communication
  - Short sentences
  - Active voice
  - Example: "Three key points. First..." instead of "Let me walk you through..."
```

### Simple Version

```yaml
style: "Minimalist - Clean design, concise language, lots of whitespace"
```

## 🎬 Example: Anime Style

### Detailed Version

```yaml
style: |
  Anime Style - Vibrant Japanese animation aesthetic
  
  Visual Design:
  - Vibrant, saturated colors
  - Dynamic compositions with action lines
  - Expressive character-style illustrations
  - Dramatic lighting and shadows
  - Speed lines and motion effects
  - Manga-style panel layouts
  
  Speaker Notes Tone:
  - Energetic and enthusiastic
  - Dramatic emphasis on key points
  - Use of exclamations and emotional language
  - Narrative storytelling approach
  - Example: "This is where everything changes!" instead of "This is an important point"
```

## 🏢 Example: Corporate Professional

### Detailed Version

```yaml
style: |
  Corporate Professional - Traditional business style
  
  Visual Design:
  - Conservative color schemes (navy, gray, white)
  - Professional charts and graphs
  - Clean, structured layouts
  - Serif or professional sans-serif fonts
  - Subtle gradients and shadows
  - Business-appropriate imagery
  
  Speaker Notes Tone:
  - Formal, professional terminology
  - Business-appropriate language
  - Structured and organized
  - Data-driven statements
  - Example: "Our analysis indicates..." instead of "We found..."
```

## 🎮 Example: Gaming/Esports Style

```yaml
style: |
  Gaming/Esports Style - Competitive gaming aesthetic
  
  Visual Design:
  - Bold, aggressive colors (red, black, neon green)
  - Dynamic angles and perspectives
  - HUD-style overlays and stats
  - Glowing effects and particle systems
  - Team/clan branding elements
  - Achievement/badge graphics
  
  Speaker Notes Tone:
  - Competitive and energetic language
  - Gaming terminology and references
  - Team-oriented phrases
  - Victory/achievement focused
  - Example: "Level up your strategy" instead of "Improve your approach"
```

## 🌿 Example: Nature/Organic Style

```yaml
style: |
  Nature/Organic Style - Earth-inspired design
  
  Visual Design:
  - Earth tones (greens, browns, beiges)
  - Organic shapes and flowing lines
  - Natural textures (wood, stone, water)
  - Botanical illustrations
  - Soft, natural lighting
  - Sustainable/eco-friendly imagery
  
  Speaker Notes Tone:
  - Calm, grounded language
  - Natural metaphors and analogies
  - Growth and sustainability focus
  - Harmonious and balanced phrasing
  - Example: "Let this idea take root" instead of "Consider this concept"
```

## 🚀 Example: Sci-Fi Space Exploration

```yaml
style: |
  Sci-Fi Space Exploration - Cosmic adventure theme
  
  Visual Design:
  - Deep space backgrounds (stars, nebulae, galaxies)
  - Sleek spacecraft and station designs
  - Holographic interfaces
  - Cosmic color palette (deep blues, purples, whites)
  - Futuristic technology elements
  - Planetary and astronomical imagery
  
  Speaker Notes Tone:
  - Exploratory and discovery-focused language
  - Scientific and astronomical references
  - Sense of wonder and possibility
  - Mission-oriented phrasing
  - Example: "Explore new frontiers in..." instead of "Learn about..."
```

## 💡 Tips for Creating Custom Styles

### 1. Be Specific
```yaml
# ❌ Too vague
style: "Cool and modern"

# ✅ Specific
style: |
  Modern Tech Style
  Visuals: Flat design, bright accent colors, geometric shapes
  Tone: Conversational, tech-savvy, forward-thinking
```

### 2. Separate Visual and Tone
Always specify both visual design and speaking tone for consistency.

### 3. Provide Examples
Include example phrases to guide the AI:
```yaml
style: |
  Military Briefing Style
  Tone: Authoritative and concise
  Example: "Mission objective: Increase efficiency by 40%"
```

### 4. Reference Existing Media
```yaml
style: |
  Marvel Cinematic Universe Style
  Visuals: Bold superhero aesthetics, dynamic action poses
  Tone: Heroic, witty, team-oriented dialogue
```

### 5. Combine Multiple Influences
```yaml
style: |
  Cyberpunk-Noir Fusion
  Visuals: Neon cyberpunk colors with film noir shadows
  Tone: Mysterious detective narrative with tech jargon
```

## 🎯 Testing Your Style

1. **Start Simple** - Test with a basic description first
2. **Iterate** - Add more details based on results
3. **Be Consistent** - Use the same style for the entire presentation
4. **Review Output** - Check if visuals and notes match your vision
5. **Refine** - Adjust your prompt based on what works

## 📋 Style Checklist

When creating a custom style, consider:

- [ ] **Color palette** - What colors define this style?
- [ ] **Typography** - What font style fits?
- [ ] **Shapes/patterns** - Geometric, organic, angular?
- [ ] **Imagery** - What visual metaphors work?
- [ ] **Tone** - Formal, casual, technical, creative?
- [ ] **Vocabulary** - What terms should be used/avoided?
- [ ] **Examples** - Can you provide sample phrases?
- [ ] **References** - Any existing media to emulate?

## 🔄 Converting Simple to Detailed

If you have a simple style that works, expand it:

**Simple:**
```yaml
style: "Gundam"
```

**Expanded:**
```yaml
style: |
  Gundam - Mecha anime style
  Visuals: Metallic armor, glowing effects, angular shapes
  Tone: Tactical, heroic, military precision
```

**Fully Detailed:**
```yaml
style: |
  Gundam Style - Mobile Suit mecha-inspired design
  
  Visual Design:
  - Towering mecha with gleaming armor
  - Glowing energy weapons and thrusters
  - Technical schematics and HUD elements
  - Military color schemes
  
  Speaker Notes:
  - Strategic military language
  - Technical mecha terminology
  - Heroic and determined tone
```

## 📚 See Also

- [Style Examples](STYLE_EXAMPLES.md) - Pre-made style examples
- [Configuration Guide](CONFIG_FILE_GUIDE.md) - YAML syntax help
- [Quick Start](QUICK_START.md) - Getting started guide
