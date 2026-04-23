# qd-company-research | 千丁公司深度研究工具

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
用 qd-company-research 研究一下 [公司名或股票代码]
```

系统自动并行执行 6 个研究流（财务/业务/战略/领导思维/批判/文化），完成后：
1. 展示采集 Review（来源数、关键发现、认知提取进度）
2. 进行认知验证（用已知决策测试思维模型预测能力）
3. 生成 `company-skill.md` 和 Web Report
4. 询问归档方式（飞书知识库 / 更新千丁上下文 / 生成 Obsidian 卡片）

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

技术栈：React 18 + Tailwind + Chart.js + D3.js，单 HTML 文件，部署至 `/var/www/proletson.me/html/`

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

**项目路径**：`~/.openclaw/workspace/skills/qd-company-research/`
