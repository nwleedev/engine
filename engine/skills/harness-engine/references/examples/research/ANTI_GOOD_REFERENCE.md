# Research Anti/Good Reference

## 1. Blog as Sole Evidence

Bad example:

```md
Conclusion: Framework X is the fastest.
Evidence: One blog post said it was the fastest.
```

Good example:

```md
Current most likely interpretation: Framework X is likely fast under specific benchmark conditions.

Evidence:
- Performance description from official documentation
- Actual benchmark code or publicly reproducible materials
- Blog post used only as supplementary explanation
```

Intent:

- Use blogs only as supplementary evidence.
- Support technical conclusions with official documentation or actual code.

## 2. Terminating at First Search Results

Bad example:

```md
Since Service A is mentioned most on the first page of search results, conclude it is the industry standard.
```

Good example:

```md
Build a candidate list from initial search results,
then expand search breadth across failure modes, cost/performance, permissions/security, and real operational case perspectives.
```

Intent:

- Do not end a search in only one direction.
- If perspectives are missing, additionally broaden the research scope.

## 3. Mixing Conclusions and Evidence in One Paragraph

Bad example:

```md
This tool has good long session resumption. It has a resume feature and other articles say it's good too.
```

Good example:

```md
Claim: This tool has strong support for long session resumption.

Evidence:
- Official documentation explicitly mentions resume or session continuation features.
- Actual usage examples or CLI references exist.

Limits:
- Resumption quality may vary depending on project structure or session history management approach.
```

Intent:

- Separate claims from evidence.
- Also include limitations or counter-evidence.
