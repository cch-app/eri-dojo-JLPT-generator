---
name: tailwind-nextgen-ui-ux
description: Designs modern, accessible UI/UX using Tailwind CSS as the default styling approach. Use for any UI changes: new components, layout work, visual polish, responsive design, and interaction states.
---

# Tailwind CSS “next‑gen” UI/UX

## When to use

Use this skill for **any** work that affects UI/UX (components, pages, layouts, styling, responsiveness, micro-interactions).

## Default approach

- Use **Tailwind CSS** utilities for styling.
- Keep UI consistent via shared spacing/typography/color patterns.
- When a pattern repeats, **extract a reusable component** instead of duplicating long class strings.

## UI/UX checklist (apply by default)

- **Responsive**: design mobile-first; ensure layouts adapt at common breakpoints.
- **Accessible**: visible focus states, sufficient contrast, semantic HTML, keyboard-friendly interactions.
- **States**: handle hover/focus/active/disabled/loading/empty/error states.
- **Consistency**: align padding, radii, shadows, and typography across the UI.
- **Simplicity**: prefer clear hierarchy and readable density over decorative complexity.

## Implementation notes

- Prefer composition of small UI primitives (Button, Input, Card, Dialog, etc.).
- Avoid ad-hoc inline styles unless Tailwind cannot express the requirement.
- If Tailwind config/design tokens exist, follow them; don’t invent new token conventions without being asked.

