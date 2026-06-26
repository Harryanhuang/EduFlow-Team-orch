---
id: T03-Item18
difficulty: C
calculator: no-calc
type: frq
---

Let \( f \) be continuous on \( [0, 3] \) with \( f(0) = 1 \), \( f(1) = -1 \), \( f(2) = 2 \), and \( f(3) = -2 \).

(a) Using the Intermediate Value Theorem, determine the minimum number of distinct zeros that \( f \) must have in the interval \( (0, 3) \).
(b) Is it possible for \( f \) to have exactly 2 zeros in \( (0, 3) \)? Justify your answer.
(c) Could \( f \) have exactly 3 zeros in \( (0, 3) \)? Justify.

## Answer
(a) Consider consecutive sign changes:
- \( f(0) = 1 > 0 \) and \( f(1) = -1 < 0 \): By IVT, there is at least one zero in \( (0, 1) \).
- \( f(1) = -1 < 0 \) and \( f(2) = 2 > 0 \): By IVT, there is at least one zero in \( (1, 2) \).
- \( f(2) = 2 > 0 \) and \( f(3) = -2 < 0 \): By IVT, there is at least one zero in \( (2, 3) \).

These three intervals are disjoint, so \( f \) has at least **3 distinct zeros** in \( (0, 3) \).

(b) No. Since the IVT guarantees at least one zero in each of the three disjoint intervals \( (0,1) \), \( (1,2) \), and \( (2,3) \), there must be at least 3 zeros. Two zeros is impossible.

(c) Yes. A function could have exactly one zero in each of the three intervals. For example, a polynomial or piecewise linear function passing through the given points with exactly one crossing per subinterval would achieve exactly 3 zeros. There is no upper bound from the IVT alone—the function could oscillate and have infinitely many zeros.

## Explanation
The IVT applied over consecutive subintervals with sign changes provides a lower bound on the number of zeros. The bound is tight in the sense that exactly that many zeros can occur, but the IVT does not limit the maximum number.
