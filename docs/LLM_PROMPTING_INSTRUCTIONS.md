"""
System: General
Module: LLM Prompting Instructions
Purpose: Define how to create prompting plans and task breakdowns for feature development or debugging
"""
# LLM Prompting Instruction Guide

This guide explains how to create precise prompting plans for ChatGPT-5 sessions used in feature development or debugging. Always tailor prompts to the current repository and keep them minimal, actionable, and compliant with Suno Automation standards.

## Core Workflow
- **Study First:** Review all relevant project files, configuration, and documentation before drafting any prompt. Never rely on assumptions.
- **Clarify Scope:** Confirm the exact feature or defect context, required entry points, and documented constraints.
- **Think Hard:** Craft the leanest plan that fulfills the request without overengineering. Keep SRP, YAGNI, and the Minimum Viable Approach in mind.

## Task and Prompt Breakdown
1. Identify the minimal set of sub-tasks required to accomplish the request.
2. Split each sub-task into its own LLM prompt so the conversation stays focused and iterative.
3. Ensure the plan remains understandable to a junior developer; avoid unexplained shortcuts or implied steps.
4. Order prompts logically (discover -> design -> implement -> verify) and keep each prompt tightly scoped.
5. Explicitly request the necessary file contents or confirmation of absence before coding.
6. Remember this is a prompting plan; articulate steps so the assistant can execute them sequentially.

## XML Prompt Template
Use the following XML-styled template for every ChatGPT-5 interaction. Embed the mandatory quality paragraph inside the `<quality>` element; do **not** place it outside the prompt or as a trailing note.

```xml
<task>
  <role>You are a very helpful senior developer that will help me with my tasks/request. Do not overengineer solutions. Make the explanations comprehensive and easy to understand.</role>
  <objective>[Concise statement of the specific sub-task]</objective>
  <instructions>
    <step>Ask for the latest contents (or confirm non-existence) of [required files] before proceeding.</step>
    <step>Study the provided files and supporting documentation thoroughly before coding.</step>
    <step>Request clarifications whenever requirements, constraints, or expectations are unclear instead of making assumptions.</step>
    <step>[Implementation or analysis directives adhering to project standards and naming conventions.]</step>
    <step>Break the solution into minimal, testable changes while following the Minimum Viable Approach.</step>
    <step>Explain reasoning and next steps in language that remains accessible to a junior developer.</step>
  </instructions>
  <contextRequest>Always obtain the relevant context/code/files instead of assuming or relying on assumptions.</contextRequest>
  <quality>Before you respond, develop an internal rubric for what defines a "world-class" and "industry-standard" answer to my request (task, analysis, or problem solving). Then internally iterate and refine the draft until it scores top marks against your rubric. Provide only the final perfected output. Always provide a comprehensive and detailed breakdown. Always think hard about the given topic, problem, and the solution. Always flag the responses that you are not confident so that I can research it further. Always use industry standard, best practices, and professional recommendations when programming. Always search and use the latest documentations and information regarding programming technologies as of the date of the conversation. Always ask for further clarifications whenever requirements, constraints, or expectations are unclear instead of relying on assumptions. Always keep the prompting plan understandable and approachable for a junior developer.</quality>
  <meta>Flag any parts of the response you are not confident about so they can be reviewed.</meta>
</task>
```

## Mandatory Quality Paragraph
- The text inside the `<quality>` element is required verbatim for every prompt.
- Never move, duplicate, or restate the paragraph outside the XML wrapper.
- If the template needs additional guidance, add new `<step>` entries or adjacent elements; do not relocate the quality paragraph.

## Additional Guidance
- Remind the LLM that all variables, constants, and files must respect project naming conventions and file headers. Use the established patterns if the language lacks defaults.
- Keep each prompt actionable by referencing specific files, functions, or modules.
- Encourage the LLM to request clarifications whenever gaps appear rather than assuming.
- Defer linting/tests until core functionality exists, then mention validation steps explicitly.
- Reassess the prompting plan after each LLM response and adjust subsequent prompts if new information appears.

Use this document as the authoritative reference when preparing LLM prompting plans for feature delivery or debugging within this repository.
