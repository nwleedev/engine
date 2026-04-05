# Frontend Anti/Good Reference

## 1. 서버 상태 복제

나쁜 예시:

```tsx
const [profile, setProfile] = useState<User | null>(null);

useEffect(() => {
  fetch("/api/profile")
    .then((res) => res.json())
    .then(setProfile);
}, []);
```

좋은 예시:

```tsx
function ProfileScreen() {
  const profileQuery = useQuery({
    queryKey: ["profile"],
    queryFn: fetchProfile,
  });

  if (profileQuery.isLoading) return <Spinner />;
  return <ProfileCard profile={profileQuery.data} />;
}
```

의도:

- 서버 데이터를 로컬 state로 복제하지 않는다.
- Query 계층이 서버 상태의 단일 진실 공급원이 되게 한다.

## 2. useEffect fetch 남용

나쁜 예시:

```tsx
useEffect(() => {
  let cancelled = false;

  fetch(`/api/posts?tag=${tag}`)
    .then((res) => res.json())
    .then((posts) => {
      if (!cancelled) setPosts(posts);
    });

  return () => {
    cancelled = true;
  };
}, [tag]);
```

좋은 예시:

```tsx
const postsQuery = useQuery({
  queryKey: ["posts", tag],
  queryFn: () => fetchPosts(tag),
});
```

의도:

- fetch를 effect 생명주기에 묶지 않는다.
- 캐시, 로딩, 오류, 재검증을 데이터 계층에서 처리한다.

## 3. 폼 초기값 분산 주입

나쁜 예시:

```tsx
const form = useForm<UserForm>();

useEffect(() => {
  if (!profile) return;
  form.setValue("name", profile.name);
  form.setValue("email", profile.email);
}, [profile, form]);
```

좋은 예시:

```tsx
const form = useForm<UserForm>({
  values: profile
    ? { name: profile.name, email: profile.email }
    : undefined,
});
```

또는:

```tsx
useEffect(() => {
  if (!profile) return;
  form.reset({ name: profile.name, email: profile.email });
}, [profile, form]);
```

의도:

- 초기값 주입 시점을 문서로 명확히 고정한다.
- `setValue` 반복 호출로 필드별 동기화를 하지 않는다.

## 4. FSD slice 내부 구현 직접 import

나쁜 예시:

```tsx
import { useAuthModel } from "@/features/auth/model/useAuthModel";
import { AuthButton } from "@/features/auth/ui/AuthButton";
```

좋은 예시:

```tsx
import { useAuth, AuthButton } from "@/features/auth";
```

의도:

- 다른 slice의 내부 구현 경로에 직접 접근하지 않는다.
- slice 외부에서는 public API만 사용하게 제한한다.

## 5. FSD cross-import로 feature 조립

나쁜 예시:

```tsx
import { addToCart } from "@/features/cart/model/addToCart";

export function ProductCard() {
  return <button onClick={() => addToCart("sku-1")}>Add</button>;
}
```

좋은 예시:

```tsx
import { ProductCard } from "@/entities/product";
import { AddToCartButton } from "@/features/add-to-cart";

export function ProductListItem() {
  return (
    <div>
      <ProductCard />
      <AddToCartButton productId="sku-1" />
    </div>
  );
}
```

의도:

- 같은 layer의 다른 slice를 직접 엮어서 흐름을 만들지 않는다.
- 상위 layer에서 조립하거나, 공통 도메인 로직은 더 적절한 layer로 이동한다.
