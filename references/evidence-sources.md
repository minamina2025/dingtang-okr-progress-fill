# 证据源

采集 OKR 进展草稿证据时使用本参考。公司通用 skill 不预设某个部门、岗位或业务系统；搜索范围由线上 KR、用户 Memory、公司规则、领域规则和当前用户权限共同决定。

## 来源顺序

1. 先读取线上 Dingteam OKR 结构。线上 O/KR 和旧草稿不一致时，以线上为准。
2. 使用 Memory 作为线索索引：标题、文件夹、日期、项目别名、owner 和链接都只是线索，不是最终证据。
3. 在 DWS 已授权时，搜索当前用户可读范围内的钉钉文档/Wiki/知识库。不要把某个部门文件夹写成所有人的默认来源；只有 KR、Memory 或领域规则指向某文件夹时，才优先搜索它。
4. 业务系统只在与 KR 相关且当前用户有权限时使用。例如招聘/面试 KR 才使用招聘系统，销售 KR 才使用 CRM，研发/交付 KR 才使用研发系统。
5. 日志、会议纪要、待办、聊天、日历、AI 搜问/通讯录、本地文件和代码仓库，只在与 KR 相关时使用。

## 周期边界

证据必须匹配目标 OKR 周期。填写 Q3 进展时，只能用 Q3 证据证明 Q3 本期完成；不能因为 Q3 证据不足，就用 Q2 文档、Q2 会议、Q2 自评或 Q2 系统记录充当 Q3 进展。

- 上一周期证据可以作为背景、基线、历史状态或“本期开始前已经存在”的证明，但不能算作本期完成。
- 只有 OKR 自身、公司规则或用户确认的特殊口径明确写了跨周期累计、延续项目、历史基线、上季度遗留纳入本期等属性时，才可以把跨周期证据纳入计算。
- 使用跨周期证据时，必须在 `calculationBasis` 或说明中拆开写清 `本期完成证据` 和 `历史/基线证据`。
- 没有清晰日期或周期归属的证据，不能直接当作目标周期证据；应标记为周期不明或证据缺口。

## 证据标签

- `result`: delivered artifact, launch, acceptance, adoption, completed list, closed issue, signed/paid state, onboarding.
- `metric`: numerator/denominator, count, conversion, rate, before/after, dashboard value.
- `process`: meeting, draft, alignment, planning, pending interview, todo, partial design.
- `gap`: no login, no permission, missing export, unclear denominator, contradictory source.

## 脱敏

可见 OKR 文字和生成截图不得包含薪资/期权金额、候选人姓名、私人联系方式、简历细节、员工绩效分、原始面试评价、个人评估细节、客户敏感商业条款或其他不适合管理者可见说明展示的信息。带权限控制的链接可以作为证据指针，但可见叙述必须保持抽象和安全。

## 管理者可见证据呈现

OKR 进展会被用户的管理者和协作者阅读，所以证据指针必须能在本机之外使用。

- 不要把 `/Users/...`、`/tmp/...`、`outputs/...` 或 `file://...` 这类本地路径粘贴进 Dingteam 可见进展说明。
- 如果截图是证据，先生成脱敏图片审计产物，再把图片本身粘贴或上传到 Dingteam 富文本/评论中。可见说明只写清图片标题，不显示本地路径。
- 如果钉钉、业务系统、Dingteam 或文档 URL 是证据，展示为命名富链接。链接标题要清晰说明来源，例如 `Q3 OKR文档`、`项目上线验收记录`、`客户回款Dashboard`、`招聘Dashboard脱敏快照`。
- 裸 URL 和本地路径只能保留在本地 JSON/Markdown 审计文件里，不进入管理者可见 OKR 文本。
- 图片无法内嵌或链接无法命名时，写明 `待补内嵌截图` 或 `待补可读链接`，并把它当作呈现缺口。
