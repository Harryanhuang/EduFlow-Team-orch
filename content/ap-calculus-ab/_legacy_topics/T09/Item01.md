---
id: T09-Item01
difficulty: F
calculator: no-calc
type: mcq
---
The table above gives values for differentiable functions $f$ and $g$ and their derivatives. If $h(x) = f(g(x))$, what is the value of $h'(2)$?

| $x$ | $f(x)$ | $g(x)$ | $f'(x)$ | $g'(x)$ |
|:---:|:------:|:------:|:-------:|:-------:|
| 1   | 3      | 4      | 5       | 2       |
| 2   | 4      | 5      | −3      | 2       |
| 3   | 5      | 2      | 1       | 4       |
| 4   | 2      | 1      | −1      | 3       |
| 5   | 1      | 3      | −2      | −1      |

## Options
A) −6
B) −4
C) 3
D) 10

## Answer
B) −4

## Explanation
By the chain rule, if $h(x) = f(g(x))$, then:

$$h'(x) = f'(g(x)) \cdot g'(x)$$

Evaluate at $x = 2$:

**Step 1:** Find $g(2)$ from the table: $g(2) = 5$

**Step 2:** Find $f'(g(2)) = f'(5)$ from the table: $f'(5) = -2$

**Step 3:** Find $g'(2)$ from the table: $g'(2) = 2$

**Step 4:** Apply the chain rule: $h'(2) = f'(5) \cdot g'(2) = (-2)(2) = -4$

The answer is **−4**.

Common errors:
- (A) Using $g'(5) = -1$ instead of $g'(2) = 2$: $(-2)(-1) = 2$, or confusing signs.
- (C) Using $f'(2)$ instead of $f'(g(2))$: $f'(2) \cdot g'(2) = (-3)(2) = -6$, then sign error.
- (D) Using $f'(2)$ and forgetting $g'$: $f'(2) + g'(2) = -3 + 2 = -1$, or $f'(2) \cdot g(2) = (-3)(5) = -15$, etc.
