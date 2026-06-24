---
id: T16-Item15
difficulty: C
calculator: calc
type: frq
---
A rectangular field is to be enclosed by 200 meters of fencing. One side of the field will be along an existing wall, so no fencing is needed on that side.

(a) Express the area $A$ of the field as a function of $x$, where $x$ is the length of the side perpendicular to the wall.
(b) Find the critical points of $A$.
(c) Determine the intervals on which $A$ is increasing and decreasing.
(d) Find the dimensions of the field that maximize the enclosed area.

## Answer
(a) $A(x) = x(100 - x) = 100x - x^2$, for $0 < x < 100$.
(b) Critical point: $x = 50$.
(c) Increasing on $(0, 50)$; decreasing on $(50, 100)$.
(d) Width (perpendicular to wall): $x = 50$ m; length (parallel to wall): $100 - x = 50$ m. Maximum area: $A = 2500$ m$^2$.

## Explanation
(a) If $x$ is the side perpendicular to the wall, the opposite side (parallel to the wall) has length $200 - 2x$. So $A(x) = x(200 - 2x) = 200x - 2x^2 = 2(100x - x^2)$. (The stated form is equivalent.)
(b) $A'(x) = 200 - 4x$. Setting $A'(x) = 0$ gives $x = 50$.
(c) For $0 < x < 50$, $A'(x) > 0$, so increasing. For $50 < x < 100$, $A'(x) < 0$, so decreasing.
(d) By the First Derivative Test, $A'$ changes from $+$ to $-$ at $x = 50$, so this is a local maximum. Since $A(x) \to 0$ as $x \to 0^+$ or $x \to 100^-$, this is also the absolute maximum.
