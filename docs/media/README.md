# Media Assets

This directory contains README and documentation visuals for EduFlow Team Orch.

## Current README Set

| Asset | Source | Export | Purpose |
| --- | --- | --- | --- |
| `eduflow-team-orch-hero.svg` | editable SVG | `eduflow-team-orch-hero.png` | README hero image |
| `runtime-architecture.svg` | editable SVG | `runtime-architecture.png` | Runtime architecture diagram |
| `workflow-guided-delivery.svg` | editable SVG | `workflow-guided-delivery.png` | Workflow delivery pipeline |

The README uses SVG files because they are small, readable in git diffs, and render crisply on GitHub. PNG exports are kept for platforms that do not render SVG well.

## Regenerate PNG Exports

```bash
rsvg-convert -w 1600 -h 900 docs/media/eduflow-team-orch-hero.svg -o docs/media/eduflow-team-orch-hero.png
rsvg-convert -w 1600 -h 900 docs/media/runtime-architecture.svg -o docs/media/runtime-architecture.png
rsvg-convert -w 1600 -h 900 docs/media/workflow-guided-delivery.svg -o docs/media/workflow-guided-delivery.png
```

## Design Notes

- Keep labels short enough to read at GitHub README width.
- Prefer neutral technical diagrams over marketing-style artwork.
- Keep SVG source as the editable canonical asset; regenerate PNG after SVG edits.
