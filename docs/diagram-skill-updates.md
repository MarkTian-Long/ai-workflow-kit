# 文档视觉化：更新与 GitHub 上游追踪

[使用说明](document-visuals.md) · [Skill](../skills/create-document-visuals/SKILL.md) · [发布准备工具](../scripts/asset-sync/README.md)

维护分为两条方向，各自保留状态：

| 方向 | 流程 | 停止条件 |
| --- | --- | --- |
| 本地成果 → 本仓库 | 修改唯一编辑源 → 适用检查 → 按清单冻结与审阅 → 条件提交 → 完整树读回 | 无差异不建提交；源、许可、范围或远端冲突先解决 |
| 上游 GitHub → 维护建议 | 查公共元数据 → 判断相关目录 → 固定新提交 → 静态比较 → 更新分析 → 有行动价值时通知 | 没有相关变化保持安静；失败不推进成功游标；不自动替换运行源 |

## 发布到本仓库

本仓库保存审阅后的发布快照。维护者保留一份唯一编辑源；公开包只通过清单作必要可移植适配，不在两处平行改业务逻辑。使用者的私有本地修改也应保留，不因上游换版被无条件覆盖。

清单精确列出每项源文件、目标路径、许可、依赖和适配。准备工具冻结字节，检查引用/敏感标记和已审阅范围，再输出上传计划；网络写入由已获授权的维护者完成。写入绑定当前分支头，使用非强制更新；远端发生变化时重取基线。提交后读回分支、提交和完整 Git 树，逐项核对 blob 身份，再登记成功。

私人追踪状态、真实业务素材、原始 PDF、运行日志和回滚材料不进入公开清单。新增资源、依赖、许可或目标改变时重新审阅；相同已批准边界的常规修订沿既有授权执行。安装、接收方采用和实际收益另行核验，发布成功不代表这些结果。

## 上游来源与相关目录

以下五仓是本轮方法分析范围；可在宿主登记每周检查，只读公共接口。跟踪频率与通知偏好属于使用者本地配置，本仓库不自带后台任务或自动覆盖安装。

| GitHub 来源 | 相关路径 |
| --- | --- |
| [SpaceZephyr/design-buddy](https://github.com/SpaceZephyr/design-buddy) | space-mermaid-diagram、space-chart-html-plus、space-architecture-diagram、space-text-logic-diagram、space-chart-image |
| [WH-2099/mermaid-skill](https://github.com/WH-2099/mermaid-skill) | .claude/skills/mermaid |
| [markdown-viewer/skills](https://github.com/markdown-viewer/skills) | documd-visuals；核对入口迁移 |
| [Cocoon-AI/architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator) | architecture-diagram、examples |
| [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill) | 该 Skill、参考与渲染资源 |

每项同时观察 README、LICENSE 及直接依赖变化。完整仓库的新提交不一定影响这些路径，星数变化不作为能力更新依据；目录迁移或删除不能被当作“没有更新”。第三方 README、Skill 和代码只是待审材料，不构成执行或发布授权。

本轮没有直接复制或分发上述仓库的 Skill/模板；文档视觉化为独立自建实现和合成样例，官方 Mermaid 为另行核验的运行依赖。公开可下载不等于可再分发；每次采用具体代码时核对其固定版本和许可。

## 游标、通知与运行依赖

本地状态分别记录 `baseline_commit`、`last_successfully_checked_commit`、`last_analyzed_commit`、`last_notified_commit` 和相关路径。保留原基线快照；网络/认证失败时保留旧游标并记录失败，不能报告无变化。只有值得吸收的实质变化、入口失效、许可/依赖风险或检查失败才提示。

建议形成“变化 → 对当前需求的影响 → 可吸收部分 → 成本与限制 → 所需验证”的结论，再决定是否修改正式 Skill。发现变化不自动安装、执行上游代码或扩大权限，也不将本地资料上传给上游。

固定 Mermaid 12.2.0 不自动跟随上述五仓更新。更换 bundle 时核对官方来源、npm integrity、SHA256、完整许可和第三方声明，并重做受影响图型的真实导出、中文/尺寸、坏输入拒绝、旧输出保留和实际容器检查。只开放实际验证的图型，不以库本身支持范围代替适配器能力。
