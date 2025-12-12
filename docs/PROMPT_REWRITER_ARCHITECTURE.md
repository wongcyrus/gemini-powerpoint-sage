# Prompt Rewriter Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION GENERATION                            │
│                                                                              │
│  ┌────────────┐                                                             │
│  │   Config   │  visual_style, speaker_style                                │
│  └──────┬─────┘                                                             │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Agent Factory                                   │   │
│  │  create_all_agents(visual_style, speaker_style)                     │   │
│  └──────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                            │
│                                 ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    PromptRewriter Service                            │   │
│  │                                                                      │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │  rewrite_designer_prompt(base_prompt)                        │  │   │
│  │  │  rewrite_writer_prompt(base_prompt)                          │  │   │
│  │  │  rewrite_title_generator_prompt(base_prompt)                 │  │   │
│  │  └────────────────────────┬─────────────────────────────────────┘  │   │
│  │                           │                                          │   │
│  │                           ▼                                          │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │         Prompt Rewriter Agent (LLM)                          │  │   │
│  │  │                                                              │  │   │
│  │  │  Input:                                                      │  │   │
│  │  │  - BASE_PROMPT: Original agent instruction                  │  │   │
│  │  │  - STYLE_GUIDELINES: Visual or speaker style                │  │   │
│  │  │  - STYLE_TYPE: "visual" or "speaker"                        │  │   │
│  │  │                                                              │  │   │
│  │  │  Process:                                                    │  │   │
│  │  │  1. Analyze base prompt structure                           │  │   │
│  │  │  2. Identify key integration points                         │  │   │
│  │  │  3. Weave style throughout instructions                     │  │   │
│  │  │  4. Add concrete examples & checkpoints                     │  │   │
│  │  │  5. Make style adherence mandatory                          │  │   │
│  │  │                                                              │  │   │
│  │  │  Output: Rewritten prompt with deep style integration       │  │   │
│  │  └────────────────────────┬─────────────────────────────────────┘  │   │
│  │                           │                                          │   │
│  │                           ▼                                          │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │  Fallback (if LLM fails)                                     │  │   │
│  │  │  - _fallback_designer_rewrite()                              │  │   │
│  │  │  - _fallback_writer_rewrite()                                │  │   │
│  │  │  - _fallback_title_generator_rewrite()                       │  │   │
│  │  │  (Simple concatenation with style rules)                     │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────┬────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Styled Agents Created                             │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │   Designer   │  │    Writer    │  │   Title Generator        │  │   │
│  │  │              │  │              │  │                          │  │   │
│  │  │ Visual Style │  │Speaker Style │  │    Speaker Style         │  │   │
│  │  │  Integrated  │  │  Integrated  │  │      Integrated          │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

```
┌──────────────┐
│ User Request │
│ with Styles  │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Agent Factory receives visual_style & speaker_style      │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Creates PromptRewriter instance with styles              │
└──────┬──────────────────────────────────────────────────────┘
       │
       ├─────────────────────────────────────────────────────┐
       │                                                      │
       ▼                                                      ▼
┌──────────────────────────┐                    ┌──────────────────────────┐
│ 3a. Designer Rewrite     │                    │ 3b. Writer Rewrite       │
│                          │                    │                          │
│ Base: DESIGNER_PROMPT    │                    │ Base: WRITER_PROMPT      │
│ Style: visual_style      │                    │ Style: speaker_style     │
│ Type: "visual"           │                    │ Type: "speaker"          │
└──────┬───────────────────┘                    └──────┬───────────────────┘
       │                                                │
       ▼                                                ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Prompt Rewriter Agent (LLM) processes request             │
│                                                               │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ Analyzes base prompt structure                      │  │
│    └─────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ Identifies integration points                       │  │
│    │ - System instructions                               │  │
│    │ - Task descriptions                                 │  │
│    │ - Guidelines sections                               │  │
│    │ - Output requirements                               │  │
│    └─────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ Weaves style throughout                             │  │
│    │ - Adds style-specific language                      │  │
│    │ - Integrates concrete examples                      │  │
│    │ - Creates validation checkpoints                    │  │
│    │ - Emphasizes mandatory adherence                    │  │
│    └─────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ Returns rewritten prompt                            │  │
│    └─────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Rewritten prompt used to create agent                    │
│                                                              │
│    LlmAgent(                                                 │
│        name="designer",                                      │
│        model="gemini-3-pro-image-preview",                   │
│        instruction=rewritten_prompt  ← Style integrated!    │
│    )                                                         │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Agent generates content with style deeply embedded       │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INPUT STYLES                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Visual Style:                    Speaker Style:                   │
│  ┌─────────────────────┐          ┌─────────────────────┐         │
│  │ - Color palette     │          │ - Tone & energy     │         │
│  │ - Typography        │          │ - Vocabulary        │         │
│  │ - Layout principles │          │ - Sentence structure│         │
│  │ - Visual elements   │          │ - Rhetorical devices│         │
│  │ - Design aesthetic  │          │ - Example phrases   │         │
│  └─────────────────────┘          └─────────────────────┘         │
│           │                                  │                      │
└───────────┼──────────────────────────────────┼──────────────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PROMPT REWRITER AGENT                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Rewriting Strategy:                                                │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ 1. Parse base prompt into sections                            │ │
│  │ 2. Map style elements to relevant sections                    │ │
│  │ 3. Rewrite each section with style integration                │ │
│  │ 4. Add style-specific examples and checkpoints                │ │
│  │ 5. Emphasize mandatory adherence throughout                   │ │
│  │ 6. Validate completeness and coherence                        │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      REWRITTEN PROMPTS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Designer Prompt:                Writer Prompt:                    │
│  ┌─────────────────────┐        ┌─────────────────────┐           │
│  │ System: Style-aware │        │ System: Voice-aware │           │
│  │ Task: Style-focused │        │ Task: Tone-focused  │           │
│  │ Guidelines: Styled  │        │ Guidelines: Styled  │           │
│  │ Examples: Concrete  │        │ Examples: Concrete  │           │
│  │ Validation: Checks  │        │ Validation: Checks  │           │
│  └─────────────────────┘        └─────────────────────┘           │
│           │                                │                        │
└───────────┼────────────────────────────────┼────────────────────────┘
            │                                │
            ▼                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        STYLED AGENTS                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Designer Agent                    Writer Agent                    │
│  ┌─────────────────────┐          ┌─────────────────────┐         │
│  │ Generates slides    │          │ Generates notes     │         │
│  │ with visual style   │          │ with speaker style  │         │
│  │ deeply embedded     │          │ deeply embedded     │         │
│  └─────────────────────┘          └─────────────────────┘         │
│           │                                │                        │
└───────────┼────────────────────────────────┼────────────────────────┘
            │                                │
            ▼                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         OUTPUT                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Styled Slides                     Styled Speaker Notes            │
│  ┌─────────────────────┐          ┌─────────────────────┐         │
│  │ ✓ Correct colors    │          │ ✓ Correct tone      │         │
│  │ ✓ Correct typography│          │ ✓ Correct vocabulary│         │
│  │ ✓ Correct layout    │          │ ✓ Correct structure │         │
│  │ ✓ Correct aesthetic │          │ ✓ Correct voice     │         │
│  └─────────────────────┘          └─────────────────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Error Handling & Fallback

```
┌─────────────────────────────────────────────────────────────┐
│              Prompt Rewriter Execution                      │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Try: LLM-powered rewriting                                  │
│                                                              │
│  runner = InMemoryRunner(agent=self.rewriter_agent, app_name="agents") │
│  response_text = ""                                         │
│  for event in runner.run(user_id="user", session_id="session", │
│                          new_message=rewrite_request):     │
│      if event.content and event.content.parts:             │
│          for part in event.content.parts:                  │
│              response_text += getattr(part, "text", "")     │
│  rewritten = response_text.strip()                          │
└──────┬───────────────────────────────────────┬──────────────┘
       │                                       │
       │ Success                               │ Exception
       ▼                                       ▼
┌──────────────────────────┐    ┌─────────────────────────────┐
│ Return rewritten prompt  │    │ Log error & warning         │
│ Log success metrics      │    │ "Falling back to simple     │
│                          │    │  concatenation"             │
└──────────────────────────┘    └──────┬──────────────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────────────────┐
                          │ Fallback: Simple concatenation      │
                          │                                     │
                          │ return f"""{base_prompt}            │
                          │                                     │
                          │ MANDATORY STYLE:                    │
                          │ {style}                             │
                          │                                     │
                          │ STYLE RULES:                        │
                          │ 1. Apply this style                 │
                          │ 2. ...                              │
                          │ """                                 │
                          └──────┬──────────────────────────────┘
                                 │
                                 ▼
                          ┌──────────────────────────────────────┐
                          │ Return fallback prompt               │
                          │ System continues to work             │
                          └──────────────────────────────────────┘
```

## Key Design Principles

1. **Separation of Concerns**
   - Agent Factory: Orchestrates agent creation
   - PromptRewriter Service: Manages rewriting logic
   - Prompt Rewriter Agent: Performs intelligent rewriting

2. **Robustness**
   - LLM-powered for intelligence
   - Fallback for reliability
   - Comprehensive error handling

3. **Flexibility**
   - Supports any visual style
   - Supports any speaker style
   - Extensible to new agent types

4. **Observability**
   - Detailed logging at each step
   - Statistics on rewrite process
   - Debug mode for full prompt inspection

5. **Maintainability**
   - Clean separation of base prompts and styles
   - Reusable rewriter agent
   - Consistent interface across agent types
