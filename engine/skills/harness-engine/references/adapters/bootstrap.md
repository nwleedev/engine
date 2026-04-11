# Bootstrap Adapter

## Purpose

A starting template for harness-engine to generate an adapter draft for unknown domains that cannot be described by the representative classification set (frontend, research, backend, testing, security, ops).

## When to Use

### New Mode (No Adapter)

- When the TASK_INTAKE judgment does not match the representative classification set
- When no adapter for the domain exists in adapters/
- When the user explicitly declares "I need a new domain harness"

### Supplementary Mode (Adapter Exists + Coverage Gap)

- When an adapter exists but a gap is detected in SKILL.md's Coverage gap check
- When the adapter provides methodology (HOW) but lacks project-specific domain knowledge (WHAT)
- Example: research adapter + YouTube trend analysis, frontend adapter + an unfamiliar framework

In supplementary mode, the existing adapter is **not replaced**; only the missing domain knowledge is supplemented.

## Constraints

- Fully autonomous adapter generation is not supported by any official framework at this time.
  - Source: Anthropic Building Effective Agents, CrewAI Crafting Effective Agents
- Human-in-the-loop verification must be included.
- Adapters generated with this template are in "draft" status and must be augmented through a reflexion loop after actual use.

## Role Division in Hybrid Structure

- **Steps 1-3 (role definition, Coverage draft, user verification)**: Performed by the main agent. The main agent handles these directly since user interaction is required.
- **Step 4 (result reflection)**: The content confirmed by the main agent is passed to the harness generation sub-agent.
- **Step 5 (Reflexion loop)**: The main agent makes judgments based on the verification sub-agent's report.

## Procedure

### Step 1: Role Bootstrapping — Main Agent

Define the expert role for the domain in specific terms.

```markdown
- Role: [specific expert title] in [domain]
  - Example: "market research specialist analyst", "UX researcher", "portfolio investment strategist"
  - Generic titles like "Researcher" or "Analyst" are prohibited
- Goal: [outcome to achieve with this harness]
  - Example: "research deliverables are directly usable for investment decision-making"
- Backstory: [expertise and work philosophy of this role]
  - Example: "An analyst with 10 years of consumer goods market research who follows the principle of cross-verifying quantitative data with qualitative insights"
```

Source: CrewAI Crafting Effective Agents — Role-Goal-Backstory architecture

### Step 2: Domain Coverage Contract Draft Generation — Main Agent

The main agent generates a draft of the required Coverage items for the domain based on the role.

Required items:
- Core axes that must be covered in this domain (minimum 4)
- Common failure modes in this domain (minimum 3)
- Primary evidence sources for this domain (official documentation, standards, academic materials, etc.)
- Quality criteria for this domain (what indicates completion)

#### Non-Development Domain Coverage Contract Examples

**Market Research/Competitive Analysis:**
- Core axes: problem identification and severity, market size (TAM/SAM/SOM), competitive solution comparison (minimum 2), user segments, differentiation strategy
- Failure modes: confirmation bias (data cherry-picking), "idea without users" trap, market size overestimation
- Primary evidence sources: government statistics, industry reports, app store/review data, actual user interviews
- Quality criteria: directly usable for investment/execution decision-making

**Strategy/Business Planning:**
- Core axes: value proposition, revenue model, key resources/activities, customer relationships/channels
- Failure modes: executing without hypothesis validation, disconnect between revenue model and user value, infeasible scope
- Primary evidence sources: Lean Canvas/Business Model Canvas, same-industry case studies, financial benchmarks
- Quality criteria: actionable execution steps and validation metrics can be derived

**Unknown Domain (encountering a field for the first time):**
- Core axes: key success factors identified through domain research (minimum 4)
- Failure modes: most frequent failure causes from domain expert interviews or literature (minimum 3)
- Primary evidence sources: official standards, academic materials, and methodology documents from industry leaders in the field
- Quality criteria: "Can a domain expert look at the deliverable and use it directly in practice?"

### Step 3: User Verification (Human-in-the-loop) — Main Agent

The main agent presents the draft to the user and requests verification.

Question format:
```markdown
Please review the following Coverage items for this domain ([domain name]).

1. Core axes: [item1], [item2], [item3], [item4]
   - Are any items missing?
   - Are any items unnecessary?

2. Failure modes: [mode1], [mode2], [mode3]
   - Have you experienced any actual failure cases?

3. Primary evidence sources: [source1], [source2]
   - Are there other reference sources?

4. Quality criteria: [criterion1], [criterion2]
   - Are these criteria sufficient?
```

Rules:
- For items where the user answers "I don't know," the agent sets conservative defaults based on general standards for the domain.
- When conservative defaults are set, that fact is explicitly noted in the adapter.

### Step 4: Result Reflection — Passed to Sub-Agent

The main agent passes the content confirmed in Steps 1-3 (Role-Goal-Backstory, Coverage Contract, user-confirmed items) to the harness generation sub-agent.

**New mode**: The sub-agent generates harness deliverables + saves to `references/adapters/<new_task_type>.md`.

**Supplementary mode**: The sub-agent does not modify the adapter file but reflects the supplemented domain knowledge directly in the harness deliverables (`.claude/skills/harness-<domain>-<name>.md`). The existing adapter's methodology is preserved as-is.

Minimum structure when saving in new mode:

Adapter file minimum structure:
```markdown
# [Domain Name] Adapter

## Role-Goal-Backstory
## Coverage Contract
## Primary Evidence Sources
## Anti/Good Required Pair List
## Dry-Run Input/Output Examples
## Stack/Tool Branching (when applicable)
## Conservative Default Annotations
```

### Step 5: Reflexion Loop — Verification Sub-Agent + Main Agent

After the harness generation sub-agent completes, the verification sub-agent independently performs verification.

1. Verification sub-agent: verifies that the generated harness covers all domain core axes
2. Main agent: reviews the verification report and reports to the user if augmentation is needed
3. Main agent: decides whether to augment the adapter (adding/modifying Coverage items)

Source: Anthropic Skill authoring best practices (Claude A -> Claude B iteration)

## Promotion Criteria

If an adapter generated via bootstrap meets all of the following conditions, promotion to the TASK_INTAKE representative classification set is considered.

- Used in actual work 3 or more times
- Evidence has accumulated that it is difficult to describe with existing classifications
- The user agrees to the promotion
