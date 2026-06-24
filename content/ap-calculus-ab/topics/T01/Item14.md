---
id: T01-Item14
difficulty: C
calculator: no-calc
type: mcq
---
Consider the statement: "\(\displaystyle\lim_{x \to 2} f(x) = 5\)." Which of the following is the correct \(\varepsilon\)-\(\delta\) interpretation?

## Options
A) For every \(\delta > 0\), there exists \(\varepsilon > 0\) such that if \(|x - 2| < \delta\), then \(|f(x) - 5| < \varepsilon\).
B) For every \(\varepsilon > 0\), there exists \(\delta > 0\) such that if \(0 < |x - 2| < \delta\), then \(|f(x) - 5| < \varepsilon\).
C) There exists \(\varepsilon > 0\) such that for every \(\delta > 0\), if \(0 < |x - 2| < \delta\), then \(|f(x) - 5| < \varepsilon\).
D) For every \(\varepsilon > 0\), there exists \(\delta > 0\) such that if \(|x - 2| < \delta\), then \(|f(x) - 5| < \varepsilon\).

## Answer
B

## Explanation
The formal definition: \(\lim_{x \to a} f(x) = L\) means for every \(\varepsilon > 0\), there exists \(\delta > 0\) such that if \(0 < |x - a| < \delta\), then \(|f(x) - L| < \varepsilon\). Key features: (1) \(\varepsilon\) is given first (we must work for any desired closeness to \(L\)); (2) the condition \(0 < |x - a|\) excludes \(x = a\) — the limit does not depend on \(f(a)\); (3) \(\delta\) depends on \(\varepsilon\). Option B captures all these correctly.
