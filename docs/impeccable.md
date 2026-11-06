# Impeccable：安装与选用指南

Impeccable 为编码助手提供界面评审与改进方法，适合针对已有页面或组件提出 `critique`、`audit`、`polish` 等明确请求。本 Kit 只提供本指南及上游入口；第三方 Skill、CLI、引擎二进制、插件和钩子均从上游单独获取。

## 来源、版本与许可

本指南于 2026-11-06 核对以下固定源码。版本号、Git 引用和引擎版本分别记录，不以当前 `main` 替代固定来源。

| 项目 | 已核对内容 |
| --- | --- |
| 作者与上游 | Paul Bakaus；[pbakaus/impeccable](https://github.com/pbakaus/impeccable)；[官网与文档](https://impeccable.style/docs) |
| 固定源码 | [`c8891a9ae865d6ee311836ae5199bfce0fe115b1`](https://github.com/pbakaus/impeccable/tree/c8891a9ae865d6ee311836ae5199bfce0fe115b1) |
| Skill / npm 包元数据 | [`SKILL.md`](https://github.com/pbakaus/impeccable/blob/c8891a9ae865d6ee311836ae5199bfce0fe115b1/.agents/skills/impeccable/SKILL.md) 与 [`package.json`](https://github.com/pbakaus/impeccable/blob/c8891a9ae865d6ee311836ae5199bfce0fe115b1/package.json) 均声明 `4.8.0`；此项不证明 npm 包已发布或存在同名 Git tag |
| 引擎版本 | [`scripts/VERSION`](https://github.com/pbakaus/impeccable/blob/c8891a9ae865d6ee311836ae5199bfce0fe115b1/.agents/skills/impeccable/scripts/VERSION) 为 `0.1.18`；与 Skill 版本分别编号 |
| Windows x64 引擎校验值 | [`engine-checksums.txt`](https://github.com/pbakaus/impeccable/blob/c8891a9ae865d6ee311836ae5199bfce0fe115b1/.agents/skills/impeccable/scripts/engine-checksums.txt) 记录 `impeccable-windows-x64.exe` 的 SHA-256 为 `8f61e96b0c97001546a824d79b44f46b423b560f3eb1a0cc44a8695a1b395d9f` |
| 许可与署名 | [Apache-2.0，Copyright 2025 Paul Bakaus](https://github.com/pbakaus/impeccable/blob/c8891a9ae865d6ee311836ae5199bfce0fe115b1/LICENSE)；[`NOTICE.md`](https://github.com/pbakaus/impeccable/blob/c8891a9ae865d6ee311836ae5199bfce0fe115b1/NOTICE.md) 另记录原生平台参考资料来自 ehmo 的 [platform-design-skills](https://github.com/ehmo/platform-design-skills)，原许可为 MIT |

`v4.8.0` Git tag 尚未确认可用，按上述完整 commit 获取。校验清单中的哈希只给出预期字节；它不证明下载渠道当前可达、安装成功或目标机器运行兼容。

## 安装：选一个用户级目录

1. 从上述固定 commit 获取上游源码；按正在使用的编码宿主选择对应的 Skill 构建。Codex 构建位于 `.agents/skills/impeccable/`。
2. 确认宿主实际识别的唯一用户级 Skills 目录，再复制整个 `impeccable` Skill 文件夹。上游 README 给 Codex 的示例为 `$HOME/.agents/skills/`；既有宿主若使用 `$CODEX_HOME/skills/`，沿用其已确认入口。不要同时保留两份活动副本，也不要把整个仓库复制进 Skills 目录。
3. 保留 `SKILL.md`、所需 `reference/`、`scripts/`，并同时带上该固定提交仓库根目录中的 `LICENSE` 与 `NOTICE.md`。遇到同名旧版先备份并替换，避免把新文件叠加到旧目录而留下过期引擎。复制本指南不会安装 Skill。
4. 手动复制不登记宿主钩子或子 Agent。重新加载宿主后，在 Skill 列表中确认 `impeccable` 的来源路径，再做下面的最小验证。

上游还提供 `npx impeccable install` 与 `update`，安装器会询问宿主、项目级或全局范围，并提供钩子。需要这条路径时，先核验所选 npm 版本与来源，再审阅写入范围和选项；本指南默认采用手动复制，不自动启用安装器、插件、钩子或子 Agent。详细操作见固定版本的 [README](https://github.com/pbakaus/impeccable/blob/c8891a9ae865d6ee311836ae5199bfce0fe115b1/README.md#installation)。

## 依赖与网络边界

| 使用方式 | 依赖与行为 |
| --- | --- |
| 阅读 Skill / 手动复制 | 不需要 Node.js；需要支持 Agent Skills 的编码宿主 |
| Skill 启动器 | 使用对应操作系统与架构的自包含引擎；缺少可用引擎时，启动器可能首次联网下载至用户缓存。Windows 使用 `scripts/impeccable.cmd`，其他平台使用相应启动器 |
| 选择 npm 安装器 | 该固定源码的 `package.json` 要求 Node.js `>=18.19.0`，并需要 npm/npx 与下载权限；这不是手动安装 Skill 的依赖 |
| 对运行页面执行检测 | 上游说明 URL 检测使用已安装的 Chrome 或 Edge；源文件检测和渲染后检测覆盖的问题不同 |

首次运行前审阅启动器的来源、固定版本、校验清单、下载位置与写入位置。有预装引擎时先核对版本与 SHA-256；本 Kit 不分发或代替验证二进制。引擎不可用时，按 Skill 的降级说明直接读取项目现有上下文，并如实说明哪些检测未运行。

上游允许用 `DO_NOT_TRACK=1` 或项目配置中的 `"telemetry": false` 关闭其所述匿名选择记录。但上游明确说明，这不会停止新设计过程对视觉方向目录的请求。因此，“关闭遥测”不等于完全离线；敏感项目应先核对当前版本的[隐私说明](https://impeccable.style/privacy)及实际所需的数据流。

`live` 是独立的浏览器迭代模式，不是普通 Skill 使用的前提。固定版本 README 说明：其 Apply 在没有活跃聊天会话轮询时，可能回退调用绕过审批与沙箱的本地编码 CLI，并传递暂存编辑与页面上下文。本指南不启用该模式或扩大权限。若另行选用，应先审查完整行为；上游提供 `IMPECCABLE_LIVE_COPY_AGENT=chat` 限制为聊天会话，或 `off` 关闭 Apply。也不要为此放宽生产站点的 CSP。

## 与其他设计方法如何分工

| 当前任务 | 优先方法 | 使用边界 |
| --- | --- | --- |
| 已有页面、组件需要评审或有明确改进目标 | Impeccable，例如 `critique`、`audit`、`polish` | 指定页面、组件与目标；保留现有产品事实、设计约束和范围外行为 |
| 从零创建界面，视觉方向开放 | `frontend-design` | 先围绕受众、主要任务与真实内容确定视觉方向；Impeccable 可用于后续局部评审，两者无需重复跑完整流程 |
| 按用户授权截图还原交互界面 | `pm-image-to-prototype` 或现有截图复刻流程 | 以参考图的布局、内容和状态为验收依据，保持参考一致性 |
| 按用户授权 URL 还原交互界面 | `pm-url-to-prototype` 或现有 URL 复刻流程 | 先检查页面与交互；只获取授权范围内的内容和资源 |
| 已定设计系统下的小文字、样式修改 | 直接按项目规范修改 | 保持变更范围，检查受影响区域，无需启动完整设计流程 |

Impeccable 的风格建议不能覆盖明确的参考图、品牌规范、事实文案或业务验收要求。报告、幻灯片、文档仍使用各自的制作与交付流程；纯后端任务不使用本 Skill。选用更多工具本身不证明效果更好。

## 第一次使用与验收

在可回滚的项目副本中，从一个具体目标开始。例如在 Codex 中输入：

```text
$impeccable critique 设置页的表单分组与主要操作
```

这是评审请求。需要实际修改时，再明确指定修改对象与目标。`init` 会写入 `PRODUCT.md`，`document` 会生成 `DESIGN.md`，应按项目上下文管理；不要为一次局部修改自动重建已有正式设计材料。

安装后的最小验证依次是：宿主能发现唯一 Skill 来源；启动器的 `engine-probe` 返回预期版本并正常退出；在一个真实且可回滚的目标上完成所需命令。发生界面修改时，实际查看受影响的渲染结果并执行关键动作，检查尺寸按交付场景确定。

Skill 可见、版本探测成功、静态检测通过和界面验收分别证明不同事情。本指南只核对来源与文档，不声明任何目标机器已安装成功、运行成功或取得设计改善。

更新时重新固定 commit、核对引擎版本与哈希，再替换唯一活动副本。回滚时恢复此前备份；单独获取的引擎缓存、钩子或插件按各自所有权处理，不能通过删除其他工具的共享配置回滚。
