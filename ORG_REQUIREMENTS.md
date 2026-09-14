# Organizational Requirements — Landing Page

Source of truth for the Copilot cross-check. Feed this file plus the Figma
screen to GitHub Copilot and ask for a coverage table.

> **Before the workshop:** the rows below are a working baseline, not Phoenix's
> approved standard. Replace anything marked `[לאימות]` with the organization's
> real policy wording, or delete the row. A cross-check against invented
> requirements teaches the wrong lesson.

## 1. Content and messaging

| ID | Requirement | Source |
|---|---|---|
| CNT-01 | Every page states the product name and the insuring entity. | `[לאימות]` |
| CNT-02 | A displayed premium is accompanied by a disclaimer that the final price depends on underwriting. | `[לאימות — רגולציה]` |
| CNT-03 | The primary call to action appears above the fold and is repeated once below. | Baseline |
| CNT-04 | No superlative claims ("הזול ביותר", "המהיר ביותר") without a dated source. | `[לאימות]` |

## 2. Forms and data collection

| ID | Requirement | Source |
|---|---|---|
| FRM-01 | Collect only fields required for the stated purpose; each additional field has a documented justification. | `[לאימות — פרטיות]` |
| FRM-02 | Sensitive identifiers (ID number, license plate) are masked on input and never echoed back in plain text. | `[לאימות]` |
| FRM-03 | Every required field has a visible required indicator **and** a defined validation message. | Baseline |
| FRM-04 | Marketing consent is opt-in, unchecked by default, with explicit wording naming the channels. | `[לאימות — דיוור]` |
| FRM-05 | A link to the privacy notice appears adjacent to the form, not only in the footer. | `[לאימות]` |

## 3. States and error handling

| ID | Requirement | Source |
|---|---|---|
| STA-01 | Each interactive element defines default, hover, focus, disabled and error states. | Baseline |
| STA-02 | Submission defines a loading state and both success and failure outcomes. | Baseline |
| STA-03 | Error messages state what went wrong and what to do next; no error codes shown to the customer. | Baseline |
| STA-04 | A partially completed form does not lose entered data on a failed submit. | Baseline |

## 4. Accessibility

| ID | Requirement | Source |
|---|---|---|
| ACC-01 | Text contrast meets WCAG 2.2 AA (4.5:1 body, 3:1 large text). | WCAG 2.2 AA |
| ACC-02 | Every input has a persistent visible label — placeholder text is not a label. | WCAG 2.2 AA |
| ACC-03 | Focus order follows the RTL reading order and focus is always visible. | WCAG 2.2 AA |
| ACC-04 | Meaning is never conveyed by color alone. | WCAG 2.2 AA |
| ACC-05 | Icons carry a text alternative or are marked decorative. | WCAG 2.2 AA |

## 5. Language and layout

| ID | Requirement | Source |
|---|---|---|
| LNG-01 | Full RTL layout: alignment, field order, icon direction, and numeric formatting. | Baseline |
| LNG-02 | Hebrew is the primary language; mixed Latin terms appear only where no accepted Hebrew term exists. | `[לאימות]` |
| LNG-03 | Dates in DD/MM/YYYY, currency with the ₪ symbol. | Baseline |

## 6. Brand and consistency

| ID | Requirement | Source |
|---|---|---|
| BRD-01 | Colors, typography and spacing come from the approved design system. | `[לאימות]` |
| BRD-02 | Logo placement, clear space and minimum size follow brand guidelines. | `[לאימות]` |
| BRD-03 | Button hierarchy is consistent: one primary action per view. | Baseline |

## The cross-check prompt

```text
You are assisting a system analyst. Two sources are available:
this requirements file, and the landing page screen read from Figma.

Produce a coverage table with one row per requirement ID:

| ID | Requirement | Matching element in Figma | Status | Gap / note |

Status is one of: Covered / Partial / Missing / Cannot determine from design.

Rules:
- Quote the Figma layer name you relied on. If you cannot name a layer,
  the status is "Cannot determine from design".
- Do not infer intent that is not written in either source. Anything you
  inferred goes in the note, marked "assumption to verify".
- Do not comment on visual taste. Only coverage of stated requirements.
- Requirements a static design genuinely cannot satisfy (for example
  behavior on submit) are "Cannot determine from design", not "Missing".

End with the three gaps carrying the highest business risk, and say why.
```

## What to watch for in the demo

- **"Cannot determine from design" is the interesting answer**, not a failure.
  It is exactly where an analyst adds value that the design file cannot.
- If Copilot marks something Covered without naming a layer, that is a
  hallucination — call it out live. It is a better teaching moment than a
  clean run.
- Follow-up worth showing: ask it to turn the Missing rows into draft
  requirement statements with acceptance criteria or input for the user-story
  agent from Lab 6.
