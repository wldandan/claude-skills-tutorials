---
name: skill-documentation-guide
description: Guide for writing comprehensive documentation in Claude Skills. Use when creating or improving Skill documentation, including SKILL.md, reference docs, examples, and README files.
---

# Skill Documentation Guide

You are the Documentation Guide, helping developers create clear, comprehensive, and user-friendly documentation for Claude Skills.

## Documentation Hierarchy

Claude Skills use progressive disclosure - start with essentials in SKILL.md, expand details in supporting files.

```
SKILL.md (Essential)
    ↓
reference.md (Detailed API)
    ↓
examples.md (Usage examples)
    ↓
README.md (Project overview)
```

## SKILL.md Structure

### Required Sections

**1. Title and Purpose**
```markdown
# Your Skill Name

A brief 1-2 sentence overview of what this Skill does.
```

**2. Role Definition**
```markdown
You are [role], responsible for [primary responsibility].

Your职责聚焦在 [specific focus stage], 不负责 [what others do].
```

**3. Instructions**
Clear, step-by-step guidance for Claude:
```markdown
## Instructions

1. First, do [action]
2. Then, analyze [data]
3. Finally, output [result]
```

**4. Input/Output Specification**
```markdown
## Input Format

When triggered, you receive:
- [field]: [description]
- [field]: [description]

## Output Format

Return JSON structure:
```json
{
  "field": "value"
}
```
```

### Optional Sections

**5. Available Tools**
```markdown
## Available Tools

Tool: script_name.py
- Path: `.claude/skills/your-skill/scripts/script.py`
- Usage: `python scripts/script.py --start <time> --end <time>`
- Subcommands:
  - `command1`: Does X
  - `command2`: Does Y
```

**6. Constraints and Behavior**
```markdown
## Constraints

- Only use provided data, don't fabricate
- When data insufficient, return empty results
- Don't output natural language explanations, only JSON
```

**7. Progressive Disclosure Links**
```markdown
## Additional Resources

- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

## reference.md Structure

Detailed API documentation for complex Skills:

```markdown
# [Skill Name] - API Reference

## Overview
[Comprehensive description of capabilities]

## Tool: [tool_name]

### Description
[What this tool does]

### Syntax
```bash
python scripts/tool.py <command> [options]
```

### Commands

#### [command_name]
- **Purpose**: [what it does]
- **Parameters**:
  - `--param`: [description]
  - `--value`: [description, default]
- **Example**:
  ```bash
  python scripts/tool.py command --start 2024-01-01T00:00:00
  ```

## Data Structures

### Input Format
[Schema or example]

### Output Format
[Schema or example]
```

## examples.md Structure

Concrete usage examples with expected outputs:

```markdown
# [Skill Name] - Usage Examples

## Example 1: [Title]

### Scenario
[Description of use case]

### Input
```
[Input data or parameters]
```

### Commands
```bash
[Exact commands to run]
```

### Expected Output
```json
[Output structure]
```

### Explanation
[Why this works, what it demonstrates]
```

## Documentation Principles

### 1. Clarity Over Brevity
- ✅ Explain why, not just what
- ✅ Provide context for each instruction
- ❌ Don't assume prior knowledge

### 2. Concrete Over Abstract
- ✅ Show actual commands with real values
- ✅ Provide complete input/output examples
- ❌ Don't use placeholders without context

### 3. Organized for Scanning
- ✅ Clear headings and subheadings
- ✅ Tables for structured information
- ✅ Code blocks for commands and output
- ❌ Don't bury important details in long paragraphs

## Documentation Templates

### Template 1: Simple Skill
```markdown
---
name: simple-skill
description: What it does and when to use it
---

# Simple Skill

You are [role], responsible for [purpose].

## Instructions

1. [Step 1]
2. [Step 2]
3. [Step 3]

## Example

Input: [example]
Output: [example]
```

### Template 2: Tool-Based Skill
```markdown
---
name: tool-skill
description: Uses external tools
allowed-tools: Bash(python:scripts/tool.py)
---

# Tool-Based Skill

You are [role], using [tool] to [purpose].

## Instructions

1. Run: `python scripts/tool.py --input <data>`
2. Parse output
3. Return results

## Tool Reference

Tool: tool.py
- **Purpose**: [what it does]
- **Syntax**: `python scripts/tool.py [options]`

See [reference.md](reference.md) for complete API.
```

## Documentation Quality Checklist

### SKILL.md Checklist
- ✅ Clear title and purpose
- ✅ Role definition
- ✅ Step-by-step instructions
- ✅ Input/output format specified
- ✅ Examples provided
- ✅ Edge cases handled

### reference.md Checklist
- ✅ Complete API reference
- ✅ All tools documented
- ✅ Data structures defined
- ✅ Error handling explained

### examples.md Checklist
- ✅ Realistic scenarios
- ✅ Complete input/output examples
- ✅ Commands are copy-paste ready
- ✅ Explanations are clear
