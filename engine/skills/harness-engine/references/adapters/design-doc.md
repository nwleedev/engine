# Design Document Task Adapter

## Purpose

When harness-engine generates or augments a design document domain harness, this adapter is additionally applied after the common `research` phase to enforce the **minimum contract** specific to the design document task_type.

Design documents include RFCs, ADRs (Architecture Decision Records), system design documents, API design documents, migration plans, and similar artifacts.

## Coverage Contract

A design document harness must include the following items. If any are missing, the harness is deemed incomplete.

### Required Axes (All Design Documents)

1. **Problem Definition**
   - Current state (As-Is) and pain points
   - Trigger for the change — what made this design necessary
   - Success criteria (in measurable form)
   - Non-functional requirements (performance, security, scalability, cost, etc.)
2. **Alternative Analysis**
   - At least 3 alternatives (including maintaining the status quo)
   - Pros/cons comparison matrix per alternative
   - Risk and cost estimates for each alternative
   - Explicit rejection rationale
3. **Decision Record**
   - Selected alternative and selection rationale
   - Decision participants/stakeholders
   - Decision date
   - Re-evaluation conditions (under what circumstances should this decision be revisited)
4. **Implementation Plan**
   - Phased milestones
   - Dependencies and prerequisites
   - Gradual rollout strategy (when applicable)
   - Estimated timeline range
5. **Rollback/Recovery Plan**
   - Failure scenario definitions
   - Rollback procedures
   - Data recovery strategy (when applicable)
   - Monitoring/alerting criteria

### Items That Must Be Investigated in the Project Contract Packet

- Document type (RFC, ADR, system design, API design, migration)
- Target audience (engineers, executives, cross-team)
- Existing architecture/system status
- Organization's decision-making process (whether approval is required)
- Whether existing design document templates/conventions exist

## Primary Evidence Sources

Design document harness rules use the following sources as primary evidence:

1. Official documentation for the target technology (architecture guides, best practices)
2. Standard design patterns (GoF, DDD, CQRS, Event Sourcing, etc. when applicable)
3. Organization's existing ADR/RFC archive
4. Academic materials (distributed systems, security, and other relevant areas)

Supplementary materials:
- Context7 MCP: quick reference for technology stack-specific documentation
- Sequential Thinking MCP: structuring complex alternative analysis

## Anti/Good Minimum Required Pair List

### Problem Definition

| Case | Anti Content | Good Content |
|---|---|---|
| Solution-first | Starting with "We will adopt X" without stating why it is needed | Describing in order: current problem -> motivation -> success criteria |
| Vague success criteria | "Improve performance" | "P95 response time under 200ms, throughput over 1000 RPS" |
| Missing scope | Describing only functional requirements, no non-functional requirements | Explicitly stating non-functional requirements: performance, security, cost, operational complexity, etc. |

### Alternative Analysis

| Case | Anti Content | Good Content |
|---|---|---|
| Single alternative | Describing only one technology to adopt | At least 3 alternatives (including status quo) + comparison matrix |
| Biased comparison | Highlighting only the pros of the preferred alternative | Analyzing pros, cons, risks, and costs of each alternative equally |
| No rejection rationale | Listing alternatives without stating why they were not selected | Stating specific rejection rationale for each rejected alternative |

### Decision Record

| Case | Anti Content | Good Content |
|---|---|---|
| Implicit decision | Describing only the implementation direction without decision rationale | Explicit decision statement + rationale + participants + date |
| Permanent decision | Absolute decision without re-evaluation conditions | Specifying re-evaluation trigger conditions ("re-evaluate when traffic increases 10x") |

### Implementation Plan

| Case | Anti Content | Good Content |
|---|---|---|
| Big-bang deployment | Switching the entire system at once | Phased milestones, gradual rollout (canary, blue-green, etc.) |
| Ignoring dependencies | Establishing a timeline without verifying prerequisites | Dependency graph, critical path identification |

### Rollback/Recovery

| Case | Anti Content | Good Content |
|---|---|---|
| No rollback plan | Assuming "there won't be problems" and not planning for rollback | Rollback procedures per failure scenario + data recovery strategy |
| Deployment without monitoring | Relying on manual verification after deployment | Automated alerting criteria + rollback trigger definition |

## Dry-Run Input/Output Examples

### Positive Case: RFC Structure Verification

**Input**: "Write a design document for separating the authentication system from the monolith into a microservice."

**Expected Output (direction the harness should guide)**:

- Require defining current monolith authentication pain points first
- At least 3 alternatives (maintain monolith, separate auth service, BFF pattern, etc.)
- Comparison matrix per alternative (complexity, security, latency, operational cost)
- Migration phase plan + rollback strategy

### Negative Case: Solution-First Detection

**Input**: "Write a design document for adopting Kafka."

**Expected Output (pattern the harness should block)**:

- Solution-first -> detected as anti-pattern
- Require problem definition starting with "why Kafka is needed"
- Require comparison of alternatives (RabbitMQ, SQS, status quo, etc.)

## Document Type Branching

The emphasis of required axes varies depending on the design document type:

| Type | Emphasized Axes | Axes That May Be Relaxed |
|---|---|---|
| **RFC** | Alternative analysis, decision record | Detailed implementation plan (written separately after RFC approval) |
| **ADR** | Decision record, re-evaluation conditions | Detailed implementation plan (decision record is the core of ADR) |
| **System Design** | Implementation plan, rollback/recovery | — (all axes required) |
| **API Design** | Interface contract, backward compatibility | Internal implementation details |
| **Migration Plan** | Implementation plan, rollback/recovery, data conversion | — (all axes required) |

Finalize the document type in the contract packet first, then focus on that type's emphasized axes.

## Design Rationale

- Coverage Contract required axes: cross-analysis of Google Design Docs, Stripe RFC process, and ADR (Architecture Decision Record) standard structure
- Minimum 3 alternatives for analysis: standard decision-making framework to prevent cognitive bias (including status quo enforces the "do nothing" alternative)
- Anti/Good required pairs: based on recurring defect patterns from actual design reviews
