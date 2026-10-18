# ai-workflow-kit

**中文** | [English](README.en.md)

按任务选用的 Skill、SOP、模板和小工具。先选想完成的事，再按入口说明取用对应内容；不必安装整套 Harness。

## 按任务选择

| 想完成的事 | 推荐入口 | 怎么选、得到什么 |
| --- | --- | --- |
| 拆解问题、比较方案再作决定 | [结构化分析 Skill](skills/structured-analysis-discussion/SKILL.md) | 根据目标、约束和证据，梳理必要条件、反例、未知与建议。 |
| 保存成果、交接给下一次会话 | [会话保存与交接](sops/session-handoff.md) | 先用一页 SOP；需要多会话收口等完整流程时，再按指南取用 Skill。 |
| 制作流程、角色、架构或状态图 | [文档制图指南](docs/document-visuals.md) | 改现成例子用图样；按新需求制作、导出和检查图形用 Skill。 |
| 整理成便于阅读与比较的汇报 | [HTML 汇报模板](templates/html-report/README.md) | 修改报告骨架，桌面浏览器打开；用于阅读，不是交互式产品 Demo。 |
| 把整份本地文档转成 Markdown | [文档转换工具](scripts/document-conversion/README.md) | 处理 PDF、Word 等文档，便于阅读与搜索；不保留全部版式，无 OCR。 |
| 只提取 PDF 中需要的页面 | [PDF 按页读取](scripts/pdf-on-demand/README.md) | 先看逐页索引，再选页提取；与整份格式转换不同，无 OCR。 |
| 按需求制作可操作的产品 Demo | [需求到 Demo SOP](sops/prd-to-demo.md) | 对照需求实现交互、实际检查成功与异常路径，标明模拟范围。 |
| 把网页研究结果接回当前项目 | [网页研究回流 SOP](sops/web-research-to-local.md) | 围绕决定补证据，核对来源与反例，再合并回项目的正式材料。 |

## 如何取用

SOP 可直接阅读或复制其中的任务请求。Skill 可先让 AI 明确读取所选 `SKILL.md`，在小任务中试用；需要安装时，只复制完整的所选 Skill 目录到宿主支持的位置。模板、图样和脚本保留整个对应目录及根 [LICENSE](LICENSE)，再按各自说明使用。

“单独取用”不等于每项都有独立下载包，也不等于无需依赖。遇到同名 Skill，先保留旧源并审阅适配；文件存在、被发现、命中和执行成功分别核验。分析 Skill 的 `validating` 表示方法收益仍在观察，不是宿主启停开关。宿主有效规则与当前用户授权优先，本仓库不增加工具能力或权限，也不自动安装内容或开启后台调度。

需要长期协作规则、任务文件与续接基础时，再看 [harness-starter](https://github.com/MarkTian-Long/harness-starter)。个人偏好与机器适配留在自己的私有层；正式采用时固定提交，核对依赖与当地规则。

## 维护与发布

维护者先按[资产选择与去重规范](sops/asset-selection.md)复用已有评估、判断与现有入口的关系，再用[发布准备工具](scripts/asset-sync/README.md)处理已获准的快照。普通使用者不必运行发布工具。

目录按 `skills/`、`sops/`、`templates/`、`diagrams/`、`scripts/` 组织；目录类型不是首页分类。相同任务的指南、Skill 和示例共用一个推荐入口，具体选法留在入口内，不因增加一种形式就新增一行。

本仓库接收经过核验的发布快照；每项内容保留唯一编辑源，通过清单导出。修订先回原源，远端已有经授权的修订须先合并，不能用旧快照覆盖；尚未回源时保留明确待办。新增资产或目标先核对来源、权属、依赖与数据范围；同范围常规修改经适用检查后发布。无变化不建空提交，缺失来源不自动删除。

私人画像、账号配置、客户材料、真实报告、运行日志和发布者的内部清单不随源码分发。文件数、发布数量或检查通过都不等于长期使用效果。

原创内容按 [MIT](LICENSE) 提供；第三方依赖各自适用其许可证。来源见 [ATTRIBUTION](ATTRIBUTION.md)，实际检查与局限见 [VALIDATION](VALIDATION.md)。
