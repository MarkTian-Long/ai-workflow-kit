# 来源与归属

本快照的 Skill、SOP 和说明为本集合的自有文本，按仓库 [MIT License](LICENSE) 提供。session-closeout、共用沉淀标准和会话交接 SOP 来自同一维护源的通用方法；公开快照没有包含私人任务回执、客户原文、账号或机器配置。

structured-analysis-discussion 吸收以下公开项目的方法概念，未复制或打包其代码，也不运行或安装这些框架：

| 概念来源 | 固定提交 | 吸收内容 |
| --- | --- | --- |
| [stanford-oval/storm](https://github.com/stanford-oval/storm) | `fb951af7744dab086e34962e9bc6fe878e145f83` | 多视角问题、证据整理、先结构后结论 |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | `4ed377ee9110e912d4f5e1be43b317b87455053c` | 固定任务和指标以比较候选方法 |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | `679e7ecb64a2e09042b009b549b81dc0d0b983bb` | 方法、模型、质量、耗时和成本的评估矩阵 |

固定提交沿用方法来源记录，本次整理没有更新上游版本。相关来源和维护边界也随单项 Skill 保存在其 [provenance-and-maintenance](skills/structured-analysis-discussion/references/provenance-and-maintenance.md) 中，便于单独采用。

新增 HTML 汇报模板、流程图与 SVG、文档转换包装器及发布准备工具为本集合独立原创的通用实现和合成示例。HTML 只采用阅读导航、长表、证据等高层需求，未复制公司内部模板的代码、图标或业务文本；图样不来自实际项目。

文档转换工具依赖单独安装的 [Microsoft MarkItDown 0.1.7](https://github.com/microsoft/markitdown/tree/v0.1.7)，其 [MIT 许可证](https://github.com/microsoft/markitdown/blob/v0.1.7/LICENSE) 由上游维护。此处仅分发自有包装器和依赖声明，不捆绑 MarkItDown 或其可选依赖；其他依赖的许可仍分别适用。

资产选择、需求到 Demo、网页研究回流三份 SOP，以及 PDF 按页读取包装器与合成样例生成脚本，均为本集合的原创通用说明或实现。没有直接再分发内部 SOP、真实 PDF、组织控制面或第三方 Skill。

PDF 工具的核心依赖 [pypdf 6.10.0](https://github.com/py-pdf/pypdf/tree/6.10.0) 采用 [BSD-3-Clause](https://github.com/py-pdf/pypdf/blob/6.10.0/LICENSE)；可选合成样例使用 [ReportLab 4.4.9](https://pypi.org/project/reportlab/4.4.9/)，沿上游 BSD 许可。两者均独立安装，不捆绑上游包、字体或素材。
