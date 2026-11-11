# 来源、依赖与维护

版本0.1.0，2026-11-11。本文、SOP、检查器与合成样例为独立编写的通用内容，按本包 [MIT](../LICENSE) 许可提供；没有复制第三方 Skill 正文、主题、图片或实现。参考概念不构成兼容性和效果保证。

| 参考 | 固定来源 | 借鉴与边界 |
| --- | --- | --- |
| Adaptive Travel Planner | [c2dd8913](https://github.com/ryunana/adaptive-travel-planner-skill/tree/c2dd8913dfc2af6ad6e42cd2440340dc0cb33642) | 参考路线、行李、天气和组合疲劳；未运行或捆绑上游 Skill。 |
| Trip Planner Skill | [3f957770](https://github.com/skywain/trip-planner-skill/tree/3f957770c6978180e3a626f5751dabb06c4657de) | 参考路线骨架与单一数据源；不打包多主题渲染器。 |
| Agent Skills | [格式规范](https://agentskills.io/specification) | 2026-11-11核对 SKILL.md、frontmatter 与按需附件；没有宣称全部宿主实测。 |
| Open-Meteo | [官方文档](https://open-meteo.com/en/docs) | 2026-11-11核对日期、时区、单位、缺值和模式来源；本包不调用接口、不附密钥，接入时重查条款。 |
| GitHub Pages | [官方工作流说明](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) | 构建产物与部署分开；匿名目标页和浏览器验收为本方法的额外交付要求。 |

核心文字无运行依赖。可选检查器仅需 Python 3.10+ 标准库，不联网、不改文件；实际查询与浏览器由宿主提供。第三方参考如将来直接改编，必须重新审查固定版本许可并保留适用声明。

本公开包是经授权的发布快照；唯一编辑源与发布回执由维护者另行保管。原稿已整理为同一来源中的精确文件映射，不维持两份独立正文。修改先读当前远端并与主源合并，不能以旧快照覆盖授权修订；新增发布文件同步维护允许清单及中英文入口。

安装者保存完整目录，不需要本仓库其余 Skill。先让宿主显式读取 SKILL.md 做小任务，再分别检查安装、发现、触发和结果。不会自动安装、设置后台任务或授权外部服务。
