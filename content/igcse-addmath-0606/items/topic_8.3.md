# Topic 8.3 — Integration
## Items File

**Item 1 [F]**
Question: Find ∫ 4x³ dx.
Answer: x⁴ + C
Difficulty: F
Topic: 8.3
Explanation: Using the power rule: ∫xⁿ dx = x^(n+1)/(n+1) + C. So ∫4x³ dx = 4 × x⁴/4 + C = x⁴ + C.
Tags: integration, power rule, indefinite integral
**Item 2 [F]**
Question: Evaluate ∫₀² (3x² + 1) dx.
Answer: 10
Difficulty: F
Topic: 8.3
Explanation: ∫(3x²+1)dx = x³ + x + C. Evaluate from 0 to 2: [x³+x]₀² = (8+2) − (0+0) = 10.
Tags: integration, definite integral, fundamental theorem
**Item 3 [S]**
Question: Find ∫ sin x dx.
Answer: −cos x + C
Difficulty: S
Topic: 8.3
Explanation: Since d/dx(cos x) = −sin x, we have d/dx(−cos x) = sin x. So ∫ sin x dx = −cos x + C.
Tags: integration, trigonometric functions
**Item 4 [S]**
Question: Evaluate ∫₁² (2x + 1/x) dx.
Answer: 4 + ln 2
Difficulty: S
Topic: 8.3
Explanation: ∫(2x + 1/x)dx = x² + ln|x| + C. Evaluate from 1 to 2: [x² + ln x]₁² = (4 + ln 2) − (1 + 0) = 3 + ln 2.
Tags: integration, definite integral, logarithm
**Item 5 [S]**
Question: Find ∫ e^x dx.
Answer: e^x + C
Difficulty: S
Topic: 8.3
Explanation: Since d/dx(e^x) = e^x, the derivative of e^x is itself. So ∫e^x dx = e^x + C.
Tags: integration, exponential function
**Item 6 [S]**
Question: Find the area bounded by y = x², x = 0, x = 2 and the x-axis.
Answer: 8/3
Difficulty: S
Topic: 8.3
Explanation: Area = ∫₀² x² dx = [x³/3]₀² = 8/3 − 0 = 8/3. Since y = x² ≥ 0 in [0, 2], this is the area.
Tags: integration, area under curve, definite integral
**Item 7 [C]**
Question: Evaluate ∫₀^π sin² x dx.
Answer: π/2
Difficulty: C
Topic: 8.3
Explanation: sin² x = (1 − cos 2x)/2. So ∫₀^π sin² x dx = ∫₀^π (1−cos 2x)/2 dx = [x/2 − (sin 2x)/4]₀^π = (π/2 − 0) − (0 − 0) = π/2.
Tags: integration, trigonometric, definite integral
**Item 8 [C]**
Question: Find ∫ x · e^x dx using integration by parts.
Answer: (x − 1)e^x + C
Difficulty: C
Topic: 8.3
Explanation: ∫u dv = uv − ∫v du. Let u = x, dv = e^x dx. Then du = dx, v = e^x. So ∫x e^x dx = x e^x − ∫e^x dx = x e^x − e^x + C = (x−1)e^x + C.
Tags: integration, integration by parts, exponential
**Item 9 [C]**
Question: Find the area enclosed by y = x + 2 and y = x^2 from x = -1 to x = 2.
Answer: 9/2
Difficulty: C
Topic: 8.3
Explanation: Intersection at x = -1 and x = 2. Area = integral of (x + 2 - x^2) from -1 to 2. Antiderivative F(x) = x^2/2 + 2x - x^3/3. F(2) = 4/2 + 4 - 8/3 = 10/3. F(-1) = 1/2 - 2 + 1/3 = -7/6. Area = 10/3 - (-7/6) = 20/6 + 7/6 = 27/6 = 9/2. Verify: approximate area = (3 + 0 - 0) avg height × 3 width ~ 4.5 units^2.
