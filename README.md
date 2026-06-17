# 千丁公司深度研究工具

**提取目标公司认知操作系统，生成可复用的 AI Skill**

---

## 核心价值

将公司研究流程转化为自动化工作流，输出：
- **company-skill.md**：可直接 `\load` 的 AI Skill（思维模型 + 决策启发式 + 价值观）
- **Web Report**：龙湖配色 HTML 报告（含认知层可视化）

**研究周期**：3-5 天 → 1-2 小时

---

## 使用方式

```bash
python run_improved.py [company] --research-dir output
```

当前入口处理**已有研究文件**，不自动启动六路采集。流程为：
1. 确认公司身份和研究目录
2. 检查 6 路研究文件和 cognitive 文件是否齐全
3. 展示采集 Review（来源数、关键发现、认知提取进度）
4. 对 cognitive 文件进行三重验证
5. 生成 `company-skill.md`

如果需要补齐研究，推荐的 AI 执行方式不是串行跑完 A/B/C/D/E/F，而是“主管 + 六路研究员”的并行模式：

1. 主管同时启动 A 财务、B 业务、C 战略、D 领导思维、E 批判视角、F 文化符号六路研究。
2. 每一路完成后单独向用户汇报摘要、来源质量、不确定性和产物路径，并等待确认。
3. 用户可以只要求某一路返工；已确认的其他研究流不受影响。
4. 六路全部确认后，再进入 Review 汇总、认知提取和质量检查。

本地 `run_improved.py` 仍只负责处理已经落盘的研究文件；并行研究属于 AI 执行层的协作协议。

如果只想生成阶段性 Review：

```bash
python run_improved.py [company] --research-dir output --review-only
```

---

## 输出产物

### company-skill.md 结构

```markdown
---
name: [company]-perspective
description: [Company] 的认知操作系统
version: 4.0-extracted
source: qd-company-research
---

## Mental Models（思维模型）
### 1. [模型名称]
- **核心**: 一句话描述
- **来源证据**: [✅跨域] D流 + C流
- **预测验证**: 解释过哪些决策（吻合度 85%）
- **排他性**: [✅排他]/[⚠️通用]
- **confidence**: high

## Decision Heuristics（决策启发式）
...

## Values & Anti-patterns（价值观与禁忌）
...

## Honest Limits（诚实的局限）
...

## 千丁启示（Qianding Mapping）
- 可借鉴的思维模型
- 风险对照
- 决策模式参考
```

### Web Report 模块

1. 财务概览（3-5 年趋势）
2. 业务分部 Master-Detail
3. 估值对标（可比公司 + 溢价计算）
4. 千丁启示（认知迁移、风险对照、决策模式参考）
5. **认知层可视化**（D3.js 思维网络图、决策启发式卡片、验证状态标色）

Web Report 目前是目标产物设计，尚未由 `run_improved.py` 自动生成。若需要交付 HTML，应基于已生成的 `company-skill.md` 和研究文件另行生成。

---

## 质量要求

- 每条思维模型必须标注：**来源 + 验证状态 + confidence**
- 三重验证至少满足两项方可进入核心 Skill（跨域出现 / 预测能力 / 排他性）
- 保留矛盾观点，不强行统一
- 对未知问题主动标注不确定性
- 所有模型可追溯至原始来源

---

## 与千丁的关联

- **认知迁移**：目标公司哪些思维模型值得千丁借鉴？
- **风险对照**：目标公司的认知盲区，千丁是否有类似风险？
- **决策模式参考**：千丁未来遇到类似战略岔路口时，可参考该公司的决策启发式

---

**默认研究目录**：仓库内 `output/`，也可以通过 `--research-dir` 指定。
