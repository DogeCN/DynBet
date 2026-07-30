from session import Session, Vault, Strategy
from strategy import (
    Flat,
    Allin,
    Ratio,
    Martingale,
    DAlembert,
    Fibonacci,
    Stepping,
    Labouchere,
    Peak,
)
from game import Game
from visualize import Visualizer
from utils import positive, same
from functools import cached_property
import random


class Dice(Game):
    def __init__(self, dice: list[int], amount: int, rate: float):
        self.dice = dice
        if not positive(self.length, amount, rate):
            raise ValueError
        self.amount = amount
        self.rate = rate

    def once(self, bet: float) -> float | None:
        if self.random():
            return bet * self.rate

    def random(self) -> bool:
        result = [self.roll() for _ in range(self.amount)]
        if same(result):
            return False
        total = sum(result)
        return total >= self.mean

    def roll(self):
        return random.choice(self.dice)

    @property
    def length(self):
        return len(self.dice)

    @cached_property
    def mean(self):
        return (sum(self.dice) * self.amount + self.length - 1) // self.length


def money(session: Session):
    return [n.vault.money for n in session.data.nodes]


ROUNDS = 10000
INITIAL = 10000.0
SEED = random.random()
dice = Dice([i for i in range(1, 7)], 3, 2.0)


def run(strategy, rounds=ROUNDS, seed=SEED):
    # 每次固定种子保证各策略面对相同骰子序列
    random.seed(seed)
    v = Vault(INITIAL, 10.0)
    # 用 Dice 游戏跑指定轮数
    s = Session(dice, v)
    for _ in range(rounds):
        if v.money <= 0:
            break
        s.run(strategy)
    return s


# 待测策略: 平注 / 比例 / 负渐进 / 正渐进 / 取消系统 / 自适应
strategies = {
    "Flat 10 (Baseline)": Flat(10.0),
    "1% Bankroll": Strategy().apply(Allin()).apply(Ratio(0.01)),
    "2% Bankroll": Strategy().apply(Allin()).apply(Ratio(0.02)),
    "Martingale": Strategy().apply(Flat(10.0)).apply(Martingale()),
    "Rev. Martingale": Strategy().apply(Flat(10.0)).apply(Martingale(reverse=True)),
    "DAlembert": Strategy().apply(Flat(10.0)).apply(DAlembert()),
    "Rev. DAlembert": Strategy().apply(Flat(10.0)).apply(DAlembert(reverse=True)),
    "Fibonacci": Strategy().apply(Flat(10.0)).apply(Fibonacci()),
    "1326 System": Strategy().apply(Flat(10.0)).apply(Stepping([1, 3, 2, 6])),
    "Paroli 1-2-4": Strategy().apply(Flat(10.0)).apply(Stepping([1, 2, 4])),
    "Labouchere": Labouchere(Flat(10.0))
    .apply(Flat(10.0))
    .apply(Flat(20.0))
    .apply(Flat(30.0))
    .apply(Flat(40.0)),
    "Peak -> 2%, else 1%": Peak(Strategy().apply(Allin()).apply(Ratio(0.02))).apply(
        Strategy().apply(Allin()).apply(Ratio(0.01))
    ),
}

random.seed(SEED)
win_count = 0
for _ in range(ROUNDS):
    if dice.random():
        win_count += 1
WIN_RATE = win_count / ROUNDS * 100
BET = 10.0
PAYOUT = 2.0
EXPECTED_FINAL = INITIAL + ROUNDS * BET * (WIN_RATE / 100 * PAYOUT - 1)

print(
    f"Battle: {ROUNDS} 回合, Vault({INITIAL}, {BET}), 骰宝大小单双, seed={SEED}, 胜率 = {WIN_RATE:.2f}%\n"
)
results = {}

for name, strategy in strategies.items():
    try:
        session = run(strategy)
        balances = money(session)
        final = balances[-1]
        peak = max(balances)
        low = min(balances)
        drawdown = (peak - low) / peak * 100 if peak > 0 else 0
        busted = final <= 0

        results[name] = {
            "balances": balances,
            "final": final,
            "peak": peak,
            "min": low,
            "drawdown": drawdown,
            "busted": busted,
        }

        status = "[爆仓]" if busted else ("[盈利]" if final > INITIAL else "[亏损]")
        print(
            f"{name:<25} | 最终: {final:>10.1f} | 峰值: {peak:>10.1f} | 回撤: {drawdown:>5.1f}% | {status}"
        )
    except Exception as e:
        print(f"{name:<25} | [失败] {str(e)[:60]}")
        results[name] = None

# --- 余额曲线 ---
viz = Visualizer(f"策略大横评 - {ROUNDS} 回合实战对比", "回合数", "余额 ($)")

sorted_results = sorted(
    [(n, d) for n, d in results.items() if d],
    key=lambda x: x[1]["final"],
    reverse=True,
)

colors = [
    "#FF6B6B",
    "#4ECDC4",
    "#45B7D1",
    "#96CEB4",
    "#FFEAA7",
    "#DDA0DD",
    "#98D8C8",
    "#F7DC6F",
    "#BB8FCE",
    "#85C1E9",
]

for i, (name, data) in enumerate(sorted_results):
    viz.add(
        data["balances"],
        f"{name} (${data['final']:.0f})",
        color=colors[i % len(colors)],
        alpha=0.8,
    )

viz.hline(INITIAL, f"初始资金 ${INITIAL:.0f}", color="gray", linestyle="--")
viz.hline(
    EXPECTED_FINAL,
    f"期望终点 ${EXPECTED_FINAL:.0f} (胜率 {WIN_RATE:.2f}%)",
    color="red",
    linestyle=":",
).show()

# --- 统计图 ---
import matplotlib.pyplot as plt

valid = {n: d for n, d in results.items() if d}

if valid:
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    names = list(valid.keys())
    finals = [valid[n]["final"] for n in names]
    peaks = [valid[n]["peak"] for n in names]
    drawdowns = [valid[n]["drawdown"] for n in names]
    survival = [0 if valid[n]["busted"] else 1 for n in names]

    axes[0, 0].barh(
        names, finals, color=["#4CAF50" if f > INITIAL else "#F44336" for f in finals]
    )
    axes[0, 0].axvline(x=INITIAL, color="gray", linestyle="--", label="初始资金")
    axes[0, 0].set_title("最终余额对比")
    axes[0, 0].set_xlabel("余额 ($)")

    axes[0, 1].barh(names, peaks, color="#2196F3")
    axes[0, 1].axvline(x=INITIAL, color="gray", linestyle="--", label="初始资金")
    axes[0, 1].set_title("峰值余额对比")
    axes[0, 1].set_xlabel("余额 ($)")

    axes[1, 0].barh(names, drawdowns, color="#FF9800")
    axes[1, 0].set_title("最大回撤率 (%)")
    axes[1, 0].set_xlabel("回撤率 (%)")

    axes[1, 1].barh(
        names, survival, color=["#4CAF50" if s else "#F44336" for s in survival]
    )
    axes[1, 1].set_title("存活率 (1=存活, 0=爆仓)")
    axes[1, 1].set_xlabel("存活状态")

    plt.tight_layout()
    plt.show()

# --- 总结报告 ---
print("\n" + "=" * 70)
print(f"大横评总结报告: {ROUNDS} 回合, 骰宝大小单双 (胜率 {WIN_RATE:.2f}%)")
print("=" * 70)

winners = [(n, d) for n, d in results.items() if d and d["final"] > INITIAL]
losers = [(n, d) for n, d in results.items() if d and 0 < d["final"] <= INITIAL]
busted = [(n, d) for n, d in results.items() if d and d["final"] <= 0]

print(f"\n盈利策略 ({len(winners)}/{len(results)}):")
for i, (name, data) in enumerate(
    sorted(winners, key=lambda x: x[1]["final"], reverse=True), 1
):
    pct = (data["final"] - INITIAL) / INITIAL * 100
    print(
        f"  {i}. {name:<23} {pct:>+7.1f}%  (峰值: ${data['peak']:.0f}, 回撤: {data['drawdown']:.1f}%)"
    )

print(f"\n亏损但存活 ({len(losers)}/{len(results)}):")
for i, (name, data) in enumerate(
    sorted(losers, key=lambda x: x[1]["final"], reverse=True), 1
):
    pct = (data["final"] - INITIAL) / INITIAL * 100
    print(
        f"  {i}. {name:<23} {pct:>+7.1f}%  (最低: ${data['min']:.0f}, 回撤: {data['drawdown']:.1f}%)"
    )

if busted:
    print(f"\n爆仓清零 ({len(busted)}/{len(results)}):")
    for name, data in busted:
        print(f"  - {name:<23} 血本无归")

if winners:
    best = max(winners, key=lambda x: x[1]["final"])
    print(f"\n冠军策略: {best[0]}")
    print(
        f"   最终余额: ${best[1]['final']:.2f}  ({(best[1]['final']-INITIAL)/INITIAL*100:+.2f}%)"
    )
    print(f"   峰值余额: ${best[1]['peak']:.2f}  最大回撤: {best[1]['drawdown']:.1f}%")

print("\n" + "=" * 70)
HOUSE_EDGE = (100 - WIN_RATE * PAYOUT) / 100 * 100
EXPECTED_LOSS = ROUNDS * BET * HOUSE_EDGE / 100
print(
    f"庄边 {HOUSE_EDGE:+.2f}%/手。Flat {BET:.0f} 连下 {ROUNDS} 回合，预期盈亏 = ${-EXPECTED_LOSS:+.0f}。"
)

print("\n洞察分析:")

if HOUSE_EDGE > 0:
    print(f"  * 庄家优势 {HOUSE_EDGE:.2f}%，长期看数学期望为负，不建议持续高频下注。")
    if WIN_RATE >= 47 and WIN_RATE <= 50:
        print(
            f"  * 胜率 {WIN_RATE:.2f}% 接近公平赔率，短期运气能掩盖庄边，但长期必亏。"
        )
    elif WIN_RATE < 47:
        print(f"  * 胜率仅 {WIN_RATE:.2f}%，庄边极为明显，远离此类游戏。")
elif HOUSE_EDGE < 0:
    print(f"  * 玩家优势 {-HOUSE_EDGE:.2f}%！数学期望为正，凯利公式最大化长期收益。")
else:
    print(f"  * 庄边≈0，完全公平赌局，比拼的是资金管理和心理素质。")

bust_count = len([d for d in results.values() if d and d["busted"]])
total_valid = len([d for d in results.values() if d])
if bust_count > 0:
    bust_rate = bust_count / total_valid * 100
    print(
        f"  * 爆仓率 {bust_rate:.0f}% ({bust_count}/{total_valid})，步进策略在负EV下加速破产。"
    )

winners_any = [(n, d) for n, d in results.items() if d and d["final"] > INITIAL]
if winners_any:
    avg_dd = sum(d["drawdown"] for _, d in winners_any) / len(winners_any)
    if avg_dd > 50:
        print(f"  * 盈利策略平均回撤 {avg_dd:.0f}%，大起大落，心理素质要求极高。")
    elif avg_dd > 20:
        print(f"  * 盈利策略平均回撤 {avg_dd:.0f}%，波动可控，但仍需风控。")
    else:
        print(f"  * 盈利策略平均回撤仅 {avg_dd:.0f}%，这条策略曲线非常稳健。")

proportional_names = ["Bankroll", "Ratio"]
step_names = [
    "Martingale",
    "DAlembert",
    "Fibonacci",
    "Labouchere",
    "Stepping",
    "1326",
    "Paroli",
]
flat_names = ["Flat", "Baseline"]
busted_set = {n for n, d in results.items() if d and d["busted"]}

if any(any(k in n for k in step_names) for n in busted_set):
    print("  * 所有「负渐进/序列系统」全部爆仓，马丁格尔类策略请慎用。")
elif winners:
    winner_name = best[0]
    if any(k in winner_name for k in proportional_names):
        print(f"  * 冠军「{winner_name}」是比例下注，负EV下比例下注是最优风控。")
    elif any(k in winner_name for k in flat_names):
        print(f"  * 冠军「{winner_name}」是平注，简单就是美，其他花式都是徒增方差。")
    elif any(k in winner_name for k in step_names):
        print(f"  * 冠军「{winner_name}」是步进系统，此轮运气占主要成分，不可复制。")
    else:
        print(f"  * 冠军「{winner_name}」，混合策略展现了组合优势。")

if HOUSE_EDGE > 0 and any("Peak" in n for n, d in results.items() if d):
    peak_results = [(n, d) for n, d in results.items() if d and "Peak" in n]
    if peak_results:
        best_peak = min(peak_results, key=lambda x: x[1]["drawdown"])
        peak_pct = best_peak[1]["peak"]
        low_pct = best_peak[1]["min"]
        print(
            f"  * Peak 锁利类中「{best_peak[0]}」从峰值 ${peak_pct:.0f} 回撤至 ${low_pct:.0f}，"
            f"最大回撤 {best_peak[1]['drawdown']:.2f}%，风控可参考。"
        )

print("=" * 70)
