# 本地文档转 Markdown

把明确选中的本地文档转换为 UTF-8 Markdown，方便后续阅读、搜索和讨论。默认保护原文件和已有输出；这是可单独使用的命令行小工具，无需安装 Skill。

## 快速使用

需要 Python 3.10 或以上。在本目录使用自己的 Python 环境安装依赖；下面的安装命令会从包索引下载依赖，转换命令本身不下载文件。

```sh
python -m pip install -r requirements.txt
python convert.py examples/sample.html output/sample.md
```

也可指定本地文档与输出路径；路径含空格时加引号。输出父目录不存在时会创建。

```sh
python convert.py "input/document.pdf" "output/document.md"
python convert.py examples/sample.html output/sample.md --overwrite
```

`--overwrite` 只允许替换输出，仍拒绝输入与输出为同一文件，包括指向同一文件的链接。默认遇到已有输出即拒绝。转换失败时不会先清空已有输出；成功时打印实际输出位置。

## 支持与边界

接受本地 `.html`、`.htm`、`.pdf`、`.docx`、`.pptx`、`.xlsx`、`.xls`、`.csv`、`.txt` 和 `.md` 文件。不接受 URL、`file://` 或 UNC 共享路径，不递归处理文件夹。普通本地路径可以使用相对或绝对形式。

工具调用 MarkItDown 的 `convert_local`，仅注册本地文档转换器；不启用插件、音视频转写、云端文档服务或联网 AI，也不请求链接、图片或网页。它不是恶意文件沙箱；只转换有权处理且来源可信的本地文件。

PDF 不提供 OCR，扫描件可能无可提取文字。Markdown 不保留原版式、分页和全部图表；空结果会报错，不表示原文没有内容。转换不替代原件、视觉检查或事实核验，关键数值、表格、引用和图片仍应回看原文。

## 依赖、许可与验证

直接依赖固定为 MarkItDown 0.1.7，启用的文档格式 extras 见 [requirements.txt](requirements.txt)。可在独立虚拟环境安装；源码不含本机路径、安装位置、密钥或自动安装逻辑。

MarkItDown 0.1.7 的 [官方发行说明](https://pypi.org/project/markitdown/0.1.7/) 声明 Python ≥3.10 和 MIT；[该版本官方许可证](https://github.com/microsoft/markitdown/blob/v0.1.7/LICENSE) 可直接核对。本目录只包含原创包装器、说明、依赖声明和合成 HTML，不捆绑上游源码或依赖包；依赖仍各自遵循其许可证。本目录原创内容按所在仓库的 MIT 许可提供。

本次实际核验为合成 HTML 转换：标题、中文、列表、表格和链接保留，以及缺输入、同一输入输出、已有输出保护、显式覆盖和缺依赖提示。没有逐格式验证所有文档，也不证明扫描 PDF、复杂版式或实际业务文档可完整转换。

退出码：`0` 成功；`2` 路径或输出保护拒绝；`3` 缺少导入依赖；`4` 转换或本地读写失败。缺少格式所需的可选依赖也可能由上游以转换失败返回，错误信息会保留原因。
