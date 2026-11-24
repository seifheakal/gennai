# Prompts and planning inputs

The inputs used to build this project with Claude Code, kept verbatim as a record. Targets and quality labels written in them (coverage percentages, "Championship A+", line counts) were goals given to the coding assistant, not measured results; the measured results are in the root README.

| File | Used for |
|---|---|
| `course_brief.pdf` | The university course brief: phases, model constraint (free-tier, open-source or local LLMs only) and grading pillars. |
| `project_plan.md` | The original project plan written before implementation (architecture, phases, chosen free-tier model). |
| `phase1_claude_prompt.md` | Prompt for building Phase 1 (page exploration and locator generation). |
| `phase1_claude_template.md` | Shorter copy-paste version of the Phase 1 prompt. |
| `phase2_master_prompt.txt` | Main prompt for Phase 2 (test design with EP, BVA, state combinations, prioritisation, feedback loop). |
| `phase2_detailed_specification.txt` | Phase 2 algorithm and architecture specification given alongside the master prompt. |
| `phase2_implementation_guide.txt` | Phase 2 layer-by-layer build plan and data models. |
| `phase2_part2.txt` | Follow-up prompt to finish the remaining Phase 2 layers. |
| `phase3-build-plan.txt` | Build plan for Phase 3 (test code generation, Page Objects). |
| `phase3-full-build.txt` | Prompt to build all Phase 3 layers in one pass. |
| `phase4-full-build-plan.txt` | Build plan for Phase 4 (execution, results, reporting). |
| `phase4_optimal_prompt.txt` | Longer Phase 4 "build now" prompt covering all six planned layers. |
| `phase4_send_to_claude.txt` | Shorter Phase 4 prompt prepared for sending to Claude. |
| `FINALIZATION_PROMPT.md` | The task used with Claude Code (Opus) to turn the course version into this repo. |
