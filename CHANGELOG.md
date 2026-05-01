# CHANGELOG


## v0.2.0 (2026-05-01)

### Chores

- Ci fix
  ([`d5b4446`](https://github.com/KelvinChung2000/typed-argparse/commit/d5b444686219ef4d934fd020187d390f968817bb))

### Features

- **builder**: Infer nargs="?" for positional args with defaults; add const metadata
  ([`f0f153e`](https://github.com/KelvinChung2000/typed-argparse/commit/f0f153e11ece72bc42433c3684808e62246ad3fa))

Two related improvements aimed at making typed-argparse-gen a drop-in replacement for hand-written
  argparse parsers in cmd2-based CLIs.

1. Positional arguments with defaults now infer ``nargs="?"``. Previously, ``Annotated[Path,
  Argument(help_text="...")] = Path()`` built a positional that argparse still flagged as required,
  which contradicts the signature. The builder now mirrors the long-standing argparse pattern: a
  positional with a default is "optional" via ``nargs="?"``. Existing behaviour for collections and
  explicit ``Argument(nargs=...)`` is unchanged.

2. ``Argument`` and ``Option`` accept a ``const`` keyword that is forwarded to
  ``parser.add_argument(...)``. This unblocks the common pattern where an option may be passed bare
  (defaulting to a sentinel) or with a value, e.g.::

Annotated[OptMode | None, Option("--optimise", nargs="?", const=OptMode.BALANCE)] = None

``const`` defaults to a private sentinel so the keyword is omitted entirely when the user does not
  pass it, preserving argparse's own default of ``None``.

Both changes are covered by new tests in TestPositionalDefaults and TestConstMetadata.


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
