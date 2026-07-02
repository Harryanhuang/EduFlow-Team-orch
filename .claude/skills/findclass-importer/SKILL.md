---
name: findclass-importer
description: Use when importing local exam-paper PDFs into the FindClass admin question bank, especially for scanning materials, resumable uploads, audit checks, failure reports, success reports, and replenishment checklists.
---

# FindClass Importer

把本地学科资料导入 FindClass 题库后台，并留下可恢复、可审计、可复盘的产物。

## 什么时候用

在这些场景直接用：

- 用户要把 `/Volumes/Halobster/学科资料` 下的试卷和答案批量导入 FindClass
- 用户要继续一个中断的上传任务
- 用户要检查哪些资料上传失败、哪些资料已经成功入库
- 用户要根据异常清单整理需要补齐的资料路径
- 用户要复用本次 FindClass 上传流程

不要硬套在这些场景：

- 只是整理本地 PDF，不需要进 FindClass 后台
- 用户没有当前后台登录态或有效 token，且任务必须真实上传
- 后台接口字段已经变化但还没重新确认

## 核心路径

- 工具目录：`tools/findclass_importer/`
- 默认输出目录：`outputs/findclass_importer/`
- manifest：`outputs/findclass_importer/manifest.jsonl`
- 异常清单：`outputs/findclass_importer/anomalies.jsonl`
- 可恢复上传进度：`outputs/findclass_importer/resumable_upload_progress.jsonl`

## 执行流程

### 1. 扫描本地资料

```bash
python3 -m tools.findclass_importer.cli scan
```

扫描会生成：

- `manifest.jsonl`：可直接导入的问答卷和答案卷配对
- `anomalies.jsonl`：缺配对、未映射分类、文件过大、多文件组等异常
- `summary.json`：扫描汇总
- `question_type_tree.json`：后台分类树缓存

### 2. 小批量验证

真实全量上传前，先跑 pilot 或小范围：

```bash
python3 -m tools.findclass_importer.cli pilot
python3 -m tools.findclass_importer.cli upload --dry-run
```

确认字段、分类、上传接口和查重行为都正确后，再进入全量。

### 3. 获取 token

优先使用临时环境变量，不要把 token 写进文件：

```bash
export FINDCLASS_TOKEN='当前后台 token'
```

如果 Chrome 已打开并登录 `admin.findclass.top`，可以用 `tools.findclass_importer.full_upload_goal.read_chrome_token()` 从当前登录态读取 token。

### 4. 可恢复上传

全量或续跑优先用可恢复上传器：

```bash
python3 -m tools.findclass_importer.resumable_upload --report-every 25
```

它会：

- 读取 `manifest.jsonl`
- 跳过 `resumable_upload_progress.jsonl` 里已经处理过的 index
- 每条上传后立刻追加进度
- 每条成功或跳过后马上做后台回查和 PDF 链接检查
- 中断后可直接重跑同一命令续传

如果没有 `FINDCLASS_TOKEN`，可以用一个短 Python 入口从 Chrome 登录态注入 token：

```bash
python3 - <<'PY'
from tools.findclass_importer.full_upload_goal import read_chrome_token
from tools.findclass_importer import resumable_upload
import sys

token = read_chrome_token()
args = resumable_upload.build_parser().parse_args(['--token', token, '--report-every', '25'])
sys.exit(resumable_upload.run(args))
PY
```

### 5. 完整审计

上传结束后至少检查：

- `manifest.jsonl` 行数是否等于已处理唯一 index 数
- 是否有缺失 index 或重复 index
- `created / skipped_existing / failed` 数量
- 非失败行是否都有 audit
- audit 是否匹配后台记录
- `examFile` 和 `answer` 链接是否可访问

本次使用的收尾产物约定：

- `complete_audit_summary.json`
- `failed_upload_report.md`
- `failed_upload_report.json`
- `successful_upload_report.md`
- `successful_upload_report.json`
- `material_replenishment_checklist.md`
- `material_replenishment_checklist.json`

### 6. 失败报告

失败报告要区分两类：

- 上传失败：接口报错、网络超时、空文件、文件过大等
- 审计失败：后台记录存在但字段或 PDF 链接检查不通过

每条至少写清：

- manifest index
- display name
- typeId
- 本地问答卷路径
- 本地答案卷路径
- 失败原因
- 是否建议重试、补文件、压缩文件或修后台记录

### 7. 成功报告

成功报告要同时统计：

- 新建成功
- 后台已存在而跳过
- 按 `field` 统计
- 按 `source_root` 统计

JSON 明细保留每条记录的本地路径、上传 URL、后台回查结果和链接检查结果。

### 8. 资料补齐清单

基于 `anomalies.jsonl` 和本轮失败项整理：

- `missing_pair`：缺问答卷或缺答案卷，优先补齐 sample path 对应目录
- `unmapped_type`：本地有资料但后台分类树缺叶子，补后台分类或调整映射
- `file_too_large`：超过当前后台 10MB 限制，压缩、拆分或调整上传接口
- `multi_file_group`：同一组多套候选文件，人工确认保留哪套
- `ignored_or_unparsed`：其他资料、ER、SC、PEF 等，确认是否需要入库
- 本轮上传/审计失败：作为最高优先级单独列出

## 操作原则

- 不覆盖后台已有题目，先用 `typeId + name + year + season + field` 查重
- token 只临时读取或通过环境变量传入
- 全量任务必须用可恢复进度文件，不做只存在内存里的批量上传
- 中断后先看 `wc -l resumable_upload_progress.jsonl` 和最后一条 index，再续跑
- 上传完成前不要只看批次结果；最终报告必须基于全量 progress 重算
- 对网络超时类失败优先重试，对空文件/缺文件类失败先补资料
- 对后台分类缺失不要硬改 manifest，应先补分类树或明确映射规则

## 已验证基线

2026-05-27 跑完一轮 FindClass 全量导入：

- manifest 总数：4268
- 已处理：4268
- 新建成功：3406
- 已存在跳过：858
- 上传失败：4
- 审计失败：2

对应产物位于 `outputs/findclass_importer/`。
