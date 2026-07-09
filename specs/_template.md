# <Component Name> Specification

Brief description of the component's purpose and what problem it solves.

## Stack

- List allowed runtime dependencies here (e.g., Python 3.x, pandas, numpy)
- Only dependencies listed here may be used by the builder

## Inputs

<!-- Describe the data this component receives — shapes, formats, sources. -->
<!-- Do NOT specify function signatures; the builder decides those. -->

- Describe input 1: what it is, its format/type, where it comes from
- Describe input 2: ...

## Outputs

<!-- Describe what this component produces — data shapes, formats, destinations. -->

- Describe output 1: what it is, its format/type
- Describe output 2: ...

## Behavior

<!-- Describe the transformation rules, business logic, and edge-case handling. -->
<!-- Focus on WHAT happens, not HOW the code should be structured. -->

- Rule 1: Describe a behavioral rule or transformation
- Rule 2: ...

## Acceptance Criteria

<!-- The tester derives ALL test cases from this section. -->
<!-- Each criterion should be a concrete input → expected output example. -->

- [ ] Given X, the component produces Y.
- [ ] Given edge case Z, the component produces W.

## Non-goals

<!-- The auditor checks that implementation does NOT include anything listed here. -->

- This component does NOT handle ...
- Out of scope: ...

## Invariants

<!-- The auditor verifies these hold true across the entire implementation. -->

- Invariant 1: A property that must always hold (e.g., "No function may access data from a future timestamp").
- Invariant 2: ...
