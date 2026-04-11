# Source Analysis Adapter

## Purpose

When harness-engine generates or augments a large-scale codebase exhaustive analysis harness, this adapter is additionally applied after the common `research` phase to enforce the minimum contract for the `source-analysis` task_type.

## Coverage Contract

A source analysis harness must include the following items.

### Required Axes

1. **Scope Sealing**
   - Input root and comparison root
   - Actual file count
   - Whether exclusions exist
2. **File Inventory**
   - Per-file role, subsystem, and import/export summary
3. **Symbol Catalog**
   - Function/class/method/type/constant declarations
   - Explicit handling of files with 0 symbols
4. **Subsystem Map**
   - Top-level responsibilities and major entry points
5. **Public Surface Diff**
   - Correspondence between the original source and the public distribution/documentation
6. **Coverage Ledger**
   - Match between actual file count and catalog count
   - Confirmation of 0 omissions

### Items That Must Be Finalized in the Contract Packet

- Input source root
- Comparison target root
- Conservative defaults for symbol extraction method
- Internal signal tag criteria
- Provenance separation rules

## Primary Evidence Sources

1. Actual source tree
2. Public distributions or public bundles
3. Official documentation
4. Existing investigation documents and public issues

Rules:

- Do not declare a source-analysis harness when no actual source tree exists.
- Absence of a public bundle is evidence, but not a conclusion in itself.

## Anti/Good Minimum Required Pairs

### Scope

| Case | Anti | Good |
|---|---|---|
| Sampling estimation | Reading only some files and judging the whole | Calculating the total file count and cataloging all files |
| Silent exclusion | Not recording files that were not read | Explicitly noting the reason for exclusion or 0-symbol status in the ledger |

### Catalog

| Case | Anti | Good |
|---|---|---|
| Missing file descriptions | Leaving only a path listing | Recording file roles and subsystems |
| Method omission | Listing only classes and omitting internal methods | Recording declared symbols by type |

### Interpretation

| Case | Anti | Good |
|---|---|---|
| Provenance mixing | Using public evidence and non-public artifacts at the same strength | Separating provenance and verdict strength |
| Bundle string over-interpretation | Confirming policy/feature based solely on string existence | Verifying code paths and context together |

## Dry-Run Input/Output Examples

### Positive Case

**Input**: "Read the entire source tree provided by the vendor and organize the differences between internal branches and the public surface."

**Expected Output**:

- Total file count calculation
- File/symbol catalog
- Public distribution diff
- Coverage ledger

### Negative Case

**Input**: "Let's just read a few representative files and draw a rough conclusion."

**Expected Output**:

- Warning that source-analysis cannot be applied
- Exhaustive analysis scope and minimum deliverable requirements

## Design Rationale

- Existing research harnesses are strong in claim/evidence management but do not enforce an exhaustive source catalog.
- For large codebase analysis, a coverage ledger and shard structure are needed as a separate minimum contract.
