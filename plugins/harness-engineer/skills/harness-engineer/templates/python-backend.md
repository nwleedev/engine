---
domain: python-backend
language: auto
keywords: [function, class, api, endpoint, query, db, database, fastapi, django, flask]
file_patterns: ["*.py", "app/**/*.py", "api/**/*.py", "src/**/*.py"]
updated: 2026-04-18
---

# Python Backend Harness

## Purpose
This file defines the **ideal structure standard**, not the current project state.

## Core Rules

- [ ] Type hints required — all function parameters and return values
- [ ] Catch specific exception types — no bare `except Exception`
- [ ] DB queries via ORM or parameter binding (no raw SQL string concatenation)
- [ ] Never access env vars via `os.environ.get` directly — use a config module
- [ ] Tests use fixtures/mocks, not a real DB

## Pattern Examples

### Type Hints

<Good>
```python
def get_user(user_id: int) -> dict[str, str]:
    return {"id": str(user_id), "name": "Alice"}
```
</Good>

<Bad>
```python
def get_user(user_id):
    return {"id": user_id, "name": "Alice"}
```
No type hints — errors undetectable until runtime
</Bad>

---

### Exception Handling

<Good>
```python
try:
    result = db.query(User).filter_by(id=user_id).one()
except NoResultFound:
    raise HTTPException(status_code=404, detail="User not found")
```
</Good>

<Bad>
```python
try:
    result = db.query(User).filter_by(id=user_id).one()
except Exception:
    pass  # silences all exceptions — impossible to debug
```
</Bad>

## Anti-Pattern Gate

```
Using `except Exception`?           → Replace with specific exception type
Function missing type hints?        → Add parameter and return type annotations
Concatenating SQL strings?          → Replace with ORM or parameter binding
```
