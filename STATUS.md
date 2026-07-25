# Artifact Status

Paper: “Suborbital and Orbital Real-Time Localization of Gamma-Ray Bursts via Utility-Guided Coordination”

## Intended badges

The authors intend to apply for the following EMSOFT 2026 artifact badges:

- **Available**
- **Reviewed**
- **Reproducible**

## Rationale

### Available

The artifact consists of two persistently archived components:

1. the source code, environment specifications, precomputed results, analysis notebook, documentation, and accepted paper version, archived as a version-specific snapshot of the artifact repository; and
2. the large detector models and transient datasets, distributed separately through Zenodo with a published checksum.

The corresponding persistent identifiers are:

> **Artifact DOI:** TODO
>
> **Artifact Dataset DOI:** https://doi.org/10.5281/zenodo.21497891

Continued development will take place in the following GitHub repository:

> **GitHub repository:** https://github.com/Daisy0419/GRB-Search-Pipeline

### Reviewed

The artifact provides:

- a short path that regenerates Figures 4–11 from the distributed results;
- a complete path that regenerates the training and evaluation results; and
- an optional path for rerunning the platform-sensitive mapping benchmark.

The required commands, inputs, output locations, and expected outputs are documented in `README.md`.

### Reproducible

The artifact includes the author-created code, methods, environment specifications, simulated inputs, and analysis workflow needed for an independent evaluator to regenerate the computational results. The complete workflow is documented in README Sections 1–4.

## Scope and limitations

- Figures 1–3 are explanatory diagrams rather than experiment outputs.
- Exact timing values are platform-sensitive. The reference hardware is
  specified in `REQUIREMENTS` and `README.md`.
- Sections 1–3 require Linux ARM64 (`aarch64`).
- The optional Intel portion of Figure 4 requires Linux x86-64.
- The full experiment is computationally expensive; approximate runtimes are
  listed in `REQUIREMENTS`.
