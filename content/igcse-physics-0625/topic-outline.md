# IGCSE Physics (0625) Topic Outline

基于 Cambridge IGCSE Physics (0625) 现行 syllabus。
全量覆盖 Core + Supplement（Extended 暂不覆盖）。

## 知识领域概览

| 编号 | 领域 | Topic 数量 |
|------|------|------------|
| 1 | General physics — Measurement & motion | 5 |
| 2 | General physics — Forces & energy | 6 |
| 3 | Thermal physics | 6 |
| 4 | Waves & optics | 9 |
| 5 | Electricity & magnetism | 11 |
| 6 | Nuclear physics | 5 |
| 7 | Space physics | 4 |
| **总计** | | **46** |

## Topic 列表

### 1 — General physics: Measurement & motion

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 1.1 | Physical quantities, SI units, measuring length and time | Core | 无 |
| 1.2 | Speed, velocity, acceleration, distance-time and speed-time graphs（含 scalars vs vectors、terminal velocity） | Core | 1.1 |
| 1.3 | Free fall, g, air resistance | Core | 1.2 |
| 1.4 | Mass, weight, centre of gravity | Core | 1.1 |
| 1.5 | Density, measuring density of solids and liquids | Core | 1.1 |

### 2 — General physics: Forces & energy

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 2.1 | Force as push/pull, resultant force, F=ma | Core | 1.2 |
| 2.2 | Hooke's law, spring constant, force-extension graph | Core | 1.5 |
| 2.3 | Work = Fd, energy types, conservation, Ek=½mv², Ep=mgh | Core | 1.2, 2.1 |
| 2.4 | Power = W/t, P = Fv, efficiency | Core | 2.3 |
| 2.5 | Energy resources and electricity generation | Core | 2.3 |
| 2.6 | Pressure in liquids (p=ρgh), atmospheric pressure, gas pressure | Core+S | 1.5 |

### 3 — Thermal physics

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 3.1 | Kinetic particle model: solids, liquids, gases | Core | 无 |
| 3.2 | Temperature scales, thermometers, thermal equilibrium | Core | 无 |
| 3.3 | Thermal expansion of solids, liquids, gases | Core | 3.1 |
| 3.4 | Heat transfer: conduction, convection, radiation | Core | 3.1 |
| 3.5 | Specific heat capacity, Q=mcΔT | Core+S | 2.3 |
| 3.6 | Melting, boiling, latent heat, heating/cooling curves | Core+S | 3.1, 3.5 |

### 4 — Waves & optics

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 4.1 | Wave properties: frequency, wavelength, amplitude, v=fλ | Core | 无 |
| 4.2 | Transverse vs longitudinal waves | Core | 4.1 |
| 4.3 | Wavefronts, reflection, refraction | Core | 4.1 |
| 4.4 | Light: reflection in plane mirrors, ray diagrams | Core | 4.3 |
| 4.5 | Refraction, refractive index (n=sini/sinr), critical angle, TIR | Core+S | 4.3, 4.4 |
| 4.6 | Thin converging lens: focal length, ray diagrams, magnification | Core+S | 4.3 |
| 4.7 | Electromagnetic spectrum: regions, properties, uses | Core | 4.2 |
| 4.8 | Sound: production, propagation, speed, echo, pitch, loudness | Core | 4.2 |
| 4.9 | Ultrasound: principles and applications | Core+S | 4.8 |

### 5 — Electricity & magnetism

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 5.1 | Simple magnetic phenomena, magnetic fields | Core | 无 |
| 5.2 | Electrical quantities: charge, current, emf, potential difference, resistance | Core | 无 |
| 5.3 | Electrical circuits: symbols, series and parallel, switches | Core | 5.2 |
| 5.4 | Ohm's law, V=IR, resistance of wires | Core | 5.2, 5.3 |
| 5.5 | Potential divider, thermistor, LDR | Core+S | 5.4 |
| 5.6 | Capacitors: charge storage, time-delay, smoothing | Core+S | 5.3 |
| 5.7 | Power = IV = I²R, energy = IVt, cost of electricity | Core | 5.4 |
| 5.8 | Household wiring: live, neutral, earth, plugs, fuses, circuit breakers | Core | 5.7 |
| 5.9 | Electromagnetic induction, a.c. generator, transformers | Core+S | 5.1, 5.4 |
| 5.10 | Force on a current-carrying conductor, d.c. motor, Fleming's left-hand rule | Core+S | 5.1, 5.3 |
| 5.11 | Electromagnets, relay, loudspeaker, magnetic relay | Core+S | 5.1, 5.3 |

### 6 — Nuclear physics

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 6.1 | Atomic model: nucleus, protons, neutrons, electrons, nuclide notation | Core | 无 |
| 6.2 | Radioactivity: alpha, beta, gamma, detection | Core | 6.1 |
| 6.3 | Half-life, decay curves, calculations | Core+S | 6.2 |
| 6.4 | Nuclear fission and fusion | Core+S | 6.1 |
| 6.5 | Safety, background radiation, uses of radioisotopes | Core | 6.2, 6.3 |

### 7 — Space physics

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 7.1 | Earth and Solar System, orbits | Core | 无 |
| 7.2 | Stars: life cycle, Sun as a main-sequence star | Core+S | 无 |
| 7.3 | Galaxies, universe expansion, Big Bang evidence | Core+S | 7.1, 7.2 |
| 7.4 | Gravitational field strength, weight on other planets | Core | 1.4 |

## 字段规范

- `ID`: 章节式 ID（`1.1`, `1.2`...），对应 QA 文件名中 `.` 转 `-`
- `Topic`: 英文官方或接近官方表述
- `Core/Supplement`: Core 为必做，Supplement 标注 Core+S
- `前置`: 仅填真实依赖；没有则写 `无`

## 产出约束

- topic-outline 只定义范围、层级、先修、覆盖关系
- 不在 outline 中写长篇教学解释
- 每个 outline 条目都必须能一一映射到一个 QA 文件

## QA 配套

每个 topic 对应一份 QA 文件，详见 `qa/` 目录。
QA 文件命名约定：`<topic-id>-<topic-slug>.md`，例如 `1-1-physical-quantities-measurement.md`。
