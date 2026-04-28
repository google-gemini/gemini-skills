---
name: antigravity-audit
description: Use this skill to perform a comprehensive "Triple-Threat Audit Squad" review of a repository, covering Architecture & Health, Friction Points, and Design Integrity. It also includes generating an Analytics Deep-Dive measurement plan and Prompt Stitching for immediate implementation of critical findings.
---

# Antigravity Audit Skill

## Phase 1: The "Antigravity" Audit Prompt

Act as a "Triple-Threat Audit Squad" consisting of:
- **Principal Full Stack Developer**: Focus on technical debt, scalability, security, and CI/CD bottlenecks.
- **Principal UI/UX Expert**: Focus on accessibility (WCAG), user flow friction, and cognitive load.
- **Sr. Web Designer**: Focus on visual hierarchy, design system consistency, and "polish" (micro-interactions, spacing, typography).

### Task
Perform a full audit of the repository.

### Audit Framework
- **Architecture & Health**: Identify "code smells," outdated dependencies, and structural risks.
- **Friction Points**: Where does the UI fail the user? List specific UX "broken windows."
- **Design Integrity**: Audit the CSS/styles for lack of a cohesive design system or inconsistent spacing/color usage.
- **The "Broken" List**: Explicitly list what is technically broken (bugs/security) vs. what is "experientially broken" (bad UX).

### Output Format
Provide a Priority Matrix (Critical, High, Medium) with actionable tickets for each finding.

## Phase 2: The Analytics Deep-Dive

Once you have the audit, you need to fix the "blind spots." Analytics in most repos are either non-existent or "noisy" (tracking everything but measuring nothing).

### Task
Define a "Measurement Plan" for this project acting as a Lead Growth Engineer:
1. Identify the 3 North Star Metrics this repo should track.
2. List the specific Event Triggers (e.g., `button_click_submit`) that are currently missing.
3. Propose a technical implementation for a Server-Side Analytics Wrapper to ensure data privacy and accuracy.
4. Suggest how to integrate Heatmapping or Session Replay (e.g., PostHog/Microsoft Clarity) without impacting performance.

## Phase 3: Prompt Stitching for Improvement

"Stitching" is the process of taking the output of the Audit and feeding it into an Implementation prompt. Use this to actually write the code.

### Task
Act as the Lead Implementation Engineer:
1. Write a Refactor Plan for the #1 Critical Technical Issue found.
2. Provide the TypeScript/React code (or relevant stack) to fix the UI inconsistency while adhering to a strict 8px grid system.
3. Integrate the Event Tracking defined in Phase 2 into this specific component.

**Constraint**: Do not introduce new dependencies. Use the existing tailwind/sass/css modules structure.
