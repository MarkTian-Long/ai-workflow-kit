# 本地 PDF 按页读取

先查看各页有多少可提取文字，再只提取需要的页。工具不上传文件、不调用网络、不修改PDF，也不自动安装依赖。

## 开始使用

需要 Python 3.10 或以上。在本目录使用自己的环境安装核心依赖：

```sh
python -m pip install -r requirements.txt
python pdf_pages.py index input/manual.pdf output/index.md
python pdf_pages.py extract input/manual.pdf output/selected.md --pages "1,3-5"
```

页码指PDF物理页，从 **1** 开始，可能与纸面页码不同。支持单页、闭合范围和逗号组合，重复页去重后升序输出；0、负数、反向范围、空页段和越界页码会报错。索引扫描全部页面，但只输出文字量、状态与短预览，不输出全文。

默认低文本阈值为40个非空白字符，可用 `--low-text 80` 调整。`text` 表示达到该阈值；`low_text` 表示少量可提取文字；`no_text` 表示未提取到文字。少量或空文字不能证明页面没有内容。工具**不提供OCR**，图片文字、扫描件、表格版式和页眉页脚需要回看原件或渲染相关页面。

## 文件保护与失败

只接受明确的本地 `.pdf` 文件，不接受URL、`file://`或UNC共享路径。输出限 `.md` 或 `.txt`，以UTF-8保存，必要时创建父目录。

已有输出默认拒绝；确认只替换派生文件时才加 `--overwrite`。输入与输出为同一文件或指向同一文件的链接始终拒绝。加密PDF直接失败，不尝试空密码、解密或绕过保护；请由权利人提供获准可读副本。读取、页码或转换失败时不先清空旧输出。

退出码：`0` 完成；`2` 输入、选择或保护规则拒绝；`3` 缺核心依赖；`4` 加密、损坏、零页PDF、提取或本地读写失败。错误写入标准错误，不伪装成空文本成功。工具不是恶意PDF沙箱，只处理有权使用且来源可信的文件。

## 生成合成样例

仓库只提供生成脚本，不附带业务PDF。样例有三页：正常文字、少量文字、无文字层的栅格图案。第三页用于检查空文本警告，不代表真实扫描件的全部情况。

```sh
python -m pip install -r requirements-examples.txt
python examples/generate_sample.py output/synthetic.pdf
python pdf_pages.py index output/synthetic.pdf output/synthetic-index.md
python pdf_pages.py extract output/synthetic.pdf output/synthetic-selected.md --pages "2-3"
```

生成脚本同样拒绝已有文件。ReportLab只用于可选样例生成，不是解析工具的运行依赖。

## 依赖、许可与核验范围

核心依赖固定为 [pypdf 6.10.0](https://pypi.org/project/pypdf/6.10.0/)，采用 [BSD-3-Clause](https://github.com/py-pdf/pypdf/blob/6.10.0/LICENSE)。可选样例依赖为 [ReportLab 4.4.9](https://pypi.org/project/reportlab/4.4.9/)，采用其项目声明的BSD许可。依赖均独立安装，本目录不捆绑上游源码、包或字体；原创包装器、生成脚本和说明按所在仓库MIT许可提供。

本工具使用合成PDF实际检查逐页索引、指定页提取、低/空文本提示、加密拒绝及常见路径/页码/输出保护。没有证明复杂文档的文字顺序、表格结构、图片语义或真实扫描件可完整读取；派生文字不是版面或事实正确性的独立证据。
