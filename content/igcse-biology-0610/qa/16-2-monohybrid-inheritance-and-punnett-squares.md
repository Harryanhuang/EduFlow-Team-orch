# QA: 16.2 — Monohybrid inheritance and Punnett squares

## Topic 名称
Monohybrid inheritance and Punnett squares（单因子遗传与庞尼特方格）

## Topic 定义
掌握单因子遗传（monohybrid inheritance）的核心术语与分析方法。等位基因（allele）是同一基因（gene）的不同版本，位于同源染色体的相同位点（locus）。基因型（genotype）是个体的等位基因组合（如 TT, Tt, tt），表现型（phenotype）是可观察的性状（如高茎/矮茎）。显性（dominant）等位基因在杂合状态下即可表达，用大写字母表示（如 T）；隐性（recessive）等位基因仅在纯合状态下表达，用小写字母表示（如 t）。纯合子（homozygous）的两个等位基因相同（TT 或 tt），杂合子（heterozygous）的两个等位基因不同（Tt）。掌握单因子杂交（monohybrid cross）的分析方法：确定亲本基因型 → 确定配子类型 → 用 Punnett square（庞尼特方格）列出所有可能的合子组合 → 计算基因型比例（genotypic ratio）和表现型比例（phenotypic ratio）。完全显性（complete dominance）时 F₂ 表现型比例为 3:1（基因型 1:2:1）；不完全显性（incomplete dominance）时杂合子表现为中间型，F₂ 比例为 1:2:1（表现型与基因型一致，如红花 × 白花 → 粉花）；共显性（co-dominance）时两个等位基因同时表达，如人类 ABO 血型中 Iᴬ 和 Iᴮ 共显性产生 AB 型。掌握测交（test cross）的原理：将表现型为显性的未知基因型个体与隐性纯合子（homozygous recessive）杂交，通过后代表型比例推断亲本基因型（若全显性则亲本为纯合显性，若 1:1 则为杂合子）。理解谱系图（pedigree diagram）的基本符号：正方形代表男性，圆形代表女性，实心/着色表示表现型患病/表达性状，水平线表示交配，垂直线表示子代。能够计算简单遗传概率（probability）：用 Punnett square 中的格子数比例或乘法定理（product rule）计算连续事件概率。

## 关键知识点
- Allele：different version of the same gene at the same locus on homologous chromosomes
- Genotype：genetic constitution of an organism（e.g., TT, Tt, tt）
- Phenotype：observable characteristic resulting from genotype and environment
- Dominant allele：expressed in phenotype even when heterozygous; represented by capital letter（T）
- Recessive allele：only expressed in phenotype when homozygous; represented by lowercase letter（t）
- Homozygous：two identical alleles（TT = homozygous dominant; tt = homozygous recessive）
- Heterozygous：two different alleles（Tt）
- Monohybrid cross：inheritance of a single characteristic controlled by one gene with two alleles
- Punnett square：grid showing all possible combinations of gametes and resulting offspring genotypes
- Complete dominance：heterozygote shows dominant phenotype; F₂ phenotypic ratio = 3:1, genotypic ratio = 1:2:1
- Incomplete dominance：heterozygote shows intermediate phenotype; F₂ phenotypic ratio = 1:2:1（e.g., snapdragon flower colour）
- Co-dominance：both alleles expressed equally in heterozygote; no intermediate（e.g., ABO blood group IᴬIᴮ = AB phenotype）
- Test cross：cross unknown genotype（showing dominant phenotype）with homozygous recessive → offspring reveal hidden genotype
- Pedigree diagrams：square = male, circle = female, shaded = affected, horizontal line = mating, vertical line = offspring
- Probability in genetics：
  - Chance of particular genotype = number of favourable squares / total squares in Punnett square
  - Product rule：probability of two independent events both occurring = multiply individual probabilities
- Codominance vs incomplete dominance：co-dominance = both traits fully visible（AB blood = both A and B antigens）; incomplete dominance = blended/intermediate trait（pink flower = not red, not white）

## 前置知识
- 16.1 Chromosomes, genes, DNA（DNA、基因、染色体、等位基因基础）
- 2.2 Cell division — meiosis（配子形成与分离定律的细胞学基础）
- 15.1 Asexual and sexual reproduction（遗传变异来源）
- 基础概率数学（fractions, ratios, percentages）

## 常见错误
- 等位基因字母大小写混用（显性必须大写，隐性必须小写，同一基因用同一字母）
- 将 genotype 与 phenotype 混淆：genotype 是基因组合，phenotype 是外观特征
- 在 Punnett square 中忘记配子为单倍体（只含一个等位基因）
- 计算比例时包含亲本代（P generation）而非仅子代（F₁/F₂）
- 不完全显性与共显性混淆：incomplete = 中间型（粉花），co-dominance = 两者同时表达（AB 血型）
- 测交时误将未知基因型与另一个显性个体杂交（正确应为与 homozygous recessive 杂交）
- 谱系图中混淆水平线（交配）与垂直线（亲子关系）
- 忘记概率计算中"and"用乘法，"or"用加法（互斥事件）
- 在 co-dominance 中试图用显性/隐性解释（如 ABO 血型中 Iᴬ 和 Iᴮ 对 i 为显性，但 Iᴬ 与 Iᴮ 之间为共显性）
- 将 3:1 比例误用于 incomplete dominance 情境（应为 1:2:1）

## 可出题方向
- 给定亲本基因型，构建 Punnett square 并计算 genotypic/phenotypic ratios
- 区分 complete dominance, incomplete dominance, co-dominance 并给出实例
- 设计测交实验推断未知基因型并预测结果
- 分析谱系图推断遗传模式（显性/隐性）并计算个体基因型概率
- 解释 Mendel's law of segregation 的细胞学基础（meiosis 中同源染色体分离）
- 计算连续两代的遗传概率（如两个杂合子婚配产生隐性后代的概率，再求连续两胎均为隐性的概率）
- 给定表现型比例反推亲本基因型（如 1:1 比例提示测交）
- 应用题：结合 ABO 血型分析亲子鉴定或输血兼容性
- 综合题：从基因 → 等位基因 → 基因型 → 表现型 → 遗传概率的完整分析
- 讨论为什么 Mendel 选择豌豆（true-breeding, easily grown, many offspring, clear contrasting traits）
