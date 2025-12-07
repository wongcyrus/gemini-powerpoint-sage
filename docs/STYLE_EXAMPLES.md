# Style/Theme Examples for Gemini Powerpoint Sage

The `--style` parameter allows you to customize the visual and narrative style of your presentation. This affects both the speaker notes tone and the slide visual design.

> 💡 **New!** For detailed, multi-line style prompts, see [Style Prompts Guide](STYLE_PROMPTS.md)

## Usage

### Command Line
```bash
# Gundam/Mecha style
python main.py --pptx presentation.pptx --pdf presentation.pdf --style "Gundam"

# Cyberpunk style
python main.py --pptx presentation.pptx --pdf presentation.pdf --style "Cyberpunk"

# Minimalist style
python main.py --pptx presentation.pptx --pdf presentation.pdf --style "Minimalist"

# Corporate/Professional (default)
python main.py --pptx presentation.pptx --pdf presentation.pdf --style "Corporate"
```

### Environment Variable
```bash
# Set in .env file
PRESENTATION_STYLE=Gundam

# Then run without --style flag
python main.py --pptx presentation.pptx --pdf presentation.pdf
```

## Style Examples

### 🤖 Gundam Style
**Visual Design:**
- Futuristic, mecha-inspired aesthetics
- Bold angular shapes and tech elements
- Military/tactical color schemes
- Technical diagrams and schematics

**Speaker Notes Tone:**
- Strategic and tactical language
- Military precision terminology
- Technical mecha/engineering references
- Example: "Deploy this solution across all sectors..." instead of "Use this solution..."

### 🌃 Cyberpunk Style
**Visual Design:**
- Neon colors (cyan, magenta, purple)
- Glitch effects and digital aesthetics
- Dystopian tech vibes
- High contrast, dark backgrounds

**Speaker Notes Tone:**
- Edgy, tech-savvy language
- Slightly rebellious or disruptive tone
- Hacker/tech culture references
- Example: "Hack the system by..." instead of "Improve the system by..."

### ⚪ Minimalist Style
**Visual Design:**
- Clean lines and simple shapes
- Lots of whitespace
- Monochromatic or limited color palette
- Sans-serif typography

**Speaker Notes Tone:**
- Clear, concise, no fluff
- Direct communication
- Short sentences
- Example: "Three key points. First..." instead of "Let me walk you through three important considerations..."

### 💼 Corporate/Professional Style (Default)
**Visual Design:**
- Conservative, business-appropriate
- Professional color schemes (blues, grays)
- Traditional layouts
- Charts and data visualizations

**Speaker Notes Tone:**
- Formal, professional terminology
- Business-appropriate language
- Structured and organized
- Example: "Our analysis indicates..." instead of "We found..."

## Custom Styles

You can create your own custom styles by providing descriptive names:

```bash
# Anime style
python main.py --pptx presentation.pptx --style "Anime - vibrant colors, dynamic compositions"

# Retro 80s style
python main.py --pptx presentation.pptx --style "Retro 80s - neon colors, geometric patterns"

# Nature/Organic style
python main.py --pptx presentation.pptx --style "Nature - organic shapes, earth tones, natural imagery"

# Sci-Fi style
python main.py --pptx presentation.pptx --style "Sci-Fi - futuristic, space themes, holographic effects"
```

### Multi-Line Detailed Styles

For maximum control, use multi-line YAML style definitions in your config file:

```yaml
style: |
  Gundam Style - Mecha-inspired futuristic design
  
  Visual Design:
  - Metallic armor aesthetics with glowing energy effects
  - Angular, geometric shapes and technical diagrams
  - Military/tactical color schemes
  
  Speaker Notes Tone:
  - Strategic and tactical language
  - Military precision terminology
  - Example: "Deploy this solution" instead of "Use this solution"
```

**See [Style Prompts Guide](STYLE_PROMPTS.md) for detailed examples and templates.**

## Tips

1. **Be Descriptive**: The more descriptive your style name, the better the AI can interpret it
2. **Consistency**: Use the same style for all slides in a presentation for visual consistency
3. **Audience**: Choose a style appropriate for your audience (e.g., Corporate for business meetings, Minimalist for academic presentations)
4. **Experiment**: Try different styles to see which works best for your content

## Examples in Action

### Technical Presentation with Gundam Style
```bash
python main.py --pptx cloud_architecture.pptx --pdf cloud_architecture.pdf --style "Gundam"
```
Result: Technical diagrams with mecha-inspired aesthetics, speaker notes using tactical/strategic language

### Marketing Pitch with Cyberpunk Style
```bash
python main.py --pptx product_launch.pptx --pdf product_launch.pdf --style "Cyberpunk"
```
Result: Neon-colored slides with glitch effects, edgy and disruptive speaker notes

### Academic Presentation with Minimalist Style
```bash
python main.py --pptx research_findings.pptx --pdf research_findings.pdf --style "Minimalist"
```
Result: Clean, simple slides with lots of whitespace, concise and direct speaker notes
