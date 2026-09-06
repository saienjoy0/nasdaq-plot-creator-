# NEW SKILL INTEGRATION ARCHITECTURE v1

## Purpose

Integrate new independent decision layers without replacing existing Story Engine, Fox, Entertainment Critic, Visual Intelligence, or Production Reliability systems.

## Pipeline

```
Project Auditor
        |
        v
Editorial Director
        |
        v
Causal Research
        |
        v
Story Plan
        |
        v
Story Engine
        |
        v
Audience Retention Critic
        |
        v
Entertainment Critic
        |
        v
Final Production
        |
        v
Visual Intelligence
        |
        v
Renderer / Acceptance
```

## Responsibility Boundary

### Project Auditor

Input:
- repository state
- skills
- designs
- tests
- workflows

Output:
- architecture map
- missing capability report
- duplicate capability report
- risk report

### Editorial Director

Input:
- candidate topics
- research summary
- market context

Output:
- why now
- audience reason
- recommended angle
- reject decision when weak

### Audience Retention Critic

Input:
- story package
- script draft

Output:
- opening strength
- curiosity gap
- scene retention risk
- emotional progression review

## Non-goals

Do not duplicate:
- Story Engine narrative construction
- Entertainment Critic final judgment
- Visual Director rendering decisions
- Reliability validation

## Design Principle

Add editorial intelligence before production rather than increasing generation complexity.
