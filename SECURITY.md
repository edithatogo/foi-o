# Security and safety policy

This project handles public records and process metadata, but the domain is legally and socially sensitive. Security issues include privacy leakage, unsafe agent authority, prompt-injection risks, poisoned tool descriptions, re-identification, and over-confident legal automation.

## Reportable issues

Please report:

- schemas that allow an agent to mark a legal decision as final without human certification;
- examples that expose unnecessary personal information;
- mappings that erase source uncertainty;
- prompt templates vulnerable to untrusted-document instruction following;
- provenance gaps that could mislead downstream systems;
- unsafe MCP/tool descriptions.

## Baseline safety stance

Agent outputs are process-support artefacts unless they are explicitly human-certified. A system built on this repo should treat autonomous grant/refusal/redaction/charging/complaint outcomes as invalid by default.
