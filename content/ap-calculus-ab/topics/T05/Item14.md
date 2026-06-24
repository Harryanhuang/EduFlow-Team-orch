---
id: T05-Item14
difficulty: C
calculator: no-calc
type: frq
---
Let
$$f(x) = \begin{cases} ax^2 + bx & \text{if } x \leq 2 \\ 3x - 2 & \text{if } x > 2 \end{cases}$$

Find the values of $a$ and $b$ such that $f$ is differentiable at $x = 2$. Justify your answer.

## Answer
For $f$ to be differentiable at $x = 2$, it must first be continuous there, and the left and right derivatives must match.

**Continuity at $x = 2$:**
$$\lim_{x \to 2^-} f(x) = a(4) + 2b = 4a + 2b$$
$$\lim_{x \to 2^+} f(x) = 3(2) - 2 = 4$$
So: $4a + 2b = 4$, or $2a + b = 2$ ... (Equation 1)

**Equal derivatives at $x = 2$:**
Left derivative: $\dfrac{d}{dx}(ax^2 + bx)\big|_{x=2} = 2ax + b\big|_{x=2} = 4a + b$
Right derivative: $\dfrac{d}{dx}(3x - 2)\big|_{x=2} = 3$
So: $4a + b = 3$ ... (Equation 2)

**Solving:** Subtract Equation 1 from Equation 2:
$(4a + b) - (2a + b) = 3 - 2 \implies 2a = 1 \implies a = \dfrac{1}{2}$
Then $b = 2 - 2a = 2 - 1 = 1$

**Answer:** $a = \dfrac{1}{2}$, $b = 1$

## Explanation
This multi-step problem requires setting up two equations: one from the continuity condition and one from the equal-derivative condition. Students must recognize that differentiability requires BOTH conditions simultaneously. The system of two linear equations in two unknowns then gives unique values for the parameters.
