"""
System: Crime Patrol
Module: Coding Agent Task Planning
Purpose: Outline how to architect implementation plans and task breakdowns for coding agents executing repository work
"""
# Coding Agent Task Planning Guide

This guide explains how to architect concise, execution-ready plans for coding agents working in the Crime Patrol repository. Use it whenever you need to design implementation or debugging tasks that will be executed directly, rather than scripted as LLM conversations.

## Core Workflow
- **Study First:** Inspect relevant files, configuration, prior discussions, and open changes before drafting a plan. Never rely on assumptions.
- **Clarify Scope:** Confirm the requested feature, defect, or investigation target. Capture required entry points, constraints, and acceptance expectations.
- **Minimum Viable Approach:** Outline the leanest path that satisfies the request while respecting SRP, YAGNI, and naming conventions.
- **Evidence Gathering:** Note any open questions, missing inputs, or approval requirements so the executor resolves them up front.

## Planning Principles
- **Single Responsibility Steps:** Each plan item must pursue one cohesive outcome (for example, Add input validation or Cover scenario with tests).
- **Progressive Breakdown:** Decompose any large or complex objective into smaller single-responsibility tasks before execution.
- **Sequenced Progression:** Order tasks logically: discovery → design → implementation → validation → wrap-up.
- **Observable Deliverables:** Phrase steps so completion can be verified (new file, updated function, passing test suite, documented decision).
- **Repository Alignment:** Call out mandatory standards such as file headers, variable prefixes, constants for magic values, API versioning, and Result-pattern error handling.

## Task Decomposition Guidelines
1. Baseline assessment: identify existing files or modules that require updates or confirmation.
2. Design decisions: capture minimal design choices (data flows, interfaces, naming) needed before code changes start.
3. Implementation steps: break work into discrete code edits, each scoped to a single responsibility and bounded file set.
4. Validation steps: specify linting, typing, tests, or manual checks required for confidence.
5. Documentation and cleanup: include updates to docs, changelogs, or follow-up tickets when applicable.
6. Risk flags: highlight uncertainties or dependencies; instruct the agent to surface them before proceeding.

## Plan Checklist Template
Use the following structure as a starting point and tailor wording to the specific request.

Plan Name: [Concise objective]

Context Summary:
- Repository areas: [modules or files]
- Key constraints: [naming rules, MVA, Result pattern, headers, etc.]
- Open questions: [list each item or state None]

Assumptions:
- [Document each assumption; request clarification when uncertain]

Task Steps:
1. Discovery – gather file references, existing behaviour, and configuration details.
2. Design – record the minimal design choice or confirmation needed before coding.
3. Implementation – describe the single-responsibility code change to apply.
4. Validation – list the tests, linting, and manual checks required.
5. Documentation and wrap-up – capture docs, notes, or risk follow-ups.

If any task step remains broad or couples multiple outcomes, split it into separate entries before starting work.

Validation Checklist:
- All naming conventions and prefixes observed.
- Required file headers present in new or edited files.
- Result-pattern error handling used for expected failures.
- API endpoints versioned with /api/v{n}/... when touched.
- Tests or scripts executed and outcomes recorded.

Risk and Confidence:
- Provide a confidence rating per step (High, Medium, or Low).
- Flag any areas that need subject-matter review or a follow-up ticket.

## Quality Requirements
- Maintain clarity so a junior developer can execute the plan without guesswork.
- Cite specific files or functions using repository-relative paths such as src/module/file.ts:42.
- Avoid ambiguous verbs like handle or update unless paired with explicit artefacts or acceptance criteria.
- Always request missing information rather than assuming; embed those requests in the plan.
- Reference validation commands explicitly (for example, npm run lint, npm run typecheck, ruff check).

## Mandatory Quality Directive
Include the following statement verbatim in planning templates and any agent-facing outputs so the quality expectations remain explicit:

"<quality>
Before you respond, develop an internal rubric for what defines a "world-class" and "industry-standard" answer to my request (task, analysis, or problem solving). Then internally iterate and refine the draft until it scores top marks against your rubric. Provide only the final perfected output. Always provide a comprehensive and detailed breakdown. Always think hard about the given topic, problem, and the solution. Always flag the responses that you are not confident about so that I can research it further. Always use industry standard, best practices, and professional recommendations when programming. Always search and use the latest documentations and information regarding programming technologies as of the date of the conversation. Always ask for further clarifications whenever requirements, constraints, or expectations are unclear instead of relying on assumptions.
</quality>"

## Plan Maintenance
- Revisit and adjust the plan after each major discovery or stakeholder update.
- Track status (pending, in progress, completed) to maintain visibility.
- Document deviations from the plan with rationale and updated steps.
- When handing off, include the latest status, risks, and outstanding questions.

Use this document as the authoritative standard when preparing actionable task plans for coding agents within the Crime Patrol project.
