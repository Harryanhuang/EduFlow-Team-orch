---
name: web-access-chrome-bridge
description: Maintain the docker-chrome CDP bridge that powers web-access skill inside EduFlow Team agents. Use when adding the skill to a new agent, diagnosing CDP port failures, or resetting the proxy after container restart. Also covers cross-project access (Obsidian Edu / global ~/.agents) and GitHub private backup + sync workflow.
metadata:
  type: reference
  generated_by: worker_builder
  date: 2026-07-01
  source: T-79 实战经验 + symlink 安装完工 + 下载路径统一到系统 Downloads + 全局 web-access 升级 + GitHub 私有备份仓 + 同步脚本
---

# web-access ↔ docker-chrome CDP Bridge

## Use When

- 为某个 agent 接入 web-access skill（必须先有 symlink）
- 诊断 `curl http://localhost:9233/json/version` 失败 / `cdp-proxy.mjs` 启动报错
- `docker compose restart` 之后需要把整条链（chrome → tcp-proxy → cdp-proxy）复位
- 改 docker-compose / Dockerfile 后的完整重建
- 给老板/manifold 解释为什么"docker --network host"在 Mac 上行不通
- 下载目录路径变更（落点统一到 `/Users/huanganan/Downloads/agent-chrome`）
- 验证 Chrome 真在跑：`/health` 显示 `connected:true`，不是看 proxy 进程存在

## 一句话全景

```
web-access skill (Agent CLI 进程内)
  → cdp-proxy.mjs :3456          (Node 长驻 HTTP→WebSocket 适配)
  → host 127.0.0.1:9233          (docker-compose 端口发布)
  → container :9223              (tcp-proxy.pl 监听)
  → container :9222              (chromium --remote-debugging-port)
```

## 端口与映射

| 位置           | 端口  | 谁监听              | 备注                          |
|----------------|-------|---------------------|-------------------------------|
| Host           | 9233  | docker-proxy        | `127.0.0.1:9233:9223` 发布    |
| Container      | 9223  | perl tcp-proxy.pl   | 监听 0.0.0.0:9223 → 9222      |
| Container      | 9222  | chromium headless   | `--remote-allow-origins='*'` |

**注意**：host 上**不要**直接监听 9222。9222 是容器内部，外部只暴露 9233。

## docker-compose 服务定义（agent-chrome）

来源：`docker-compose.yml`

```yaml
services:
  agent-chrome:
    build:
      context: ./docker/agent-chrome
    image: eduflow-agent-chrome:dev
    shm_size: "1gb"
    ports:
      - "127.0.0.1:9233:9223"        # 关键：只 loopback，9223→9222 走 tcp-proxy
    command:
      - sh
      - -lc
      - rm -f /data/profile/Singleton* &&
        perl /opt/agent-chrome/tcp-proxy.pl 9223 127.0.0.1 9222 &
        exec /usr/lib/chromium/chromium --headless=new --no-sandbox
          --disable-dev-shm-usage --disable-gpu --disable-software-rasterizer
          --remote-debugging-port=9222 --remote-allow-origins='*'
          --user-data-dir=/data/profile --download-default-directory=/downloads about:blank
    volumes:
      - agent-chrome-profile:/data/profile
      - /Users/huanganan/Downloads/agent-chrome:/downloads
      - ./docker/agent-chrome/tcp-proxy.pl:/opt/agent-chrome/tcp-proxy.pl:ro
    restart: unless-stopped
```

挂载点：
- `agent-chrome-profile:/data/profile`：chromium user-data-dir，删除 `Singleton*` 防止二次启动失败
- `/Users/huanganan/Downloads/agent-chrome:/downloads`：**下载产物统一落系统 Downloads**（2026-07-01 改的，跟 macOS 其他浏览器下载位置一致；之前的 `./downloads/agent-chrome` 项目内路径已废弃）
- `./docker/agent-chrome/tcp-proxy.pl`：纯 perl IO::Socket::INET 转发器，无外部依赖

## cdp-proxy.mjs 启动顺序

`cdp-proxy.mjs` 是 web-access skill 自带的 Node 长驻 HTTP API 进程（默认 3456）。
它**不会**自动重连 chrome，必须手动重启。check-deps 启动后 proxy 以 **detached 进程**常驻，所有 agent 共享。

```bash
# 1. 确认 docker 容器活着
docker ps | grep eduflow-team-orch-agent-chrome-1

# 2. 杀掉旧 proxy（如果有；旧的会停留在 connected:null 空转状态）
pkill -f cdp-proxy.mjs

# 3. 用 web-access 自带的 check-deps 启动新 proxy（自动 reconnect chrome）
node "${CLAUDE_SKILL_DIR}/scripts/check-deps.mjs"

# 4. 验证
curl -s http://localhost:3456/health
# 期望: {"status":"ok","connected":true,"chromePort":9233,...}

curl -s http://localhost:3456/targets | jq '. | length'  # 应返回 ≥0 的 tab 数
```

> check-deps 退出码：0=可用；1=缺依赖（按 stdout 处理）；2=浏览器偏好未定（需写入 config.env）。

## Mac host-networking 坑（必读）

**绝不要**给 `agent-chrome` 加 `network_mode: host`。

理由：
- Docker Desktop for Mac 的 host 网络**不桥接 `localhost`**。容器内 `127.0.0.1` ≠ host `127.0.0.1`。
- 即使能 ping 通 host，CDP 端口也不能用 host 路径访问。
- 正确做法：用 bridge + `ports: 127.0.0.1:9233:9223`（如上）。

替代方案也都不要用：
- ❌ `docker run --network host`
- ❌ `host.docker.internal`（这是给**容器访问 host**用的，反向不通）
- ❌ `docker.for.mac.host.internal`（同向问题）
- ❌ `extra_hosts: ["host.docker.internal:host-gateway"]`（同向）

**正确方向**：host → container 走 ports；container → host 走 host.docker.internal。

## reset 步骤（chrome 卡死 / 端口不可用时）

```bash
# 1. 重启容器
docker compose restart agent-chrome

# 2. 等 chrome 完全 ready（dpid chrome process）
sleep 3
docker exec eduflow-team-orch-agent-chrome-1 pgrep -f chromium

# 3. 验证 CDP 端口从 host 可达
curl -s http://127.0.0.1:9233/json/version | jq '.Browser'
# 期望: "Chrome/149.0.7827.196" 或更新

# 4. 重启 cdp-proxy
pkill -f cdp-proxy.mjs
node "${CLAUDE_SKILL_DIR}/scripts/check-deps.mjs"

# 5. 验证 proxy 起来
curl -s http://localhost:3456/health   # connected:true
curl -s http://localhost:3456/targets  # 至少一个 about:blank tab
```

## 完整重建步骤（改 compose / Dockerfile 后）

```bash
# 1. 重建容器（应用新的挂载/配置）
docker compose up -d agent-chrome

# 2. 验证挂载
docker exec eduflow-team-orch-agent-chrome-1 ls -la /downloads/

# 3. 验证容器内可写（双向打通）
docker exec eduflow-team-orch-agent-chrome-1 touch /downloads/.write-test && \
  docker exec eduflow-team-orch-agent-chrome-1 rm /downloads/.write-test

# 4. 重启 proxy
pkill -f cdp-proxy.mjs
node "${CLAUDE_SKILL_DIR}/scripts/check-deps.mjs"

# 5. 端到端验证
curl -s http://127.0.0.1:9233/json/version | jq '.Browser'
curl -s http://localhost:3456/health
```

## 17 个 agent 的 symlink 模板

`agent-home/<name>/.claude/skills/web-access` 必须指向项目内 `.claude/skills/web-access/`：

```bash
SRC="/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch/.claude/skills/web-access"

# 14 个核心 agent
for a in manager auto_ops worker_builder worker_course worker_qbank \
         worker_teacher worker_school worker_syllabus \
         review_course review_curriculum \
         Luke_recorder Hermes; do
  DIR="/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch/.eduflow-team-state/agent-home/$a/.claude/skills"
  mkdir -p "$DIR"
  ln -sfn "$SRC" "$DIR/web-access"
done

# 3 个补装 agent（2026-06-30 T-79 完成）
for a in worker_school worker_syllabus worker_teacher; do
  ... # 同上（确认未被前面覆盖）
done
```

> 注：`worker_school` 和 `worker_teacher` 不在 eduflow.toml `[team.agents]` 段（lazy / 隐藏 agent），`eduflow reidentify` 会报 `unknown agent`，但 symlink 本身仍生效，下次 pane 启动或手动 reidentify 时被读入。

## 验证命令

```bash
# CDP 端口（从 host）
curl -s http://127.0.0.1:9233/json/version

# CDP proxy（从 host）
curl -s http://localhost:3456/health      # connected:true 才是真连上
curl -s http://localhost:3456/targets     # 列 tab

# 浏览器+proxy 状态（check-deps 一站式）
node "${CLAUDE_SKILL_DIR}/scripts/check-deps.mjs"

# 容器进程
docker exec eduflow-team-orch-agent-chrome-1 pgrep -af chromium
docker exec eduflow-team-orch-agent-chrome-1 pgrep -af tcp-proxy

# 下载目录挂载正确（容器内）
docker exec eduflow-team-orch-agent-chrome-1 ls -la /downloads/

# 主机下载目录（应该是 /Users/huanganan/Downloads/agent-chrome）
ls -la /Users/huanganan/Downloads/agent-chrome/
```

## 已知坑

1. **dbus 错误可忽略**：`Failed to connect to socket /run/dbus/system_bus_socket` 是 chromium 启动时的常规 warning，不影响 CDP。
2. **`Singleton*` lock 残留**：如果 chromium 没正常退出，`/data/profile/SingletonLock` 会阻塞下次启动。command 里有 `rm -f /data/profile/Singleton*` 兜底。
3. **macOS 端口被占**：9233 被占用时 `docker compose up` 会失败但报得不清楚，先 `lsof -i :9233` 排查。
4. **chromium 启动慢**：cold start 5-10s 是正常的；`/json/version` 不返回时多等几秒重试。
5. **proxy 与 chrome 顺序**：必须先 chrome ready 再启 cdp-proxy，否则 proxy 会 hang。
6. **stale proxy 空转**：cdp-proxy 即使断连也会保持进程（HTTP 200 + `connected:null`），单看进程在跑不能确认可用，必须 `curl /health` 看 `connected:true`。
7. **`network_mode: host` 死路**：Docker Desktop for Mac 的 host networking 不桥接 localhost，CDP 走不通。**任何时候都不要用 `docker run --network host` 替代 compose**——总是 `docker compose up -d agent-chrome`。
8. **下载目录权限**：默认容器内 `/downloads` 由 chrome user (uid 1000) 拥有；主机 `/Users/huanganan/Downloads/agent-chrome` 必须是当前用户可写，否则挂载后容器写不进去（看起来"挂上了"但下载会 EACCES）。

## References

- web-access skill 主文件：`.claude/skills/web-access/SKILL.md`
- docker-compose：`docker-compose.yml` (services.agent-chrome)
- chrome Dockerfile：`docker/agent-chrome/Dockerfile`
- tcp-proxy 源码：`docker/agent-chrome/tcp-proxy.pl`
- 安装记录：`.eduflow-team-state/agent-home/<name>/.claude/skills/web-access`

## 跨项目接入（Obsidian Edu / Codex / 全局 web-access）

web-access 不只是 EduFlow-Team-orch 项目内使用——mac 上还有多份独立的安装路径：

| 位置 | 形态 | 谁读它 |
|---|---|---|
| `/Users/huanganan/.agents/skills/web-access/` | 实体目录（含 `config.env`，GitHub 私有备份源） | **所有路径的单一真相源** |
| `/Users/huanganan/.codex/skills/web-access` | **symlink → `../../.agents/skills/web-access`** | Codex CLI / Codex agents |
| `EduFlow-Team-orch/.claude/skills/web-access/` | 实体目录（含 `config.env`，用于 hot-reload 项目内编辑） | EduFlow Team agents（通过 agent-home 的 symlink 引用） |
| `/Users/huanganan/.claude/skills/web-access` | symlink → `../../.agents/skills/web-access` | 用户级 Claude Code |
| `/Volumes/Halobster/Obsidian Edu/.claude/skills/web-access` | symlink → `/Users/huanganan/.agents/skills/web-access` | Obsidian Edu 顶层 Claude Code |

**核心约束**：所有 `config.env` 都必须指向同一个 docker chrome 端点（`http://127.0.0.1:9233`），否则行为不一致。

**Codex 的特殊性**：从 2026-07-01 起改为 symlink 到全局——之前是 v2.4.3 独立实体目录，需要手动同步；现在升级一次、三处生效（Obsidian Edu、Codex、EduFlow Team 都跟随）。

## GitHub 私有备份 + 同步流程

web-access 上游在 [eze-is/web-access](https://github.com/eze-is/web-access)。我们用 **GitHub 私有仓**保留本地副本做长期跟踪：

- 仓地址：<https://github.com/Harryanhuang/web-access-backup>（private）
- 本地路径：`/Volumes/Halobster/web access skill/`（git 仓库，remote = 上面的 GitHub 仓）

**关键保护**：`config.env` 被 `.gitignore` 排除，**永远不进 GitHub**。docker chrome 端点是机器本地配置，跟原版无关。

### 同步脚本：`~/.local/bin/web-access-sync.sh`

```bash
# 1. 看会改哪些文件，不实际改
web-access-sync.sh --dry-run

# 2. 真正同步（git pull 备份仓 → 覆盖 ~/.agents/skills/web-access/）
web-access-sync.sh

# 3. 同步完自动重启 cdp-proxy（新脚本生效）
web-access-sync.sh --restart-proxy
```

脚本做的事：
1. `cd` 到备份仓，`git pull --rebase --autostash` 拉最新
2. 备份本地 `config.env` 到 `/tmp`
3. 把备份仓里所有 git tracked 文件复制到 `~/.agents/skills/web-access/`
4. 从 `/tmp` 恢复 `config.env`（即使脚本 bug 也不会丢）
5. 可选 `--restart-proxy`：杀 cdp-proxy 重跑 check-deps

### 升级流程（从 eze-is/web-access 上游同步新版本）

```bash
# 1. 在备份仓拉上游最新（不通过本仓 PR，手动同步更可控）
cd "/Volumes/Halobster/web access skill"
git remote add upstream https://github.com/eze-is/web-access.git 2>/dev/null || true
git fetch upstream
git merge upstream/main  # 或者 cherry-pick 想要的 commit

# 2. 解决冲突，重点关注 SKILL.md / scripts/ 的变更
#    注意：上游 .gitignore 不排除 config.env，我们这份要保留这行

# 3. 推 GitHub 私有仓
git push origin main

# 4. 同步到本地安装
web-access-sync.sh --restart-proxy
```

### 新机器初始化（如何从 GitHub 私有仓恢复 web-access）

```bash
# 1. clone 私有仓（仅代码，config.env 已排除）
git clone https://github.com/Harryanhuang/web-access-backup.git \
  /tmp/wa-backup

# 2. 创建目标目录 + 复制代码
mkdir -p /Users/huanganan/.agents/skills/web-access
cp -R /tmp/wa-backup/* /Users/huanganan/.agents/skills/web-access/

# 3. **写本机的 config.env**（指向这台机器的 docker chrome 端点）
#    注意：GitHub 仓不含 config.env（被 .gitignore 排除），
#    必须每台机器本地写，因为端口映射可能不一样。
cat > /Users/huanganan/.agents/skills/web-access/config.env <<EOF
WEB_ACCESS_BROWSER=
WEB_ACCESS_CDP_ENDPOINT=http://127.0.0.1:9233
EOF

# 4. 起 docker chrome（每台机器独立配置）
docker compose up -d agent-chrome   # 或 docker run 单独跑

# 5. 验证
node /Users/huanganan/.agents/skills/web-access/scripts/check-deps.mjs
```

### 新增 agent 接入 web-access（**永远指向全局**）

**铁律**：不要为每个 agent 复制一份 web-access。统一 symlink 到 `/Users/huanganan/.agents/skills/web-access`，升级一次、三处生效（Obsidian Edu / Codex / EduFlow Team / 任何新 agent 都跟随）。

```bash
GLOBAL="$HOME/.agents/skills/web-access"

# Claude Code 类（项目内或顶层 .claude/skills/）
ln -sfn "$GLOBAL" <agent-home>/.claude/skills/web-access

# Codex 类
ln -sfn "$GLOBAL" "$HOME/.codex/skills/web-access"

# Hermes 类（**先确认 hermes 的 skill loader 支持 symlink**，再装）
ln -sfn "$GLOBAL" "$HOME/.hermes/skills/web-access"

# 任何其他 agent 工具
ln -sfn "$GLOBAL" <该工具的 skills 目录>/web-access
```

如果 symlink 不被某个工具识别，回退方案是 rsync（但失去单一真相源）：

```bash
rsync -av --exclude='config.env' "$GLOBAL/" <目标目录>/web-access/
# 然后单独复制本机 config.env
cp "$GLOBAL/config.env" <目标目录>/web-access/config.env
```

### 验证脚本同步后行为正确

```bash
# check-deps 应识别出 WEB_ACCESS_CDP_ENDPOINT，连接 docker chrome
node /Users/huanganan/.agents/skills/web-access/scripts/check-deps.mjs
# 期望: browser: ok (Remote CDP (127.0.0.1:9233), port 9233) [WEB_ACCESS_CDP_ENDPOINT]
#       proxy: ready (Remote CDP (127.0.0.1:9233))

# proxy health
curl -s http://localhost:3456/health | jq '.status,.connected,.chromePort'
```