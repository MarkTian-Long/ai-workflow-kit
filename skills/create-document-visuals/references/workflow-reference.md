# 共享保存、导出与验收

本文件只在实际制作/交付时读取。图型、布局和语法分别读取入口指向的对应指南，不再次加载全部模式。

## 文件与唯一源

视觉是父文档的一部分，先核对父文档及输入主版本。证据记录来源与处理方式；解释图保留文字兜底；装饰图不承担精确事实。客户原件和原始截图只读。

默认 `assets/<Artifact-ID或稳定视觉名>/source` 与 `export`。图源、导出共用基础名称与逻辑版本，仅重渲染不升级内容版本。同一图只有一个编辑真值：`.mmd` 或 `.svg`；生成脚本/布局数据参与再生成时一并登记，不把两个可编辑版本长期分开维护。

## 依赖和命令

调用本机依赖定位能力获得 Node executable、Node packages。以当前 SKILL 所在目录解析脚本，不能假设 cwd。设置 `CODEX_VIS_NODE_MODULES`；可选 `CODEX_VIS_BROWSER` 指向本地 Chrome/Edge。无依赖定位工具的子任务由调用方提供已核路径，不凭空猜环境或联网安装。

~~~powershell
$node = (Get-Command node -ErrorAction Stop).Source
$env:CODEX_VIS_NODE_MODULES = Join-Path $env:LOCALAPPDATA "document-visuals-runtime\node_modules"
$skillDir = Join-Path $env:USERPROFILE ".codex\skills\create-document-visuals"
$renderer = Join-Path $skillDir "scripts\render_visuals.mjs"

& $node $renderer version
& $node $renderer inspect "source\流程.mmd"
& $node $renderer diagram "source\流程.mmd" "export\流程.svg" "export\流程.png"
& $node $renderer mermaid "source\时序.mmd" "export\时序.svg" "export\时序.png"
& $node $renderer image "source\布局.svg" "export\布局.png"
& $node $renderer check-layout "export\流程.svg" --width 1000 --output "export\流程.qa.json"
& $node $renderer pdf "父文档.md" "export\父文档.html" "export\父文档.pdf"
~~~

`inspect` 仅分析 Mermaid-lite 结构，成功不等于布局通过。标准 Mermaid 的实际类型/版本与限制见对应指南。所有输入/输出必须不同，不能覆盖唯一源。脚本默认不访问远程资源；无法离线生成时说明缺失，不把联网重试当默认降级。

## 嵌入 Markdown

~~~markdown
<!-- visual: fig-01; source=./assets/流程/source/资料处理_v0.1.mmd; source-version=v0.1 -->
![资料不足时返回补充，通过检查后继续处理](./assets/流程/export/资料处理_v0.1.svg)

*图 1｜接收、判断和补充后重新检查的处理路径。*

- 资料不足的分支返回补充，不直接进入处理。
- 精确规则、例外和验收条款仍留正文。
~~~

重要解释图包含源引用、图、结论图注和足够的文字兜底；信息性图使用非空且有信息的 alt，纯装饰图可空并标记用途。正式 Markdown 使用相对路径，不写绝对路径、Base64、临时工具 URL 或外部图片热链。检查普通/引用式图片、HTML img/srcset 对应文件、无路径逃逸和坏引用。

## 几何、语义与显示检查

- `check-layout` 在本地浏览器实际字体加载后检测其可识别的 SVG 节点和文字，报告覆盖、缺陷及限制。`--width` 设置可用容器宽度上限，小图保留固有尺寸，不会强制放大；实际尺寸见 `coverage.rendered_svg_bounds`。父文档 CSS 强制缩放时，还要在其实际容器复核。确定性问题标 revise；未识别或未覆盖的图型保持 structural-only，不能把零条报告解释为全通过。
- 连线相交不一定错误，真实汇合必须明确；启发式连线疑点复核来源、目标和业务关系。脚本不能证明节点/分支业务正确。
- 使用实际目标容器核对文字、标签、字号、分区标题、边界、裁切、箭头、对比度和主链阅读顺序。普通桌面内部文档默认只验桌面；移动端要求、已有约定或具体布局缺陷触发窄屏，不机械追加多端。
- 多图按共同语义维持形状、颜色和风格；不能以改样式删除分支。自动布局不能满足确认参考时，转显式 SVG；复杂图拆概览/局部，不靠缩字。
- SVG XML/viewBox、PNG解码、实际字体和最终容器均需相符。命令成功、文件非空、结构计数和单张放大预览不能单独替代验收。PDF仅需要时生成并检查受影响页面。

## Visual manifest

受管成果、两张以上图或需要后续复用/交付时，按 `../assets/visual-manifest.template.json` 保存一图一项：父文档/版本、用途、问题、图源与导出路径/格式/哈希/尺寸、实际renderer/engine版本、alt/图注/文字兜底、来源/许可/敏感性/外部处理及QA。

记录语义、目视、链接、清单一致性、`text_bounds_check` 和几何检查覆盖/限制。值来自实际执行，不能把默认模板版本、pending或空哈希写成通过。清单仍为试行资产一致性记录，不替代图源、正文或业务验收；不新接入全工作区阻断器。

失败先修实际缺陷并重渲染。不能修复时保留具体缺口，报告失败/部分覆盖，不创建占位图、失效链接或虚假的视觉通过。保存 tested_version、checked_at、checker、result、known_difference。项目台账与日志按父文档规则更新，不把运行记忆写回本Skill。
