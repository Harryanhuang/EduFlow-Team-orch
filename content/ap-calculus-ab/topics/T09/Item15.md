---
id: T09-Item15
difficulty: C
calculator: no-calc
type: frq
---
Let $h(x) = f(g(x))$, where $f$ and $g$ are twice-differentiable functions. The following values are given:

$$f(0) = 3, \quad f'(0) = -2, \quad f''(0) = 1$$
$$g(1) = 0, \quad g'(1) = 4, \quad g''(1) = -3$$

(a) Find $h'(1)$.

(b) Find $h''(1)$. Show all work leading to your answer.

## Answer
(a) $h'(1) = -8$

(b) $h''(1) = 22$

## Explanation
**(a)** By the chain rule:

$$h'(x) = f'(g(x)) \cdot g'(x)$$

Evaluate at $x = 1$:

$$h'(1) = f'(g(1)) \cdot g'(1) = f'(0) \cdot 4 = (-2)(4) = -8$$

**(b)** To find $h''(x)$, differentiate $h'(x) = f'(g(x)) \cdot g'(x)$ using the **product rule** and the **chain rule**:

$$h''(x) = \frac{d}{dx}[f'(g(x))] \cdot g'(x) + f'(g(x)) \cdot \frac{d}{dx}[g'(x)]$$

The first term requires the chain rule applied to $f'(g(x))$:

$$\frac{d}{dx}[f'(g(x))] = f''(g(x)) \cdot g'(x)$$

So:

$$h''(x) = f''(g(x)) \cdot [g'(x)]^2 + f'(g(x)) \cdot g''(x)$$

Evaluate at $x = 1$:

$$h''(1) = f''(0) \cdot (4)^2 + f'(0) \cdot (-3)$$
$$h''(1) = (1)(16) + (-2)(-3) = 16 + 6 = \mathbf{22}$$

The second derivative of a composite function requires both the chain rule and the product rule. The key formula is:

$$h''(x) = f''(g(x))[g'(x)]^2 + f'(g(x))\,g''(x)$$

At $x = 1$, using $g(1) = 0$ so that $f$ and its derivatives are evaluated at $0$:

$$h''(1) = f''(0) \cdot 4^2 + f'(0) \cdot (-3) = 1 \cdot 16 + (-2)(-3) = 16 + 6 = \mathbf{22}$$
