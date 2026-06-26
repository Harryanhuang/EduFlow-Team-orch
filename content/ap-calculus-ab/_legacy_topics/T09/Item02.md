---
id: T09-Item02
difficulty: F
calculator: no-calc
type: mcq
---
What is the derivative of $y = \sin(\cos x)$?

## Options
A) $-\cos(\cos x)$
B) $-\sin x \cdot \cos(\cos x)$
C) $\cos x \cdot \cos(\cos x)$
D) $-\sin x \cdot \sin(\cos x)$

## Answer
B) $-\sin x \cdot \cos(\cos x)$

## Explanation
Apply the chain rule. Let $u = \cos x$, so $y = \sin u$.

**Step 1:** Differentiate the outer function with respect to $u$:
$$\frac{dy}{du} = \cos u = \cos(\cos x)$$

**Step 2:** Differentiate the inner function with respect to $x$:
$$\frac{du}{dx} = -\sin x$$

**Step 3:** Multiply by the chain rule:
$$\frac{dy}{dx} = \frac{dy}{du} \cdot \frac{du}{dx} = \cos(\cos x) \cdot (-\sin x) = -\sin x \cdot \cos(\cos x)$$

The answer is **$-\sin x \cdot \cos(\cos x)$**.

Common errors:
- (A) Forgetting to multiply by the inner derivative $(-\sin x)$ entirely.
- (C) Using $\sin' = \cos$ for the inner function instead of $\cos' = -\sin$ (wrong inner derivative).
- (D) Differentiating the outer function as $\sin$ instead of $\cos$ (i.e., $\sin' \neq \sin$).
