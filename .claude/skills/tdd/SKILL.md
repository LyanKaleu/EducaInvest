---
name: "tdd"
description: "Test-driven development. Use when building features or fixing bugs test-first, when red-green-refactor comes up, or when the user wants integration tests."
---

# Test-Driven Development

TDD is the red → green loop. This skill is the reference that makes that loop produce tests worth keeping: what a good test is, where tests go, the anti-patterns, and the rules of the loop. Every section applies on every cycle: consult them before and during the loop, not after.

When exploring the codebase, read `GLOSSARY.md` (if it exists) so test names and interface vocabulary match the project's domain language, and respect ADRs in the area you're touching.

## What a good test is

Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good test reads like a specification: "user can checkout with valid cart" tells you exactly what capability exists, and it survives refactors because it doesn't care about internal structure.

Characteristics of a good test:

- Tests behavior that users or callers care about
- Uses the public API only
- Survives internal refactors
- Describes WHAT, not HOW
- One logical assertion per test

GOOD: test through the real interface.

```typescript
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

BAD: bypasses the interface to verify through a side channel.

```typescript
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});
```

Better: verify through the interface.

```typescript
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

## Seams: where tests go

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

**Test only at pre-agreed seams.** Before writing any test, write down the seams under test and confirm them with the user. No test is written at an unconfirmed seam. You can't test everything, so agreeing the seams up front is how testing effort lands on the critical paths and complex logic instead of every edge case.

Ask: "What's the public interface, and which seams should we test?" Give each proposed seam a one-line note on what it catches and what it misses.

When the shape of that interface is itself in question (how deep the module is, where the seam belongs, what the interface should expose), use a `codebase-design` skill if one is available, as a reference to consult, not a session to run.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, asserts on call counts or order, or verifies through a side channel (querying the database instead of using the interface). The tell: the test breaks when you refactor but behavior hasn't changed.
- **Tautological**: the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand the same way, a constant asserted equal to itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth: a known-good literal, a worked example, the spec.
  - BAD: `const expected = items.reduce((sum, i) => sum + i.price, 0); expect(calculateTotal(items)).toBe(expected);`
  - GOOD: `expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);`
- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests go insensitive to real changes, and you commit to test structure before understanding the implementation. Work in **vertical slices** instead: one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you.

## When to mock

Mock at **system boundaries** only: external APIs (payment, email), databases (sometimes; prefer a test DB), time and randomness, the file system (sometimes). Don't mock your own classes or modules, internal collaborators, or anything you control.

Design boundaries to be easy to mock:

1. **Use dependency injection.** Pass external dependencies in rather than creating them inside the function.
2. **Prefer SDK-style interfaces over generic fetchers.** One specific function per external operation (`getUser`, `getOrders`, `createOrder`) instead of one generic `fetch(endpoint, options)` with conditional logic. Each mock then returns one specific shape, test setup needs no conditionals, and it is clear which endpoints a test exercises.

## Rules of the loop

- **Red before green.** Write the failing test first, then only enough code to pass it. Don't anticipate future tests or add speculative features.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Refactoring is not part of the loop.** It belongs to the review stage (use a `code-review` skill if available), not the red → green implementation cycle.