---
name: qd-company-research
description: "千丁公司深度研究工具 v4.0：提取目标公司的思维模型，生成可复用的 AI Skill，并输出龙湖配色 Web Report。"
---

千丁（Qianding）是龙湖集团旗下数字科技子公司。

## 核心目标

提取目标公司的认知操作系统（思维模型、决策启发式、价值观），生成可复用的 AI Skill，让千丁团队站在巨人的认知肩膀上。

## 五阶段流程

1. **身份确认**：确认公司唯一标识（全称、股票代码、上市地）
2. **六路采集**：并行采集财务、业务、战略、领导思维、批判视角、文化符号
3. **认知提取**：从采集结果中提取思维模型，应用三重验证（跨域/预测/排他）
4. **双重产出**：生成 `company-skill.md`（可加载的 AI Skill）+ Web Report（含认知可视化）
5. **归档交付**：存入飞书知识库、更新千丁上下文、生成 Obsidian 卡片

## 输出产物

### company-skill.md
可直接在 Claude Code 中 `\load` 使用的公司认知 Skill，包含：
- Mental Models（思维模型）
- Decision Heuristics（决策启发式）
- Values & Anti-patterns（价值观与禁忌）
- Honest Limits（诚实边界）
- Expression DNA（表达特征）
- 千丁启示（认知迁移、风险对照、决策模式参考）

### Web Report
单文件 HTML 页面，包含财务概览、业务分部、估值对标、认知层可视化（D3.js 网络图）。

## 使用方式

```bash
用 qd-company-research 研究一下 [公司名或股票代码]
```

系统自动并行执行 6 个研究流，完成后生成产出并询问归档方式。

## 质量要求

- 每条思维模型必须标注来源、验证状态、置信度
- 三重验证至少满足两项方可进入核心 Skill
- 保留矛盾观点，不调和
- 对未知问题主动标注不确定性
