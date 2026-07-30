# 🎲 DynBet

**可扩展的下注策略蒙特卡洛回测框架**

`Game` / `Vault` / `Strategy` 三段式解耦，每种下注策略都可以用 `.apply()` 装饰器链自由组合，跑基准测试看看到底「谁能跑得更远」。

---

## ✨ 特性

- 🧩 **三段式解耦**：赌局（Game）/ 资金库（Vault）/ 策略（Strategy）各自独立，插拔式扩展
- 🔗 **策略链式组合**：`Strategy().apply(Flat(10)).apply(DAlembert())` 一套装饰器搞定任意复合策略
- 📊 **内置可视化**：余额曲线 + 4 宫格统计图（最终余额 / 峰值 / 回撤 / 存活率）开箱即用
- 🌏 **全中文报告**：基准测试输出智能洞察（庄边、胜率、爆仓率、冠军策略分析）
- 🧪 **无第三方核心依赖**：核心逻辑纯标准库，仅可视化需 `matplotlib`

---

## 📦 安装

```bash
# 仅核心逻辑（纯标准库，跑策略）
# 无额外依赖

# 跑基准测试 + 画图
pip install matplotlib
```

---

## 🚀 快速开始

### 1. 写一个自定义策略

```python
from strategy import Strategy
from vault import Vault
from data import Data

class MyStrategy(Strategy):
    def bet(self, vault: Vault, data: Data) -> Vault:
        # data.nodes 是历史下注序列，可回溯任意历史状态
        vault.withdrawal = vault.withdrawal * 2  # 简单示例：每手翻倍
        return vault
```

### 2. 组合策略

```python
from strategy import Flat, Ratio, Martingale, DAlembert, Fibonacci, Stepping, Labouchere, Peak

# 平注 10 起步 + 达朗贝尔
s = Strategy().apply(Flat(10.0)).apply(DAlembert())

# 🔥 马丁格尔（输了加注 ×2，赢了回原点）
s = Strategy().apply(Flat(10.0)).apply(Martingale())

# 🔥 反马丁格尔 / 正马丁格尔（赢了加注 ×2，输了回原点）
s = Strategy().apply(Flat(10.0)).apply(Martingale(reverse=True))

# 1% 资金比例下注
s = Strategy().apply(Allin()).apply(Ratio(0.01))

# 1326 系统（1,3,2,6 步进）
s = Strategy().apply(Flat(10.0)).apply(Stepping([1, 3, 2, 6]))

# 锁利：破新高用 2%，没破用 1%
s = Peak(
    Strategy().apply(Allin()).apply(Ratio(0.02))
).apply(
    Strategy().apply(Allin()).apply(Ratio(0.01))
)

# 拉布谢尔序列 [10,20,30,40]
s = (Labouchere(Flat(10.0))
    .apply(Flat(10.0)).apply(Flat(20.0))
    .apply(Flat(30.0)).apply(Flat(40.0)))
```

### 3. 跑基准测试

```bash
python bench.py
```

输出示例：

```
Battle: 10000 回合, Vault(10000.0, 10.0), 骰宝大小单双, seed=42, 胜率 = 48.62%

Flat 10 (Baseline)        | 最终:     7200.0 | 峰值:    10100.0 | 回撤:  31.2% | [亏损]
1% Bankroll               | 最终:      612.3 | 峰值:    11998.7 | 回撤:  96.3% | [亏损]
DAlembert                 | 最终:        0.0 | 峰值:    12500.0 | 回撤: 100.0% | [爆仓]
...
======================================================================
大横评总结报告: 10000 回合, 骰宝大小单双 (胜率 48.62%)
======================================================================
庄边 +2.76%/手。Flat 10 连下 10000 回合，预期盈亏 = $-2760。

洞察分析:
  * 庄家优势 2.76%，长期看数学期望为负，不建议持续高频下注。
  * 胜率 48.62% 接近公平赔率，短期运气能掩盖庄边，但长期必亏。
  * 爆仓率 30% (3/10)，步进策略在负EV下加速破产。
```

并弹出两张图：**策略余额曲线对比图** + **4 宫格统计图**。

---

## 📂 项目结构

```
DynBet/
├── game.py          # Game 抽象基类（赌局接口）
├── vault.py         # Vault 资金库（余额 + withdrawal + 结算）
├── strategy.py     # 内置策略：Flat / Ratio / Martingale / DAlembert / Fibonacci / Stepping / Labouchere / Peak ...
├── session.py       # Session 回合驱动器
├── data.py          # Data / Node 历史节点（可回溯任意手牌状态）
├── visualize.py     # 画图辅助（Visualizer）
├── utils.py         # 工具函数（positive / same / LCList ...）
├── bench.py         # ✨ 12 策略基准测试（开箱即用，含马丁/反马丁）
├── example.ipynb    # Jupyter 示例
└── strategy_benchmark_report.md  # 20 种子 × 12 策略 完整回测报告
```

---

## 🧠 核心设计

### Game / Vault / Strategy 各司其职

```
┌─────────┐   bet    ┌─────────┐  once()   ┌─────────┐
│ Strategy│ ───────▶ │  Vault  │ ────────▶ │  Game   │
│.apply() │          │withdraw │           │.random()│
└─────────┘          └─────────┘ ◀──────── └─────────┘
                            ▲    result
                            │
                       Data/Node 记录历史
```

- **Game**：只管抽卡 `random()` / 结算 `once(bet)`，可替换成 21 点/百家乐/轮盘…
- **Vault**：只管 `money` 余额 / `withdrawal` 下一手注码 / `result` 结算
- **Strategy**：只读 `vault` + `data`（历史节点），决定下一手注码
- **Data + Node**：完整序列，策略可回看任意历史手（达朗贝尔、拉布谢尔都靠这个实现）

### 可选停时定理友好

任意策略组合都可以和纯平注比数学期望 —— 因为框架保证了「每手独立、下注金额只依赖历史状态」，经典概率定理直接适用。

---

## 🏆 20 次蒙特卡洛回测速览

核心结论（48.6% 胜率的骰宝，1 万回合 × 20 颗种子，**共 12 策略，新增马丁/反马丁**）：

| 策略 | 跑赢数学期望概率 | 平均终值 | 最好成绩 | 爆仓率 |
| :-- | :-: | :-: | :-: | :-: |
| Labouchere 拉布谢尔 | 55% | $6,912 | $9,190 | 10% |
| Flat 10 平注 | 25% | $6,901 | $9,200 | 0% |
| 🔥 **Martingale 马丁格尔** | **15%** | **$6,038** | **$53,300 🚀** | **85%** |
| Paroli 1-2-4 | 10% | $4,746 | $7,620 | 0% |
| 1326 System | 5% | $4,210 | $7,720 | 5% |
| 1%/2% Kelly / Peak 锁利 | 0% | $9~$912 | $4,867 | 0~100% |
| 💀 **Rev.Mart 反马丁格尔** | **0%** | **$0** | **$0** | **100%** |
| DAlembert / Fibonacci / Rev.D'Al | **0%** | **$0** | **$0** | **100%** |

### 🎯 马丁格尔的关键洞察

> **Martingale = 85% 概率爆仓归零，15% 概率暴富到 $53,300（翻 5.3 倍）**
>
> 极端偏态分布：中位数 $0，95 分位 $46,060 —— 典型的「吃小亏，撞大运」策略。
> **反马丁格尔（赢了加注）则是 20/20 全灭，比正马丁还差。**

> **一句话总结：负 EV 下，不玩就是赢；非要玩，温和的拉布谢尔或纯平注是唯一不把自己玩死的方式。**

---

## 🤝 欢迎贡献

- ➕ 新游戏：继承 `Game` 实现 `once(bet: float) -> float | None` 即可
- ➕ 新策略：继承 `Strategy` 实现 `bet(vault, data)` 即可
- 🐛 Issue / PR 都欢迎

---

## 📜 License

MIT

> ⚠️ **免责声明：本项目仅供概率研究与策略学习。真实赌场永远是负 EV，不要沉迷赌博。**