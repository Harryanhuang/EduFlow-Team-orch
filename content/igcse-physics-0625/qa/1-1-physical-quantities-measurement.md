# QA: 1.1 — Physical quantities, SI units, measuring length and time

## Topic 名称
Physical quantities, SI units, measuring length and time（物理量、国际单位制、长度与时间的测量）

## Topic 定义
学习基本物理量（长度、质量、时间）及其 SI 单位，掌握常用测量工具的使用方法和读数技巧，包括刻度尺、游标卡尺、千分尺、秒表等。

## 关键知识点
- SI 基本单位：米(m)、千克(kg)、秒(s)
- 常用 SI 前缀：kilo(k), centi(c), milli(m), micro(μ) 的换算
- 刻度尺的读数方法与估读
- 游标卡尺（vernier calipers）的原理和读数（精确到 0.1mm 或 0.05mm）
- 千分尺（micrometer screw gauge）的原理和读数（精确到 0.01mm）
- 零误差（zero error）的概念和修正
- 时间测量：机械秒表、数字秒表的读数
- 多次测量取平均值以减小随机误差

## 前置知识
- 无

## 常见错误
- 游标卡尺读数时忘记加上主尺读数
- 千分尺读数时忽略半刻度线
- 忘记修正零误差（正零误差应减去，负零误差应加上）
- 单位换算时小数点移错位置（尤其 milli 和 micro 之间）
- 认为测量次数越多误差越小（只能减小随机误差，不能消除系统误差）

## 可出题方向
- 读取游标卡尺或千分尺的示数（给图）
- 计算零误差并修正测量结果
- SI 单位换算（如 mm → m, mg → kg）
- 选择合适的测量工具测量给定物体
- 计算多次测量的平均值

## 难度提示
Core：基础。要求学生能正确读数和进行基本单位换算。

## 适合题型
- 读数题（配图）
- 计算题（单位换算、平均值）
- 选择题
- 简答题（选择合适工具）

## Item-level prototype

### Question Q-1.1-01
**Difficulty**: Foundation
**Question**: A student uses a metre rule to measure the length of a notebook and records the result as 245 mm. Write this length in metres.
**Answer**: 0.245 m
**Explanation**: Convert millimetres to metres by dividing by 1000. So 245 mm = 245 / 1000 m = 0.245 m. A common error is dividing by 100 or moving the decimal point the wrong number of places.
**Tags**: si-units, unit-conversion, length-measurement

### Question Q-1.1-02
**Difficulty**: Foundation
**Question**: Write the SI prefix for each of the following: (a) 10³, (b) 10⁻³, (c) 10⁻⁶. Then convert 0.047 m into mm and μm.
**Answer**: (a) kilo (k), (b) milli (m), (c) micro (μ). 0.047 m = 47 mm = 47 000 μm.
**Explanation**: 0.047 m × 1000 = 47 mm. 47 mm × 1000 = 47 000 μm. A common error is confusing milli (10⁻³) with micro (10⁻⁶) — they differ by a factor of 1000.

**Tags**: si-prefixes, unit-conversion

### Question Q-1.1-03
**Difficulty**: Foundation
**Question**: A student reads a vernier caliper. The main scale shows 3.2 cm and the vernier scale shows that the 7th line coincides with a main scale line. The vernier has 10 divisions over 9 mm. What is the reading?
**Answer**: 3.27 cm
**Explanation**: Main scale reading = 3.2 cm. Vernier reading = 7 × 0.01 cm = 0.07 cm (each vernier division = 0.01 cm). Total = 3.2 + 0.07 = 3.27 cm. A common error is reading the wrong vernier line or forgetting to add the main scale and vernier readings together.

**Tags**: vernier-calipers, reading, length-measurement

### Question Q-1.1-04
**Difficulty**: Standard
**Question**: A micrometer screw gauge has a zero error of +0.03 mm. When measuring a wire, the sleeve shows 2 mm, the thimble shows 0.47 mm, and the half-millimetre line is not visible. What is the corrected diameter of the wire?
**Answer**: 2.44 mm
**Explanation**: Reading = 2 + 0.47 = 2.47 mm. Corrected = 2.47 − 0.03 = 2.44 mm (subtract positive zero error). A common error is adding the zero error instead of subtracting, or misreading the half-millimetre line.

**Tags**: micrometer, zero-error, correction

### Question Q-1.1-05
**Difficulty**: Standard
**Question**: A student measures the time for 20 complete swings of a pendulum three times: 24.6 s, 25.0 s, 24.8 s. Calculate the average period of one swing. State why the student measured 20 swings rather than timing a single swing.
**Answer**: Average period = 1.24 s
**Explanation**: Average time for 20 swings = (24.6 + 25.0 + 24.8) / 3 = 74.4 / 3 = 24.8 s. Period = 24.8 / 20 = 1.24 s. Measuring 20 swings and averaging reduces the effect of reaction time error on the measurement. A single swing is too quick to time accurately — the reaction time error (about 0.2 s) would be a large percentage of the period.

**Tags**: time-measurement, period, averaging, pendulum
