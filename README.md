# dingtang-okr-progress-fill

叮当 OKR 进展填写 skill。它用于为员工本人起草、校验并在确认后填写 Dingteam / 叮当 OKR 的 KR 进展，基于当前用户有权限读取的 Memory、钉钉文档、日志、会议纪要、业务系统、本地文件或代码仓库等证据生成脱敏说明。

## 能做什么

- 读取线上 Dingteam OKR 结构，避免按旧草稿填写。
- 按用户权限收集证据，并区分结果、指标、过程和缺口。
- 能量化计算进度时直接使用量化公式；不能量化时才使用定性进度参考。
- 支持领域规则和个人规则加载，但不会把某个岗位或业务领域的口径写成所有人的默认规则。
- 生成管理者可见的进展说明，要求图片内嵌、链接命名、不得出现本地路径。
- 写回 Dingteam 前必须经过用户明确确认。

## 安装

把本仓库克隆或复制到本机 skill 目录：

```bash
git clone https://github.com/minamina2025/dingtang-okr-progress-fill.git ~/.agents/skills/dingtang-okr-progress-fill
```

如果使用 Codex skill 目录，也可以同步到：

```bash
git clone https://github.com/minamina2025/dingtang-okr-progress-fill.git ~/.codex/skills/dingtang-okr-progress-fill
```

## 安全边界

- 不读取 Chrome cookies、localStorage、浏览器 profile、密码、session store、token 或 authorization header。
- 不打印 secrets、cookies、tokens、签名 URL、auth code 或任何私密凭据。
- 不在 OKR 可见文字里暴露薪资、绩效分、候选人姓名、私人联系方式、原始评价、客户敏感商业条款等信息。
- 带权限控制的链接可以作为证据指针，但可见说明文字必须脱敏。

## 目录

```text
.
├── SKILL.md
├── agents/
├── references/
├── scripts/
└── tests/
```
