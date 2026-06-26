---
id: T09-Item13
difficulty: S
calculator: no-calc
type: frq
---
Let $f(x) = e^{\sin(x)}$.

(a) Find $f'(x)$.

(b) Find the equation of the tangent line to the graph of $f$ at $x = 0$.

(c) Use the tangent line from part (b) to approximate $f(0.1)$. Is this approximation an overestimate or an underestimate? Justify your answer.

## Answer
(a) $f'(x) = \cos(x)\,e^{\sin(x)}$

(b) $y = x + 1$

(c) Approximation: $1.1$. This is an **underestimate** because $f''(0) = 1 > 0$, so $f$ is concave up at $x = 0$ and the tangent line lies below the curve near $x = 0$.

## Explanation
**(a)** By the chain rule:

$$f'(x) = e^{\sin(x)} \cdot \frac{d}{dx}[\sin(x)] = \cos(x)\,e^{\sin(x)}$$

**(b)** Evaluate at $x = 0$:

$$f(0) = e^{\sin(0)} = e^0 = 1$$
$$f'(0) = \cos(0)\,e^{\sin(0)} = 1 \cdot 1 = 1$$

The tangent line at $x = 0$ is $y - f(0) = f'(0)(x - 0)$:

$$y - 1 = 1(x - 0) \implies y = x + 1$$

**(c)** Using the tangent line $L(x) = x + 1$ to approximate $f(0.1)$:

$$L(0.1) = 0.1 + 1 = 1.1$$

To determine whether this is an overestimate or underestimate, find $f''(x)$:

$$f''(x) = \frac{d}{dx}[\cos(x)\,e^{\sin(x)}] = -\sin(x)\,e^{\sin(x)} + \cos(x) \cdot \cos(x)\,e^{\sin(x)}$$
$$f''(x) = e^{\sin(x)}[\cos^2(x) - \sin(x)]$$

At $x = 0$:

$$f''(0) = e^0[\cos^2(0) - \sin(0)] = 1 \cdot [1 - 0] = 1 > 0$$

Since $f''(0) > 0$, the function is **concave up** at $x = 0$. When a function is concave up, the tangent line lies below the curve near the point of tangency, so the linear approximation is an **underestimate**.

Verification: $f(0.1) = e^{\sin(0.1)} \approx e^{0.09983} \approx 1.10498 > 1.1$, confirming the underestimate.
