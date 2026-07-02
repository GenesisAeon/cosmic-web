# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.1] - 2026-07-01

### Fixed
- **Breaking namespace collision:** removed `genesis_os/` from the wheel — it
  overwrote `genesis-os` when both were installed via `genesis-os[full-stack]`,
  breaking `from genesis_os import GenesisOS`.
- Moved `CosmicWebSimulator` (PM N-body) to `cosmic_web.universums_sim`; re-export
  from `cosmic_web` top-level.

## [1.0.0] - 2026
### Added
- Initial v1.0.0 release as part of the GenesisAeon ecosystem-wide 1.0.0
  milestone.
- Standardized release tooling: `.zenodo.json`, GitHub Actions release
  workflow (`.github/workflows/release.yml`), `RELEASE_GUIDE.md`,
  `CONTRIBUTING.md`, issue/PR templates.

### Changed
- Project metadata (`pyproject.toml`) normalized: version, license,
  authors, `requires-python`, and GenesisAeon-ecosystem dependency pins
  bumped to their actual released floors (`entropy-table>=2.0.0`,
  `implosive-genesis>=1.0.0`, and other stack bindings to `>=1.0.0`).

## v0.1.0 (2026-03-19)

- Initial release: kosmisches Netz mit Barabási–Albert-Power-Law-Graph + Emergenz-Simulation
- CLI `cweb render`, `cweb simulate --nodes 30 --steps 10`, `cweb dashboard --port 8050`
- Interaktives Plotly/Dash-Dark-Theme-UI (Netzwerk + Bar + Scatter)
- Qualitäts-Fixes: seed-Reproduzierbarkeit, single-pass Iteration, precompute Nachbarn
- Docs + mkdocs --strict clean
- 15/15 tests, ruff + uv lock grün (sonification-Version-Fix auf 0.0.10)
- DOI: [10.5281/zenodo.19108819](https://doi.org/10.5281/zenodo.19108819)
