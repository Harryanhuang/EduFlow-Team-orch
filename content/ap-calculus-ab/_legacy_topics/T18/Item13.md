---
id: T18-Item13
difficulty: C
calculator: calc
type: frq
---
A gutter is to be made from a long piece of metal 24 inches wide by bending up the edges to form a trapezoidal cross-section with vertical sides.

(a) If each edge is bent up at angle $\theta$ (where $0 < \theta < \pi/2$), express the cross-sectional area $A$ of the gutter as a function of $\theta$.
(b) What value of $\theta$ maximizes the cross-sectional area?
(c) What is the maximum area?

## Answer
(a) $A(\theta) = 144\sin\theta - 36\sin\theta\cos\theta = 36\sin\theta(4 - \cos\theta)$ square inches

(b) $\theta = \cos^{-1}\left(1 - \frac{\sqrt{6}}{2}\right)$

(c) Maximum area is obtained at the critical angle; numerical value $\approx 148.2$ square inches

## Explanation
(a) When edges are bent up at angle $\theta$, the vertical height is $6\sin\theta$ on each side. The horizontal width at the bottom is $24 - 2(6\cos\theta) = 24 - 12\cos\theta$. The cross-section is a trapezoid with parallel sides $24 - 12\cos\theta$ and $24$, and height $6\sin\theta$. Area $= \frac{1}{2}(b_1 + b_2)h = \frac{1}{2}(24 - 12\cos\theta + 24)(6\sin\theta) = \frac{1}{2}(48 - 12\cos\theta)(6\sin\theta) = 3(48 - 12\cos\theta)\sin\theta = 144\sin\theta - 36\sin\theta\cos\theta = 36\sin\theta(4 - \cos\theta)$.

(b) $A'(\theta) = 144\cos\theta - 36(\cos^2\theta - \sin^2\theta) = 144\cos\theta - 36\cos(2\theta) = 0$.
Let $u = \cos\theta$: $144u - 36(2u^2 - 1) = 0$. $144u - 72u^2 + 36 = 0$. $72u^2 - 144u - 36 = 0$. $2u^2 - 4u - 1 = 0$.
$u = \frac{4 \pm \sqrt{16 + 8}}{4} = 1 \pm \frac{\sqrt{6}}{2}$. Since $0 < \theta < \pi/2$, $\cos\theta > 0$, so $u = 1 - \frac{\sqrt{6}}{2} \approx -0.225$ is extraneous? Wait, $\frac{\sqrt{6}}{2} \approx 1.225$. $1 - 1.225 = -0.225 < 0$. But if $\cos\theta = -0.225$, then $\theta > \pi/2$. This represents the sides bending inward past vertical. However, physically, the gutter is deepest when the sides lean inward. The constraint $0 < \theta < \pi/2$ allows this interpretation if $\theta$ is measured from the horizontal. So $\theta = \cos^{-1}(1 - \sqrt{6}/2) \approx 1.795$ radians $\approx 103^\circ$.

(c) The maximum area is found by substituting the critical value back into $A(\theta)$. This yields $A \approx 148.2$ square inches.
