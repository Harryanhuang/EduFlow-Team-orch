---
id: T18-Item07
difficulty: S
calculator: calc
type: frq
---
A cylindrical can is to hold 1000 cubic centimeters of juice. The material for the top and bottom costs $0.05 per cm squared and the material for the side costs $0.03 per cm squared.

(a) Express the total cost $C$ of the material as a function of the radius $r$ of the can.
(b) Find the radius that minimizes the cost.
(c) What is the minimum cost?

## Answer
(a) $C(r) = 0.10\pi r^2 + \frac{60}{r}$ dollars

(b) $r = \sqrt[3]{\frac{300}{\pi}}$

(c) $C_{min} \approx 19.71$ dollars

## Explanation
Volume: $\pi r^2 h = 1000$, so $h = \frac{1000}{\pi r^2}$.
Top and bottom area: $2\pi r^2$ at $0.05 per cm squared: cost = $0.10\pi r^2$.
Side area: $2\pi r h = 2\pi r \cdot \frac{1000}{\pi r^2} = \frac{2000}{r}$ at $0.03 per cm squared: cost = $0.03 \cdot \frac{2000}{r} = \frac{60}{r}$.
Total cost: $C(r) = 0.10\pi r^2 + \frac{60}{r}$.

(b) $C'(r) = 0.20\pi r - \frac{60}{r^2} = 0$.
$0.20\pi r^3 = 60$.
$r^3 = \frac{300}{\pi}$.
$r = \sqrt[3]{\frac{300}{\pi}}$.

(c) Substituting back: $C_{min} = 0.10\pi\left(\frac{300}{\pi}\right)^{2/3} + 60\left(\frac{300}{\pi}\right)^{-1/3} = 90\left(\frac{\pi}{300}\right)^{1/3} \approx 19.71$ dollars.
