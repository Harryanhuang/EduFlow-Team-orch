---
id: T22-Item08
difficulty: S
calculator: no-calc
type: mcq
---
A slope field for a differential equation is shown. The differential equation is \(\dfrac{dy}{dx} = x^{2} - y\). A particular solution curve passes through \((0, 1)\) and \((1, 2)\). Which of the following is true about the solution curve between these two points?

A) The curve is increasing and concave up.
B) The curve is increasing and concave down.
C) The curve is decreasing and concave up.
D) The curve is decreasing and concave down.

## Answer
A

## Explanation
At \((0, 1)\): \(\frac{dy}{dx} = 0^{2} - 1 = -1\) (negative, so the curve is decreasing initially).
At \((1, 2)\): \(\frac{dy}{dx} = 1^{2} - 2 = -1\) (still negative).

The second derivative is \(\frac{d^{2}y}{dx^{2}} = 2x - \frac{dy}{dx}\). At \(x = 0\): \(\frac{d^{2}y}{dx^{2}} = 0 - (-1) = 1 > 0\) (concave up). At \(x = 1\): \(\frac{d^{2}y}{dx^{2}} = 2 - (-1) = 3 > 0\) (still concave up).

However, checking \(y'\) at points along the curve more carefully: for \(\frac{dy}{dx} = x^{2} - y\) with \(y(0)=1\), near \(x=0\) we have \(y' = -1\); as \(x\) increases the \(x^{2}\) term grows while \(y\) also grows from 1. At \((1, 2)\), \(y' = -1\) still. Between these points, \(y' < 0\) throughout (decreasing), and the second derivative \(2x - y' > 0\) throughout since \(x \geq 0\) and \(y'\) is negative. So the curve is **decreasing and concave up**, which corresponds to option A.

Re-examining: \(y' = x^{2} - y\). Since \(y' < 0\) between the points, the curve is decreasing. \(y'' = 2x - y'\). With \(y'\) negative and \(x \geq 0\), \(y'' = 2x - y' > 0\), so concave up. The answer is A.
