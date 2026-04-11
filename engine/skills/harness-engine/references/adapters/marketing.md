# Marketing Task Adapter

## Purpose

When harness-engine generates or augments a marketing domain harness, this adapter is additionally applied after the common `research` phase to enforce the **minimum contract** specific to the marketing task_type.

## Coverage Contract

A marketing harness must include the following items. If any are missing, the harness is deemed incomplete.

### Required Axes (All Marketing Projects)

1. **Target Audience Definition**
   - Persona specification (demographics, behaviors, needs, goals)
   - Segmentation criteria and priority segments
   - Messaging direction per segment
2. **Campaign Structure**
   - Goal setting (awareness/consideration/conversion/retention — which stage)
   - Channel selection rationale
   - KPI definition and measurement methods
   - Budget allocation framework
3. **Creative Guidelines**
   - Tone and manner, brand voice rules
   - Content format and constraints per channel (character limits, image sizes, etc.)
   - CTA (Call to Action) design principles
4. **Experimentation/Optimization Framework**
   - A/B test design rules (hypothesis, variables, sample size)
   - Statistical significance judgment criteria
   - Iterative optimization cycle definition
5. **Performance Measurement**
   - Key metrics per funnel stage (CAC, LTV, ROAS, CTR, etc.)
   - Attribution model selection criteria
   - Reporting cadence and format

### Items That Must Be Investigated in the Project Contract Packet

- Product/service category and competitive positioning
- List of channels in use (search, social, email, display, etc.)
- Budget scale and constraints
- Legal/regulatory constraints (advertising disclosure requirements, industry-specific regulations)
- Whether existing brand guidelines exist

## Primary Evidence Sources

Marketing harness rules use the following sources as primary evidence:

1. Platform official guides (Google Ads, Meta Ads, LinkedIn Ads, etc.)
2. Industry standard frameworks (AIDA, AARRR, STP, etc.)
3. Academic marketing journals (Journal of Marketing, HBR, etc.)
4. Official platform policy documents (advertising policies, creative specifications)

Blogs and agency case studies are used as supplementary materials only.

## Anti/Good Minimum Required Pair List

### Targeting

| Case | Anti Content | Good Content |
|---|---|---|
| Vague target | Broad targeting like "all men and women ages 20-40" | Behavior/needs-based segment definition with prioritization |
| Assumption-based persona | "Probably these kinds of people" without data | Persona based on existing data, interviews, and surveys |

### Campaign Design

| Case | Anti Content | Good Content |
|---|---|---|
| Campaign without KPIs | Unmeasurable goals like "increase brand awareness" | SMART-criteria KPI definition (CTR X%, CAC under Y) |
| Indiscriminate channel expansion | Simultaneous execution across all channels without differentiated strategy | Defining roles per channel, focusing on priority channels |
| Equal budget allocation | Allocating identical proportions to all channels/creatives | Differentiated allocation based on performance data, with separate test budget |

### Creative

| Case | Anti Content | Good Content |
|---|---|---|
| Feature-listing copy | Ad copy that merely lists product features | Present the target's problem/need first -> connect to solution |
| Absent/vague CTA | Weak CTAs like "Learn more" | Specific action prompts ("Start free trial", "Get a quote") |
| Channel-ignorant format | Using identical creatives across all channels as-is | Producing creatives tailored to each channel's specifications/context |

### Experimentation/Optimization

| Case | Anti Content | Good Content |
|---|---|---|
| Intuition-based judgment | Selecting creatives based on "this seems better" | A/B test + statistical significance verification |
| Premature termination | Ending tests before sufficient data collection | Making decisions only after reaching minimum sample size |
| Multi-variable mixed test | Changing multiple variables simultaneously in one test | Single variable isolation testing, sequential experiments |

### Performance Reporting

| Case | Anti Content | Good Content |
|---|---|---|
| Vanity metrics | Reporting only likes/follower counts | Business metric-centered reporting (revenue, conversions, CAC) |
| Attribution ignored | Attributing results solely via last-click | Multi-touch attribution or intentional model selection with documentation |

## Dry-Run Input/Output Examples

### Positive Case: Campaign Structure Verification

**Input**: "Plan a marketing campaign for a new SaaS product launch."

**Expected Output (direction the harness should guide)**:

- Require target segment definition first
- Set KPIs per funnel stage
- Separate roles per channel
- Include A/B test plan

### Negative Case: Campaign Without KPIs Detection

**Input**: "Create an SNS campaign to increase brand awareness."

**Expected Output (pattern the harness should block)**:

- Unmeasurable goal -> detected as anti-pattern
- Require specific KPI definition (reach X, brand search volume increase Y%)

## Design Rationale

- Coverage Contract required axes: cross-analysis of marketing strategy frameworks (STP, AIDA, AARRR)
- Anti/Good required pairs: pattern extraction based on Anthropic Growth Marketing team case studies (ad processing 2 hours -> 15 minutes, 10x output)
- Experimentation framework: Google Ads/Meta Ads official experimentation guidelines
