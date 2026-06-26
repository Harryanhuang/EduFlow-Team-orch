---
id: T09-Item03
difficulty: F
calculator: calc
type: mcq
---
If $f(x) = e^{3x^2 + 1}$, what is $f'(x)$?

## Options
A) $e^{3x^2 + 1}$
B) $6x \cdot e^{3x^2 + 1}$
C) $3x^2 \cdot e^{3x^2 + 1}$
D) $e^{6x}$

## Answer
B) $6x \cdot e^{3x^2 + 1}$

## Explanation
Apply the chain rule. Recall that $\frac{d}{du}[e^u] = e^u$.

Let $u = 3x^2 + 1$, so $f(x) = e^u$.

**Step 1:** Differentiate the outer function:
$$\frac{d}{du}[e^u] = e^u = e^{3x^2 + 1}$$

**Step 2:** Differentiate the inner function:
$$\frac{du}{dx} = \frac{d}{dx}[3x^2 + 1] = 6x$$

**Step 3:** Multiply by the chain rule:
$$f'(x) = e^{3x^2 + 1} \cdot 6x = 6x \cdot e^{3x^2 + 1}$$

The answer is **$6x \cdot e^{3x^2 + 1}$**.

Common errors:
- (A) Forgetting to multiply by the derivative of the inner function (treating the exponent as a constant).
- (C) Using only the $x^2$ coefficient instead of differentiating the full inner expression.
- (D) Confusing $e^{3x^2 + 1}$ with a different function; this is not a valid differentiation result.
