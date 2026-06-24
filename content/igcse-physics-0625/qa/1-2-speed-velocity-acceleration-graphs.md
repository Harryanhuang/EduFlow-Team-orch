# QA: 1.2 — Speed, velocity, acceleration, distance-time and speed-time graphs

## Topic 名称
Speed, velocity, acceleration, distance-time and speed-time graphs（速率、速度、加速度、距离-时间图与速率-时间图）

## Topic 定义
学习描述物体运动的基本物理量：速率、速度、加速度的定义与计算，以及用距离-时间图和速率-时间图分析物体的运动状态。

## 关键知识点
- 速率 = 距离 / 时间（标量），速度 = 位移 / 时间（矢量）
- 加速度 = 速度变化量 / 时间，单位 m/s²
- 匀速运动 vs 变速运动
- 距离-时间图（distance-time graph）：斜率 = 速率，水平线 = 静止
- 速率-时间图（speed-time graph）：斜率 = 加速度，图线下面积 = 距离
- 从图像判断运动状态（加速、减速、匀速、静止）
- 重力加速度 g ≈ 9.8 m/s²（或考试给定为 10 m/s²）
- terminal velocity（终端速度）：自由落体时空气阻力随速度增大而增大，当空气阻力与重力平衡时，物体加速度为零，以恒定速度下落

## 前置知识
- 1.1（物理量与单位）

## 常见错误
- 混淆速率（标量）和速度（矢量）
- 距离-时间图中把纵坐标值当成速率（应看斜率）
- 速率-时间图下面积计算时分段遗漏或单位错误
- 认为速度为零时加速度也一定为零（如竖直上抛最高点）
- 读图时忽略坐标轴单位
- 认为自由落体一直在加速（忽略终端速度的存在：空气阻力与重力平衡后匀速下落）
- 认为终端速度与物体质量无关（实际上质量越大，终端速度越大）

## 可出题方向
- 根据 distance-time graph 求某段速率
- 根据 speed-time graph 求加速度和总距离
- 给定运动数据画图或补全图像
- 计算题：已知初速度、末速度和时间求加速度
- 自由落体相关计算（忽略空气阻力）
- terminal velocity：解释自由落体过程中力和加速度的变化（重力不变、空气阻力增大、合力减小至零），或从 speed-time graph 上识别终端速度（曲线最终变平）

## 难度提示
Core：基础。要求学生能用公式计算和从图像中提取运动信息。

## 适合题型
- 计算题
- 图像分析题
- 简答题（解释运动状态）
- 画图题

## Item-level prototype

### Question Q-1.2-01
**Difficulty**: Foundation
**Question**: A car increases its speed from 10 m/s to 25 m/s in 5.0 s. Calculate its acceleration.
**Answer**: 3.0 m/s^2
**Explanation**: Use acceleration = change in velocity / time. The change in velocity is 25 - 10 = 15 m/s. Then 15 / 5.0 = 3.0 m/s^2. Students often give the speed change without dividing by time, or omit the squared unit.
**Tags**: acceleration, kinematics, formula-application

### Question Q-1.2-02
**Difficulty**: Foundation
**Question**: A train travels at a constant speed of 30 m/s for 4 minutes. Calculate the distance travelled in kilometres.
**Answer**: 7.2 km
**Explanation**: Distance = speed × time = 30 × (4 × 60) = 30 × 240 = 7200 m = 7.2 km. A common error is forgetting to convert minutes to seconds (30 × 4 = 120 m) or forgetting to convert metres to kilometres.

**Tags**: speed, distance, unit-conversion, constant-speed

### Question Q-1.2-03
**Difficulty**: Foundation
**Question**: On a distance-time graph, what does each of the following represent: (a) a straight line with positive gradient, (b) a horizontal line, (c) a curve with increasing gradient?
**Answer**: (a) Constant speed. (b) Stationary (at rest). (c) Accelerating (speed increasing).
**Explanation**: The gradient of a distance-time graph equals speed. Constant gradient = constant speed, zero gradient = zero speed, increasing gradient = increasing speed. A common error is saying a curve means "moving faster" without recognising that increasing gradient specifically means acceleration.

**Tags**: distance-time-graph, gradient, speed, acceleration

### Question Q-1.2-04
**Difficulty**: Standard
**Question**: A speed-time graph shows a straight line from (0, 0) to (8 s, 16 m/s). Calculate: (a) the acceleration, (b) the distance travelled in 8 s.
**Answer**: (a) 2.0 m/s². (b) 64 m.
**Explanation**: (a) Acceleration = gradient = 16 / 8 = 2.0 m/s². (b) Distance = area under graph = ½ × 8 × 16 = 64 m. A common error is using distance = speed × time with the final speed (16 × 8 = 128 m) instead of calculating the area under the graph.

**Tags**: speed-time-graph, acceleration, area-under-graph

### Question Q-1.2-05
**Difficulty**: Standard
**Question**: Explain why a skydiver reaches a terminal velocity when falling through the air. Describe how the forces change from the moment of jumping until terminal velocity is reached.
**Answer**: Initially, weight (downward) is much greater than air resistance (upward), so there is a large resultant downward force and the skydiver accelerates. As speed increases, air resistance increases. The resultant force decreases, so acceleration decreases. Eventually, air resistance equals weight — the resultant force is zero and the skydiver falls at constant terminal velocity.
**Explanation**: The key point is that air resistance depends on speed — it increases as speed increases. A common error is saying air resistance "becomes greater than weight" at terminal velocity. At terminal velocity, the forces are equal and balanced, giving zero acceleration, not deceleration.

**Tags**: terminal-velocity, air-resistance, forces, free-fall
