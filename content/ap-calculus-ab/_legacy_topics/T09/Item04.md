---
id: T09-Item04
difficulty: F
calculator: no-calc
type: frq
---
The table gives values for differentiable functions $f$ and $g$ and their derivatives at selected values of $x$.

| $x$ | $f(x)$ | $g(x)$ | $f'(x)$ | $g'(x)$ |
|:---:|:------:|:------:|:-------:|:-------:|
| 0   | 2      | 3      | 4       | 1       |
| 1   | 3      | 4      | 5       | 3       |
| 2   | 5      | 1      | 6       | 3       |
| 3   | 4      | 2      | 7       | 2       |
| 4   | 1      | 5      | 8       | 4       |

Find the value of $\frac{d}{dx}[f(g(x))]$ at $x = 2$. Show the work that leads to your answer.

## Answer
15

## Explanation
By the chain rule:
$$\frac{d}{dx}[f(g(x))] = f'(g(x)) \cdot g'(x)$$

Evaluate at $x = 2$:

**Step 1:** Find $g(2)$ from the table: $g(2) = 1$

**Step 2:** Find $f'(g(2)) = f'(1)$ from the table: $f'(1) = 5$

**Step 3:** Find $g'(2)$ from the table: $g'(2) = 3$

**Step 4:** Multiply: $f'(1) \cdot g'(2) = 5 \cdot 3 = 15$

Therefore, $\frac{d}{dx}[f(g(x))]\big|_{x=2} = \mathbf{15}$.

Note: The table contains extra information (values at $x = 0, 3, 4$ and values of $f$ and $g$ themselves) that is not needed for this computation. A common error is to look up $f'(2)$ instead of $f'(g(2)) = f'(1)$.
