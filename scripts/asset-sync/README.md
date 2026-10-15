# 按清单准备 GitHub 发布快照

这个 Python 3.10+ 小工具从明确登记的唯一编辑源生成发布候选，保护未归属本工具的远端文件，并核对发布后的完整 Git 文件树。仅使用标准库，不联网、不找账号或密钥；GitHub 写入由当次获授权的执行者完成。

适合需要周期性导出少量 Skills、SOP、模板和脚本的个人工具库。它不会扫描或上传整台机器，也不会安装这些内容或创建后台任务。

## 从一个小件开始

复制 [catalog.example.json](catalog.example.json)，按自己的目录、仓库和许可修改。示例使用 [合成文本](example-content/hello.md)，没有真实私人路径。每个资产明确列出源文件与目标路径；新增类型通常只需增加清单条目，遇到新文件格式或验证需求时再扩展校验器。

```sh
python workflow_asset_sync.py policy-digests --catalog catalog.example.json
python workflow_asset_sync.py prepare --catalog catalog.example.json --target example --baseline baseline.json
```

`policy-digests` 只计算范围摘要。执行者必须先核对来源、再分发权、目的地、完整依赖及数据边界，取得适用授权后才把摘要填回 `approved_policy_sha256` 并将资产设为 `approved`。摘要用于发现配置变化，不是签名、权限系统或自动授权。

`baseline.json` 由可用且获授权的 GitHub 能力获取：包含 `repository`、`branch`、`commit`、`tree_sha` 和 `files`（仓库全部文件路径到 Git blob SHA 的映射）。读取确定提交的完整递归树，拒绝截断结果。已有内容的首次纳管需在目标 `adopt_existing` 中明确登记其已审阅 blob；空仓库则先有一个正常初始提交。不要用本地猜测代替远端基线。

## 审阅、提交和读回

`prepare` 返回运行目录。查看其中 `manifest.json` 的变化路径、删除项、源摘要、静态检查及完整预期树；实际候选在 `files/`，原始来源字节在只留本机的 `source-snapshot/`。

完成实际语义、隐私、许可、依赖和类型验证后，记录事实，不把下面的示例命令当成检查证据：

```sh
python workflow_asset_sync.py review --run RUN_DIRECTORY --note "实际审阅结论" --check "实际完成的检查"
python workflow_asset_sync.py upload-plan --run RUN_DIRECTORY
```

`upload-plan.json` 给出需要写入的字节、删除项、基树和预期分支头。执行者重新核对 GitHub 仓库的可见性、权限和分支头，在当前基树上创建新树、新提交；普通非强制更新必须带 `expected_sha` 或等价的条件写入。版本冲突时重新读基线和审阅，不强盖。**分支头的原子比较由 GitHub 发布能力负责，本地脚本不提供分布式锁。**

然后获取新提交的完整树和分支头，生成 `readback.json`：`repository`、`branch`、`parent`、`commit`、`head_after`、`tree_sha`、`files`。`parent` 必须是本次基线，`head_after` 必须是新提交，`files` 必须等于完整预期树。

```sh
python workflow_asset_sync.py receipt --run RUN_DIRECTORY --readback readback.json
```

只有匹配的已审阅集合及完整读回才能推进本地发布状态。晚到回执保存事实，但不会把更新的状态倒退到旧提交。发布完成与其他机器的安装、采用和真实使用分别判断。

## 变化与退出

- 普通内容修改仍从原位主源导出。源或清单在准备后变化会要求重新准备；适配锚点不再匹配时拒绝继续。
- 新资产、新目标、许可、依赖、权限或来源范围变化须审阅和更新对应策略摘要；没有全机自动发现、自动批准逻辑。
- 没有内容变化就停止，不创建空提交或仅为时间变化升版本。
- 来源缺失不是删除。退役必须明确登记 `removals` 的路径、理由和批准，并复核引用；从资产清单移除旧条目也不会默默删除远端。
- 仅修改管理路径，保留仓库其他内容。管理路径被他人改动时要求先合并；首次接管冲突路径需要明确的基线身份。
- 目标关闭时不再导出。错误发布通过新提交恢复上个完整批准集合；Git 回退不能撤回已经暴露的敏感内容。

静态检查目前面向 UTF-8 文本及 SVG，覆盖路径、引用、部分外部资源与可配置敏感模式。它不是恶意内容检测器，不能证明权属、发现所有秘密或所有脚本联网行为，不能替代真实调用与浏览器检查。本工具自有代码按仓库 MIT 许可提供；私人清单、原始输入和运行回执不要放入公开仓库。

## 维护时验证

在本目录运行 `python tests/test_workflow_asset_sync.py`，使用标准库合成夹具验证发布边界和已知失败路径。测试默认读取本目录正式脚本；维护者若在另一位置保留唯一源码，可通过 `WORKFLOW_ASSET_SYNC_SOURCE` 指定它，不应一直测某次旧构建副本。测试不联网，不访问实际账号；临时夹具仅在测试目录下建立并清理。
