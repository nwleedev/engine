# Frontend Anti/Good Reference

## 1. Server State Duplication

Bad example:

```tsx
const [profile, setProfile] = useState<User | null>(null);

useEffect(() => {
  fetch("/api/profile")
    .then((res) => res.json())
    .then(setProfile);
}, []);
```

Good example:

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

Intent:

- Do not duplicate server data into local state.
- Let the query layer be the single source of truth for server state.

## 2. useEffect Fetch Overuse

Bad example:

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

Good example:

```tsx
const postsQuery = useQuery({
  queryKey: ["posts", tag],
  queryFn: () => fetchPosts(tag),
});
```

Intent:

- Do not tie fetches to the effect lifecycle.
- Handle cache, loading, errors, and revalidation in the data layer.

## 3. Scattered Form Default Value Injection

Bad example:

```tsx
const form = useForm<UserForm>();

useEffect(() => {
  if (!profile) return;
  form.setValue("name", profile.name);
  form.setValue("email", profile.email);
}, [profile, form]);
```

Good example:

```tsx
const form = useForm<UserForm>({
  values: profile
    ? { name: profile.name, email: profile.email }
    : undefined,
});
```

Or:

```tsx
useEffect(() => {
  if (!profile) return;
  form.reset({ name: profile.name, email: profile.email });
}, [profile, form]);
```

Intent:

- Fix the default value injection timing clearly in the documentation.
- Do not synchronize field by field with repeated `setValue` calls.

## 4. Direct Import of FSD Slice Internal Implementation

Bad example:

```tsx
import { useAuthModel } from "@/features/auth/model/useAuthModel";
import { AuthButton } from "@/features/auth/ui/AuthButton";
```

Good example:

```tsx
import { useAuth, AuthButton } from "@/features/auth";
```

Intent:

- Do not directly access another slice's internal implementation paths.
- Restrict external access from outside a slice to the public API only.

## 5. Feature Assembly via FSD Cross-Import

Bad example:

```tsx
import { addToCart } from "@/features/cart/model/addToCart";

export function ProductCard() {
  return <button onClick={() => addToCart("sku-1")}>Add</button>;
}
```

Good example:

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

Intent:

- Do not create flows by directly coupling slices from the same layer.
- Assemble in a higher layer, or move shared domain logic to a more appropriate layer.
