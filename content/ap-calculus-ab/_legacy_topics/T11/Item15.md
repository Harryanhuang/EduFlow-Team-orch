---
id: T11-Item15
difficulty: C
calculator: calc
type: frq
---
Let $y = \ln(\arcsin x)$ for $0 < x < 1$. Find $\frac{dy}{dx}$ and evaluate at $x = \frac{1}{2}$.

## Answer
$\frac{dy}{dx} = \frac{1}{\arcsin x \cdot \sqrt{1 - x^2}}$; at $x = \frac{1}{2}$: $\frac{2\sqrt{3}}{\pi}$

## Explanation
By the chain rule: $\frac{dy}{dx} = \frac{1}{\arcsin x} \cdot \frac{d}{dx}[\arcsin x] = \frac{1}{\arcsin x} \cdot \frac{1}{\sqrt{1 - x^2}} = \frac{1}{\arcsin x \cdot \sqrt{1 - x^2}}$. At $x = \frac{1}{2}$: $\arcsin(\frac{1}{2}) = \frac{\pi}{6}$ and $\sqrt{1 - \frac{1}{4}} = \frac{\sqrt{3}}{2}$. So $\frac{dy}{dx} = \frac{1}{\frac{\pi}{6} \cdot \frac{\sqrt{3}}{2}} = \frac{12}{\pi\sqrt{3}} = \frac{2\sqrt{3}}{\pi}$.
