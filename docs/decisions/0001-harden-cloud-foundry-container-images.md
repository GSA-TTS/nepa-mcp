---
title: "Harden NEPA MCP container images for cloud.gov"
description: "Record the supply-chain and runtime controls for the 17 NEPA MCP Cloud Foundry images"
status: "proposed"
date: "2026-10-20"
decision_makers: ["NEPA MCP maintainers", "MCP Server Hub maintainers"]
category: "Deployment and Infrastructure"
nist_controls: ["CM-2", "CM-3", "CM-6", "SA-10", "SA-11", "RA-5", "SR-3", "SR-4", "SR-11"]
impact_level: "moderate"
ato_relevance: "yes-boundary"
risk_treatment: "mitigate"
---

# Harden NEPA MCP container images for cloud.gov

## Context and Problem Statement

The AWS MCP Server Hub launched sibling containers through a Docker socket, but
cloud.gov requires independently deployed Cloud Foundry applications. The 17
existing images also used mutable bases and dependency resolution, ran as root,
forced port 8080, exposed the repository root to the builder, and published by
default. How should the same source wrappers become reviewable deployment
artifacts for cloud.gov?

## Decision Drivers

- Cloud Foundry supplies the application port at runtime and provides no Docker socket.
- CM-2 and CM-6 require a controlled, reviewable runtime baseline.
- SR-3, SR-4, and SR-11 require traceable and reproducible component inputs.
- Least privilege requires avoiding a root runtime user.
- Publishing and deployment must be explicit human-approved actions.
- The additive `docker/` layer must continue to avoid changes to upstream server implementations.

## Considered Options

1. **Keep the AWS images unchanged** - fastest, but incompatible with dynamic ports and retains known supply-chain risks.
2. **Harden each existing wrapper independently** - preserves paths but duplicates release logic and invites drift.
3. **Use one parameterized Dockerfile and thin server wrappers** - preserve per-server images and source boundaries while sharing the complete runtime and publication policy.
4. **Build one image containing all servers** - fewer artifacts, but increases blast radius and weakens per-service isolation.

## Decision Outcome

Chosen option: **Use one parameterized Dockerfile and thin server wrappers**.
The 17 images use a digest-pinned Python base, lock-derived exact constraints,
numeric non-root runtime user, Cloud Foundry `PORT` passthrough, OCI provenance
labels, and a root build-context exclusion policy. A shared build helper
allowlists server identifiers and defaults to a local `linux/amd64` build;
publishing and the mutable `latest` tag each require an explicit flag.
Cloud.gov deployments reference the resulting image digest, not a mutable tag.

The `census` and `epa_aqs` images remain buildable for source parity but are not
deployed as shared cloud.gov applications until a per-user credential design is
approved.

### Positive Consequences

- Builds have immutable base provenance and exact Python dependency versions.
- Containers run with reduced privileges and accept the platform-assigned port.
- Accidental publication and accidental `latest` updates are prevented.
- The Docker builder no longer receives local credentials and unrelated state.
- Existing per-server image names and source wrappers remain stable.

### Negative Consequences

- Base digest and constraints updates become explicit maintenance work.
- Constraints pin exact versions but do not yet enforce package artifact hashes.
- Seventeen images still require build, scan, and smoke-test coverage.
- Local `linux/amd64` builds may require emulation on ARM workstations.

### Compliance Consequences

- Image digests, SBOMs, vulnerability scans, and verification transcripts must be retained with release evidence.
- Base and dependency refreshes require the same tests and review as application changes.
- The cloud.gov application manifests and catalog must use immutable image digests.
- This proposed record requires human maintainer and ISSO review before being marked accepted.

## Links

- [`../../docker/AGENTS.md`](../../docker/AGENTS.md)
- [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md)
- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
