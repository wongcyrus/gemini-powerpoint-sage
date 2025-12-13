# Prompt Rewriter Agent - Detailed Analysis

## Overview

The **Prompt Rewriter Agent** is a unique meta-agent in the Gemini PowerPoint Sage system that operates at agent creation time to integrate styles into other agents' prompts. Unlike content-processing agents, it modifies how other agents behave by rewriting their instructions.

## Unique Characteristics

### Meta-Agent Architecture
- **Creation Time Operation**: Runs during agent initialization, not content processing
- **Prompt Modification**: Changes other agents' behavior by rewriting their instructions
- **Style Orchestrator**: Ensures consistent style application across all content agents
- **No Direct Content Access**: Never sees slides, notes, or presentation content

### LLM-Powered Intelligence
- **Deep Integration**: Uses AI to weave styles throughout prompts, not just append
- **Contextual Placement**: Intelligently places style requirements where most effective
- **Natural Language Processing**: Understands prompt structure and optimal integration points
- **Style Type Awareness**: Handles visual vs speaker styles differently

## Technical Implementation

### Agent Specification
```python
# agents/prompt_rewriter.py
prompt_rewriter_agent = LlmAgent(
    name="prompt_rewriter",
    model="gemini-2.5-flash",  # Configurable via MODEL_PROMPT_REWRITER
    description="Rewrites agent prompts to deeply integrate visual and speaker styles.",
    instruction=PROMPT_REWRITER_PROMPT,  # Sophisticated rewriting instructions
)
```

### Service Layer
```python
# services/prompt_rewriter.py
class PromptRewriter:
    def __init__(self, visual_style: str = None, speaker_style: str = None):
        self.visual_style = visual_style or "Professional"
        self.speaker_style = speaker_style or "Professional"
        self.rewriter_agent = prompt_rewriter_agent
```

### Integration Points
```python
# agents/agent_factory.py - Called during agent creation
def create_designer_agent(visual_style: str) -> LlmAgent:
    rewriter = PromptRewriter(visual_style=visual_style)
    instruction = rewriter.rewrite_designer_prompt(DESIGNER_PROMPT)
    return LlmAgent(name="slide_designer", instruction=instruction, ...)

def create_writer_agent(speaker_style: str) -> LlmAgent:
    rewriter = PromptRewriter(speaker_style=speaker_style)
    instruction = rewriter.rewrite_writer_prompt(WRITER_PROMPT)
    return LlmAgent(name="speech_writer", instruction=instruction, ...)
```

## Rewriting Strategies

### Visual Style Integration (Designer Agent)
**Focus Areas:**
- Color palette integration throughout design sections
- Typography requirements in text handling
- Layout consistency in composition guidelines
- Visual checkpoints in output validation
- Brand consistency in quality control

**Example Integration:**
```
Original: "Generate a professional slide design"
Rewritten: "Generate a slide design using the Cyberpunk aesthetic with electric blue (#00FFFF), hot pink (#FF1493), and purple (#9D00FF) color palette. Use futuristic typography with sharp angles and ensure neon glowing effects on all text elements..."
```

### Speaker Style Integration (Writer/Translator Agents)
**Focus Areas:**
- Tone integration in writing guidelines
- Vocabulary consistency in content generation
- Voice persona in speaker sections
- Linguistic patterns in output format
- Style adherence in quality control

**Example Integration:**
```
Original: "Write speaker notes for the presentation"
Rewritten: "Write speaker notes as a Jedi Master addressing the Rebel Alliance. Use wise, inspirational language with references to 'the Force' and 'destiny'. Begin with phrases like 'There is a disturbance in the Force...' and maintain philosophical undertones about balance and hope..."
```

## Execution Flow

### Rewriting Process
```
1. Receive Rewrite Request
   ├─ Base prompt (original agent instruction)
   ├─ Style guidelines (from YAML config)
   └─ Style type ("visual" or "speaker")

2. LLM Processing (with retry logic)
   ├─ Create unique session to avoid conflicts
   ├─ Send structured rewrite request to LLM
   ├─ Collect and validate response
   └─ Retry up to 3 times if needed

3. Fallback Mechanism (if LLM fails)
   ├─ Parse original request components
   ├─ Apply template-based integration
   └─ Ensure style is still included

4. Return Rewritten Prompt
   ├─ Enhanced with style integration
   ├─ Language enforcement added
   └─ Ready for agent creation
```

### Session Management
```python
# Unique session per rewrite to avoid conflicts
user_id = f"rewriter_user_{uuid.uuid4().hex[:6]}"
session_id = f"{session_prefix}_{attempt}_{uuid.uuid4().hex[:8]}"

# Explicit session creation
runner.session_service.create_session_sync(
    app_name="agents", user_id=user_id, session_id=session_id
)
```

## Error Handling and Reliability

### Retry Strategy
- **3 Attempts**: With exponential backoff between retries
- **Session Isolation**: Fresh session for each attempt
- **Response Validation**: Ensures substantial content (>50 chars)
- **Graceful Degradation**: Falls back to concatenation if all attempts fail

### Fallback Mechanism
```python
def _fallback_to_simple_concatenation(self, rewrite_request: str, session_prefix: str) -> str:
    # Parse components from failed request
    base_prompt = extract_base_prompt(rewrite_request)
    style_guidelines = extract_style_guidelines(rewrite_request)
    
    # Apply template-based integration
    if "writer" in session_prefix or "translator" in session_prefix:
        # Add language enforcement for speaker agents
        enhanced_prompt = f"{base_prompt}\n\n{STYLE_INTEGRATION_TEMPLATE}\n{style_guidelines}"
    else:
        # Simpler integration for visual agents
        enhanced_prompt = f"{base_prompt}\n\n{VISUAL_STYLE_TEMPLATE}\n{style_guidelines}"
    
    return enhanced_prompt
```

### Language Enforcement
**Critical for Multilingual Support:**
- Ensures target language overrides style examples
- Prevents style language from bleeding into output
- Adds explicit language compliance instructions
- Validates Chinese locale handling (Simplified vs Traditional)

## Performance Characteristics

### Timing
- **Creation Time Only**: No runtime performance impact
- **One-Time Cost**: Rewriting happens once per agent type per session
- **Cached Results**: Rewritten prompts reused for all content processing
- **Parallel Safe**: Each rewrite uses isolated sessions

### Resource Usage
- **Memory Efficient**: No persistent state between rewrites
- **Session Cleanup**: Automatic cleanup after each rewrite
- **Minimal Overhead**: Fallback ensures system always progresses
- **Scalable**: Performance independent of presentation size

## Integration with Other Agents

### Affected Agents
1. **Designer Agent**: Visual style integration
2. **Writer Agent**: Speaker style integration
3. **Translator Agent**: Speaker style for translations
4. **Title Generator Agent**: Speaker style for titles

### Unaffected Agents
- **Supervisor**: Uses base prompt (coordinates styled agents)
- **Analyst**: Uses base prompt (content analysis only)
- **Auditor**: Uses base prompt (quality assessment only)
- **Overviewer**: Uses base prompt (global context only)
- **Video Generator**: Uses base prompt (video concepts only)

### Style Consistency Chain
```
YAML Config (styles/config.*.yaml)
    ↓ (visual_style + speaker_style)
Prompt Rewriter Agent
    ↓ (LLM-powered integration)
Styled Agent Prompts
    ↓ (agent creation)
Style-Aware Content Agents
    ↓ (content processing)
Consistent Styled Output
```

## Benefits of Meta-Agent Design

### Architectural Advantages
- **Separation of Concerns**: Style logic separate from content processing
- **Centralized Control**: All style integration in one place
- **Consistency**: Same style treatment for all agents
- **Maintainability**: Easy to modify style integration without changing content agents

### Operational Benefits
- **Reliability**: Fallback ensures system always works
- **Flexibility**: Can modify style integration approach without system changes
- **Debuggability**: Clear separation between style and content issues
- **Testability**: Can test style integration independently

### User Experience Benefits
- **Consistent Styling**: All content follows same style guidelines
- **Natural Integration**: Styles feel native, not forced
- **Language Safety**: Prevents style language from overriding target language
- **Quality Assurance**: Style adherence built into agent behavior

## Future Enhancements

### Potential Improvements
- **Caching**: Cache rewritten prompts to avoid redundant LLM calls
- **Style Validation**: Verify style integration quality
- **A/B Testing**: Compare different rewriting strategies
- **User Feedback**: Learn from style application success rates
- **Multi-Dimensional Styles**: Support separate color, typography, layout styles

### Advanced Features
- **Style Inheritance**: Hierarchical style systems
- **Dynamic Styles**: Runtime style modification
- **Style Analytics**: Track style effectiveness
- **Custom Rewriters**: User-defined rewriting strategies

The Prompt Rewriter Agent represents a sophisticated approach to style integration that ensures consistent, high-quality styled output while maintaining system reliability and performance.