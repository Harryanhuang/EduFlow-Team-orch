---
id: T09-Item05
difficulty: S
calculator: no-calc
type: mcq
---
What is $\frac{d}{dx}[\ln(\sin x)]$?

## Options
A) $\frac{1}{\sin x}$
B) $\cot x$
C) $\tan x$
D) $\frac{\cos x}{\ln(\sin x)}$

## Answer
B) $\cot x$

## Explanation
Apply the chain rule. Recall that $\frac{d}{du}[\ln u] = \frac{1}{u}$ for $u > 0$.

Let $u = \sin x$, so we are differentiating $\ln u$.

**Step 1:** Differentiate the outer function:
$$\frac{d}{du}[\ln u] = \frac{1}{u} = \frac{1}{\sin x}$$

**Step 2:** Differentiate the inner function:
$$\frac{du}{dx} = \frac{d}{dx}[\sin x] = \cos x$$

**Step 3:** Multiply by the chain rule:
$$\frac{d}{dx}[\ln(\sin x)] = \frac{1}{\sin x} \cdot \cos x = \frac{\cos x}{\sin x}$$

**Step 4:** Recognize the trigonometric identity:
$$\frac{\cos x}{\sin x} = \cot x$$

The answer is **$\cot x$**.

Common errors:
- (A) Forgetting to multiply by the derivative of the inner function ($\cos x$).
- (C) Reversing numerator and denominator: $\frac{\sin x}{\cos x} = \tan x$.
- (D) Applying the chain rule incorrectly by putting $\ln$ in the denominator of the inner derivative factor.
