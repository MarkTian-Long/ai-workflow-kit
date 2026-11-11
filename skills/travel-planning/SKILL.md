---
name: travel-planning
description: Use when planning, comparing, auditing, or revising travel itineraries or preparing a travel roadbook, especially when bookings, luggage, weather, last-mile transport, return deadlines, or public sharing affect the decision. 适用于旅行规划、行程审核、临时调整与路书交付。
license: MIT
compatibility: Requires current web or browser access for live facts. Optional offline checks require Python 3.10+; no third-party packages.
metadata:
  version: "0.1.0"
---

# 旅行规划与路书交付

产出可执行、可调整的计划，不以景点数量或网页复杂度衡量成功。只读用户已有材料时，也能输出有条件方案。

## 读取与路由

开始规划读取 [证据规则](references/evidence-policy.md) 和 [规划规则](references/planning-rules.md)。制作、更新或发布网页时再读 [交付验收](references/delivery-gates.md)。结构化数据及可选检查见 [数据约定](assets/trip-contract.md)；维护与借鉴边界见 [来源](references/sources.md)。不一次加载全部附件。

## 执行

1. 复用对话、截图和有效订单。确认旅行当地日期与时区、起点、人数、交通、行李、体力、必做体验及预算。候选车次不是已购订单，性别不代表体力或床型。只问会改变决定的缺口。
2. 先查决策关键事实：适用日期的开放、航班或车船班次、入口、票务包含项、寄存及返程。区分 verified、user_provided、estimate、unknown、conflict；预订状态单独记录。没有工具就披露能力边界，不虚构查询或电话确认。
3. 必要时比较少量有实质差异的路线骨架，再细化主方案。比较门到门时间、行李存取闭环、折返、体验与疲劳。两种方案若都依赖未知寄存，均为有条件，不能把换序包装成已解决。
4. 从固定返程倒排交通、等车、取物和到站提前量；各时段标注固定或建议。预算明确单位，套餐去重，未知不按零。延误先删可选活动，不压缩安全余量。
5. 天气按地点、时段及活动解释，运营状态另查公告。缺风速或降水数据不能推出低风险；给出复核时间和减项条件。
6. 输出顺序：推荐与依据 → 成立前提 → 日程及交通行李 → 预算 → 备选与少量待确认项。局部修改只说明变化及连带影响，不重写全部攻略。
7. 用户要求网页时，用同一份行程数据驱动日程、地图、交通和预算；路线、地图日期筛选和刷新状态独立。地图表达空间关系，卡片表达行动，不重复绘制装饰性伪道路。
8. 检查来源时效、时间冲突、寄存闭环、返程余量、费用单位和模块一致性。公开前脱敏，检查实际产物与匿名目标页面，不以部署绿灯替代可访问性测试。

## 完成边界

生成、保存、发布、可访问、安装、发现、触发和有效执行分别记录证据。不自动订票、付款、改签、安装插件或后台监测。没有独立 Agent 测试时，明确区分人工场景审阅、离线数据检查和独立行为验证。可重复检查见 [evals/VALIDATION.md](evals/VALIDATION.md)。
