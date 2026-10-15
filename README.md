# ai-workflow-kit

帮助人和 AI 协作的小工具与方法，按想完成的事挑一个使用。每项可以单独取用，无须接入整套 Harness。

| 你想做什么 | 从这里开始 | 输入和产物 |
| --- | --- | --- |
| 保存会话成果、归档或交接续接 | [session-closeout Skill](skills/session-closeout/SKILL.md) | 给出范围和任务材料，得到核验后的成果入口、待办和实际操作结果；原生会话工具是条件依赖 |
| 开放问题还没想清楚，先拆解再决定 | [structured-analysis-discussion Skill](skills/structured-analysis-discussion/SKILL.md) | 给出目标、约束和证据，得到必要条件、反例、未知和行动建议；不套用简单执行 |
| 不安装 Skill，直接整理会话交接 | [一页交接 SOP](sops/session-handoff.md) | 核对现有材料，复制自然语言请求，保存最小交接 |
| 制作可阅读、可比较、可追溯的汇报 | [HTML 汇报模板](templates/html-report/README.md) | 编辑空白骨架或合成示例，桌面浏览器直接打开；章节可增减 |
| 说明步骤、角色或状态变化 | [流程图制作与图样](diagrams/flowcharts/README.md) | 三组可编辑 Mermaid 与离线 SVG，含制作 SOP；按问题取用 |
| 把本地文档转成便于搜索的 Markdown | [文档转换小工具](scripts/document-conversion/README.md) | 明确的本地输入、Markdown 输出；单独安装所列依赖，无 OCR |
| 定期把批准的本地小件发布到 GitHub | [按清单准备快照](scripts/asset-sync/README.md) | 明确来源和目标，冻结、比较、审阅及完整读回；网络写入由获授权执行者完成 |

## 如何取用

SOP 直接读取。模板、图样和脚本保留整个对应目录及根 [LICENSE](LICENSE)，再按各自说明使用。Skill 可先让 Agent 明确读取所选 SKILL.md，在隔离任务试用；需要安装时仅复制完整所选目录到宿主支持的位置。遇到同名 Skill，先保留旧源并审阅自己的适配。

两项 Skill 允许宿主在适用时选择；文件存在、被发现、命中和执行成功分别核验。分析 Skill 的 `validating` 表示方法收益仍在观察，可按边界使用，不是宿主启停开关。宿主有效规则和当前用户授权优先，文本不能增加工具能力或权限。

## 内容与维护

目录按 `skills/`、`sops/`、`templates/`、`diagrams/`、`scripts/` 组织；示例随所属小件保存。可复制请求通常留在相应 SOP 或 Skill，不为每种形式创建空目录。

本仓库接收经过核验的发布快照；发布者的每项内容保留唯一编辑源，通过清单导出。修订先回原源，避免两边平行手改。新增资产或目标先核对来源、权属、依赖与数据范围；同范围常规修改经适用检查后发布。无变化不建空提交，缺失来源不自动删除，远端冲突先处理。

这个仓库不会自动安装其内容或开启后台调度。私人画像、账号配置、客户材料、真实报告、运行日志和发布者的内部清单不随源码分发。

原创内容按 [MIT](LICENSE) 提供；第三方依赖各自适用其许可证。来源见 [ATTRIBUTION](ATTRIBUTION.md)，实际检查与局限见 [VALIDATION](VALIDATION.md)。
