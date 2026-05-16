<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/references/comment-specs-by-stack.md -->

# Comment Specs by Stack
<!-- Compatibility title token: # Comment Specs By Stack -->

Use this reference after `comment-writing/SKILL.md` detects the target language, documentation generator, and project convention. Prefer the project's existing convention when it is explicit and compatible with the stack's tooling.

## Code clarity before comments

Before adding a comment that explains unclear code, check whether the approved scope allows the code to explain itself instead.

Prefer:

- Better symbol names instead of comments that decode abbreviations.
- Named constants instead of repeated magic numbers or literal strings.
- Named intermediate variables instead of dense nested expressions.
- Extracted functions when a condition, transformation, or guard has domain meaning.
- Enums or tagged values instead of unclear boolean or string mode arguments.
- Typed options, classes, or structs when several arguments form one concept.
- Smaller units when comments are only compensating for mixed responsibilities.

Boundary: do not turn a documentation or comment task into unrelated refactoring. If the clearer-code change is outside the approved scope, report it as a recommended follow-up or ask for approval.

Use each official source anchor as the starting point for stack-specific verification:

- Google C++ Style Guide, implementation comments and function argument comments: https://google.github.io/styleguide/cppguide.html#Implementation_Comments
- Google Documentation Best Practices, meaningful names and inline comments: https://google.github.io/styleguide/docguide/best_practices.html
- Google Python Style Guide, block and inline comments: https://google.github.io/styleguide/pyguide.html#385-block-and-inline-comments
- Google TypeScript Style Guide, comments and documentation: https://google.github.io/styleguide/tsguide.html#comments-and-documentation

## Stack-specific formats

| Stack | Preferred format | Applies to | Notes | Official source |
| --- | --- | --- | --- | --- |
| Java | Javadoc | Public modules, packages, classes, constructors, methods, fields, and records. | Place documentation comments immediately before declarations. Use summary text and relevant block tags such as `@param`, `@return`, `@throws`, and `@deprecated` when they add information. | https://docs.oracle.com/en/java/javase/17/docs/specs/javadoc/doc-comment-spec.html |
| Kotlin | KDoc | Public Kotlin declarations and library APIs. | KDoc starts with `/**` and supports Javadoc-style block tags plus Markdown. Dokka consumes KDoc. | https://kotlinlang.org/docs/kotlin-doc.html |
| JavaScript/TypeScript | JSDoc/TSDoc for API documentation; ordinary comments for implementation details. | Exported APIs, top-level exports, complex implementation details, and JavaScript type hints. | TypeDoc is a documentation generator, not a comment format. Avoid restating types that TypeScript already exposes. | https://jsdoc.app/, https://tsdoc.org/, and https://typedoc.org/documents/Doc_Comments.html |
| Python | Docstrings following PEP 257 and project style. | Public modules, packages, classes, functions, methods, and non-obvious logic. | Use a triple double-quoted docstring. Follow the project's Google, NumPy, or reST style when present. Put implementation comments near tricky code. | https://peps.python.org/pep-0257/ |
| Go | Go doc comments. | Packages and exported symbols. | Package comments introduce the package. Exported symbol comments should be complete sentences and work with `go doc` and pkg.go.dev. | https://go.dev/doc/comment |
| Rust | rustdoc comments. | Public crates, modules, items, traits, structs, enums, functions, and examples. | Use `///` for following items and `//!` for enclosing items. Markdown is conventional, and examples may become doctests. | https://doc.rust-lang.org/reference/comments.html |
| C# | XML documentation comments. | Public types, members, parameters, returns, exceptions, and generated API docs. | Use `///` XML comments and tags such as `<summary>`, `<param>`, `<returns>`, and `<exception>` when relevant. | https://learn.microsoft.com/dotnet/csharp/language-reference/xmldoc/ |
| PHP | PHPDoc. | Classes, methods, functions, properties, parameters, returns, exceptions, and tooling metadata. | Prefer project PHPDoc conventions and avoid tags that duplicate native types unless tooling requires them. | https://docs.phpdoc.org/ |
| Ruby | RDoc or YARD. | Public classes, modules, methods, attributes, and generated docs. | Follow the project's RDoc or YARD convention. Keep examples short and close to public APIs. | https://ruby.github.io/rdoc/ and https://yardoc.org/ |
| Swift | Documentation comments. | Public symbols and API docs. | Use Swift documentation comment syntax recognized by Xcode and DocC. Include parameters, returns, throws, and important discussion when relevant. | https://www.swift.org/documentation/docc/ |
| Objective-C | Documentation comments or project/platform convention. | Public headers, classes, protocols, properties, methods, functions, and constants. | Prefer project or current Apple DocC/Xcode symbol documentation conventions when available. HeaderDoc-style docs are legacy; keep public header docs usable without implementation files. | https://developer.apple.com/documentation/xcode/writing-documentation, https://developer.apple.com/documentation/xcode/writing-symbol-documentation-in-your-source-files, and archived legacy HeaderDoc reference: https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/HeaderDoc/ |
| C/C++ | Doxygen or project convention. | Public headers, nontrivial classes, functions, algorithms, invariants, and file-level APIs. | Use Doxygen only if the project uses it. Put API usage docs near declarations and implementation rationale near tricky implementation code. | https://www.doxygen.nl/manual/docblocks.html |
| SQL | Dialect-specific schema comments such as PostgreSQL `COMMENT ON`, plus migration notes. | Tables, columns, views, functions, migrations, and operational constraints. | Check the database dialect first. PostgreSQL supports `COMMENT ON`; MariaDB/MySQL comment syntax and support differ. Migration comments should explain compatibility, rollback, data impact, and operational ordering. | https://www.postgresql.org/docs/current/sql-comment.html, https://mariadb.com/docs/server/reference/sql-statements/comment-syntax, and https://mariadb.com/docs/server/server-usage/tables/create-table |
| Shell | Function headers and usage comments. | Scripts, functions, required environment, side effects, and destructive commands. | Document expected inputs, outputs, exit behavior, environment variables, and safety assumptions. | https://google.github.io/styleguide/shellguide.html |
| Terraform | Variable/output descriptions and module README. | Variables, outputs, modules, providers, resources with non-obvious operational constraints. | Use `description` on variables and outputs. Module README should explain inputs, outputs, examples, and operational assumptions. | https://developer.hashicorp.com/terraform/language/values/variables |
| Dockerfile | `LABEL` and non-obvious build step comments. | Image metadata, unusual build steps, security constraints, cache-sensitive ordering. | Use labels for metadata. Comment only non-obvious `RUN`, cache, user, permission, or supply-chain decisions. | https://docs.docker.com/reference/dockerfile/ |
| Kubernetes YAML | Annotations, labels, and manifest operation notes. | Workload identity, ownership, rollout, scheduling, security, and operational behavior. | Prefer standard labels and annotations. Use comments for local operational hazards that are not representable as schema fields. | https://kubernetes.io/docs/concepts/overview/working-with-objects/annotations/ |
| OpenAPI | `description` fields. | Operations, parameters, request bodies, responses, schemas, security, and error behavior. | Descriptions should help consumers integrate without reading implementation code. | https://spec.openapis.org/oas/latest.html |
| GraphQL | Schema descriptions and comments supported by the server/tooling. | Types, fields, arguments, enums, directives, and mutations. | Prefer schema descriptions that appear in introspection and generated docs. | https://spec.graphql.org/ |
| Proto | Proto comments and option fields where supported. | Messages, fields, services, RPCs, enums, and compatibility-sensitive changes. | Document wire compatibility, reserved fields, units, defaults, and migration constraints. | https://protobuf.dev/programming-guides/proto3/ |

## Review questions

- Does the selected format match the detected stack and project convention?
- Can a caller use the public API without reading implementation code?
- Does the comment explain purpose, constraints, side effects, errors, failure modes, or operational hazards?
- Is the comment close enough to the code or schema it explains?
- Would a better name, type, small function, enum, or option object remove the need for the comment inside the approved scope?
- Does any comment reveal secrets, credentials, internal endpoints, private data, or sensitive operational details?
- Are debt markers actionable with owner, reason, removal condition, or tracking reference when project convention allows them?
