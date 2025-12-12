# Style Configuration Gallery

## Available Style Configurations

The project includes several pre-configured style templates that demonstrate the power of the prompt rewriter agent. Each config combines visual aesthetics with matching speaker personas for cohesive presentations.

---

## 🤖 gundam Style (`config.gundam.yaml`)

**Visual Aesthetic:** Mecha anime with high-quality cel-shaded art, detailed mechanical designs, and dramatic space colony backgrounds.

**Speaker Persona:** Char Aznable-style antagonist - aristocratic, philosophical, and melodramatic. Speaks about "gravity" (legacy systems) vs. "evolution" (innovation).

**Best For:**
- Tech presentations with a dramatic flair
- Product launches that need epic energy
- Presentations about transformation and evolution

**Key Phrases:**
- "Their souls are weighed down by gravity!"
- "Behold, the power of the Cloud..."
- "I came here to laugh at you, but instead, I will save you!"

**Color Palette:**
- Tricolor: Blue, White, Red, Yellow
- Military schemes: OD Green, Desert Sand, Titans Blue
- Minovsky particle effects: Pink/Green glitter

**Usage:**
```bash
./run.sh --config config.gundam.yaml
```

---

## 🌌 starwars Style (`config.starwars.yaml`)

**Visual Aesthetic:** Epic space opera with Ralph McQuarrie-inspired concept art, deep space backgrounds, and cinematic lighting.

**Speaker Persona:** Jedi Master addressing the Rebel Alliance - wise, inspirational, strategic with philosophical undertones about the Force and destiny.

**Best For:**
- Strategic presentations
- Mission-critical briefings
- Inspirational talks about innovation and change
- Technical presentations that need gravitas

**Key Phrases:**
- "There is a disturbance in the Force..."
- "The fate of the galaxy hangs in the balance..."
- "This is the way"
- "May the Force be with us"

**Color Palette:**
- Deep Space Black (#000000)
- Imperial Gray (#4A4A4A)
- Rebel Orange (#FF6B35)
- Lightsaber colors: Blue, Green, Red
- Hyperspace Blue (#0077B6)
- Gold/Yellow (#FFD60A)

**Technical Terminology:**
- Servers → "Command Ships"
- Cloud → "The Outer Rim"
- Data → "Intelligence"
- Security → "Shields"
- Speed → "Lightspeed"

**Usage:**
```bash
./run.sh --config config.starwars.yaml
```

---

## 🌃 cyberpunk Style (`config.cyberpunk.yaml`)

**Visual Aesthetic:** Neon-soaked dystopian future with electric colors, dark backgrounds, and glitch effects.

**Speaker Persona:** Tech-savvy street philosopher - edgy, direct, and cutting through corporate BS with raw truth.

**Best For:**
- Disruptive tech presentations
- Startup pitches
- Presentations challenging the status quo
- Cybersecurity and hacking topics

**Key Phrases:**
- "Wake up, samurai..."
- "The system is rigged..."
- "Time to jack in..."

**Color Palette:**
- Electric Blue (#00FFFF)
- Hot Pink (#FF1493)
- Purple (#9D00FF)
- Dark backgrounds (#0A0E27)
- Neon accents and glows

**Usage:**
```bash
./run.sh --config config.cyberpunk.yaml
```

---

## 📋 Sample Style (`config.sample.yaml`)

**Visual Aesthetic:** Professional and clean with modern design principles.

**Speaker Persona:** Standard professional presenter - clear, concise, and authoritative.

**Best For:**
- Corporate presentations
- Standard business meetings
- When you want quality without dramatic theming

**Usage:**
```bash
./run.sh --config config.sample.yaml
```

---

## 🎨 Creating Your Own Style Config

### Basic Template

```yaml
# my-custom-style.yaml
pptx: "path/to/presentation.pptm"
pdf: "path/to/presentation.pdf"
region: "global"
language: "en"

style:
  visual_style: |
    [Describe your visual aesthetic here]
    - Art style and influences
    - Color palette with hex codes
    - Typography preferences
    - Visual elements and motifs
    - Composition principles
    - Mood and atmosphere
    
  speaker_style: |
    [Describe your speaker persona here]
    - Core persona and archetype
    - Tone and voice characteristics
    - Key themes to emphasize
    - Vocabulary and phrasing patterns
    - Example phrases
    - Technical terminology mappings

skip_visuals: false
generate_videos: false
retry_errors: false
```

### Style Design Tips

**For Visual Style:**
1. **Be Specific:** Include hex codes for colors, font names, specific visual references
2. **Show Examples:** Reference known aesthetics (e.g., "like Blade Runner 2049")
3. **Define Mood:** Describe the emotional impact you want
4. **Technical Details:** Specify composition rules, lighting, effects
5. **Consistency:** Ensure all elements work together cohesively

**For Speaker Style:**
1. **Define Persona:** Who is speaking? What's their background?
2. **Core Themes:** What concepts should they emphasize?
3. **Vocabulary:** Provide specific phrases and terminology
4. **Examples:** Show how they would say things
5. **Boundaries:** What should they avoid?

### Example: Minimalist Style

```yaml
style:
  visual_style: |
    Swiss Design / Minimalist Aesthetic
    - Clean, grid-based layouts with generous white space
    - Limited color palette: Black (#000000), White (#FFFFFF), 
      Accent Red (#FF0000)
    - Helvetica or similar sans-serif typography
    - High contrast, maximum readability
    - Geometric shapes and precise alignment
    - No decorative elements - form follows function
    
  speaker_style: |
    Minimalist Communicator - Less is More
    - Extremely concise and direct
    - No fluff, no filler words
    - Short sentences. Clear points.
    - Data-driven and factual
    - Confident through simplicity
    - Example: "Three points. First: speed. Second: cost. Third: scale. Done."
```

### Example: Academic Style

```yaml
style:
  visual_style: |
    Academic Conference Presentation
    - Traditional academic layout with clear hierarchy
    - Conservative color scheme: Navy (#003366), Gray (#666666), White
    - Serif fonts for titles (Times, Garamond)
    - Charts and graphs with proper citations
    - Clean, professional, no flashy effects
    - Focus on data visualization and clarity
    
  speaker_style: |
    Research Professor / Academic Expert
    - Formal and scholarly tone
    - Evidence-based arguments with citations
    - Measured pace with careful word choice
    - Technical precision and accuracy
    - Acknowledges limitations and counterarguments
    - Uses phrases like "Our research indicates...", 
      "The data suggests...", "It is worth noting that..."
```

---

## Style Comparison Matrix

| Style | Visual Intensity | Speaker Energy | Best Use Case | Formality |
|-------|-----------------|----------------|---------------|-----------|
| **gundam** | ⚡⚡⚡⚡⚡ | 🔥🔥🔥🔥🔥 | Dramatic tech reveals | Low |
| **starwars** | ⚡⚡⚡⚡ | 🔥🔥🔥🔥 | Strategic briefings | Medium |
| **cyberpunk** | ⚡⚡⚡⚡⚡ | 🔥🔥🔥🔥 | Disruptive innovation | Low |
| **professional** | ⚡⚡ | 🔥🔥 | Standard business | High |
| **minimalist** | ⚡ | 🔥🔥 | Data-focused | High |
| **academic** | ⚡⚡ | 🔥 | Research presentations | Very High |

---

## Testing Your Style

1. **Create your config file:**
   ```bash
   cp config.sample.yaml config.mystyle.yaml
   # Edit config.mystyle.yaml with your styles
   ```

2. **Test with sample data:**
   ```bash
   ./run.sh --config config.mystyle.yaml
   ```

3. **Review the output:**
   - Check `tests/sample_data/generate/` for results
   - Review speaker notes for tone and vocabulary
   - Check visuals for aesthetic consistency

4. **Iterate:**
   - Adjust style descriptions based on results
   - The prompt rewriter agent will integrate your changes
   - More specific descriptions = better results

---

## Advanced: Multi-Style Presentations

You can create different configs for different sections:

```bash
# Executive summary with professional style
./run.sh --config config.professional.yaml

# Technical deep-dive with cyberpunk style
./run.sh --config config.cyberpunk.yaml

# Vision/future section with starwars style
./run.sh --config config.starwars.yaml
```

Then combine the outputs manually for a multi-styled presentation.

---

## Style Configuration Best Practices

1. **Consistency is Key:** Visual and speaker styles should complement each other
2. **Know Your Audience:** Match style intensity to audience expectations
3. **Test First:** Always test with sample data before important presentations
4. **Be Specific:** Vague descriptions produce vague results
5. **Provide Examples:** Show the agent what you mean with concrete examples
6. **Iterate:** Refine based on output - the agent learns from specificity

---

## Contributing New Styles

Have a great style config? Share it!

1. Create your config file: `config.yourtheme.yaml`
2. Test it thoroughly
3. Document it in this file
4. Submit a pull request

Popular community styles will be added to the official collection.

---

## Quick Reference Commands

```bash
# List all available configs
ls config.*.yaml

# Use a specific style
./run.sh --config config.starwars.yaml

# Override language while keeping style
./run.sh --config config.gundam.yaml --language zh-CN

# Skip visuals (notes only) with style
./run.sh --config config.cyberpunk.yaml --skip-visuals
```

---

## Need Help?

- See `docs/PROMPT_REWRITER.md` for how styles are integrated
- See `docs/RUN_SCRIPTS_USAGE.md` for command details
- See `docs/CONFIG_FILE_GUIDE.md` for config file format
- Check example configs for inspiration
