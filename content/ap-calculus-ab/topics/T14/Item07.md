---
id: T14-Item07
difficulty: S
calculator: no-calc
type: mcq
---
Let $g(x)$ be the linearization of $g(x) = \ln x$ at $x = 1$. Which of the following statements is true?

## Options
A) $g(1.1) < \ln(1.1)$ because $g$ overestimates
B) $g(1.1) > \ln(1.1)$ because $g$ overestimates
C) $g(1.1) < \ln(1.1)$ because $g$ underestimates
D) $g(1.1) = \ln(1.1)$ exactly

## Answer
B) $g(1.1) > \ln(1.1)$ because $g$ overestimates

## Explanation
$g(1) = 0$, $g'(x) = \frac{1}{x}$, so $g'(1) = 1$. The linearization is $L(x) = 0 + 1(x-1) = x - 1$. Since $\frac{d^2}{dx^2}(\ln x) = -\frac{1}{x^2} < 0$ for $x > 0$, the function is concave down, so the tangent line lies above the curve. Thus $L(1.1) = 0.1 > \ln(1.1) \approx 0.0953$, meaning the linearization overestimates.
