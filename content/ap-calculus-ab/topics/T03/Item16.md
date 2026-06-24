---
id: T03-Item16
difficulty: C
calculator: calc
type: frq
---

The function \( f \) is defined by
\[
f(x) = \begin{cases}
ax + b, & x < 1 \\
3, & x = 1 \\
x^2 - 2x + c, & x > 1
\end{cases}
\]

(a) Find the relationship between \( a \) and \( b \) required for \( f \) to be continuous at \( x = 1 \).
(b) Find the value of \( c \) required for \( f \) to be continuous at \( x = 1 \).
(c) If \( a = 2 \), find \( b \) and verify that \( f \) is continuous at \( x = 1 \).

## Answer
(a) For continuity at \( x = 1 \), the left-hand limit must equal \( f(1) = 3 \):
\[
\lim_{x \to 1^-} (ax + b) = a + b = 3.
\]
So \( a + b = 3 \).

(b) The right-hand limit must also equal 3:
\[
\lim_{x \to 1^+} (x^2 - 2x + c) = 1 - 2 + c = c - 1 = 3.
\]
So \( c = 4 \).

(c) If \( a = 2 \), then \( b = 3 - a = 1 \). Check:
- Left-hand limit: \( 2(1) + 1 = 3 \)
- Right-hand limit: \( 1 - 2 + 4 = 3 \)
- \( f(1) = 3 \)
All three agree, so \( f \) is continuous at \( x = 1 \).

## Explanation
A three-piece piecewise function with a defined middle value requires both outer pieces to match the middle value at the transition point. This creates a system linking all three parameters.
