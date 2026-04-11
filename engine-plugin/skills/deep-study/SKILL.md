---
name: deep-study
description: "Use when the user wants to learn a domain from scratch, needs structured teaching, or says they have no knowledge about a topic. Provides step-by-step curriculum, assessments, and progressive learning."
user-invocable: true
---

# Deep Study

A skill for conducting systematic lectures from the ground up when the user lacks knowledge in a specific domain.

## When to Use

- When the user says "I don't know this area" or "I want to learn from scratch"
- When learning a new framework, library, or architecture pattern
- When domain expertise is needed (healthcare, finance, logistics, etc.)
- When a harness skill exists but the user doesn't understand its content

## Learning Procedure

### Phase 1: Assessment

Assess the user's current level before starting.

1. List 5 core concepts of the domain and ask the user's familiarity with each.
2. Ask about related experience (similar domain experience, professional experience, prior learning).
3. Confirm learning objectives (development-level? decision-making level? expert level?).
4. Based on assessment results, determine the learning level:
   - **Novice**: Doesn't know domain terminology → start with terms and basic concepts
   - **Beginner**: Knows terms but not relationships → start with structure and flow
   - **Intermediate**: Knows structure but weak in practical application → start with patterns and case studies
   - **Reinforcement**: Knows most things but weak in specific areas → focus on weaknesses

### Phase 2: Curriculum Design

Create a learning plan based on assessment results.

1. Create a list of **Units** (minimum 3, maximum 10).
2. Each Unit includes:
   - Core concepts (1-3)
   - Learning objectives (what the user can do after completing this Unit)
   - Prerequisites (relationship to previous Units)
3. Determine learning order (dependency-based).
4. Present the curriculum to the user and adjust.

### Phase 3: Lecture Delivery

Conduct each Unit with the following structure:

1. **Introduction**: Explain why this Unit matters and where it's used in practice.
2. **Core Concept Explanation**: Explain using analogies, diagrams, and real-world examples. Connect to concepts the user already knows.
3. **Examples**: Demonstrate concepts with specific code/scenarios.
4. **Comprehension Check**: Ask the user to explain concepts in their own words. Or a short quiz.
5. **Practice (optional)**: Find parts of the project code where these concepts are applied.
6. **Summary**: Summarize the Unit's key content in 3 lines.

### Phase 4: Evaluation and Progress Recording

After each Unit completion:
1. Ask for self-assessment on a 3-level scale (Understood / Roughly understood / Need review).
2. Record evaluation results in agent memory.
3. Mark Units needing review as review targets for the next session.

## Teaching Principles

- **Concrete → Abstract**: Show examples first, then derive general principles.
- **Connected Learning**: Connect new knowledge to what the user already knows.
- **Active Participation**: Prioritize questions and dialogue over one-way explanations.
- **Appropriate Depth**: Cover only the depth needed for learning objectives. Avoid excessive detail.
- **Failure Tolerance**: Explain why wrong answers are wrong and guide correct thinking processes.

## Domain Harness Integration

If a harness skill for the domain (`.claude/skills/harness-*.md`) exists, use it as curriculum foundation material. If no harness exists, suggest creating a new harness via harness-engine after learning has progressed.

The specific discovery/loading procedure is defined in the domain-professor agent.

## Prohibitions

- Do not proceed to the next Unit without the user's confirmation.
- Do not assume "everything is understood" without a comprehension check.
- Do not force advanced content unrelated to learning objectives.
- Do not teach unsourced claims as facts.
