# 统一数据约定与检查器范围

方法允许表格或结构化数据；不要为了运行脚本伪造缺失值。行程 revision 是时间轴、交通、地图和预算的共同版本，证据状态与预订状态分开。

完整应用可维护 trip、places、evidence、bookings、variants、schedule/legs、costs、weather、publication。places 保存实际入口、来源、坐标系；variants 引用地点 ID。真实数据不公开订单号。unknown、null 不是零或 false。

## 附带的最小 JSON 契约

[sample](synthetic-trip.json) 是合成输入，日期、地点、报价均不是旅行建议。Python 检查器仅识别如下字段，不是全量 JSON Schema 或自动路线求解器。

| 字段 | 约定 |
| --- | --- |
| travelers / currency | 正整数人数、统一币种；quantity 已是数量，不再自动乘人数。 |
| recommendation / conditions | ready 表示前提已满足；未核实前提改 conditional。conditions 用 id、status。 |
| evidence | id、status、source、checked_at、valid_for；脚本检查字段存在，不打开来源证明事实。 |
| bookings | id、state、display_as_booked；candidate/pending/cancelled 不可显示为 booked。 |
| luggage | day、stored_at、retrieve_at、confirmed；只覆盖寄存取回模型，随身携带用人工审阅，不伪造寄存记录。 |
| return_leg | event、planned_leave 为带 UTC offset 的 ISO 时间；arrival_buffer_min、ride_min、wait_min、pickup_min 非负。 |
| schedule | 当前已选方案的一条不重叠时间轴，start/end 带 offset；不要把多个备选塞入同一数组。 |
| costs | 唯一 id、unit_price、quantity、basis；basis 为 per_person/room_night/vehicle/vehicle_day/group。included_in 指向已计费套餐，null 金额报告未知。 |
| weather | state、provider、fetched_at、previous_fetched_at、wind_kmh、rain_probability、assessment；failed 不改变旧时间，low_risk 不允许缺关键字段。 |
| publication | claims_public_access 及 artifact/anonymous_page/interaction 的 passed/failed/not_run 状态。 |

在 Skill 目录内运行：

```sh
python scripts/check_trip.py assets/synthetic-trip.json
python -m unittest discover -s evals -p 'test_*.py' -v
```

返回 issues、known_subtotal、per_person_known、budget_complete、target_arrival 和 latest_leave。检查结果依赖输入声明，不能验证来源是否伪造、未声明活动、真实交通、天气安全、缺失的关键约束或完整隐私。CLI 对不支持/损坏的输入退出2；发现待处理问题退出1。输出的最迟离场时间只服从输入预算，不是保证赶车的承诺。
