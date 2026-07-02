# Specification: PSC reporting profile and aggregate reports

## Objective

Map event logs to PSC reporting categories, explicitly flag non-derivable metrics, and produce sample aggregate reports.

## GitHub Linkage

- Repository: https://github.com/edithatogo/foi-o
- Issue: https://github.com/edithatogo/foi-o/issues/15
- Project: https://github.com/users/edithatogo/projects/10

## Requirements

- Define an explicit PSC reporting profile over FOI-O NZ event logs and request profiles.
- Identify which PSC metrics are derivable, partially derivable, or not derivable from public FYI data.
- Produce deterministic sample aggregate reports from committed fixtures.
- Ensure reporting outputs do not imply official government reporting or legal certification.

## Acceptance Criteria

- Reporting mappings are validated against schema or deterministic table contracts.
- Sample aggregate reports include derivability notes and caveats.
- Tests cover derivable, partially derivable, and non-derivable metrics.
- Documentation states the difference between public FYI-derived indicators and official PSC reporting.
