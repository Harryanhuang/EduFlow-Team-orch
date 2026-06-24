---
id: T01-Item15
difficulty: C
calculator: no-calc
type: frq
---
Let
\[
f(x) = \begin{cases}
x^2 - 1, & x < 1 \\
kx + 2, & x \geq 1
\end{cases}
\]

(a) For what value of \(k\), if any, does \(\displaystyle\lim_{x \to 1} f(x)\) exist?
(b) With that value of \(k\), is \(f\) continuous at \(x = 1\)? Justify.
(c) For a different value \(k = 5\), find \(\displaystyle\lim_{x \to 1^+} f(x)\) and explain why the two-sided limit does not exist.

## Answer
(a) \(k = -2\)
(b) Yes, because \(f(1) = -2(1) + 2 = 0 = \lim_{x \to 1} f(x)\).
(c) \(\lim_{x \to 1^+} f(x) = 7\); the two-sided limit DNE because left-hand limit is 0 and right-hand limit is 7.

## Explanation
(a) Left-hand limit: \(\lim_{x \to 1^-} (x^2 - 1) = 0\). Right-hand limit: \(\lim_{x \to 1^+} (kx + 2) = k + 2\). For the limit to exist, we need \(0 = k + 2\), so \(k = -2\). Wait, let me recompute: \(k + 2 = 0 \Rightarrow k = -2\).

(b) With \(k = -2\), \(f(1) = -2(1) + 2 = 0 = \lim_{x \to 1} f(x)\). So yes, \(f\) is continuous at \(x = 1\).

(c) With \(k = 5\), \(\lim_{x \to 1^+} f(x) = 5(1) + 2 = 7\). Since \(\lim_{x \to 1^-} f(x) = 0 \neq 7\), the two-sided limit does not exist.
