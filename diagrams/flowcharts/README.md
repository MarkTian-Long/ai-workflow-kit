# 可编辑流程图样

本目录是[文档制图指南](../../docs/document-visuals.md)下的轻量示例，不是另一套制图产品。**只想参考或改写现成流程时从这里开始；需要按新需求制作、导出和检查更多图时，转到指南中的 Skill 路线。** 不需要同时取用两套内容。

输入是已确认的步骤、角色、规则与未知，输出是可编辑 Mermaid 图源及离线 SVG 预览。先选要回答的问题，再取一个合成例子改写；不要求每份报告都画三种图。

| 想回答的问题 | 图源 | 离线预览 |
| --- | --- | --- |
| 先做什么，何时分支，返工回哪里？ | [主流程](main-flow.mmd) | [主流程预览](main-flow.svg) |
| 谁负责什么，在哪里交接和检查？ | [角色协作](role-collaboration.mmd) | [角色协作预览](role-collaboration.svg) |
| 对象有哪些状态，什么事件让它迁移，异常如何结束？ | [状态及异常](states-and-exceptions.mmd) | [状态及异常预览](states-and-exceptions.svg) |

使用前看 [流程图制作 SOP](制作SOP.md)。`.mmd` 是纯文本，可用编辑器修改；`.svg` 可在浏览器中离线查看，无外链字体、图标、脚本或网络依赖。无需安装 Skill 即可阅读和参考，但修改 `.mmd` 后重新生成预览仍需要兼容的渲染器。

## 不要混用渲染入口

本目录的主流程和角色协作图采用标准 Mermaid 流程语法，**不能直接交给当前 Skill 的 `diagram` 命令**；其标准 `mermaid` 命令也尚未开放流程图。要使用该 Skill，请按[流程语法指南](../../skills/create-document-visuals/references/flowchart-guide.md)改写到受支持子集，或按[显式 SVG 路线](../../skills/create-document-visuals/references/svg-layout-guide.md)制作并重新核对关系。状态图对应 `mermaid` 路线，仍须完成依赖准备及实际导出检查。具体选择见[制图指南](../../docs/document-visuals.md#现成图样与-skill-的兼容边界)。

这些 SVG 是与 Mermaid 表达相同节点、边、条件和责任的原生离线布局，不是本 Skill 已成功渲染全部图样的证明；其他兼容渲染器的布局也可能不同。

改动业务输入时，同时更新对应文字、图源与预览；不能只改 SVG 或把旧预览当新事实。三个例子都是原创中性合成资料，按集合根目录的 MIT 许可提供，不代表任何真实项目的制度或验收。采用者需核对自己的规则与权限；本目录没有自动化业务执行能力。
