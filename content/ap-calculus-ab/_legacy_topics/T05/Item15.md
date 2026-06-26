---
id: T05-Item15
difficulty: C
calculator: calc
type: frq
---
A particle moves along a straight line. Its position $s(t)$ in meters at selected times $t$ in seconds is given below.

| $t$ (s) | 0    | 0.5  | 1.0  | 1.5  | 2.0  | 2.5  | 3.0  |
|---------|------|------|------|------|------|------|------|
| $s(t)$ (m) | 0.000 | 0.375 | 1.000 | 1.125 | 0.000 | -3.125 | -8.000 |

(a) Approximate the velocity $v(1)$ using the data from the table. Explain which method you chose.

(b) Approximate the velocity $v(2)$ using the data from the table.

(c) During which time interval does the particle appear to change direction? Justify using your velocity estimates.

## Answer
(a) Using the symmetric difference quotient at $t = 1$:
$$v(1) \approx \frac{s(1.5) - s(0.5)}{1.5 - 0.5} = \frac{1.125 - 0.375}{1} = 0.750 \text{ m/s}$$
This method is preferred because it uses points on both sides of $t = 1$, giving a centered approximation.

(b) Using the symmetric difference quotient at $t = 2$:
$$v(2) \approx \frac{s(2.5) - s(1.5)}{2.5 - 1.5} = \frac{-3.125 - 1.125}{1} = -4.250 \text{ m/s}$$

(c) The particle changes direction between $t = 1.5$ and $t = 2.0$. At $t = 1$, the velocity is approximately $0.75$ m/s (positive, moving right). At $t = 2$, the velocity is approximately $-4.25$ m/s (negative, moving left). Since velocity changes sign, the particle reverses direction somewhere in this interval. This is consistent with $s(t)$ increasing up to $t = 1.5$ and then decreasing.

## Explanation
This problem connects the derivative (velocity as the derivative of position) to a real-world context. Students must choose appropriate difference quotients, compute them, and interpret sign changes in the derivative as direction changes. The data comes from $s(t) = t^2(3 - t)$, so $v(t) = 6t - 3t^2 = 3t(2 - t)$, with $v(1) = 3$ and $v(2) = 0$ — the approximations capture the trend though with discretization error.
