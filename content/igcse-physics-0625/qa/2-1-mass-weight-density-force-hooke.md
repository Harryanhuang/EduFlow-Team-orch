# QA: 2.1 — Mass, weight, density, force as push/pull, Hooke's law

## Topic 名称
Mass, weight, density, force as push/pull, Hooke's law（质量、重量、密度、力、胡克定律）

## Topic 定义
学习质量与重量的区别、密度的定义与测量方法、力的基本概念和效果，以及弹簧伸长量与拉力之间的关系（胡克定律）。

## 关键知识点
- 质量（kg）vs 重量（N）：质量是物质含量（标量），重量是重力（矢量）
- 关系式：W = mg（g ≈ 9.8 或 10 N/kg）
- 密度 = 质量 / 体积，单位 kg/m³ 或 g/cm³
- 规则固体密度测量：刻度尺测体积 + 天平测质量
- 不规则固体密度测量：排水法（displacement method）
- 液体密度测量：量筒 + 天平
- 力的效果：改变运动状态、改变形状、改变方向
- 力的单位：牛顿（N），力是矢量
- 胡克定律：F = kx（在弹性限度内，伸长量与拉力成正比）
- 弹簧常数 k = F/x，单位 N/m
- 弹性限度（limit of proportionality）的概念

## 前置知识
- 1.1（物理量与单位）
- 1.2（速率/加速度，用于理解力的效果）

## 常见错误
- 混淆质量和重量（认为在月球上质量也变小）
- 密度单位换算错误（1 g/cm³ = 1000 kg/m³）
- 排水法读数时以液面凹面顶部为准（应以凹面底部/最低点为准）
- 胡克定律中用总长度代替伸长量 x
- 认为胡克定律在所有范围内都适用（超过弹性限度不适用）
- 忘记力是矢量，答题时不说明方向

## 可出题方向
- 计算物体的重量（给定质量和 g 值）
- 密度计算（规则/不规则物体、液体）
- 设计实验测量某物体的密度
- 胡克定律实验数据分析（表格或图像）
- 求弹簧常数 k 或伸长量 x
- 质量与重量的对比说明题

## 难度提示
Core：基础。要求学生能区分概念、进行基本计算和描述实验方法。

## 适合题型
- 计算题
- 实验设计题
- 简答题
- 数据分析题（表格/图像）
- 对比说明题

## Item-level prototype

### Question Q-2.1-01
**Difficulty**: Foundation
**Question**: State two differences between mass and weight.
**Answer**: (1) Mass is a scalar (magnitude only); weight is a vector (has direction — downwards). (2) Mass is measured in kilograms (kg); weight is measured in newtons (N). (3) Mass is constant everywhere; weight changes with gravitational field strength.
**Explanation**: Mass measures the amount of matter; weight is the gravitational force on that matter. A common error is saying "mass changes on the Moon" — mass stays the same, only weight changes because g is different.

**Tags**: mass, weight, scalar, vector

### Question Q-2.1-02
**Difficulty**: Foundation
**Question**: An astronaut has a mass of 75 kg. Calculate the astronaut's weight on Earth (g = 9.8 N/kg) and on the Moon (g = 1.6 N/kg).
**Answer**: Weight on Earth = 735 N. Weight on Moon = 120 N.
**Explanation**: W = mg. Earth: 75 × 9.8 = 735 N. Moon: 75 × 1.6 = 120 N. The astronaut's mass is the same in both places (75 kg), only weight changes. A common error is confusing the units or giving the mass as the weight.

**Tags**: weight, W=mg, calculation, gravity

### Question Q-2.1-03
**Difficulty**: Foundation
**Question**: A rectangular block has dimensions 5 cm × 4 cm × 2 cm and a mass of 160 g. Calculate its density in g/cm³ and in kg/m³.
**Answer**: 4.0 g/cm³ = 4000 kg/m³
**Explanation**: Volume = 5 × 4 × 2 = 40 cm³. Density = mass / volume = 160 / 40 = 4.0 g/cm³. Convert: 4.0 × 1000 = 4000 kg/m³. A common error is forgetting that 1 g/cm³ = 1000 kg/m³ (multiply by 1000, not 100).

**Tags**: density, calculation, unit-conversion

### Question Q-2.1-04
**Difficulty**: Standard
**Question**: Describe how you would measure the density of an irregularly shaped stone using a measuring cylinder and a balance.
**Answer**: (1) Measure the mass of the stone using the balance. (2) Partially fill the measuring cylinder with water and record the initial volume. (3) Gently lower the stone into the water and record the new volume. (4) The volume of the stone = final volume − initial volume (displacement method). (5) Calculate density = mass / volume.
**Explanation**: The displacement method works because the stone displaces a volume of water equal to its own volume. A common error is not subtracting the initial volume from the final reading, or reading the meniscus incorrectly (read from the bottom of the meniscus).

**Tags**: density, experiment, displacement-method, irregular-solid

### Question Q-2.1-05
**Difficulty**: Standard
**Question**: A spring has a natural length of 12 cm. When a 3 N weight is hung from it, the spring extends to 18 cm. Calculate the spring constant. What will the spring's length be when a 5 N weight is attached (assuming Hooke's law still applies)?
**Answer**: Spring constant k = 0.5 N/cm (or 50 N/m). Length with 5 N = 22 cm.
**Explanation**: Extension = 18 − 12 = 6 cm. k = F/x = 3/6 = 0.5 N/cm. With 5 N: extension = F/k = 5/0.5 = 10 cm. New length = 12 + 10 = 22 cm. A common error is using the total length instead of the extension in the Hooke's law formula, or forgetting to add the extension back to the natural length.

**Tags**: Hooke's-law, spring-constant, calculation, extension
