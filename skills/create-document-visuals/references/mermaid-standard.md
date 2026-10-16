# 标准 Mermaid 的独立本地路线

在明确需要原生时序、状态机或实体关系表达时读取。保留已有 Mermaid-lite 作为普通流程默认路线；本路线使用固定官方 Mermaid 12.2.0 standalone bundle，目前适配器只放行以下三类，不因库本身功能多就承诺全部图型。

| 图型 | 源首行 | 使用条件与最低语义 |
| --- | --- | --- |
| 时序图 | `sequenceDiagram` | 关心参与方按时间交互；写清参与者、消息顺序、返回、条件与失败分支 |
| 状态机 | `stateDiagram-v2`（也识别 stateDiagram） | 关心对象生命周期；写清状态、触发事件、条件、起止及允许的返回 |
| 实体关系 | `erDiagram` | 关心对象关系；默认只列主要对象、用途和一对一/一对多/多对多等数量关系；修改、发布、停用或删除的影响以必要文字说明，详细字段设计仅用户明确要求时展开 |

图型以所问问题和维护者决定，不以图名或模板凑内容。不要把顺序交互、生命周期状态、数量关系互相近似替换。实际需求未明确的关系保留未知，不用示例补造。

## 本地执行

公开安装包首次使用本路线前，显式运行 `node <Skill目录>/scripts/install_mermaid_bundle.mjs --download`。此准备步骤从固定官方 npm 来源取回并核验 bundle，需要联网；清单与完整许可已随包保留，之后渲染保持离线。依赖与准备见[安装说明](../../../docs/document-visuals.md)。

依赖为现有 Node、Playwright 与本地 Chrome/Edge，路径通过依赖定位能力取得。`CODEX_VIS_NODE_MODULES` 指向现有 node_modules，可选 `CODEX_VIS_BROWSER` 指向浏览器；不全局安装，不访问在线渲染服务。

~~~powershell
& $node $renderer mermaid "source\申请交互.mmd" "export\申请交互.svg" "export\申请交互.png"
& $node $renderer check-layout "export\申请交互.svg" --width 1000 --output "export\申请交互.qa.json"
~~~

`mermaid` 独立于 `diagram`/`inspect`；不要把本路线源传给旧 parser。当前新增导出采取不覆盖策略：目标 SVG 或 PNG 已存在时拒绝，选择新的目标并在核验后按父文档约定替换引用；源文件始终唯一。坏语法、资源/配置拒绝不产生新的成功导出，也不删除旧结果。

## 实际限制

- 适配器固定字体/配色与严格安全配置，源内 frontmatter、初始化配置、HTML、点击、回调、外部URL、图标/图片和样式覆盖被拒绝。不是任意 Mermaid 源的无条件兼容承诺。
- 原生 SVG text 与本地字体，不用 foreignObject。库完整性按随包 SHA-256 检查；浏览器禁止外部请求。有网络尝试或输出为空则拒绝导出。
- 时序、状态与ER的几何结构不同于简单流程。检查器可能仅覆盖部分结构或返回 structural-only；必须目视实际图及最终容器，并核对语义/数量关系，不把零几何错误当完整通过。
- 源大小与导出尺寸有本地资源上限；复杂图应拆概览/局部。其他图型、源配置放开或更换版本属于后续有界验证，不自动同步上游到运行副本。

## 合成样例与来源

样例用于验证引擎，不是当前客户或公司规则：[时序](../evals/mermaid-fixtures/sequence.mmd)、[状态](../evals/mermaid-fixtures/state.mmd)、[实体关系](../evals/mermaid-fixtures/er.mmd)。先按实际需求改写语义，不复制示例角色或字段作为事实。

官方库与许可位于 [vendor目录](../assets/vendor/mermaid/)，依实际保留的 provenance/NOTICE 查看固定版本、完整性和第三方归属。共享保存/嵌入/清单与验收见 [共享工作流](workflow-reference.md)。
