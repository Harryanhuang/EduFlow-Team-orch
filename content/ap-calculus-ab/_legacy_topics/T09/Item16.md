---
id: T09-Item16
difficulty: F
calculator: no-calc
type: mcq
---
Let $f(x) = |\sin(x)|$.

Which of the following is true?

## Options
A) $f'\!\left(\dfrac{\pi}{4}\right) = \dfrac{\sqrt{2}}{2}$ and $f'(\pi)$ exists and equals $-1$
B) $f'\!\left(\dfrac{\pi}{4}\right) = \dfrac{\sqrt{2}}{2}$ and $f'(\pi)$ does not exist
C) $f'\!\left(\dfrac{\pi}{4}\right) = -\dfrac{\sqrt{2}}{2}$ and $f'(\pi)$ does not exist
D) $f'\!\left(\dfrac{\pi}{4}\right) = 0$ and $f'(\pi)$ does not exist

## Answer
B) $f'\!\left(\dfrac{\pi}{4}\right) = \dfrac{\sqrt{2}}{2}$ and $f'(\pi)$ does not exist

## Explanation
**Step 1: Find $f'(\pi/4)$.**

Near $x = \pi/4$, we have $\sin(x) > 0$ (since $\pi/4$ is in the first quadrant). Therefore, in a neighborhood of $\pi/4$:

$$f(x) = |\sin(x)| = \sin(x)$$

So:

$$f'\!\left(\frac{\pi}{4}\right) = \cos\!\left(\frac{\pi}{4}\right) = \frac{\sqrt{2}}{2}$$

**Step 2: Determine whether $f'(\pi)$ exists.**

At $x = \pi$, we have $\sin(\pi) = 0$. To check differentiability, examine the left and right derivatives:

For $x$ slightly less than $\pi$ (e.g., $x \in (\pi/2, \pi)$): $\sin(x) > 0$, so $f(x) = \sin(x)$ and $f'(x) = \cos(x)$.

$$f'_-(\pi) = \lim_{x \to \pi^-} \cos(x) = \cos(\pi) = -1$$

For $x$ slightly greater than $\pi$ (e.g., $x \in (\pi, 3\pi/2)$): $\sin(x) < 0$, so $f(x) = -\sin(x)$ and $f'(x) = -\cos(x)$.

$$f'_+(\pi) = \lim_{x \to \pi^+} [-\cos(x)] = -\cos(\pi) = -(-1) = 1$$

Since $f'_-(\pi) = -1 \neq 1 = f'_+(\pi)$, the left and right derivatives disagree, so **$f'(\pi)$ does not exist**. The graph of $f(x) = |\sin(x)|$ has a sharp corner (cusp) at $x = \pi$.

**Why the distractors are wrong:**
- (A) incorrectly claims $f'(\pi) = -1$, using only the left-hand derivative.
- (C) has the wrong sign for $f'(\pi/4)$ — near $\pi/4$, $\sin(x) > 0$ so the absolute value does nothing.
- (D) incorrectly gives $f'(\pi/4) = 0$, confusing the derivative with the function value or evaluating $\cos(x)$ at the wrong point.
