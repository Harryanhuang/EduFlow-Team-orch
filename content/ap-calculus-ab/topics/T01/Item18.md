---
id: T01-Item18
difficulty: C
calculator: calc
type: frq
---
Consider the function \(f(x) = \dfrac{e^x - 1}{x}\) for \(x \neq 0\).

(a) Use a calculator to complete the table below to 6 decimal places:

| \(x\)     | \(-0.1\) | \(-0.01\) | \(-0.001\) | \(0.001\) | \(0.01\) | \(0.1\) |
|-----------|----------|-----------|------------|-----------|----------|---------|
| \(f(x)\)  |          |           |            |           |          |         |

(b) Based on your table, estimate \(\displaystyle\lim_{x \to 0} f(x)\).
(c) The actual limit equals \(\ln e\). Explain why this makes sense conceptually — what famous derivative is this limit computing?

## Answer
(a) Table values:

| \(x\)     | \(-0.1\)   | \(-0.01\)  | \(-0.001\) | \(0.001\)  | \(0.01\)   | \(0.1\)    |
|-----------|------------|------------|------------|------------|------------|------------|
| \(f(x)\)  | 0.951626   | 0.995017   | 0.999500   | 1.000500   | 1.005017   | 1.051709   |

(b) The limit appears to be 1.
(c) This limit is the definition of the derivative of \(e^x\) at \(x = 0\).

## Explanation
(a) Values computed using \(f(x) = \frac{e^x - 1}{x}\):
\(f(-0.1) \approx 0.951626\), \(f(-0.01) \approx 0.995017\), \(f(-0.001) \approx 0.999500\), \(f(0.001) \approx 1.000500\), \(f(0.01) \approx 1.005017\), \(f(0.1) \approx 1.051709\).

(b) As \(x \to 0\) from both sides, \(f(x) \to 1\).

(c) By definition, \(f'(a) = \displaystyle\lim_{h \to 0}\frac{f(a+h) - f(a)}{h}\). For \(g(x) = e^x\) at \(a = 0\):
\[
g'(0) = \lim_{h \to 0}\frac{e^{0+h} - e^0}{h} = \lim_{h \to 0}\frac{e^h - 1}{h}
\]
Since \(\frac{d}{dx}e^x = e^x\), we have \(g'(0) = e^0 = 1\). This connects the limit concept directly to the derivative.
