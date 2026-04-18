---
domain: python-backend
language: auto
keywords: [함수, function, class, 클래스, api, endpoint, 엔드포인트, 쿼리, query, db, 데이터베이스]
updated: 2026-04-18
---

# Python Backend Harness

## 이 파일의 용도
현재 프로젝트 상태가 아닌 **이상적인 구조의 기준**입니다.

## 핵심 규칙

- [ ] 타입 힌트 필수 — 함수 파라미터·반환값 모두
- [ ] 예외는 구체적 타입으로 — `except Exception` 금지
- [ ] DB 쿼리는 ORM 또는 파라미터 바인딩 사용 (SQL 인젝션 방지)
- [ ] 환경변수는 `os.environ.get` 직접 접근 금지 — 설정 모듈을 통해 접근
- [ ] 테스트는 실제 DB 대신 fixture/mock 사용

## 패턴 사례

### 타입 힌트

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
타입 힌트 없음 — 런타임 전까지 오류 탐지 불가
</Bad>

---

### 예외 처리

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
    pass  # 모든 예외를 무시 — 디버깅 불가
```
</Bad>

## 안티패턴 게이트

```
except Exception 쓰려는가?   → 구체적 예외 타입으로 교체
타입 힌트 없는 함수인가?     → 파라미터·반환값 타입 추가
SQL을 문자열로 조립하는가?   → ORM 또는 파라미터 바인딩으로 교체
```
