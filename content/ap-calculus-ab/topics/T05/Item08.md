---
id: T05-Item08
difficulty: S
calculator: no-calc
type: mcq
---
Let $f(x) = |x - 2|$. Which of the following statements is true?

## Options
A) $f$ is continuous at $x = 2$ and differentiable at $x = 2$.
B) $f$ is continuous at $x = 2$ but not differentiable at $x = 2$.
C) $f$ is not continuous at $x = 2$ and not differentiable at $x = 2$.
D) $f$ is not continuous at $x = 2$ but differentiable at $x = 2$.

## Answer
B

## Explanation
The function $f(x) = |x - 2|$ is continuous everywhere because $\lim_{x \to 2} |x - 2| = 0 = f(2)$. However, it is not differentiable at $x = 2$ because the left-hand and right-hand limits of the difference quotient do not agree:

$$\lim_{h \to 0^-} \frac{|2 + h - 2| - 0}{h} = \lim_{h \to 0^-} \frac{-h}{h} = -1$$
$$\lim_{h \to 0^+} \frac{|2 + h - 2| - 0}{h} = \lim_{h \to 0^+} \frac{h}{h} = 1$$

Since the one-sided limits differ, $f'(2)$ does not exist. This is the classic "corner point" example showing that continuity does not imply differentiability.
