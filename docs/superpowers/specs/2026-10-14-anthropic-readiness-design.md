# Anthropic Readiness：详细设计

创建日期：2026-10-14。更新日期：2026-10-15。修订：6。状态：规格与阶段 A 计划已获用户批准，在当前会话顺序实施。当前执行与验证状态见 docs/harness/progress.md；本文件描述目标契约，不代表全部功能已交付。

## 1. 目标与成功条件

为只掌握最终 API 的测试人员提供本地黑盒 CLI，分别回答：指定交付是否满足声明的 Anthropic Messages 协议约束；固定版本 Claude Code 是否完成指定任务；同一测试契约下两次交付是否出现变化。结果不得自动归因于 daemon、转换器或模型内部。

协议随时间演进是核心需求。用户应能选择一个明确 API 版本及测试规则快照，测端点在该契约下的兼容性；项目应能周期发现官方变化、更新规则与用例，同时保留旧版评估能力。最终结果用于选择并锁定有实测依据的 Agent 运行组合，不能把更新测试器等同于自动升级用户的工作流。

首个可验收交付是阶段 A：安装后可离线证明检测器能识别已知错误，并显式启用少量真实请求，得到版本化 JSON、离线简体中文 HTML/Markdown 和可定位的证据。阶段 A 不输出 Claude Code ready。

标准开发和 CI 环境为 Linux Dev Container，用户交付包含独立 Docker CLI 镜像；开发和运行均不依赖 macOS、Homebrew 或用户本机 Python。容器是主要上手方式，Python wheel 作为可选安装形式保留，测试与判定逻辑共用同一个包。

源码拟托管在维护者个人 GitHub 账号，GitHub Actions 负责检查、构建及受控发布，Docker Hub 为首选公开镜像分发渠道。提供面向人类与 Agent 的贡献指南、Issue/PR 模板和仓库内协议维护命令。报告采用工程/学术文档式排版，兼顾离线阅读、打印和 Agent 解析。

开发 harness 是首期工程能力：为人和编程 Agent 提供可发现的仓库上下文、可复现环境、统一检查入口、可定位失败和阶段交接记录。格式、静态类型、数据 schema、架构依赖、检测器回归与打包/容器检查都是可执行门禁，不以提示词“请保证质量”代替验证。

开发与独立实测验收分离，以固定源码、配置、case ID 和产物对齐。历史报告仅作只读依据，不复制实际 endpoint、模型名、原始日志或临时探针进入产品。源码、注释、机器字段与 case ID 使用英文；本设计与面向用户的说明使用简体中文。

### 方案选择

采用 Python 3.11+、httpx、jsonschema、PyYAML、pytest，使用标准库 argparse、dataclasses、html 和 zipfile（后期导出）。用 uv 锁定依赖，标准开发/镜像基线为 Python 3.12 的固定 patch 和固定 Linux 基础镜像摘要，发布 Python wheel 与 Docker 镜像；不绑定 uv 作为用户运行时要求。

替代方案一是改造现有测试工具，但需更换其核心 SSE 和通过条件，且会继承与本任务无关的功能。替代方案二是只通过 SDK 测试，开发更快，却会丢失聚合前事件异常。选择直接 HTTP 加独立纯函数检测器，SDK 留作补充适配器。

选用共享基础、分别构建开发与运行目标：开发镜像含编辑/测试工具，运行镜像仅安装 wheel、规则包及运行依赖。相比把开发镜像直接交付用户，后者更小且版本边界清楚；相比维护两套无关 Dockerfile，共用基础与锁文件更容易保持一致。无需引入 Kubernetes、常驻服务或数据库。

## 2. 范围与分阶段边界

| 阶段 | 可交付能力 | 明确的验收边界 |
| --- | --- | --- |
| A | Python 工程/harness、GitHub CI 检查与构建、贡献指南/模板、Dev Container、Docker 运行镜像、固定协议包、4 个基础 API case、回放与 JSON/HTML/Markdown 报告 | 统一门禁及容器离线验收；规则/证据可追踪；报告与合法对照；不宣称完整工具闭环 |
| B | 流式工具、禁用工具、随机工具结果消费、错误工具结果恢复、显式版本矩阵 | 有效前序调用与匹配的 tool_use_id；答案只在工具结果中出现；矩阵每行独立契约及预算 |
| C | 固定版本 Claude CLI 的可选容器与原生适配器、3 个基础工作流、运行组合锁定建议 | 工具执行、产物字节、独立测试、有效结束；记录 Linux 容器/宿主机的运行边界 |
| D | 重复/重试、比较、重评分、脱敏导出、协议更新 Agent 命令/周期维护、开源发布准备 | 不覆盖旧规则/证据；协议候选经审阅/回归后进入新包；GitHub/Docker Hub 发布独立配置 |

Thinking、并行工具为可选 profile，完成专门用例后才能标记实现。后台/嵌套子 agent、Compaction、原始 CLI HTTP 抓取、长上下文、压测、云平台、数据库、LLM Judge 不在基础首版验收范围。标签只记录异常候选，不独立证明推理泄漏。

各阶段先交付本地固定提交、验证命令、样例产物、限制及交接说明；GitHub 仓库创建、源码推送和 Docker Hub 发布在进入相应步骤时按维护者明确授权进行。A 即提供可提交的 GitHub Actions 定义和本地等价验证入口；仓库连接前将远端检查标为未运行，不能凭 workflow 文件存在声称 GitHub CI 通过。公开 CI 的产品测试只用合成数据，不调用真实目标。

协议版本可选与精确锁定在 A 就实现，不能推迟到维护阶段；D 增加周期检查与候选更新工具。定时检查官方资料属于独立维护任务，不改变测试默认离线或真实端点显式启用的约束。

## 3. 模块与接口

```text
CLI -> config + case registry -> runner -> transport
                                       -> validator
                                       -> evidence writer -> result.json -> HTML
replay -> capture reader ---------------> validator
```

| 模块 | 职责与主要接口 | 约束 |
| --- | --- | --- |
| config.py | load_target(path) -> TargetConfig | 负责文件读取和配置校验；不联网；凭据由执行层在运行时注入 |
| contracts.py | resolve_contract(id, revision) -> ContractBundle | 验证清单与哈希；精确选择版本，禁止运行时联网取 latest |
| models.py | ContractSpec、AssertionResult、AttemptResult、RunResult | 纯领域数据，不依赖 HTTP/CLI 或文件加载器 |
| transport.py | send(RequestSpec, Limits) -> Capture | 有界增量读取，返回完整或部分证据及终止原因 |
| sse.py | feed(bytes)、finish() -> SSEFrame | 只处理 SSE framing，不理解 Anthropic |
| validation/messages.py | validate_message(value, contract) | 按所选规则包的响应结构与工具约束 |
| validation/stream.py | consume(frame)、finish(termination) | 有序状态机、可持续收集异常 |
| cases.py | versioned CaseDefinition registry | 前置条件、预算、请求、断言、profile 成员关系 |
| runner.py | run(plan, transport) -> RunResult | 调用计数、状态聚合、原子落盘；A 阶段顺序执行 |
| evidence.py | sanitize、persist、reference | 统一脱敏和受限相对路径；报告器不可直接读取环境 |
| reporting.py | render(result, destination) | 纯离线，统一转义 HTML |
| cli.py | validate / run / replay / report / contracts list、show | 默认无网络；明确退出码 |

实现采用 src/anthropic_readiness，测试在 tests，合成 fixtures 在 tests/fixtures，机器 schema 与规则包随包放入 resources/schemas 与 resources/contracts，通用配置在 examples。各模块只依赖表中下游接口，验证器能脱离网络运行。第 16 节定义 Python 工程结构与开发门禁；A 不引入插件系统、通用工作流引擎或异步并发。

## 4. 目标配置契约（target schema v1）

示例为通用占位配置，不是本机真实目标：

```yaml
schema_version: "1.0"
name: example-local-target
delivery_id: example-build-001
protocol: anthropic.messages
messages_url: http://127.0.0.1:8000/v1/messages
model: example-model
api_version: "2023-06-01"
beta_headers: []
protocol_contract:
  id: anthropic-messages-2023-06-01-core
  revision: "1.0.0"
auth:
  mode: none
capabilities:
  streaming: true
  tools: true
  thinking: false
  parallel_tools: false
response_model_policy: request_or_alias
response_model_aliases: []
limits:
  connect_timeout_s: 5
  read_timeout_s: 30
  attempt_timeout_s: 90
  run_timeout_s: 300
  max_response_bytes: 4194304
  max_event_bytes: 262144
  max_events: 10000
  max_requests: 4
  max_tokens: 512
```

所有字段按版本化 schema 校验；拒绝未知字段、重复 YAML key、字符串假布尔、非有限数字、空模型、无效 URL 与非正限额。禁止 URL 内嵌凭据、fragment、query；只支持 http/https，Messages URL 原样使用，不猜测或补齐 /v1。允许回环、内网地址，因为这正是目标场景。默认验证 TLS，不跟随 redirect，httpx trust_env=false，避免继承代理改变测试路径。

auth.mode=api_key 时必须提供 credential_env（合法环境变量名），值缺失记环境阻塞，配置文件不支持字面密钥。请求使用 x-api-key；none 不发送任何模拟鉴权值。A 不验证鉴权安全性，不调用模型列表、不通过列表决定是否可测。anthropic-version、anthropic-beta 和 Content-Type 由已解析配置生成，A 不支持任意请求头覆盖。beta_headers 为空时不发 beta 头，否则去重并按固定顺序发送；不注入 SDK 或模型名推导的 beta。

protocol_contract 必须精确解析为随工具发布且已审阅的规则包（第 14 节）。api_version、beta 集合、profile/case 与规则包支持范围不相符时，在发送请求前报配置错误。revision 是本工具规则版本，不是 Anthropic API 日期；spec_as_of 使用实际核对资料的日期。A 首个包只验证选定 Messages 核心子集，beta_headers 必须为空；beta 头序列化器用合成契约做离线自测，不据此宣称首包支持真实 beta 能力。

model 结构与模型身份分别断言。response_model_policy 是必填项：structure_only 只验证非空字段并明确身份未检查；request_or_alias 要求返回值等于请求 model 或显式别名，精确比较，不进行前缀猜测。别名属于交付契约，不是自动学习结果。能力不从模型名字推断；选了必需 profile 却声明其能力为 false 时保留 SKIP 并使评估不完整，不能通过更改分母变成通过。

配置指纹采用已解析、填充默认值、排序键的规范 JSON 的 SHA-256；包含 endpoint、model、能力、别名、限额、auth 模式与变量名、API 版本、beta 集合、规则包 ID/revision/哈希，不包含凭据值。delivery_id 单独保存，不参与配置契约指纹；D 的可比性规则允许交付编号变化。

## 5. 请求、预算与证据采集

A 每个 case 只运行一个 attempt，每个 attempt 最多一个请求；默认关闭重试和缓存。能力不符或用户排除时不发送请求。执行前显示计划，--dry-run 仅展示脱敏计划。真实执行命令 run 和 B 阶段 matrix 必须带 --allow-live；replay、report、validate、contracts list/show 均不访问网络。D 的资料更新仅由 check-updates --allow-network 单独启用。

预检发现 max_requests 小于计划最坏请求数时返回配置错误，不开始执行。运行中到达 run_timeout_s 时保留已有结果，尚未执行的必需 case 记 INDETERMINATE（run_deadline_exceeded），不当作用户主动 SKIP。attempt 与 run 的时限分别控制；配置中的总时限不保证每个 case 都能用满自身时限。

时间使用 UTC ISO 8601 保存，HTML 默认注明 Asia/Shanghai。耗时与事件到达使用 monotonic 时钟，不受系统时间调整影响。接收到响应头、第一块应用字节、每个读取片段、每个已派发 SSE frame 和终止分别记录相对时间。

Capture 包含脱敏请求、HTTP 状态、白名单响应头、应用响应体、读取片段长度与相对时间、SSE frames、终止原因、观察到的字节数、保留字节数和完整性。终止拆为 protocol_end（message_stop/error_event/none）和 capture_end（eof/timeout/read_error/capture_limit/cancelled）。应用字节指 HTTP 库提供的响应内容，已移除 HTTP 传输 framing，可能已做内容解压；不宣称抓到 TCP 包或 HTTP chunk。读取边界只用于重放，不用于协议合法性判定。

message_stop 后继续读取至 HTTP EOF 或既有限额，检查实际观察到的尾随事件。已完整关闭消息但连接未关闭时，已证实的消息结束和内容断言不改判；必需的“尾部采集完整”断言为 INDETERMINATE，未发现其他错误时整体评估不完整。不得凭缺少 HTTP EOF 推断消息一定截断。error_event 同样记录协议终止与采集终止，但已知服务错误仍使任务 FAIL。

响应体、单事件、事件数均有上限；超限立即停止，capture_end=capture_limit 并记录具体 limit_kind。字节上限针对解压后的应用数据，必须在增量读取/解压路径限制内存，不能等完整响应进入内存后才检查。总时限需覆盖持续 ping 的流，不能只依赖单次 read timeout。A 在内存中保留有界响应，结束/失败后统一脱敏落盘；不中途把凭据写入临时文件。可捕获异常、Ctrl-C 与部分流尽力生成可读结果，能确认的缺陷保留，未执行部分不可标为通过；SIGKILL、断电或无法写盘时不承诺完整产物。

### 默认落盘内容

```text
<new-output-directory>/
  result.json
  report.html
  report.md
  evidence/<case_id>/<attempt_id>/
    request.json
    response.json
    body.bin
    reads.json
    events.jsonl
```

response.json 保存传输元数据与终止原因，body.bin 保存应用响应体，reads.json 保存读取观测，events.jsonl 保存 SSE 事件视图；非流式响应的事件文件为空。无法开始请求的 case 仍在 result.json 中保留前置条件结果，不伪造响应证据。

输出目录必须不存在，采用排他创建；目录权限 0700、文件 0600（支持的平台）。每个文件先在同目录写临时文件再原子替换。证据路径必须留在输出目录，不接受绝对路径、.. 或符号链接越界。JSON 引用包含相对路径、SHA-256、event 序号或 JSON Pointer。失败断言必须至少有一个证据引用；没有可定位证据时只能判证据不足。

### 脱敏与“原始”的含义

请求头白名单为 Content-Type、Accept、anthropic-version、anthropic-beta；响应头白名单为 Content-Type、Content-Encoding、request-id、anthropic-request-id、retry-after，名称不区分大小写。只记录相应存在字段，不要求目标返回所有可选头。x-api-key、Authorization、Cookie、Set-Cookie 以及任何未列入白名单的头不落盘。运行时已知密钥及其 JSON 转义形式在配置快照、响应、事件、错误、stdout/stderr 和允许项值中统一替换，跨读取边界的密钥先合并后处理。判定在脱敏前的内存数据上执行。

body.bin 在未替换时是保留的应用原始响应；发生替换时明确标记 transformed=true、transforms=[credential_redaction]，保留原字节数与原始哈希，不再宣称逐字节原始证据。脱敏后的事件引用用序号，不错误沿用被替换前的字节偏移。A 不提供明文密钥证据保留开关。

reads.json 的长度/时刻描述采集时原始读取，仅在 body.bin 未转换且完整性满足时用于原边界回放。转换后的 body.bin 按新的读取方案回放，不能按旧长度切片后宣称复现原始边界；events.jsonl 另存脱敏的事件视图。脱敏影响的语义字段不可从掩码内容重新验真，相关重评分断言为 INDETERMINATE；报告展示原评估结果，不从脱敏正文重算原结论。

已知凭据脱敏不等同于识别一切业务秘密。真实目标输出仍留在本地、被 Git 忽略；公开 fixtures 全为合成数据。D 的导出采用显式白名单和再次扫描，不能直接压缩整个工作目录。

## 6. SSE 解码与协议验证

### 6.1 两层模型

SSE framing 服从 WHATWG：处理 UTF-8 跨读取、开头 BOM、LF/CRLF/CR、多行 data（以换行连接）、注释、无冒号字段、id/retry 与未知字段。空行才派发事件，EOF 不派发未结束的事件。无 event 名时 framing 默认名为 message；Anthropic 验证层仍检查其是否满足显式事件名契约。[WHATWG SSE](https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream)

framing 不因一个 JSON 片段不可独立解析而报错。UTF-8 使用增量解码；无效字节单独保留编码异常，不能把边界处暂未齐全的字符当作非法。JSON 验证严格拒绝 NaN/Infinity；错误需指向事件序号或未派发尾部。OpenAI 风格 [DONE] 不是 Anthropic 的结束事件。

Anthropic 验证层核对事件名与 data.type、有序消息/块生命周期及最终消息。工具参数由 input_json_delta 拼接，在块关闭后解析；不要求每个 delta 为完整 JSON。未知事件按前向兼容要求保存并提示，不单独判 FAIL。[Anthropic Streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)

下述不变量与第 7 节用例定义首个规则包的待实现契约，不是对所有历史及未来版本的全局假设。contracts.py 将已解析包转为纯数据 ContractSpec 供验证器使用；验证器不依赖规则文件加载器。将来有不同流式格式时选择独立规则实现，不能用最新版规则检查旧版后声称旧版不兼容。

### 6.2 状态与不变量

消息状态为 BEFORE_START -> CONTENT -> MESSAGE_DELTA -> STOPPED，另记录 ERROR；已知无效事件形成断言后不清空状态或丢弃前次证据。除注释、ping、未知扩展事件外：

- message_start 必须恰好一次，载荷为 assistant Message，初始 content 为空；重复起始不能用后一次覆盖前一次。
- content_block_start 仅在 CONTENT；index 为非布尔的非负整数，与最终数组位置对应，从 0 连续分配且不可复用。块内部状态为 OPEN/CLOSED，按 index 分别维护，不能只保存一个全局“当前块”。
- content_block_delta 必须关联已打开且未关闭的块；已知 delta 类型必须匹配块类型。text_delta.text 是字符串，input_json_delta.partial_json 是字符串。
- content_block_stop 只能关闭一次；允许无 delta 的块，不强制 text 或 JSON delta 数量大于零。工具 ID 必须非空且在响应内唯一。
- message_delta 只能在所有块关闭后出现，可出现多次；最终已知字段合并，usage 不重复累加。MESSAGE_DELTA 后不重新打开内容块。
- message_stop 恰好一次，在 message_delta 后且没有未关闭块；停止后出现已知内容/生命周期事件判错。ping/注释不改变生命周期。
- 正常 EOF 且未发生 error_event 时，缺 message_start/message_delta/message_stop 或未关闭块均有独立断言。仅在终止前存在未派发的有效 data 事件尾部时认定截断；完整终止后的注释或无 data 尾部不自动判错。发生超时/读错误时，缺尾部相关断言为证据不足。

未知顶层事件在其他已知不变量均满足时可保留限定 PASS，加上未验证扩展提示。未知内容块或 delta 若影响该 case 的内容重建，相关断言 INDETERMINATE；已证实的重复起始等 FAIL 不会被它掩盖。不把新扩展类型自动当成协议缺陷。

HTTP 200 中收到 error 事件时，记录服务错误并使本次任务 FAIL，failure_domain=service_error；错误事件本身是允许的协议表达，不直接称 SSE 格式损坏。保留已观测协议缺陷，并避免随后缺 message_stop 产生误导性的重复根因。

### 6.3 响应与工具输入

消息最小契约检查 id、type=message、role=assistant、model、content 数组、stop_reason、stop_sequence 和 usage 核心数值类型。允许新增字段，不硬编码消息/工具 ID 前缀，不用可见文本长度推算 token 数。[Messages API](https://platform.claude.com/docs/en/api/messages/create)

文本 case 需要非空可见文本且按任务自然结束。max_tokens 是合法协议停止，但受控短任务未完成时 behavior 断言 FAIL；保留 protocol=PASS 的可能性。未知 stop_reason 标为该项 INDETERMINATE，不擅自扩充受支持契约。stop_sequence 的关系随请求约束校验，不假设每种合法停止原因都适用于本 case。[Stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)

非流式工具 input 必须是 JSON 对象且通过本 case 的 Draft 2020-12 input_schema；空对象并非普遍非法，只有缺少该工具所需字段才失败。强制工具 case 必须名称、调用次数、参数精确语义、非空唯一 ID 与 stop_reason=tool_use 同时正确，不能仅凭“存在 tool_use”通过。

流式工具验证器 A 阶段接受合成 fixtures 自测，但真实流式工具 case 留到 B。普通工具流初始 input={} 配合后续分片是合法对照；最终拼接 JSON 为非对象、缺字段或错误名称才失败。非空初始 input 与后续分片并存时不猜测合并语义，记相关参数重建 INDETERMINATE，并保留原事件。

## 7. 阶段 A 用例与 profiles

| Case ID / version | 请求与上限 | 必需断言 | 所属 profile |
| --- | --- | --- | --- |
| ANT-MESSAGE-001 / 1 | 非流式简短问候；1 请求 | HTTP/JSON/消息核心结构、模型策略、非空文本、自然完成 | anthropic-basic / 1 |
| ANT-TEXT-SSE-001 / 1 | 流式 Hello 类提示；1 请求 | SSE framing、生命周期、模型策略、文本、自然完成 | anthropic-basic / 1 |
| ANT-TEXT-SSE-002 / 1 | 流式 Count 类提示；1 请求 | 同上；记录独立请求结果，不替代 Hello | anthropic-basic / 1 |
| ANT-TOOL-FORCED-001 / 1 | 非流式强制 get_weather(location="Hanoi")；1 请求 | 精确工具名、恰好一次、有效 ID、input schema、Hanoi、tool_use 停止 | anthropic-tools-smoke / 1 |

问候两个 case 的 user content 固定为 `Say hello in one short sentence.`，只要求非空文本，不用确定性规则伪称验证了问候语义。Count 固定为 `Count from 1 to 5, using digits.`，behavior 断言抽取文本中所有连续数字串，要求依次为 1、2、3、4、5；不限制标点或额外不含数字的文字。其任务断言与通用协议断言分开，不把格式偏好混入协议。

工具 case 提示固定为 `Use get_weather to check the weather in Hanoi.`；工具 schema 为对象，location 为唯一必填字符串字段且 additionalProperties=false，tool_choice={type:tool,name:get_weather}；不实际查询天气。案例请求内容在 case version 中固定，不能临时修改后沿用旧版本。每个 case 的 max_tokens=min(512, limits.max_tokens)，实际请求值进入测试指纹；因预算导致任务截断仍按结果判定，不能自动补发更大预算请求。

默认 run 选择 anthropic-basic，最多 3 个请求；加选 anthropic-tools-smoke 后去重共 4 个。profiles 通过显式 case 集合表示，无隐式包含/重复统计。运行前校验预算足够；不足为使用错误，不偷减 case。claude-code-basic、tool-loop、optional-thinking、optional-parallel 在未实现阶段不可作为已完成 profile 被选择；CLI 明确报“此版本未实现”，报告列出未覆盖范围。

标签候选检查限这些未要求输出标签的受控任务，只记录 <analysis>、<summary>、<think>、<thinking> 的位置与任务结果。A 不据此执行“推理泄漏”断言，也不据标签出现将一个已完成协议 case 改判失败。

## 8. 状态、聚合与退出码

断言包含 id/version、category（protocol/behavior/client/environment）、required、status、reason_code、预期摘要、实际摘要和 evidence_refs；没有单一百分比总分。protocol 为线路格式与契约，behavior 为直接 API 的受控任务，client 为真实 CLI 的工具链和产物，environment 为执行前提/采集条件。

| 状态 | 判定依据 |
| --- | --- |
| PASS | 已执行并且必需证据足以证明约束满足 |
| FAIL | 观测结果违反必需契约或受控任务要求 |
| SKIP | 能力明确不支持或用户显式排除；记录原因 |
| BLOCKED | 本地缺凭据/CLI/必需工具、权限阻止执行或目标无法建立连接等依赖阻塞 |
| INDETERMINATE | 超时、读取中断、本地采集限额、未知扩展阻碍判定或证据不完整 |

HTTP 明确返回非成功状态导致任务 FAIL，附 HTTP/service_error 分类；401/403 同样保留实测响应，不静默改成 BLOCKED。DNS/拒绝连接/TLS 建连失败记录 BLOCKED，仅说明当前访问受阻，不能推断模型能力。正常 EOF 的不完整流为协议 FAIL；reset/timeout 的缺尾部为 INDETERMINATE。若此前已捕获重复起始等确定错误，attempt 仍为 FAIL，同时保留采集中断。

各维度单独汇总。case/attempt 必需断言中优先级为 FAIL > BLOCKED > INDETERMINATE > SKIP > PASS，纯前置条件跳过可无网络断言。非必需诊断不改变 case 状态；未开展的维度显示 not_evaluated，不对空断言集合求得 PASS。profile 所有必需 case 必须有记录，缺记录不能 PASS。

profile readiness：必需 case 任一 FAIL 为 not_ready；无 FAIL 但存在 BLOCKED/INDETERMINATE/SKIP/缺失或零必需用例为 incomplete；非空必需集合全部 PASS 为 passed。该词仅表示这个 profile/version 的本次样本，不叫认证。总报告以各 profile 的结论并列展示。

CLI 退出码：0=选定 profile 全部通过或纯报告/配置操作成功；1=有必需 FAIL；2=命令/配置/输出路径错误；3=评估不完整；4=工具内部异常；130=SIGINT；143=SIGTERM。中断或内部异常优先返回对应退出码，结果仍保留已发现 FAIL；正常评估结束时混合失败与不完整返回 1。离线错误回放返回 1 是预期检测结果，pytest 验证这些预期时正常返回 0。

## 9. 机器结果与离线报告

result.json 使用独立版本化 schema 1.0。顶层字段为 schema_version、run_id、assessment_id、source_run_id、mode（live/replay）、started_at、finished_at、tool、execution_environment、contract、target、plan、profiles、cases、evidence、report_context、limitations。source_run_id 仅重评分时引用原运行，其余为 null；assessment_id 标识本次评分，run_id 标识本次执行。tool 保存包版本、Git commit、dirty、Python/依赖版本；无 Git 时 commit=null，不伪造可复现提交。

plan 保存 profile/case/assertion 版本、已解析预算、尝试/重试策略、实际请求数及规范配置/测试指纹。contract 保存 API 版本、beta 集合、规则包 ID/revision/哈希、规范资料截至日期、规则实现版本和已覆盖/未覆盖特性。target 保存脱敏配置与 delivery_id。case 保存 required、前置条件、attempts 和按维度结果；attempt 保存 UUID、序号、status、termination、耗时、observations 和 assertions。断言结果自身也使用五态，不使用缺省 true。

结构校验使用 JSON Schema 检测未知状态、必需字段缺失、错误类型与负计数；独立语义校验核对 plan/case/assertion 关系、ID 唯一性、必需记录齐全、计数与状态聚合、证据路径/哈希/指针。跨文件关系不能只靠 JSON Schema 保证。写文件前与读取报告时均校验；不支持的 schema revision 明确拒绝，迁移须显式生成新产物。report 不重写原始结果。

HTML 自包含，无 CDN、外部脚本或联网资源，所有目标/模型/响应字符串转义。按以下顺序呈现：限定结论与运行模式；API/beta/规则包与覆盖范围；请求/独立 case/断言数量；各 profile 与协议/任务维度；失败和证据定位；逐次记录；跳过/阻塞/未覆盖；版本与预算。合成回放醒目标“离线合成数据”，不得看起来像真实服务测试。

响应中含 script、HTML、恶意路径也只显示为文本，证据链接由内部验证后的引用生成。报告不把大量重复断言通过当成大量独立成功请求；不输出不带样本量的稳定率。

report.md 与 HTML 从同一 RunResult 生成，不维护第二套判定逻辑；JSON 是结构化事实来源。report_context 保存版本化的方法简介、必要术语、来源引用和结果解读边界，全部来自随包维护的模板与规则资料，不在报告生成时联网或调用模型。详细内容、风格与阅读契约见第 18 节。

## 10. 检测器验收矩阵

每个错误 fixture 都需合法对照和明确预期 assertion ID；测试不仅检查总状态，还检查指定缺陷被命中、证据可定位。使用合成模型/ID/密钥，禁止依赖本机 daemon。

| 类别 | 必需样本与反误报 |
| --- | --- |
| 文本流 | 合法最小流、多内容块、零 delta 块、多 message_delta、ping 与注释 |
| 生命周期 | 重复/缺 message_start、重复 stop、stop 后内容、未开块 delta、关闭后 delta、重复/负/布尔/跳号 index、未关闭块 |
| framing | 单字节读取、每个字节切分位置、UTF-8 字符拆分、BOM、CRLF 跨读取、单 CR、多行 data、未知字段、末尾半事件 |
| 事件数据 | event/type 不匹配、非法 JSON、非对象 data、未知顶层事件、未知内容/增量、合法及非法 UTF-8 |
| 工具 | 正确工具、schema 允许的空对象、缺必填参数的空对象、错误名、重复 ID、字符串 input、合法 JSON 分片及错拼/截断 |
| 传输终止 | 正常 EOF 截断、HTTP 错误、HTTP 200 error、读超时/reset、持续 ping 超总时限、响应/事件大小上限 |
| 配置 | none 不发 key、缺 key、本机 URL 不被拒、别名允许/不允许、能力 false、未知键、重复键、无预算不发请求 |
| 版本基线 | 精确发出版本/beta 头、未知 API 或包 revision 请求前拒绝、API 与包不匹配、规则包哈希损坏、未实现 beta 拒绝、升级工具后旧包 golden 结果不漂移 |
| 结果与报告 | 五态聚合、必需 case 缺失、JSON schema、证据 hash/path、HTML 注入、重复请求不被隐藏、输出目录不覆盖 |
| 脱敏 | 认证头、JSON 转义密钥、跨读取的密钥、异常文字、报告内容，已转换证据不得声称原始字节 |

合法流在所有单切分位置及固定种子的多切分计划下必须得到相同语义与状态；只允许读取时间/边界元数据变化。这验证应用读取碎片处理，不声称覆盖真实 TCP 分块行为。

B 另加错误 tool_result ID、随机结果未消费、工具错误恢复的假成功。C 另加 CLI 缺失/版本不符、工具缺失/权限拒绝、子 agent 无返回、最终声称成功但产物错误、末尾换行错误。后期 fixtures 不能替代阶段 A 已交付要求。

## 11. 后续阶段必须继承的契约

B 的多轮 case 在收到有效工具请求后才生成随机 nonce，nonce 只进入 tool_result，不进入最初提示；保留完整 assistant content 及对应工具 ID。预先验证输入工具结果关联；若测试器自己生成了不合法续接请求，记录工具内部错误，不归类为目标失败。外部断言核对随机值被消费。成功闭环最多 2 请求；错误恢复 case 单独预算。自动选择和并行不得混为强制工具通过。

C 固定用户配置的 expected_version，测试运行时不自动升级/安装 CLI。可选 claude-runner 镜像在构建时安装固定发行版本；原生模式调用用户已有 CLI。运行新建临时工作区及隔离配置，显式目标、模型、外部 MCP 禁用和最小工具许可；不使用跳过权限检查参数。保存版本、init 工具集、参数与 stream-json（标为客户端事件）。缺工具/权限拒绝为 BLOCKED；有调用而无结果的超时为 INDETERMINATE，正常结束却缺必需子 agent 返回或产物为 FAIL。外部再校验文件精确字节、固定测试哈希和测试结果。所有命令执行只针对新建 fixture 工作区，具体容器边界见第 15 节。

D 记录 repeat_index 与 retry_index：重复试验和失败后重试分别标识，均保留独立 attempt 和首次结果。case 状态按所有已执行必需 attempt 聚合；重试后成功也保留 case=FAIL，并另示 first_attempt_status、final_attempt_status 与 recovered。可靠性统计以计划重复试验的首次 attempt 为分母，重试恢复率另列，不混用相关样本。默认并发 1，预算包括所有重试。

比较键排除时间、UUID、凭据和 delivery_id；比较时显式检查协议、API/beta/规则包、case/assertion/profile 版本、能力/模型/别名、CLI 版本、请求参数、预算和重试策略。endpoint 或交付编号变化列明；其他契约差异默认不可直接比较，不合成统一总分。跨协议版本并列测试属于第 14 节的兼容矩阵，不能被当作同一基线的回归比较。可靠性模式只报告观测分子/分母与抽样策略。

## 12. 实施进入条件与独立验收

阶段 A 实施计划以本规格为需求依据，按可独立验证的任务拆分，采用失败测试先行。阶段 B/C/D 已定义的接口与验收边界应保留，但 A 不提前实现后续功能。开发、离线门禁与真实目标验收分别记录，不将某一层通过代替另一层。

实施顺序先建立最小可执行 harness：依赖锁、包骨架、Dev Container、检查入口和首个正反测试；此时未实现的阶段 A 产品要求保留未完成。随后逐项实现配置/规则包、SSE/消息/工具断言、证据/报告和 runtime；每项沿用同一组门禁。harness 能运行不等同产品验收通过。

阶段 A 独立验收包包括：固定本地提交、依赖锁、AGENTS.md 与统一检查入口、机器可读质量门禁结果、GitHub 检查/构建定义、贡献指南及模板、Dev Container 定义、Docker 构建/运行命令与镜像 ID、容器内离线测试结果、合法/错误 fixture 回放命令与预期退出码、通用 target 示例、首个固定协议包及来源清单、一次合成 JSON/HTML/Markdown 及 limitations。独立验收方在新输出目录自行跑真实目标，不将先前失败历史当成本轮结果。实测发现检测器问题回开发方修正。

阶段 A 完成条件：所有离线矩阵通过；合法对照不误报；关键错误命中指定断言；结果通过 schema；报告可离线阅读且无密钥；4 个 live case 可供独立运行；精确选用协议包并验证 API 头与版本来源；未实现 profiles/协议版本明确不可选择。未经独立实测，只能声明“检测器离线验收通过”，不能声明目标通过。

容器也是 A 的验收要求：干净环境可构建 Dev Container 与 runtime，容器内完成离线测试，runtime 无宿主机 Python 依赖地生成可保存的报告，退出码/中断能正确传递。Docker 环境受阻时可继续做不依赖它的开发与离线验证，但阶段 A 必须注明容器验收未完成，不能仅凭配置文件存在宣称交付通过。

## 13. 设计来源

- 只读概要：`/Users/jiangyuan/Documents/learn/ai/apitest/wecode-claude/design-handoff/overview.md`。
- 只读选型报告：`/Users/jiangyuan/Documents/learn/ai/apitest/wecode-claude/candidate-evaluation.html`。
- 2026-10-14 核对的主来源：[Anthropic Streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)、[Messages](https://platform.claude.com/docs/en/api/messages/create)、[Stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)、[WHATWG SSE](https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream)。它们为协议依据；预算、状态归类、模块接口和产品范围是本项目的设计决策。

本地历史资料仅为来源追溯，其他开发者不需要这些绝对路径或聊天记录才能实施本规格。产品、CI 和 harness 均不得依赖它们。

## 14. 协议演进、指定版本评估与工作流锁定

### 14.1 必须区分的版本

| 维度 | 含义与固定方式 |
| --- | --- |
| api_version | 实际发出的 anthropic-version，使用官方公布且工具有对应实现的 API 日期 |
| beta_headers | 实际启用的精确 beta 名称集合，空集合也是需要记录的选择 |
| protocol_contract | 本工具测试契约的 ID、不可变 revision、内容哈希与截至日期；不是官方 API 版本 |
| tool / case / assertion / result schema | 测试器实现、用例、断言与产物格式各自的版本，不能合并成一个日期 |
| client / model / delivery | Agent 或 SDK 精确版本、模型及可得的模型交付标识、端点服务交付编号、能力与运行配置 |

固定 API 日期并不冻结所有可观察行为。官方允许同版本增加可选输入、输出及事件变体；beta 又有自己的演进和废弃过程。[API versioning](https://platform.claude.com/docs/en/api/versioning)、[Beta headers](https://platform.claude.com/docs/en/api/beta-headers)

因此本工具承诺可复现“某规则快照对某交付、某特性子集的实测结果”。不承诺通过一组有限用例就证明完整 API 兼容，也不保证固定日期能够约束上游模型权重、路由或未来输出。服务与模型无法固定的部分在锁定建议中逐项列出。

### 14.2 不可变协议规则包

每个受支持契约在包资源 resources/contracts/<id>/<revision>/manifest.json 中定义：manifest_schema_version、id、revision、protocol、api_version、beta_headers、spec_as_of、sources、rules、profiles、coverage、engine_compatibility、content_sha256。

sources 为规范 URL、检索日期、规范正文规范化哈希、相关章节锚点与必要的简短依据，不以活动网页正文替代固定规则。source 摘要用于追溯，不批量再分发完整官方文档。哈希须在实施时取实际资料计算，不能填占位值。正文变化若只是排版，规范化比较尽量消除噪声；提取失败必须报维护检查失败，不能视为“无变化”。

rules 记录 assertion ID/version、规则实现 key、参数、来源章节、适用 API/beta 条件及正/反 fixture；profiles 列出完整必需 case 及版本、请求模板/哈希、能力策略与必需项；coverage 列出已覆盖与不覆盖特性。manifest 仅是数据，由随工具审阅发布的实现 key 白名单解释，不能从下载资料加载代码或直接生成可信断言。

content_sha256 是规范化清单（不含自身哈希）及所引用运行资源清单的内容摘要；包内资源必须逐一验哈希。fixture ID/预期哈希随清单保存，构建时对照 tests/fixtures 校验，运行镜像不依赖仓库测试目录或开发依赖。另记录 validator 实现版本和工具提交，不能仅因数据清单相同便声称判定器行为相同。任何规则含义、请求或必需集合变化都发布新 revision；修 bug 同样不能静默改变旧结果。旧包保留，与新包并行；不以 URL 内容变化覆盖旧文件。

工具升级必须运行全部保留包的 golden 回归。若发现旧包有缺陷，标记已知问题及替代 revision，允许用户明确复现旧实现或使用原固定工具版本；不重写历史报告。若新工具无法运行某旧包，contracts show 明确说明所需工具版本，不能宣称此包已在新引擎上原样复现。

旧证据可以用新规则重新评分，但必须创建新 assessment_id、新输出目录，引用 source_run_id、原证据哈希、原规则/引擎及本次规则/引擎，并列出发生变化的断言。原结果始终保留；重新评分不是新的 live attempt，不能增加实际请求数或可靠性样本量。脱敏或截断证据不足以执行新断言时按证据不足处理，不从报告摘要补造原响应。

用户通过 contracts list/show 查本地包的 API 日期、beta、截至日期和覆盖范围；run/replay 仅按精确 ID/revision 解析，不支持静默 latest。未来版本、未收录版本及尚未实现的旧协议显示“测试器尚不支持”，与“被测端点不兼容”分开。

A 首次仅收录官方 2023-06-01 的 Messages 核心规则快照；不为凑多版本数量把日期自增为虚构 API，不将历史 Completions 格式套进 Messages。多个快照可能使用同一个官方 API 日期，这是正常的规则演进。

### 14.3 指定版本测试与兼容矩阵

单次运行从 target 配置取得 API 日期、beta、规则包；传输层验证实际生成的请求头与所选契约一致，报告同时记录 requested_contract 与发送证据。所有重试、多轮请求必须沿用相同版本和 beta；禁止遇错后自动去 beta、换版本、换协议再把成功计入原契约。

B 增加 matrix --target <path> --matrix <path> --allow-live。矩阵文件列出具名行：api_version、beta_headers、protocol_contract、profiles、repeat（D 前固定为 1）；端点、模型、交付编号和能力策略来自同一目标。每行独立新运行及证据目录，额外生成 matrix.json/html；事前展示行数、case 数和请求上限总和，由全局预算约束，禁止扫描所有日期猜版本。

同一 API 日期的不同 beta 集合或不同规则快照也可以并列，但报告明确标为“特性/规则快照差异”，不伪称多种官方 API 版本。只有有依据且已实现的版本可作行。旧版本 deprecated 或停止可用时显示官方状态与验证日期，不自动从历史矩阵删除。

矩阵每行展示：请求版本、规则快照、已覆盖特性、protocol/behavior/client 分项状态、失败断言、独立样本数、版本选择语义的证据级别。没有 FAIL 不代表所有能力已测。不可从“较新版本通过”推断“所有旧版本通过”，也不自动选日期最大的版本。不同 API/beta/profile 行不汇总一个通过率；可展示共同 case 的状态差异，以及新增、移除和未覆盖项。

“服务接受这个 header”与“服务按该版本处理请求”分开。黑盒不能直接证明 daemon 没有忽略版本头。版本识别控制 case 只有在包中有官方依据的可区分行为时才声明验证；非法版本控制需显式选择、独立预算，接受非法值仅形成版本选择未验证的诊断，不直接证明所有正常版本都错误。没有区分证据时标 version_semantics=unverified，不得写成已确认版本协商。

### 14.4 周期更新协议及用例

项目维护配置默认每月检查一次官方 version history、release notes、Messages/streaming 参考和已实现 beta 的说明，频率可配置，也支持人工按需触发。调度仅生成资料更新候选，不自动迁移用户配置、运行真实端点测试或发布规则包。

D 提供 contracts check-updates --allow-network --out <new-directory>，抓取固定白名单官方来源，记录来源哈希/日期、归一化正文差异和受影响规则清单，产出 update-candidate.json/md。此命令不需要目标凭据、不请求被测端点、不修改已发布规则包、不更改运行配置。无变化时不产生新包；发现文档变化是审查信号，不自动等价为协议语义变化。

仓库定时维护 workflow 调用该命令并保存候选 artifact；与默认离线测试 job 分开，不对外发消息、不自动合并或发布。维护者用仓库内 update-anthropic-protocol Agent 命令读取候选并推进规则/用例修订；该命令的完整契约见第 17 节。工具尚未开源时可由本地任务调度器调用同一底层检查命令。公开运行环境不可访问文档时明确失败并保存诊断，不能捏造最新状态。

候选到可用规则包的流程：维护者核对官方差异 -> 确定 API/beta/能力影响 -> 编写或更新规则与 case -> 为每条变化加入合法对照及单缺陷反例 -> 运行新包及保留旧包的离线回归 -> 在有授权的验收环境进行选定真实测试 -> 审阅后以新 revision 随工具发布。自动化可以辅助发现和准备差异，规则含义变更必须经代码审阅，不能直接从网页或 LLM 输出执行生成用例。

维护审阅将变化明确分类为新增可选能力、既有规则澄清、协议行为变化、纯文字修改或测试器缺陷。beta 转正、废弃或移除时，发布标明适用条件和迁移关系的新 revision；某 beta 不可用不能覆盖稳定基础能力的独立结果。历史规则包的存在不代表服务当前仍支持该版本。

若仅收录新资料但相关能力尚未实现，候选保留 uncovered 标记，不能发布一个省略新必需规则却号称完整最新版兼容的包。被固定的用户不自动迁移；升级建议附规则差异、预期行为变化和复测命令。常规测试保持离线解析本地规则包，不每次启动都联网检查新版本。

### 14.5 帮助使用者锁定稳定工作流

C/D 的报告生成一个只含非秘密信息的 workflow-lock.json 建议产物：精确 client 名称/版本、API 日期、beta 集合、规则包 ID/revision/哈希、模型与响应映射、服务 delivery_id、目标配置指纹、所需能力、被测 profile、样本量、通过 run ID 和未固定因素。用户仍以环境变量注入凭据。

建议分层表示，不能用同一个 PASS 混淆：

1. configured：用户已声明所需组合；还没有真实客户端请求证据。
2. observed：有该客户端实际请求元数据，能观察版本、beta 与模型；与声明的差异逐项显示。
3. workflow_verified：相同观察到的组合完成选定真实工作流，按任务结果和样本量限定。

客户端版本固定、API header 固定和服务按版本执行是三个独立维度；version_semantics 继续单列。仅协议用例通过时可以提供协议配置建议，但不能输出 workflow_verified。两次样本均通过不能称“长期稳定”，可靠性模式按重复实测结果提供依据。

适配器提供版本化 PinningRecipe，记录客户端有哪些有官方依据且已验证的设置方法、适用客户端版本与已知限制。不能假设任意 Agent 都暴露 API 版本开关，也不能因设置了某个自定义 header 就假定其覆盖客户端默认头。生成的配置示例必须对应选定 Agent；无可靠设置途径时标 pinning=unsupported，建议锁定已验证客户端版本/交付或请求上游提供版本化服务入口，而不是宣称强行固定成功。

真实客户端版本观测证据可由受信的网关请求元数据或后续本地观察适配器提供；未具备该入口的 C 运行仍可交付任务验收，但锁定建议最多为 configured。未来的 HTTP 捕获/代理必须单独验收其透传行为，不能悄悄改写版本头、去掉 beta 或替换正文来“修复”兼容性。

客户端观测按每次请求保存 request_id、parent/子 agent 关联（可获得时）、模型、API 日期、精确 beta 集合、相关请求特性与 capture_point（client_egress / observer_ingress / observer_egress / gateway_ingress）。不可只保存整轮 beta 并集；不可由客户端发出位置的观察推断不可见上游实际收到什么。某些请求缺少观测时，锁定证据只覆盖已观察子集；声明与观测不一致单列为 pin_mismatch。

推荐选择顺序为：满足用户所需功能 -> 协议与真实客户端工作流均通过 -> 版本约束具备证据且可实际应用 -> 重复样本表现及维护状态。无符合条件的行时明确报告无法推荐，而不是自动降级到缺失所需工具/子 agent 能力的版本。客户端、模型、服务交付或 beta 集合变化均要求复测，不将旧锁文件当作永久保证。

### 14.6 分阶段版本能力验收

- A：离线解析首个规则包、检测哈希篡改、按配置发精确版本头、拒绝不支持/不匹配契约且不联网、报告协议范围和快照截至日期。
- B：同一端点多行测试各自证据与预算不混用；模拟两个规则快照证明按指定包选规则；不把合成版本标为官方版本；任何降级请求均不得混入原行成功。
- C：客户端无法固定或无法观测时如实显示；观测不符不能生成已验证锁定；实际任务通过也不能掩盖 beta/版本漂移。
- D：合成文档变更能生成候选；无变更不改包；抓取/解析失败可见；新增 revision 不修改旧包及历史结果；旧包 golden 回归失败阻止发布；固定配置不因更新检查而迁移；旧证据重新评分有独立 assessment_id 且不增加实测样本。

## 15. Dev Container 开发与 Docker 交付

### 15.1 环境方案与维护边界

Dev Container 是标准开发入口，必须由 CI 验证；Docker CLI 镜像是推荐的用户运行入口。两者共享 Python 基础和同一 uv.lock，通过同一个根目录 Dockerfile 的不同 target 构建。Dev Container 元数据遵循开放规范，不绑定特定编辑器；文档同时提供支持该规范的编辑器入口和 devcontainer CLI 的 build/up/exec 用法。[Dev Container specification](https://containers.dev/implementors/json_reference/)

推荐 Debian slim 的 Python 基础，开发与运行选择同一个 Python patch 版本，避免 Alpine/musl 与常用原生依赖产生额外兼容分支。Dockerfile 固定基础镜像的多架构摘要和 uv 版本/摘要，依赖安装严格使用锁文件，不在创建环境时解析最新版。OS 包的实际版本保存在构建清单；后续升级通过依赖维护变更与回归，不自动改变已发布镜像。

容器一致性是版本与验收契约，不承诺不同机器重建的 image ID 必定逐字节相同。用户需要复用已验收构建时固定镜像 digest；构建脚本中的镜像摘要由实施时实际解析取得，不在设计中虚构。后续更新 OS 安全补丁、Python 或开发工具时重建、复测并发布新的工具/镜像版本，协议规则包不因此自动升级。

不强制 Docker Desktop 这一产品，也不依赖 macOS 系统调用。最低验收环境为 Linux 容器、Docker Engine/BuildKit；macOS/Windows 可通过具备 Linux 容器能力的本地运行时使用。其他 OCI 引擎可作为补充支持，只有实际验证后才声称兼容。

### 15.2 开发目录与构建目标

```text
.devcontainer/devcontainer.json  -> Dockerfile target dev
Dockerfile                      -> base / build / dev / runtime
.dockerignore                   -> 排除真实配置、日志、凭据、本机环境
uv.lock                         -> 共用依赖锁
docs/container-usage.md          -> 容器开发、运行、联网与输出说明
```

base 提供固定 Python 与基础运行环境；build 从锁文件构建 wheel 及运行依赖；dev 额外提供固定 uv、Git、pytest 和开发检查工具，以普通用户操作挂载的源代码；runtime 只包含运行必需内容与 wheel 中的规则包。采用多阶段构建，避免将编译、编辑和测试工具一并放入用户镜像。[Docker multi-stage builds](https://docs.docker.com/build/building/multi-stage/)

devcontainer.json 设置明确的 workspace、remoteUser、开发构建 target 和容器内安装命令。依赖创建过程不得读取宿主机 Homebrew、Python site-packages 或本机 .venv。Linux 虚拟环境与缓存放容器专用卷或容器目录，避免把 macOS/Windows 的二进制依赖带入 Linux；Linux bind mount 的 UID/GID 与目录可写性显式处理，不靠长期 root 运行解决。

Dev Container 默认不挂载 Docker socket，不启用 privileged，不创建嵌套 Docker daemon。离线测试在 dev 容器中运行；构建最终镜像由宿主构建器或 CI 的独立 image job 完成。这样不要求每位开发者在开发容器内再操作宿主 Docker。

### 15.3 用户运行与文件契约

交付内容是按需启动、结束即退出的 CLI 容器，无常驻 HTTP 服务、无默认端口发布。runtime 默认普通用户，ENTRYPOINT 直接启动本项目 CLI，默认命令显示帮助；参数和退出码与 wheel 安装版一致。用户运行时不安装依赖、不下载测试规则，纯回放/报告命令可用 network=none 验证。

运行约定：/config 只读挂载目标配置；/output 可写挂载报告父目录；/tmp 为有界临时空间。每次 run 在 /output 下创建新的目录，容器删除后报告和证据仍保留；拒绝覆盖前轮目录的语义不变。runtime 支持只读根文件系统，临时数据只写显式可写位置；阶段 C 的 CLI HOME/工作区另行挂载。

文档提供 docker build、docker run --rm 和可选 Compose 一次性服务的完整示例。Compose 只是参数便利层，不是必须依赖，不添加数据库或后台调度服务。本地构建使用本地标签；公开交付使用维护者确认的 Docker Hub 命名空间、版本标签与 digest，发布配置流程见第 17 节。

凭据仅运行时通过环境传入，不写 Dockerfile、build ARG、镜像层、通用 Compose 文件或 Git。用户自有 env 文件必须被 Git/build context 排除；shell 示例不把真实值直接展开到命令行。挂载只限配置、输出与生成的测试工作区，不默认挂载整个 HOME、原评估目录或用户 Claude 登录配置。

输出权限以当前容器身份可写为前提。Linux 示例支持指定 UID/GID 或预先配置卷所有者；目录不可写时明确失败，不自动放宽为全员可写。macOS/Windows bind mount 的权限表现单独验证，不从 Linux 结果推断。SIGTERM/SIGINT 要触发有界清理、保留已有证据和正确退出码；C 的子进程必须一并回收。

### 15.4 访问被测端点

容器内的 127.0.0.1 指容器自身；不能把宿主机 localhost 配置原样当成容器可达地址。工具不暗中改写目标 URL，每种路径使用明确配置，报告记录实际连接地址与 execution_environment。目标服务只绑定宿主回环地址时，需要逐平台验证能否从所选容器网络到达。

| 端点位置 | 配置方式与边界 |
| --- | --- |
| 远程或内网可达 API | 使用容器能解析和连接的原 URL；记录 DNS、VPN、CA 等环境阻塞 |
| 同一容器网络中的服务 | 以服务 DNS 名和容器端口配置，不要求暴露公网端口 |
| Docker Desktop 宿主服务 | 文档优先给 host.docker.internal 示例，实际可达性另验；不保证任何本地运行时都实现相同别名 |
| 原生 Linux 宿主服务 | 可显式加 host-gateway 主机映射，但这不使只监听 127.0.0.1 的服务自动变成 bridge 可达；此类情况提供显式 host network 方案 |

Docker Desktop 的宿主别名和 host network 存在平台/配置条件，按官方文档给出说明，不默认启用 host network，也不为连通测试修改用户 daemon 的监听地址、防火墙或鉴权。[Docker host access](https://docs.docker.com/desktop/features/networking/networking-how-tos/)、[Host network driver](https://docs.docker.com/engine/network/drivers/host/)

文档先用合成测试服务器验证对应网络配置，再由原会话显式执行真实 API case。连接失败按环境 BLOCKED，不当作协议 FAIL。为 host access 选择不同目标地址的配置会改变配置指纹；矩阵/回归需将连接路径差异展示出来，不能默默视为同一路径。

### 15.5 Claude Code 工作流的容器边界

基础 runtime 镜像不捆绑 Claude Code；API 协议测试用户无需安装它。C 阶段增加单独的可选 claude-runner 构建目标，在 Linux 镜像内安装并固定一个经验证的官方 CLI 发行版本及其依赖，构建后核对 --version。具体发行渠道和校验方式按该固定版本的官方安装资料确定，记录版本、平台及来源摘要；禁止 latest 或运行时静默升级。

不能把宿主机 macOS 的 claude 二进制挂进 Linux 容器后宣称能直接运行。容器版验收的是 Linux CLI 的工作流；若要判断用户 macOS 本地 CLI，仍需原生适配器单独执行，并在报告中明确客户端平台。原生路径是补充验收入口，不是开发环境的前置条件。

容器 CLI 的 HOME、工作区、配置与凭据独立；不继承用户登录目录和外部插件。CLI 版本或平台缺少可用工具、要求交互登录而无法完成、安装发行不可得等记 BLOCKED；不能以容器化为理由跳过权限检查或降低文件/子 agent 断言。容器只限定进程与文件环境，不保证上游模型或服务行为稳定。

### 15.6 构建溯源、架构与验收

Docker 构建保存工具版本、Git commit/dirty（可得时）、基础镜像 digest、锁文件哈希、Python/OS/依赖版本；使用 OCI 标签保存版本与源码修订。结果中的 execution_environment 记录 native/container、OS、CPU 架构、客户端平台及可得的镜像标识。容器进程若不能自行得知实际 image digest，标明其来自构建元数据或外部启动记录，不伪称独立观测；无需挂 Docker socket 获取这些信息。

首个容器交付目标为 linux/amd64 与 linux/arm64，A 完整验收需分别验证构建与运行；使用模拟运行时明确记录。若暂时只能验证一个架构，可交付明确标注的平台阶段性产物，但不能宣称 A 的容器验收全部完成。相同规则、fixture 和运行参数在两种架构下应产生一致的语义结果，时间、UUID、路径和环境元数据可不同。

阶段 A 的环境验收至少包括：

- 从干净源码按锁文件构建 dev 和 runtime；Dev Container CLI 能启动并执行离线测试，编辑器内环境不是唯一验证方式。
- 容器内运行全部离线检测器测试；runtime 以普通用户、只读根文件系统、禁网运行合法及错误回放，退出码与报告符合预期。
- 挂载输出目录后删除容器，JSON/HTML/证据仍可读取；只读配置未被修改；目录冲突、权限错误可诊断。
- 合成服务器覆盖同网络访问及可用平台上的宿主服务访问；失败归类环境阻塞，不依赖真实 daemon。
- 检查镜像和构建 context 不含真实 target、原始服务日志、密钥、.env、本机 .venv、缓存及历史评估材料。
- 记录每个实际验证的 CPU 架构、镜像 ID/摘要及命令；没有 Docker/daemon 权限时保留未验证状态，不能用 Dockerfile 静态检查替代构建运行。

CI 的 dev 测试、runtime 构建/离线冒烟和跨架构任务共用同一个锁文件；依赖下载只发生在构建/准备阶段，测试阶段禁止外部网络，不带真实目标凭据。纯回放可完全禁网；合成 HTTP 集成使用只能访问测试服务器的隔离网络。周期协议维护仍按第 14 节单独联网，不能混入离线 CI。

## 16. AI 编程 SDLC harness 与现代 Python 规范

### 16.1 官方实践的采用与取舍

2026-10-14 查阅以下官方资料；它们是实践依据，具体工具选型与门禁范围是本项目的决定，不是厂商指定的统一标准。

| 来源 | 本项目采用的做法 |
| --- | --- |
| [OpenAI：Iterating development workflows with Codex](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex) | 仓库指引、阶段计划、重要上下文与真实验证证据各有归属，可由新会话接手 |
| [OpenAI：Rethinking skills and prompts for GPT-6 Astra（2026-09-11）](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | 指引简短且按需读取；明确自主执行边界；不积累互相冲突、过度约束的提示词 |
| [Anthropic：Harness design for long-running application development（2026-03-24）](https://www.anthropic.com/engineering/harness-design-long-running-apps) | 将工作拆成可验收单元、分离实现与评价；保留能改善效果的 harness 部件，持续简化 |
| [Anthropic：Effective harnesses for long-running agents（2025-11-26）](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | 有固定验收清单、环境启动方式与跨会话交接；增量交付，不能看见部分功能就宣布全部完成 |

“harness”在这里指开发脚手架、上下文入口、确定性验证和证据反馈闭环，不是再造一个 Agent 平台。保留现有 Codex/Claude Code 的执行循环；不新增默认付费模型调用、LLM Judge、常驻多 Agent 服务或模型专属 SDK 依赖。独立审阅可以由人或获授权的另一 Agent 执行，硬门禁不依赖其自然语言肯定。

### 16.2 仓库结构与单一事实来源

```text
AGENTS.md                         # shared repository guidance and command map
CLAUDE.md                         # thin pointer to shared guidance, if needed
pyproject.toml                    # metadata, build, dependency groups, tool config
uv.lock
.python-version                   # standard development Python patch
.pre-commit-config.yaml
src/anthropic_readiness/
  __init__.py
  __main__.py
  py.typed
  cli.py / runner.py / cases.py
  models.py / sse.py
  config.py / contracts.py / transport.py / evidence.py / reporting.py
  validation/
  resources/
    schemas/
    contracts/
tests/
  unit/ integration/ acceptance/ harness/ fixtures/
scripts/check.py
docs/
  architecture.md
  development.md
  container-usage.md
  harness/acceptance.json
  harness/progress.md
  decisions/
  superpowers/specs/
  superpowers/plans/
.github/workflows/
```

AGENTS.md 是短导航：项目目标、目录职责、启动/检查命令、语言约定、完成标准和实测边界；按任务指向架构、开发或协议维护文档，不要求每次微小改动阅读全部历史。若使用 CLAUDE.md，仅引用同一规则来源，不维护第二套相互漂移的规范。项目指引遵循用户已有授权，不让每次修改、运行离线测试、修复失败都重新请求许可。

详细设计拥有需求/边界；阶段计划拥有实施步骤；acceptance.json 只索引稳定 requirement ID、阶段、必要检查 ID 与证据要求；progress.md 保存当前进度、重要决定、已运行检查、阻塞和下一步。原始检查日志留在被忽略的 artifacts/checks 下，文档引用其标识/摘要，不复制所有输出和聊天记录。测试报告是“实际是否通过”的依据，不能由手工改一个 passes=true 替代。

新会话按当前任务读取 AGENTS.md、相关计划/进度及相关代码，检查 Git 状态和已有验证证据后续作。重要架构取舍写精简 ADR 并链接，不将本机路径、短期失败或重复叙述全部堆入全局指引。文档与测试标准发生实质变化时随代码一起审阅。

### 16.3 Python 工程约定

使用 PyPA 的 src 布局与 pyproject.toml，build backend 选固定版本 Hatchling；定义包元数据、requires-python、CLI entry point、运行依赖和 dev 依赖组，避免 setup.py、自改 sys.path 或 PYTHONPATH=src 作为安装替代。[PyPA src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)、[pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)

声明 Python >=3.11，同时 CI 至少覆盖声明下界 3.11 与标准开发版本 3.12；仅测过 3.12 时不能据此宣称全部 Python 版本已验收。源码与测试采用该下界支持的语法，Ruff/mypy 的目标版本一致。包的 schema/契约使用 importlib.resources 读取，不依赖仓库 cwd；wheel 安装后的资源清单必须与源码清单一致。

Ruff 同时负责格式与 lint，mypy strict 作为唯一主静态类型检查器，pytest 作为主测试框架，不叠加 Black/Flake8/Pyright 做同类检查。[Ruff configuration](https://docs.astral.sh/ruff/configuration/)、[mypy strict](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict)

公共接口、领域模型、适配器和测试辅助函数显式标注类型；使用 dataclass、Enum/Literal、TypedDict 和 Protocol 表达边界。外部 JSON/YAML 先按 object/JSON 值接收，经运行时校验后窄化为领域类型，不能用 cast 或 Any 伪装已校验。第三方缺少类型信息时使用固定 stubs 或小范围适配层；禁止全局 ignore_missing_imports、无解释 type: ignore、整包关闭严格检查。例外必须局部、带错误码和理由，作为评审项。

Ruff 初始规则集覆盖基础错误、导入排序、现代语法、常见 bug、无效简化和 pytest 习惯；具体启用列表固定在 pyproject。检查模式不改文件；自动格式化/修复是显式开发动作。异常使用领域错误与稳定原因码，CLI 层统一呈现；不在模块导入时联网、安装依赖、创建输出或读取凭据。

pytest 启用 strict-config、strict-markers 与 importlib 导入模式，单元/离线集成/显式 live 测试分标记；默认集合不带目标凭据，禁用外部网络。离线集成可在专用测试网络访问合成服务器，不允许访问真实端点。必要资源警告、未等待协程和不受控 warning 作为失败，第三方已知 warning 只作精确过滤。[pytest integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)

### 16.4 强制质量门禁

标准入口为 `uv run --frozen python scripts/check.py --suite fast` 与 `--suite full`；Dev Container 和 CI 调用同一脚本，Make/编辑器任务只作快捷入口。准备环境时 `uv sync --locked`，检查时验证 lock 与 manifest 一致并使用已准备依赖，不能悄悄更新锁。[uv locking](https://docs.astral.sh/uv/concepts/projects/sync/)

准备与验证分开：先安装锁定的运行、开发和构建依赖并准备离线 wheelhouse；检查进程设置 UV_OFFLINE=1，构建使用已锁定的 build backend 和无联网构建隔离方案。fast/full 不得自行联网同步缺失包；依赖尚未准备好时报告环境阻塞。门禁脚本不触发自身递归；其反例测试使用临时合成子项目和可控命令。

| 门禁 | 必须验证的内容 | 适用入口 |
| --- | --- | --- |
| lock | pyproject/uv.lock 一致、固定工具版本、无检查时更新 | fast/full |
| format/lint | Ruff format --check 与 Ruff check，零违规 | fast/full |
| type | mypy strict 覆盖 src、tests 与 scripts；不隐藏缺失类型 | fast/full |
| architecture | Import Linter 检查禁止反向依赖、循环和验证层依赖基础设施 | fast/full |
| schema/contract | Draft 2020-12 schema 自身有效；配置/结果/规则包/harness 清单正反样本；资源与哈希完整性 | fast/full |
| unit/regression | 纯验证器合法/单缺陷 fixtures、切分不变性、五态聚合及关键回归 | fast/full |
| integration/acceptance | 合成 HTTP/SSE、CLI 退出码、脱敏/证据/离线 HTML 等产物验收 | full |
| packaging | 构建 wheel/sdist，干净环境非 editable 安装，在仓库外运行并读取所有规则/schema | full |
| documentation | AGENTS/开发文档所列固定入口存在；仓库内链接、验收 ID 与检查映射无悬空引用 | full |
| container | devcontainer 启动、runtime 构建/运行、普通用户输出及离线冒烟、已声明架构 | 独立 image job；阶段 A 完成交付必需 |

架构门禁使用 Import Linter 的层级/禁止依赖契约。底层 models/sse 不依赖执行器或适配器；validation 依赖领域契约类型，不反向导入 CLI、runner、transport、文件式配置/规则加载器、evidence 或 reporting；I/O 留在适配器。规则所需纯数据类型与加载器分开，以免为获取类型而引入 I/O 层。[Import Linter](https://import-linter.readthedocs.io/en/stable/)

数据 schema 验证、Python 静态类型、架构依赖三类检查都执行，不能相互替代；机器产物还需第 9 节定义的语义及证据校验。schema 与手写类型之间的映射使用序列化往返/负样本契约测试维持一致，不另外维护未经验证的第二份 schema。对外 schema 变化先更新版本策略和迁移/兼容说明。

每条必需行为都关联可执行验收项；未实现、没有测到或采集失败不能标通过。生成 coverage 报告识别未测分支，但不为了百分比写重复实现的测试，也不以高覆盖率替代指定故障 fixture 的命中证明。架构/类型/schema/check runner 也有反例验收：在临时合成项目注入违规时，必须命中对应门禁且返回失败，不修改真实源码来做自测。

检查器逐项记录 command、check_id、开始/结束、退出码、状态、日志位置、工具版本与输入指纹，输出有独立 schema_version 的 check-result.json 和简短控制台摘要；全部必需检查实际完成才有整体 PASS。门禁结果至少区分 passed、failed、blocked、not_run，不套用目标兼容性五态掩盖 CI 错误。命令缺失、超时、零测试、所需 job 没有运行或输出格式错误都不可当通过。检查不会擅自追加新的 live 测试或循环调用模型。

fast 通过只表示快速检查通过，不冒充 full 或 container 通过。阶段完成时将 full 结果与 image job 的证据汇总，绑定相同源码/锁/规则指纹；源码随后变化时旧证据不再是当前通过依据。检查结果模型与产品被测端点结果分开，避免将测试器自身 CI 通过误解为目标 API 通过。阶段实施期间允许当前检查基线通过，但尚未实现的阶段必需要求仍为 incomplete；不能删除验收索引条目来宣称阶段完成。

验证记录保存执行当时的 commit/dirty 和源码内容指纹。提交只改变 Git 元数据且受检内容不变时，可按内容指纹关联已有检查证据，但不能追改原报告的构建字段；对外以“干净提交构建”交付的 wheel/镜像必须由该提交重新构建并验证。避免将提交前 dirty 产物冒充固定提交产物。

### 16.5 SDLC 反馈闭环、审阅与 CI

每个实施单元遵循：选定已同意的验收要求 -> 最小失败测试 -> 实现 -> 受影响检查 -> 修复 -> 相应阶段完整门禁 -> 审阅 -> 本地提交及交接。失败输出直接给出可复跑命令和定位；把反复出现的真实失误转成窄范围测试、静态规则或文档纠正，不无限堆提示词。遇到同一检查失败，先诊断根因，不重复原命令碰运气。

pre-commit 提供本地快速检查便利，配置引用相同已锁定工具/脚本，不另建一套浮动版本。CI 必须独立执行完整必需门禁，不能因本地 hook 通过便跳过。PR 检查失败时禁止合并；GitHub 仓库接入时按第 17 节配置必需 checks。workflow 定义本身不等于远端保护已启用，不自动合并。

CI 分为 fast/full、Python 支持矩阵、container、显式协议资料维护任务；真实 API/Claude CLI 实测须单独授权并有预算。离线 job 准备依赖后在隔离网络内运行，固定 workflow action 的提交及工具依赖，保留机器报告供审阅。没有运行的付费/真实服务测试只列未测，不要求开发者为日常离线门禁提供 API key。

阶段审阅检查需求满足、错误 fixture 命中、关键失败路径、门禁是否被削弱以及文档/产物一致性。不得为了绿灯删除必需 case、宽松化 schema、关闭 strict、扩大 ignore 或自动重写 golden 期望；若契约确实要变，按规则包/用例版本变更处理并解释依据。由同一 Agent 自审时明确说明，不声称独立审阅。

完成记录必须区分实现、离线门禁、容器验证、真实目标验收和仍未覆盖项；进度恢复不依赖聊天历史。harness 的命令、文件与规则依据实际失败和成本定期调整；可删除已无效的约束，但保留变更依据和回归证据。开发 harness 不会自动变成被测服务的运行依赖。

### 16.6 阶段 A 的 harness 验收

- 新环境按仓库指引启动后，无本机 Python 依赖地执行同一 fast/full 入口；入口、锁和 CI 配置一致。
- 合成 lint、类型、架构、schema、单缺陷 fixture 及检查命令故障分别让对应门禁失败；缺工具或零用例不能得到全绿。
- 安装 wheel 后离开源码目录仍能列出固定规则包、校验配置、回放并输出 JSON/HTML；包资源缺失会使 packaging 门禁失败。
- 新会话仅凭仓库的目标、计划、进度及检查证据能辨认已完成/未完成要求；无需用户重述历史聊天。
- 关键回归具有稳定验收 ID；修改检查规则、schema、golden 期望或必需 case 集合时，差异可见且有审阅依据。
- 同一源码/依赖锁/规则指纹绑定的 full 和 container 证据齐备后，才能宣称阶段 A 开发验收完成；服务兼容性仍由独立实测结果决定。

## 17. GitHub 协作、构建发布与协议维护命令

### 17.1 GitHub Actions 的职责与产物

维护者个人 GitHub 仓库为协作入口，复用第 16 节同一检查脚本。默认分支名称、仓库名和镜像命名空间由实际配置解析，不在源码中写死本人的账号信息。A 提供检查/构建与协作文件，D 完善公开发布操作手册和协议维护；工作流只在仓库实际接入后产生远端运行记录。

| 工作流 | 触发与职责 | 产物和权限边界 |
| --- | --- | --- |
| ci.yml | pull_request、默认分支 push、workflow_dispatch；fast/full、Python 3.11/3.12、文档/模板和 amd64 runtime 冒烟 | check-result、JUnit/coverage、wheel/sdist、合成示例报告；contents:read，不需要目标或 Docker Hub 凭据 |
| container-matrix.yml | workflow_dispatch、定期维护及发布前；两种架构构建/运行与 Dev Container 验证 | 测过的 OCI 产物、架构/摘要/构建清单；不默认推 registry |
| release.yml | 维护者手动触发，明确受信 ref 与是否发布；默认只构建验证 | 完成两架构验证后才可在发布步骤使用 Docker Hub 凭据，返回镜像 digest 与版本清单 |
| protocol-watch.yml | 每月或手动；运行第 14 节资料检查 | 文档差异候选 artifact；无模型/目标凭据，不执行生成规则或自动提交 PR |

PR 的必需汇总检查 ci-required 显式核对所有配置为必需的子任务，失败、取消、未运行均不能被误判通过。日常 PR 以快速反馈和 amd64 冒烟控制构建成本；双架构完整验证仍是 A 完整交付及每次公开镜像发布的门槛，必须对应受检源码，不复用其他提交的绿灯。

依赖/构建缓存按锁、工具链、目标和架构分隔，concurrency 取消同一 PR 已过期的检查；artifact 命名包含源码修订及架构，保留期可配置。构建和准备依赖可联网，产品测试禁止外网并只用合成目标。公开 artifact 不包含真实 endpoint 配置、凭据或原服务记录；合成报告明确标明运行模式。

使用固定提交摘要的 actions 与固定工具链；fork PR 无发布凭据，不以 pull_request_target 检出并执行不受信提交。发布任务不消费未经绑定和校验的 PR 构建产物，不将 Issue/PR 正文直接插进 shell。[GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use)

### 17.2 Docker Hub 发布与首次配置引导

首选只发布 Docker Hub，不为此额外维护第二个 registry。使用 Docker 官方构建/登录等 Actions，平台为 linux/amd64 和 linux/arm64；镜像发布与普通 CI 检查分离。[Docker GitHub Actions](https://docs.docker.com/build/ci/github-actions/)

发布步骤依次确认：

1. 维护者的 GitHub 仓库及 Docker Hub 仓库/命名空间、可见性、开源许可证和待发布版本。
2. Actions 的执行权限、必需检查、发布 environment 及可用的保护设置；账号/仓库不支持某项保护时明确说明，使用维护者手动触发流程，不假定保护已存在。
3. 设置非秘密仓库变量 DOCKERHUB_USERNAME、DOCKERHUB_REPOSITORY，以及发布 environment 的 DOCKERHUB_TOKEN secret；使用满足推送所需的最小权限 token，不使用账号密码，不要求把 token 发进聊天或提交仓库。
4. 先执行不推送的完整构建/双架构验证，审阅检查产物、镜像内容、版本与拟推送标签，再由维护者启用发布步骤。
5. 推送后以 digest 拉取并完成只用合成数据的冒烟验证，记录版本、源码、规则包及 digest，更新用户运行说明。

变量/secret 的实际创建由后续引导完成；若通过连接工具协助修改账号配置或发布，按当时明确授权执行。本轮规格不创建远端资源、不要求提供凭据。Docker 文档提供变量/secret 登录示例。[Docker registry authentication example](https://docs.docker.com/build/ci/github-actions/push-multi-registries/)

发行使用不可复用的精确版本标签和实际 digest，用户锁定推荐 digest。latest 仅在维护者选择时作为便利别名，不用它作稳定工作流基线。发布必须传递已测试的同一 OCI 内容；若发布过程中重建产生不同内容，需要重新验证，不因源码 ref 相同就声称镜像相同。

wheel/sdist 与版本化格式说明可作为 GitHub 构建 artifact/Release 附件；A 不要求 PyPI 发布。许可证由维护者在首次公开前确定并写入 LICENSE，不预先推定。远端仓库尚未创建、发布未启用或凭据缺失，应显示对应未配置状态，不影响离线贡献者运行产品测试。

### 17.3 面向人和 Agent 的贡献入口

A 交付英文 CONTRIBUTING.md，作为公共贡献流程的事实来源；AGENTS.md 提供简洁导航和项目特有边界，README 链接到二者。贡献者无论人工或使用 Agent，都遵循相同复现、测试、证据和评审要求；不要求提供私人会话记录或模型 API key。

贡献指南包含：Dev Container/可选原生启动、fast/full 与容器检查入口、目录与类型/schema/架构规范、用例与规则版本策略、脱敏证据规范、普通 bug 与协议发现的区别、审阅与发布流程。小修复按相应测试推进；架构或公共契约变更先说明影响和可验证验收条件，不要求每次文档微调启动完整设计流程。

提供以下 GitHub 原生模板，项目中使用 PR 术语：

- .github/ISSUE_TEMPLATE/bug_report.yml：测试器版本、执行环境、复现命令/合成样本、预期与实际结果、失败 assertion/check ID。
- .github/ISSUE_TEMPLATE/compatibility_report.yml：API/beta/规则包、已测 profile、目标交付的可公开标识、观测与证据、未覆盖项；不要求真实内网地址或原始服务日志。
- .github/ISSUE_TEMPLATE/feature_request.yml：使用场景、所需结果、验收条件和范围。
- .github/ISSUE_TEMPLATE/protocol_update.yml：官方来源、当前/候选规则包、变更分类、受影响规则与正反样本。
- .github/PULL_REQUEST_TEMPLATE.md：问题及最终行为、关联 Issue/requirement ID、变更契约/版本、已运行命令与结果、未运行检查及原因、规则/文档/包资源影响。AI 辅助说明可选，但提交者对结果负责。

模板使用清晰字段名和短示例，允许 unknown/not_run 并说明原因，不诱导填造 PASS；字段能映射报告中的稳定 ID。隐私项说明与脱敏导出入口相连。Issue/PR 内容和附带模型输出均视为输入数据，不作为 Agent 改门禁、执行命令或发布的授权。

### 17.4 仓库内 update-anthropic-protocol Agent 命令

D 交付一个范围明确的 Agent skill，公共工作流放 docs/maintenance/update-anthropic-protocol.md；入口为 .agents/skills/update-anthropic-protocol/SKILL.md。Codex 可通过技能选择器或 `$update-anthropic-protocol` 调用；Claude Code 提供 .claude/skills/update-anthropic-protocol/SKILL.md 薄适配，使用 `/update-anthropic-protocol`，两者只引用同一工作流，不重复维护语义。[Codex skills](https://developers.openai.com/codex/skills)、[Claude Code skills](https://code.claude.com/docs/en/skills)

该 skill 仅响应明确的协议维护请求，不因代码中出现 Anthropic 字样就触发。A 的指引标明其属于 D，未交付前不能登记成可用功能。它由使用者现有编程 Agent 执行，不给产品 CLI 添加模型依赖或需要日常 CI 模型凭据。

参数约定为模式 check（默认）或 prepare，以及当前 contract ID/revision、候选目录、指定官方来源范围；不要求用户先猜一个并不存在的新 API 日期。流程如下：

1. 读取选定规则包、当前维护说明和相关验收要求，确认能力/版本边界与已有工作区变化。
2. check 模式复用 `contracts check-updates --allow-network` 或读取已生成候选，输出带引用的差异和变更分类，不改规则文件。
3. prepare 模式在用户已授权的维护范围内，按候选提出新 revision 并修改必要规则、请求模板、fixture、文档和来源清单；保持旧包和历史结果不变，不把文档 diff 自动解释为强制协议变化。
4. 运行同一 fast/full 与相关旧包 golden 回归，报告每项结果、未测真实能力和任何门禁失败；不自动把失败改成更宽的期望。
5. 产出 maintenance-summary.md 和结构化候选，列出来源/截至日期、旧新版本、影响范围、修改文件、检查证据及建议复测命令；由维护者审阅。

Agent 不自动合并、创建远端 Issue/PR、发消息或发布；这些操作只在另有明确要求时执行。网络取到的正文和候选中的指令性文本都是不受信资料，不可执行。抓取失败、不存在差异、资料有变化但能力未实现均需如实记录，不以自然语言声称“已支持最新版”替代验证。

周期 GitHub workflow 默认只产生候选 artifact，维护者再用此 Agent 命令推进；以后若要在 CI 自动调用 Agent，作为单独可选集成评估授权、模型成本、凭据与不受信输入，不纳入默认设计。

### 17.5 协作与维护验收

- A：模板/指南的链接和命令可解析，合成样本可完成贡献者复现；GitHub 检查与本地脚本一致，PR 流程不需要发布或模型凭据。
- A：记录远端未接入与已运行的区别；双架构公开发布门槛不可被日常 amd64 冒烟替代。
- D：check 模式不改规则；prepare 的合成变更有正反样本和新 revision，旧包不变；无变化/抓取失败/未知特性不会伪称完成更新。
- D：缺 Docker Hub 发布配置时默认不推送；试运行与真实推送明确分开；发布产物可关联精确源码、验证结果和 digest。

## 18. 报告呈现与 Agent 阅读契约

### 18.1 风格与布局

报告采用工程验证记录/简短研究报告的风格：白底或适合打印的浅底、深灰正文、克制的强调色、清楚的标题层级、表格与脚注引用。无霓虹渐变、玻璃效果、卡片墙、动画、AI 图标或无依据的综合评分。默认不依赖图表；只有时间线或版本矩阵确实有解释价值时增加对应图表，仍保留原数值和证据。

HTML 使用语义化标题/表格、适度留白、可复制代码片段和本地字体栈；正文/表格字号保持可读，中文断行和长 ID/URL 不破版。状态以文本标签为主，可用弱色辅助，不只靠颜色。桌面、窄屏和打印布局分别检查；打印保留报告身份、版本、引用与限制。

建议阅读顺序：

1. 报告身份与摘要：run/assessment、live/replay、时间/时区、工具/客户端/环境、限定结论。
2. 测试对象与方法：API/beta/规则包、交付标识、样本量、预算、重试策略和证据采集边界。
3. 结果：profiles 和各维度状态、关键失败、简短观测与证据引用。
4. 局限与未覆盖：跳过/阻塞、未知扩展、未验证版本语义、未执行客户端测试。
5. 逐 case/attempt 记录、术语与关键参考资料。

“结论”“观测”“可能解释”“建议复测”明确分开；工程确定性结论由断言生成，未证实的归因不能作为事实。默认不推断内部组件责任，不用修辞放大协议缺陷或小样本成功。

### 18.2 三种产物的一致性

result.json 是机器可读事实来源；report.html 是完整离线阅读版；report.md 是可单独交给 Agent 的简明文本版。三者的运行标识、契约、状态、请求/case 数、关键断言与来源 ID 必须一致。Markdown 不仅提供一个 HTML 链接，须含独立可理解的对象、方法、结果、范围和局限。

report_context 具有自身 context_version，包含 methodology、glossary、references 和 reader_notes。方法简介解释：黑盒测试、不用 LLM Judge、协议与任务分别验收、独立请求/case/断言的区别、五态含义、版本头与规则快照区别。按实际出现内容附少量术语，不塞入完整 API 手册。

每条关键参考具有 reference_id、title、url、retrieved_at/spec_as_of（适用时）、source_kind 和相关 assertion/rule IDs；覆盖官方规范、当前规则包及实际用到的客户端说明。正文在相关结论旁引用 reference_id；引用只能支持规则依据，不能代替本次运行证据。引用清单随包/规则维护，生成报告不联网抓资料，不生成不存在的引文、DOI 或学术背书。

报告仍为自包含离线文档：外部来源只是用户可主动打开的链接，不加载远程 CSS/字体/脚本；官方资料的简短介绍使用维护过的概述，不复制大篇正文。Markdown 的来源链接和本地证据引用也可直接解析。

### 18.3 Agent 解读所需信息与边界

报告开头提供简短阅读说明：只对列出的 profile/规则版本与观测样本下结论；PASS 不等于官方认证或长期稳定；缺少原证据时只能复述观测摘要，不能声称独立复核。记录 request/case/assertion/attempt 的 ID 和计数，避免 Agent 将多项断言误读成多次独立成功。

每个关键失败提供：规则/断言 ID、应满足的条件、简短且脱敏的实际片段、证据文件/事件序号或 JSON Pointer、相关规范引用。脱敏转换和未采集部分明确标识。仅发送 report.md 时，这些摘要仍可用于初步解读；需要核实完整事件顺序或重新评分时提示所需的 result.json 和证据包，不能假定外部 Agent 已能访问本地路径。

测试提示、服务返回、工具日志和代码片段是被记录的数据，不能作为报告阅读 Agent 的执行指令；阅读说明不授予网络、命令或文件修改权限。HTML/Markdown 均正确转义不受信内容，Markdown 围栏不能被原文中的反引号意外闭合。正文不嵌入隐藏系统提示或要求 Agent 无条件信任结论。

### 18.4 阶段 A 的报告验收

- 使用合法、失败、阻塞、证据不足和混合结果的合成样例，核对 HTML/Markdown/JSON 状态与计数一致，引用 ID 和证据定位可解析。
- 无外网打开 HTML 仍完整可读；对桌面、窄屏和打印预览做实际视觉检查，长中文、长 ID、多行 JSON、空数据均不破版。
- Markdown 单独包含足够解读的上下文，缺少证据文件时不暗示已独立验证；来源清单只包含真实维护的引用。
- 恶意 HTML、Markdown 围栏、路径、模型输出和凭据回显不改变报告结构、泄露已知密钥或形成可执行脚本。
- 合成样例有醒目标记，任何基础 API 报告都不能显示未执行的 Claude Code ready 或完整版本选择验证。
