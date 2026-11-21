# 实验委托模型拆解册

南麓材料实验室（9人）把委托单上的业务依赖整理为可验证的3NF关系，并保留候选键、闭包、最小覆盖和无损校验证据。

## 业务工作流

原先设计员在Excel里堆叠委托号、客户、检测项、方法与结果，再手工画表结构。痛点：依赖口径难确认、复合键容易漏判、拆表后无法证明无损。上游为委托单和已确认业务规则，本项目承接关系草案登记、函数依赖编辑、3NF合成、验证报告导出，下游为实验数据录入系统的数据库设计人员。

核心实体：关系草案 Relation、函数依赖 Dependency（规则草稿）、规则生效期 RulePeriod/RuleEntry、分解报告 Report。5业务页和独立登录页；管理员另有审计页。业务规则不执行为SQL，属性名是纯数据。

### 规则生效期与更正口径

规则按**生效日期版本化**，委托分解严格按**业务发生日（委托日期）**取当天适用的生效期：

- **基线生效期**：把「依赖编辑」确认的规则冻结为首个不可变生效期（每关系一次）。
- **补录更正**：提交更正日起的完整规则状态，登记为新生效期，可回溯插入到任意两个生效期之间，因此一条更正可以跨多个生效期；没改的规则原样抄入（未改规则照旧）。
- **委托日期选期**：取 `effective_from <= 委托日期` 的最近生效期。同一天的新报告使用更正后的规则；已受理（入队）的报告即使还没算完，也永久沿用受理时冻结的原规则。
- **并发冲突**：同一关系同一生效日期的并发更正由唯一约束拦截并返回 409；带幂等键的已成功更正重试直接返回原生效期，不重复登记。
- **缺档拦截**：委托日期早于最早生效期（或关系没有任何生效期）时拒绝入队，错误信息指出具体缺口区间；生效期时间线页展示每个关系的覆盖起点。
- 报告快照 `rule_provenance` 冻结生效期编号、生效日、来源（baseline/correction）、更正说明与完整规则；证据页与导出 JSON 均可查所用生效期和每条规则。

## 快速启动

```sh
cp .env.example .env
docker compose up -d --build
docker compose exec -T backend python -m scripts.seed_demo
```

前端 http://localhost:18243 ，后端 http://localhost:19243/docs ，MySQL localhost:17743。

|角色|账号|密码|权限|
|---|---|---|---|
|admin|admin@nanlu.test|Demo2026!|草案/依赖写入、运行、审计|
|operator|operator@nanlu.test|Demo2026!|草案/依赖写入、运行、导出|
|viewer|viewer@nanlu.test|Demo2026!|只读与导出，写API403|

## 一天的工作剧本

09:00 operator登录；09:05打开 `NL-1117-A` 材料检测委托单；09:10查看五属性 `委托号,客户,检测项,方法,结果`；09:15确认 `委托号→客户`、`检测项→方法`、`委托号,检测项→结果`；09:18在「规则生效期」建立 2026-01-01 基线；09:20按委托日期 2026-03-10 执行 `shift-20261117` 分解任务；09:25候选键为 `{委托号,检测项}`，拆出委托客户、检测项方法、委托检测结果3个关系；09:30导出 `report-1.json`（含所用生效期与冻结规则）；09:40 viewer复核3NF/依赖保持/无损均通过；10:00 admin审计。

补录更正演练：对 `NL-1117-A` 登记 2026-06-01 生效期（新增 `委托号→检测项`，旧规则照旧）。委托日 2026-05-31 的报告仍用基线3条规则，委托日 2026-06-01 当天的新报告用4条更正后规则；已受理未算完的报告不受影响。对同一日期再次提交更正返回 409 冲突，带同一幂等键重试不重复登记。

另有 `NL-1117-B` 的循环依赖 A→B/B→A与独立属性C，候选键AC/BC；`NL-1117-C` 没有确认依赖，完整属性集作为唯一候选键，不凭空猜测业务规则。

## 算法说明

Python真算，MySQL保存草案/依赖与结果，Redis传递任务，独立worker执行。

1. 属性闭包：迭代应用所有X→a，直到不再增加属性。
2. 候选键：先取不出现在RHS的必需属性，再按大小枚举其余属性子集；若闭包覆盖全集且不含已知候选键，加入结果。**最多10个属性/64条依赖**，最多1024个子集；超限API422/算法ValueError，避免指数搜索失控。
3. 最小覆盖：RHS拆成单属性，去平凡依赖；逐一删除左侧多余属性、移除冗余依赖。
4. 3NF合成：按最小覆盖左侧分组，删除被包含关系；若无关系含候选键，补入候选键关系。无依赖时保留全属性关系。
5. 验证：精确生成F+在各分解关系上的投影，枚举局部候选键，逐非平凡投影依赖检查3NF；所有原始依赖须可由投影并集推出。tableau追赶法依据FD合并符号，出现全a符号行则无损，报告包含见证行、合并步骤与最终表。

复合、循环、空决定项、无依赖均支持。不在任何RHS中的属性强制进入候选键。入队时按委托日期解析生效期并冻结快照（含 `rule_provenance` 生效期溯源与完整规则），后续更正不会改变已有报告。结果JSON含SHA256（溯源并入摘要），固定输入应有固定输出。失败态包括引用关系外属性、重复/空属性、属性超过10、依赖超过64、规则日期缺档、同日并发更正冲突、队列错误；页面可恢复并重新执行。

这是小型关系模型设计辅助工具，FD由人工提供，不能从脏数据自动推断业务规则；不连接生产数据或自动执行DDL。精确投影在10属性内有界，仍可能随依赖复杂度增加耗时。单worker串行队列，不带生产任务重试/崩溃续跑。

## 工程结构

|服务|技术|职责|
|---|---|---|
|frontend|原生HTML/CSS/JS + Nginx|5业务页（含规则生效期）、登录、共享业务表格与报告组件|
|backend|Python3.11/FastAPI/SQLAlchemy/PyJWT|校验、权限、审计、快照与导出|
|worker|Python3.11|闭包、候选键、3NF与chase|
|db|MySQL8.0|JSON属性与依赖、任务报告|
|redis|Redis7|持久任务队列|

目录：`frontend/src/{api,stores,types,components/common,hooks,pages,router,utils,constants}`；`backend/src/{routes,controllers,services,models,schemas,middlewares,utils,constants,config}`；`backend/scripts/seed_demo.py`；`backend/migrations/001_initial.sql`。每核心实体贯穿模型/schema/service/route/API/store/page。组件table/badge/frame复用，hooks/session/feedback和utils/forms/html共用；request_id/errors双后端中间件。

枚举：角色admin/operator/viewer、任务queued/running/completed/failed、生效期来源baseline/correction；前后端定义位于 `backend/src/constants/enums.py` 和 `frontend/src/constants/enums.js`，security/reports、frame/badge消费；worker持久化状态。

规则生效期 API：`GET /rule-periods`（时间线与覆盖起点）、`POST /rule-periods/baseline`（建立基线）、`POST /rule-periods/corrections`（补录更正，支持 `idempotency_key`）、`GET /rule-periods/effective?relation_id=&on_date=`（按业务日期查当日规则与缺口）；分解报告 `POST /reports` 必传 `commission_date`。

环境变量见.env.example：COMPOSE_PROJECT_NAME、FRONTEND_PORT/BACKEND_PORT/DB_PORT、DB_PASSWORD、JWT_SECRET、SEED_DEMO。默认密码仅本地演示，JWT8小时。seed按自然键只补缺失关系、初始依赖与规则生效期（含 `NL-1117-A` 的 2026-06-01 演示更正），不覆盖用户修改，重复执行幂等。schema由SQLAlchemy metadata.create_all初始化，无在线迁移引擎。

本地开发：Python3.11安装backend/requirements.txt，配置DATABASE_URL/REDIS_URL后从backend运行 `uvicorn src.main:app --reload`、`python -m src.worker`；前端用Nginx同源代理/api。5服务均有健康检查和健康依赖，数据库/Redis/worker产物为独立命名卷。停止清空：`docker compose down -v --remove-orphans`。

UI为酒红档案册，双字体由Google Fonts加载，离线有回退且业务不依赖字体网络。

## License

MIT。真实测试脚本、截图与结果保存在源码外 `../../test-artifacts/gb-4104/`。
