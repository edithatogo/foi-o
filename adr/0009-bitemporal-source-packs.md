# Adopt bitemporal jurisdiction source packs

**Status:** Proposed  
**Date:** 2026-07-09

## Context

FOI-O V2 must add empirical and multi-jurisdiction capability without discarding mature implementation surfaces or overstating public evidence.

## Decision

Resolve legal sources at event time using effective and observation time, version relationships, hashes, calendars, authority identity history, and rights metadata.

## Consequences

- Legal assertions can be reproduced against the source version effective for an event and the version actually observed by the system.
- Jurisdiction profiles must publish effective intervals, observation timestamps, content hashes, version relationships, and source rights.
- Missing effective dates or unresolved source conflicts block confirmed legal conclusions and enter the source-review queue.
- Source-pack maintenance becomes a release responsibility independent of ontology schema releases.
