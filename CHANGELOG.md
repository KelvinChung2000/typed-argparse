# CHANGELOG


## v0.1.0 (2026-04-30)

### Features

- Initial public release of typed-argparse
  ([`5e9017e`](https://github.com/KelvinChung2000/typed-argparse/commit/5e9017e0b209fc606462b63845563bb7579899e7))

A small annotation-driven CLI helper that converts typed function signatures into
  argparse-compatible parsers, aimed at simple CLIs, scripting tools, and lightweight LLM-facing
  command wrappers.

Public API: - build_parser() / build_parser_from_function() build an argparse.ArgumentParser from a
  typed function signature - Argument and Option metadata for use inside Annotated[] hints -
  unwrap(), call(), parse_and_call() for namespace-to-call dispatch - build_subcommand_parser() for
  small multi-command CLIs - with_annotated() optional cmd2 integration (typed-argparse[cmd2])

Type inference covers int, float, str, bool, Path, Decimal, Enum, Literal, Optional / X | None, and
  list/set/tuple collections of those. Multi-word parameter names produce dashed flags (e.g.
  --dry-run) while the dest and Python parameter stay underscored. *args and **kwargs are skipped
  during parser construction.

The core package has no required third-party runtime dependencies.
