# 文档制图：选用与安装

## 先选用法

**有自己的输入，需要 AI 帮你制作、导出和检查图形，默认走本页的 Skill 路线。** 只想参考或改写现成流程，可直接取[流程图样](../diagrams/flowcharts/README.md)，不必安装 Skill；看 SVG 预览无需渲染环境，修改图源后重新生成则需要兼容工具。

Skill 与图样是同一任务的两种起步方式，不是两套都要安装的产品。图样只覆盖主流程、角色协作和状态异常，不能代替全部图型的制作能力；两者也不保证使用相同语法入口。

[Skill 入口](../skills/create-document-visuals/SKILL.md) · [更新与上游追踪](diagram-skill-updates.md)

## Skill 的制作路线

`create-document-visuals` v0.3.0 为本地 Markdown 制作可编辑流程、角色交接、架构/关系、原生时序、状态与 ER 图。renderer 为 0.2.0；原 Mermaid-lite 保留，新增图型显式使用固定 Mermaid 12.2.0。图源和导出归当前父文档，示例不代表真实业务规则。

| 需求 | 使用路线 | 产物与边界 |
| --- | --- | --- |
| 步骤、判断、条件与返回 | `diagram`，原 Mermaid-lite | `.mmd` → SVG/PNG；有限流程子集，不是全部 Mermaid |
| 角色交接或复杂布局 | 显式 SVG，按模板改写 | SVG 唯一源，PNG 兼容；模板角色按事实增减 |
| 时序、状态、ER | `mermaid`，固定本地引擎 | `.mmd` → SVG/PNG；仅开放这三类，源配置/HTML/URL/点击不开放 |
| 文字越框、节点相交与部分连线疑点 | `check-layout` | 可保存 JSON；部分覆盖保留 structural-only，仍需语义与实际容器目视 |

## 现成图样与 Skill 的兼容边界

[轻量图样](../diagrams/flowcharts/README.md)不是全部都能直接传入 Skill 的示例集：

| 图样 | 当前怎样使用 |
| --- | --- |
| `main-flow.mmd`、`role-collaboration.mmd` | 含标准 Mermaid 的节点、边标签或分区语法，不能直接交给简化的 `diagram`；`mermaid` 路线目前也不接收流程图。可用已核验的兼容渲染器，或按[流程指南](../skills/create-document-visuals/references/flowchart-guide.md)改写为受支持子集；角色布局也可走[显式 SVG](../skills/create-document-visuals/references/svg-layout-guide.md)。改写后必须重新核对业务关系。 |
| `states-and-exceptions.mmd` | 图型对应标准 `mermaid` 路线，不能交给 `diagram`；仍须先准备依赖并检查实际导出，不据图型匹配宣称已运行通过。 |
| 已有 `.svg` 预览 | 可直接离线查看；它们是语义对应的原生布局，不是本 Skill 已渲染所有 `.mmd` 的证明。 |

只做参考或修改图样不必安装完整 Skill。需要 Skill 流程样例时，优先使用[流程指南中的合成样例](../skills/create-document-visuals/references/flowchart-guide.md#合成样例)，而不是把不兼容图样原样输入。扩展渲染器是另一项变更，本页不承诺自动兼容或自动改写。

## 取用与依赖

保留完整 `skills/create-document-visuals/` 目录，复制到宿主支持的 Skill 位置。已存在同名 Skill 时先保留原件，核对自己的适配再替换。也可先在隔离任务明确读取入口试用。目录包含原创 MIT 许可及固定第三方许可；本机压力/拒绝测试和私人运行记录不在发布包内。

本次实际验证环境为 Windows、本地 Chrome/Edge、Node 24。运行依赖为 `@viz-js/viz 3.25.0`、`sharp 0.35.5`、`playwright 1.62.1`、`marked 17.0.5`；这些包独立安装，不随本仓库捆绑。其他系统、浏览器和版本需要在当地验证。公开包保留固定 Mermaid 12.2.0 清单和完整许可，首次使用标准路线前按下方步骤从官方 npm 下载并核验 bundle；准备完成后渲染不通过 CDN 或在线绘图服务加载。

已有 Codex 捆绑运行时时，优先通过宿主的依赖定位能力取得 Node 和 node_modules；否则可在独立用户目录安装固定依赖。下面是由使用者执行的安装示例，安装阶段需要网络；渲染阶段保持本地。

~~~powershell
$runtimeDir = Join-Path $env:LOCALAPPDATA "document-visuals-runtime"
npm install --prefix $runtimeDir --no-audit --no-fund @viz-js/viz@3.25.0 sharp@0.35.5 playwright@1.62.1 marked@17.0.5
$env:CODEX_VIS_NODE_MODULES = Join-Path $runtimeDir "node_modules"
$skillDir = Join-Path $env:USERPROFILE ".codex\skills\create-document-visuals"
$renderer = Join-Path $skillDir "scripts\render_visuals.mjs"
node $renderer version
node (Join-Path $skillDir "scripts\install_mermaid_bundle.mjs") --download
~~~

下载脚本只取固定官方 npm 压缩包，核对 SHA512 后只提取唯一目标文件，再核对 bundle SHA256 和字节数。没有 npm 安装脚本、账号、上传或全局配置写入；已有相同 bundle 直接返回，已有不同文件拒绝覆盖。离线电脑可在允许联网的环境按同一固定清单准备，再通过当地获准方式放入 vendor 目录。

需要既有本地 Chrome 或 Edge；找不到时用 `CODEX_VIS_BROWSER` 指定其 executable。该 Skill 不自动下载浏览器、不写全局 PATH、不接云账号。字体采用系统本地字体；中文显示需当地有可用的 CJK 字体。

## 调用与输出

先读命中路线的指南，保存当前文档的唯一图源；普通流程使用其支持的子集，原生图不能传给旧 parser。

~~~powershell
node $renderer inspect ".\source\flow.mmd"
node $renderer diagram ".\source\flow.mmd" ".\export\flow.svg" ".\export\flow.png"
node $renderer check-layout ".\export\flow.svg" --width 1000 --output ".\export\flow.qa.json"
node $renderer mermaid ".\source\state.mmd" ".\export\state.svg" ".\export\state.png"
~~~

`mermaid` 拒绝覆盖已存在的目标；选择新目标后核验，再更新父文档引用。`--width` 是容器宽度上限，不强制放大小图；父文档 CSS 缩放时还要检查实际容器。几何命令退出码 0 为已覆盖几何通过、2 为需修正、3 为部分/不支持或待复核、1 为运行失败，不能统一把非零写成同一种结果。

重要图保留源引用、替代文本、图注与必要文字解释。需要 PDF 时才生成，不能用图片替代精确规则或验收条款。

## 已知限制与许可

合成试用曾出现“几何通过但返回线穿主链”，因此自动检查不替代业务语义、所有连线歧义或目视。分区自动布局仍可能穿标题；转显式 SVG 或拆图是可用的处理路径，不承诺自动修图。没有开放全部 Mermaid 图型、拖拽编辑器或第三方图片 API。

自建代码、指南、模板和合成样例按 [MIT](../skills/create-document-visuals/LICENSE) 提供。固定 Mermaid 的来源、版本、哈希见 [MANIFEST](../skills/create-document-visuals/assets/vendor/mermaid/MANIFEST.json)，MIT 和第三方声明随包保留；DOMPurify 采用 Apache-2.0 许可选项。独立安装的 Node 包分别适用其上游许可。
