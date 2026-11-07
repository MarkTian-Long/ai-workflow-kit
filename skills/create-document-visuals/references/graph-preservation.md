# 已有图重绘：关系保真检查

用于已确认流程的重绘、横竖版切换、节点合并或发布格式迁移；新建简单图和仅改配色不必增加此流程。本项复用现有 SVG 路线与 `check-layout`，不新增 Skill、渲染引擎或 Mermaid 方言。

## 从一次性脚本吸收什么

保留“先核对节点与条件边，再布图；字体/文字边界单独检查；记录实际来源与导出身份；未目视检查就保留 pending”的做法。不要把固定盘符、系统字体路径、13 个特定节点、手写坐标、固定向下的箭头和单一 PNG 画幅变成通用能力。

布局参数与图意分开：已确认源定义对象、文本、条件和方向；坐标、画幅、端口与折线是可替换布局。必要时加高画布，但不拉伸原图，不删除需求判断来凑横排。长图适合一个渠道，不等于符合另一个站点的尺寸或安全契约。

## 基线不是第二份可编辑正文

从已确认源提取一次只读关系基线，记录源版本；重绘后对照该基线，不用待验收的新图反向生成期望结果。需要更改图意时先完成内容确认，再更新基线。源中删掉 Mermaid 并改用图片后，不能继续假定正文里还存在 Mermaid；保留实际可再生成的 `.mmd` 或图源与布局脚本。

基线 JSON 仅要求以下两个字段；兼容制作记录中 `nodes` 对象、`edges` 数组的形态。额外的来源记录可保留，不代表自动验证了它们：

```json
{
  "nodes": {"check": "需要补充材料？", "return": "返回补充", "next": "继续处理"},
  "edges": [
    {"from": "check", "to": "return", "label": "需要"},
    {"from": "check", "to": "next", "label": "不需要"}
  ]
}
```

节点 ID、节点文字、方向、条件标签与重复边数量均参与比较；声明顺序不参与。只忽略换行，不删除普通空格、不把否定词或近义词自动等同。未知端点、重复 JSON 键和不完整数据报错。

## 可选的离线检查器

`scripts/check_graph_preservation.py` 只用 Python 标准库，需 Python 3.10+。它不解析 Mermaid；不要再复制一次性脚本的宽松正则。Mermaid 仍交给既有已声明的引擎，不支持的语法必须明确失败。

SVG 沿用 [布局指南](svg-layout-guide.md) 的标记：节点是 `g[data-visual-node]`；边是 `g[data-visual-edge][data-from][data-to]`，包含标为 `data-visual-line="true"` 的 path/line/polyline。条件必须出现在边组的 `<text>` 中，仅填写隐藏属性不能代替条件文字。节点含辅助说明时，用 `data-visual-label="true"` 明确主标签 `<text>`；多行主标签可以分别标记。

图题、背景等非关系元素显式标为 `data-visual-decoration="true"`；不要用该标记隐藏未核对的业务内容。无标记的图、存在无法归属的绘制元素或缺失边线时报告 unsupported，不能把零命中当通过。标准 Mermaid/Graphviz 的原始 SVG 不保证符合此契约，未适配时沿既有人工语义复核，不强行宣称已自动覆盖。

由宿主定位当前 Skill 的 `SKILL_DIR`，不假定脚本在当前工作目录；输入输出路径均相对当前任务。`BASELINE_SHA256` 来自重绘前已冻结的基线，不从候选图生成。命令只输出检查报告，不安装依赖、不联网、不改图、不发布：

```sh
python "$SKILL_DIR/scripts/check_graph_preservation.py" source/graph.json export/flow.svg --baseline-sha256 BASELINE_SHA256 --report export/graph.qa.json
```

可通过 `--source source/flow.mmd` 核对基线中的 `sourceSha256`。没有该参数时来源哈希明确标记未核对；基线中的旧 Windows 路径不会被自动打开。默认拒绝覆盖不同报告；明确更新同一报告时加 `--replace-report`，但始终禁止报告路径覆盖或别名指向输入文件。

返回码：0 仅表示 `declaration-match`；2 表示关系差异，须修订；3 表示 SVG 覆盖不支持；1 表示调用/输入错误。正常报告记录基线与 SVG 的 SHA256、差异和范围，不携带字体文件或自动批准结论；调用错误可能包含本机路径，运行回执默认留在任务本地，不上传共享 Skill。

## 不能省略的后续验收

这个工具核对的是**图源声明与基线是否一致**，不是关系事实证明。即使边的 `data-from/data-to` 正确，实际 `d` 坐标仍可能画错；隐藏文字、字体缺字、箭头尺寸和最终容器缩放也可能有问题。工具刻意保留 `visual_review_performed=false` 与 `platform_verified=false`，不会自动更新正式 visual manifest 的批准状态。

继续运行原有 `check-layout`，再在最终 HTML/Markdown 容器按实际阅读宽度目视检查。几何检查、人工语义复核、最终容器验收和发布结果分别记录；全部成立才形成完整验收结论。已有 manifest 可引用本报告路径/哈希，不另建重复的运行台账。

## 维护与采用

本补强以候选补丁提出：先回维护者的唯一编辑源，执行受影响测试，再按原清单重新导出到 Kit；不直接合并公开快照来制造第二份真源。原有 `diagram / mermaid / image / check-layout` 命令保持不变。已安装副本、博客页面与双机采用记录不会随 PR 自动变化。
