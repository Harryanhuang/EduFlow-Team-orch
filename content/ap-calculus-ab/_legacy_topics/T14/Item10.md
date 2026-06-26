---
id: T14-Item10
difficulty: C
calculator: calc
type: mcq
---
The linearization of $f(x) = x^3$ at $x = 2$ is used to approximate $f(2.1)$. The actual value is $f(2.1) = 9.261$. Which of the following statements is true?

## Options
A) The approximation $9.2$ overestimates the actual value.
B) The approximation $9.2$ underestimates the actual value.
C) The approximation $9.2$ is exactly equal to the actual value.
D) The approximation $9.2$ is not accurate because $f$ is not linear.

## Answer
B) The approximation $9.2$ underestimates the actual value.

## Explanation
$f(2) = 8$, $f'(2) = 12$, so $L(x) = 8 + 12(x-2)$. Thus $f(2.1) \approx L(2.1) = 8 + 12(0.1) = 9.2$. Since $f''(x) = 6x > 0$ for $x > 0$, $f$ is concave up. A concave-up curve lies above its tangent line, so $f(2.1) > L(2.1)$. The actual value $9.261 > 9.2$, confirming the approximation underestimates. The linearization is designed for small displacements; the error increases with the second derivative and the square of the displacement.
