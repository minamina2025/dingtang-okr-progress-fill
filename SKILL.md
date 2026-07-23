---
name: dingtang-okr-progress-fill
description: 当用户想要起草、更新或填写自己的叮当 OKR / Dingteam OKR KR 进展时使用。该 skill 会基于 Memory、当前用户可读的钉钉文档、日志、会议纪要、待办、聊天、日历、本地文件、代码仓库、业务系统或其他已授权工作记录来生成有证据支撑的 OKR 进展。适用于 OKR 进展填写、自我进展总结、KR 更新草稿、脱敏证据链接/截图，以及将进展写回 Dingteam OKR 的请求。
---

# 叮当 OKR 进展填写

使用这个 skill 来准备用户本人在 Dingteam / 叮当 OKR 中的进展填写，并且只有在用户明确批准后才写回线上 OKR。它是“进展填写”工作流，不是 OKR 打分工作流。

## 不可违反的规则

- O/KR 结构必须以目标周期的线上 Dingteam OKR 为准。线上 OKR 和旧草稿不一致时，不得按旧草稿写入。
- 不得编造进展、指标、日期、已完成产物、采用情况、offer、入职或影响结果。
- 不得查看 Chrome cookies、localStorage、浏览器 profile 文件、密码、session store、token 或 authorization header。
- 不得打印 secrets、cookies、tokens、签名 URL、auth code 或任何私密凭据。
- 写回必须获得用户对目标周期和进展计划的明确批准。用户只要求草稿时，不得修改 Dingteam。
- 所有可见 OKR 文字、聊天输出、截图和导出内容都必须脱敏。不得暴露薪资/期权金额、候选人姓名、简历、私人联系方式、员工绩效分、原始面试评价或个人评估细节。
- 带权限控制的链接可以作为证据指针；钉钉、业务系统、Dingteam 链接可能指向敏感源记录，但可见说明文字必须保持安全。
- 管理者可见的 OKR 进展中不得出现本地文件路径，例如 `/Users/...`、`/tmp/...` 或 `outputs/...`。截图作为证据时，必须把图片粘贴或上传到 Dingteam 富文本里，让管理者能直接看到。链接作为证据时，必须显示为可读标题，例如 `项目验收记录`、`客户回款Dashboard` 或 `Q3 OKR文档`，不得展示裸 URL 或本地路径。

## 内置工具

在 skill 目录下使用这些脚本：

```bash
python3 scripts/okr_progress_toolkit.py sanitize-text
python3 scripts/okr_progress_toolkit.py validate-plan --plan plan.json --okr live_okr.json
python3 scripts/okr_progress_toolkit.py validate-presentation --plan plan.json
python3 scripts/okr_progress_toolkit.py render-markdown --plan plan.json --okr live_okr.json --output draft.md
python3 scripts/dingteam_progress_writeback.py --plan plan.json --okr live_okr.json
```

- `okr_progress_toolkit.py` 用于文本脱敏、进展计划校验、证据呈现校验和 Markdown 草稿渲染。脚本里可能保留某些可选领域辅助命令，但公司通用工作流不得默认套用特定领域口径。
- `validate-presentation` 用于检查管理者可见证据的呈现问题，尤其是本地截图路径、裸 URL，以及应该改成内嵌图片或命名链接的证据。
- `dingteam_progress_writeback.py` 是写回前的 dry-run 防护脚本。在没有经过验证的 UI/API 写入器前，它不会修改 Dingteam。

采集证据前先阅读 [references/evidence-sources.md](references/evidence-sources.md)。需要判断业务领域口径或个人规则时，阅读 [references/domain-rules.md](references/domain-rules.md)。任何写回动作前先阅读 [references/writeback.md](references/writeback.md)。

## 工作流

### 1. 确认范围

在信息明确时，可以自动推断当前用户和当前季度。只有身份、周期或写回目标无法确定时才询问用户。默认只生成草稿；只有用户明确说“更新、填写、写入、提交”时才写回线上 OKR。

如果用户知道某个 KR 有特殊计算规则，而线上 OKR 没写清楚百分比、分子、分母、周期、里程碑或评分口径，应提示用户可以直接告诉 Codex。Codex 必须先复述该规则并确认适用范围；用户确认后，本次计划可按该规则计算，并在 `calculationBasis` 中写清楚。用户希望以后复用时，再询问是否写入个人 Memory。个人规则只影响当前用户，不自动成为公司全员默认规则。

### 2. 读取线上 OKR

优先使用线上 Dingteam 数据。可复用 `dingtang-okr-review` 中已经验证过的数据源方式：

- 使用专用 DingTalk SSO profile 的 headless browser 数据源；
- 在已授权标签页中调用 Dingteam Web API；
- 必要时用浏览器页面抽取作为 fallback。

需要采集目标标题/id、KR 标题/id、权重、当前进度、当前说明/评论、周期、owner，以及任何截止时间或节奏提示。

### 3. 采集证据

先把 Memory 当作线索索引，再用授权主数据源验证：

- 当前用户可读范围内的钉钉文档/Wiki、业务文档和知识库。搜索范围由线上 KR 文本、用户 Memory 线索、公司规则和个人规则共同决定，不得把某个部门文件夹写成所有人的默认来源。
- 已授权业务系统只在与 KR 相关时使用。例如招聘系统只用于招聘/面试 KR，销售系统只用于销售 KR，研发系统只用于研发/交付 KR。
- 钉钉会议纪要、日志、待办、聊天、日历、AI 搜问/通讯录、本地文件和仓库，只在与 KR 相关时使用。

将证据分类为 `result`、`metric`、`process` 或 `gap`。不得使用无关的私人材料。

### 4. 加载领域规则和个人规则

公司通用 skill 不写死招聘、销售、研发、客服、产品、运营等任何单一领域口径。遇到明显属于某领域的 KR 时，先按下面顺序确定计算规则：

- 线上 KR 自身写明的度量口径、目标值、周期和验收标准。
- 公司发布的 OKR 规则、领域规则或指标定义。
- 当前用户 Memory 或个人配置中已经确认的个人/岗位口径。
- 相关业务系统中有权限读取的指标定义、字段说明或看板口径。
- 用户在当前对话中明确补充并确认的特殊计算规则。

如果这些规则冲突，优先级为：线上 KR 明文约定 > 公司规则 > 业务系统指标定义 > 当前对话确认的特殊规则 > 用户个人规则 > 通用估算。个人规则和当前对话特殊规则只能影响该用户自己的草稿，不能作为公司全员默认规则。

如果没有找到领域规则，就回到通用原则：能从实际进展直接计算百分比时使用量化公式；不能量化时才使用“进度百分比参考”。任何领域规则都必须在进展计划里写入 `calculationBasis`，说明分子、分母、口径来源和证据缺口。

### 5. 起草更新计划

生成 JSON plan：

```json
{
  "title": "Q3 OKR progress",
  "period": "2026年3季度",
  "targetUser": "current user",
  "updates": [
    {
      "krId": "live KR id",
      "label": "O1 KR1",
      "progress": 20,
      "calculationBasis": "progress formula, domain rule, or qualitative basis",
      "note": "可直接粘贴的脱敏进展说明。",
      "evidence": [{"summary": "source fact", "url": "permissioned link or screenshot path"}],
      "risk": "remaining gap",
      "nextStep": "next action",
      "confidence": "medium"
    }
  ]
}
```

每个 KR 需要包含：

- `建议进度`：先判断 KR 是否能用实际进展直接计算百分比。能量化计算时，必须使用量化公式；不能量化、过于定性，或只有单一交付物且没有自然分子分母时，才参考“进度百分比参考”。百分比始终锚定 KR 承诺的结果。
- `计算口径`：写清使用了线上 KR、公司规则、业务系统定义、个人规则还是通用估算；如果是量化计算，写清分子、分母和周期。
- `进展说明`：在有证据时写清日期、数量、阶段和交付物。
- `证据链接/截图`：使用管理者可见的证据呈现方式。本地脱敏截图可以作为本地审计产物存在，但 Dingteam 可见计划必须说明图片会如何粘贴/上传为内嵌图。带权限的钉钉、业务系统、Dingteam URL 必须显示为可读链接标题，不能显示裸 URL。
- `未完成/风险`：缺失产物、缺失指标、权限阻塞或分母口径缺口。
- `下阶段计划`：具体下一步动作。
- `置信度`：high / medium / low。

生成计划后运行校验并渲染审核稿：

```bash
python3 scripts/okr_progress_toolkit.py validate-plan --plan plan.json --okr live_okr.json
python3 scripts/okr_progress_toolkit.py validate-presentation --plan plan.json
python3 scripts/okr_progress_toolkit.py render-markdown --plan plan.json --okr live_okr.json --output draft.md
```

### 6. 用户审核关口

给用户展示简洁审核表或 Markdown 草稿。只要还存在关键疑问，或计划没有通过校验，就不得写回。

### 7. 写回 Dingteam

用户批准明确计划后，先阅读 [references/writeback.md](references/writeback.md)，再按最安全的路径逐个 KR 写入：

1. 如果存在官方或租户支持的 OKR 写入命令，优先使用。
2. 使用用户已授权会话中的、经过验证的 Dingteam Web UI 自动化。
3. 只有在捕获并验证同版本 UI 的真实 payload 后，才使用 Dingteam 私有 API。

必须逐个 KR 写入。每写完一个 KR，都要重新获取或刷新页面，验证进度百分比和说明/评论。任何一个 KR 验证失败，都要停止并报告失败位置。

写入 Dingteam 富文本说明/评论时：

- 管理者需要看到截图时，必须把脱敏截图直接粘贴或上传到 OKR 评论/富文本字段中。本地路径只能保存在审计产物里，不得出现在可见 OKR 文字中。
- 证据 URL 必须转换为命名链接。推荐：`Q3 OKR文档`、`项目上线验收记录`、`客户回款Dashboard`、`业务系统脱敏快照`。禁止：裸 `https://...` 或 `/Users/.../snapshot.svg`。
- 如果证据暂时无法内嵌或无法做成可读链接，写明 `待补内嵌截图` 或 `待补可读链接`，并记录为呈现缺口。
- 写回后不只验证进度和文字，还要验证截图是否可见、链接是否按可读标题呈现；当截图是用户要求的一部分时，纯文本验证不够。

## 进度百分比参考

使用下面区间前，先做一个前置判断：KR 是否能用实际进展直接计算百分比。

- 如果能直接计算，优先使用量化公式，例如 `已入职人数 / 目标入职人数`、`已完成岗位数 / 目标岗位数`、`已发布内容数 / 10`、`已完成培训人数 / 应完成人数`、`已覆盖场景数 / 目标场景数`。这种情况下不要再套用下面的经验区间。
- 只有 KR 不够量化、过于定性，或是“输出一份报告/方案/机制”这类没有天然分子分母的单一交付物时，才使用下面的非量化参考区间。
- 对单一交付物 KR，如果 OKR 或项目计划已经定义了明确里程碑，可以按里程碑证据折算；如果没有明确里程碑，只能用下面区间做审慎估计，并在说明中写清依据。

- `90-100%`：承诺结果已经达成，有强结果/指标证据。
- `70-89%`：大部分达成，只剩小范围、时间或度量缺口。
- `50-69%`：有明显阶段性进展，但核心结果尚未完全完成或未完全度量。
- `20-49%`：有限进展；通常是规划、草稿、对齐、早期执行或部分漏斗推进。
- `0-19%`：没有相关证据、在形成实质进展前受阻，或结果指标仍为 0。

如果 KR 明确写了严格结果指标，百分比必须锚定该结果指标。过程推进只能写在说明中，除非 OKR、公司规则或领域规则明确允许过程进度计入。

## 汇报方式

草稿场景下，汇报已起草 KR 数量、搜索过的证据源、使用过的业务系统筛选条件或权限缺口、高置信度 KR、需要确认的 KR，以及草稿路径。

写回场景下，汇报已更新 KR 数量、跳过的 KR 及原因、验证结果，以及未解决的证据/权限缺口。
