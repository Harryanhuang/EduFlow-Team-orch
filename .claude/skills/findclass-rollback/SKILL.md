---
name: findclass-rollback
description: Rollback a teacher publish operation. Use when a teacher record was incorrectly published, needs to be removed from the server, or local publish_status needs to be reset.
---

# FindClass Rollback

回滚已发布的老师资料。

## 什么时候用

- 用户说"撤销刚才的发布"
- 老师说资料有误需要从服务器下架
- 用户要把已发布的老师恢复为 draft 状态
- 本地 sync_id 需要清空重新发布

## 回滚级别

### 本地回滚（安全）

仅修改本地 Markdown 状态：
- `sync_id` → `null`
- `publish_status` → `draft`
- `publish_time` → `null`

这不影响服务器数据，适用于"还没上传就发现本地资料有问题"。

### 服务器回滚（需谨慎）

通过服务器 API 操作：
- 删除或标记下线 `tb_user` 记录
- 删除关联 `tb_user_info` 记录
- 本地回写状态

## 标准流程

### 1. 确认回滚范围

```bash
# 读取老师 Markdown 文件
# 确认 sync_id / publish_status 当前值
```

### 2. 本地回滚

编辑 Markdown 文件：
- `sync_id: null`
- `publish_status: "draft"`
- `publish_time: null`

### 3. 服务器回滚（如需要）

通过 FindClass 后台 API 或管理界面操作。
操作后确认服务器记录已删除或已下线。

### 4. 记录回滚原因

在 Markdown 备注中或 log 中记录：
- 回滚原因
- 回滚时间
- 操作人

## 操作原则

- 先本地回滚，再考虑服务器回滚
- 服务器回滚前确认老师确实在服务器上
- 回滚后确认本地状态正确（可重新发布）
- 不要把回滚操作本身当成失败——有时候下架是业务需要
- 压缩图目录（webp）可以保留，下次发布可复用
