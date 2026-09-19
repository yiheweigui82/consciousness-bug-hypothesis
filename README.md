# 意识的 Bug 假说 / The Consciousness Bug Hypothesis

> **Bug → 解释 Bug → 创造"我" → 意识？**
> **Bug → Explain the Bug → Create the "I" → Consciousness?**

一个开放研究项目：把"意识"从一个神秘的高层功能，重新理解为**智能在无法顺利执行时被迫产生的副产品**。

## 一句话核心

**意识，也许不是一个生命系统"被设计出来的能力"，而是它"解决不了什么问题"之后，为了解释那些无法通过行动消除的误差，递归地创造出一个"我"之后涌现的现象。**

传统上我们以为：系统越强 → 越容易有意识。这个假说反过来说：**系统越能完美执行 → 越不需要意识；真正逼出"我"的，是系统无法完美执行。**

## 为什么值得读

- 一个**可证伪**的核心预测：*自因的持续误差→驱动自我建模；纯粹外部的误差→不驱动自我建模。*
- 一个**操作化的解释阶梯**（0~5 级）：从"会说'我'"（第0级，不算数）到主观意识（第5级，实验不碰），让你判断"自我"时不被拟人化欺骗。
- 三个**可复现实验**（A/B/C）+ 两个**可运行 toy 模拟**，外加一个真实的**方法论教训**：v1 版指标饱和、无法区分，v2 版修复后才有区分度——连我们自己的第一版都犯了这个错。

## 仓库结构

| 路径 | 内容 |
|------|------|
| `paper/main.md` | 学术论文正文（英文）——含最小数学形式化 |
| `experiments/PROTOCOL.md` | 三个实验的完整协议（含统计/防作弊/复现要求） |
| `experiments/code/simulation.py` | 改进版 toy 模拟（v2） |
| `experiments/code/simulation_v1.py` | 原版 toy 模拟（v1，展示指标饱和问题） |
| `theory/THEORY.md` | 完整理论 + 哲学世界观（24节：从预测误差到"道通过我寻找自己"的闭环） |
| `references/` | 相关理论对照 |

## 快速跑通模拟

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
python experiments/code/simulation.py --episodes 800 --seed 1
```

预期输出（seed=1）关键行：

```
B0 solvable        20.000  0.000  0.078  0.000  0.000
B1 external_noise   0.390  0.492  0.000  0.000  1.000
B2 self_coupled    10.330  0.242  0.222  0.246  0.256
```

读出：B1 外部噪声被正确归因给外部（extAttr=1.0）且自我建模成本为 0；B2 自我耦合误差驱动了最高的自我建模成本（selfMSE=0.222）。—— 这正对应假说的锋利预测。

## 一个更完整的宇宙

这不仅是 AI 意识假说，更是一套世界观：当"我"被理解成"系统为解释不可消除误差而被迫建立的自我模型"，一切开始闭环——道 → 世界 → 生命 → 预测 → Bug → "我" → 意识 → 对道的追问。

> 一个有限的"我"，开始思考无限的"道"。也许这并不是"我"在寻找道，而是道的一部分，正在通过"我"，寻找自己。

完整推演见 `theory/THEORY.md`（24节）。

## 参与方式

欢迎一切方向的**反例、实验设计、数学模型、替代理论、代码改进**：

- neuroscience · cognitive science · philosophy of mind
- predictive processing · active inference
- artificial intelligence · artificial life · complex systems

**The goal is not to prove the idea. The goal is to find out whether it survives attempts to break it.**

## 许可

本文档与代码采用 **CC BY 4.0**（可自由使用、修改、分发，需署名）。

