# TexForge · 过程式材质纹理生成与通道打包工坊

> 把节点式配方变成可复现的 PBR 贴图与通道包：同一 `resolution + seed + 节点图` 逐像素一致，每次生成留一条 `TextureVariant` 供对比、回滚与打包。

模拟客户：**栖刻视觉**（35 人建筑可视化 / 产品广告公司，材质组 6 人 = 2 TA + 4 材质美术，每月并行 10+ 项目）。
本系统替换「Substance Designer 手工模板 + 网盘 + 命名规范文档」这一段：上游是客户材质 brief，下游是 UE / Unity 材质实例与外包团队，中间产出的是**可复现的配方、可对比的变体、命名与通道映射都合规的打包 PNG**。

---

## 快速启动

```bash
cp .env.example .env
docker compose up -d
```

- 前端：<http://localhost:18111>
- 后端 API 文档：<http://localhost:19111/docs>
- 首个 backend 启动会自动执行 seed（`SEED_DEMO=true`），也可手动重跑：

```bash
docker compose exec backend python -m scripts.seed_demo
```

seed **幂等**：按 `email` / `slug` 自然键 upsert，重复执行不会产生第二份 `PRJ-2611-陶土外墙`、不会重复插变体、不覆盖用户已改过的节点参数。

### 演示账号（密码统一 `TexForge@2026`）

| 账号 | 角色 | 说明 |
|---|---|---|
| `ta@qike-vision.com` | admin / owner | TA：建/复制/删除配方、定通道规范 |
| `artist@qike-vision.com` | member / editor | 材质美术：改 seed 出变体、对比与回滚 |
| `pm@qike-vision.com` | member / viewer | 外包 PM：只读核对与下载，生成接口返回 403 |

### seed 生成的记录

- 3 个账号（同一 `upsert_user` 分支，不为每个账号写独立逻辑）
- 3 条 `MaterialRecipe`，全部 `PRJ-2611`：`PRJ-2611-陶土外墙`（7 节点 / 1024）、`PRJ-2611-拉丝金属`（5 节点 / 512）、`PRJ-2611-织物`（6 节点 / 512），均 `status=ready`、缩略图可加载
- 每条配方 2 个 `TextureVariant`：六个通道键齐全、`preview_path` 指向共享卷真实文件、`seam_score` 与 `generation_ms` 真实计算、`revision` 从 1 起连续
- 1 条 `ChannelPack`：`preset=orm`、`output_format=png`，文件 `terracotta_wall_orm_1024.png`

---

## 典型使用场景（一天的工作流）

1. 客户 brief 到，要求「哑光陶土外墙」。TA 登录后从样本册复制上一项目配方，改名 `PRJ-2611-陶土外墙`（项目标签 `PRJ-2611`），分辨率 1024。
2. 进 `/recipes/:id/editor`：**7 个节点** value 噪声 → fbm → worley 颗粒 → domain warp → 高度 → 法线 → AO，右侧 `<ParamInspector>` 改参数（400ms 防抖保存），提交生成。
3. 材质美术接着改 3 个 seed 各生成一次，得到 3 个 `TextureVariant`（revision 递增），在 `/preview` 用材质球看颗粒密度、法线强度、tiling 重复感。
4. 在 `/variants` 左右对比：每版 `generation_ms` 与 `seam_score` 都来自后端真实计算；把接缝最好的一版设为当前版本，反例版本留档不删。
5. 在 `/packs` 选 ORM 预设（`r=roughness, g=metallic, b=ao, a=height`），预检通过后打包，下载 `terracotta_wall_orm_1024.png`；再把映射另存为项目预设。
6. 外包 PM 用只读账号进 `/variants` 与 `/packs` 核对「分辨率、接缝、seed 与配方记录一致」后下载。
7. 第二天改色：只动 base_color 相关节点、seed 不变，重新生成的 checksum 与前一天同 seed 结果一致，用来证明「只改了颜色，没顺手改别的」。

> 剧本里的 92 / 88 / 71 是接缝评分的示例读数；本仓库所有展示出来的数值都是后端 `texture/seam.py` 实际算出的整数，README 与页面都读同一份记录，不在前端写死。

---

## 主要功能

- **配方与节点编辑**：纸片式节点画布、拖拽坐标批量 PATCH、连线成环/槽位类型校验、禁用节点后重新生成
- **真实生成**：FastAPI + Celery 异步，numpy 逐像素计算 base_color / normal / roughness / metallic / ao / height 六通道
- **版本对比与接缝评分**：擦除对比、`seam_score` 分段条、`generation_ms`、checksum
- **通道打包**：ORM / MRA 预设、RGBA 四槽映射、重复占用与缺失通道预检、下载 8bit RGBA PNG
- **配额与限流**：`users.daily_generation_quota` + Redis 滑动窗口 + 配方级生成互斥锁
- **审计日志**：配方新建/复制/删除、变体删除、打包下载写 `audit_logs`，前端 `<ActivityTrail>` 展开最近 10 条

---

## 技术栈

| 层 | 选型 |
|---|---|
| 前端 | Vue 3.4+ / TypeScript 5 / Vite 5 / Pinia / Axios / Three.js r160+ / Tailwind CSS 3.4 |
| 后端 | Python 3.11 / FastAPI / SQLAlchemy 2.0 / Pydantic v2 / Celery 5 / numpy / Pillow |
| 数据库 | MySQL 8.0（utf8mb4，JSON 列存节点参数与通道映射） |
| 队列 / 缓存 | Redis 7（Celery broker + 限流窗口 + 生成锁 + 预设） |
| 反向代理 | Nginx（`/api/` 反代 backend，SPA fallback） |

---

## 目录结构与共享卷

```
gb-542/
├── docker-compose.yml          # name: texforge，5 服务，无 version
├── .env / .env.example
├── README.md
├── frontend/                   # Vue SPA + Nginx
│   └── src/{api,stores,types,components,hooks,pages,router,utils,constants,styles}
├── backend/                    # FastAPI + SQLAlchemy + numpy 纹理管线
│   ├── app/{routes,controllers,services,models,schemas,middlewares,utils,texture,constants,config,tasks}
│   ├── alembic/versions/
│   └── scripts/seed_demo.py
└── worker/                     # Celery worker + 心跳 healthcheck
    ├── Dockerfile
    ├── entrypoint.sh
    └── healthcheck.py
```

命名卷：

| 卷 | 容器挂载 | 用途 |
|---|---|---|
| `mysql_data` | db:/var/lib/mysql | MySQL 数据 |
| `redis_data` | redis:/data | AOF 持久化 |
| `artifact_data` | backend & worker:/data/artifacts | 六通道 PNG、打包 PNG |
| `preview_data` | backend & worker:/data/previews | 材质球预览图（缩略图） |

`backend` 与 `worker` 共享 `artifact_data` / `preview_data`，Celery 任务写盘后后端与 Nginx 直接可读。

---

## 环境变量

| 变量 | 含义 | 默认值 |
|---|---|---|
| `COMPOSE_PROJECT_NAME` | Compose 项目名 / 容器名前缀 | `texforge` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | MySQL 业务库与账号 | `texforge_db` / `texforge_user` / `texforge_pwd` |
| `DB_ROOT_PASSWORD` | MySQL root 密码 | `texforge_root_pwd` |
| `JWT_SECRET` | JWT 签名密钥 | `change_me_to_a_long_random_string` |
| `FRONTEND_PORT` | 前端宿主机端口 | `18111` |
| `BACKEND_PORT` | 后端宿主机端口 | `19111` |
| `DB_PORT` | MySQL 宿主机映射端口 | `17611` |
| `REDIS_URL` | Celery broker / 限流 Redis | `redis://redis:6379/0` |
| `ARTIFACT_DIR` | 贴图产物目录 | `/data/artifacts` |
| `PREVIEW_DIR` | 预览图目录 | `/data/previews` |
| `MAX_UPLOAD_MB` | 上传上限 | `16` |
| `GENERATION_DAILY_QUOTA` | 新用户默认每日生成配额 | `60` |
| `SEED_DEMO` | 启动时是否自动灌演示数据 | `true` |

`SEED_DEMO=false` 可启动空库版本（只有表结构），用于干净环境演示。

---

## Docker 部署说明

- 5 个服务：`frontend`、`backend`、`worker`、`db`、`redis`，全部带 healthcheck（worker 用心跳文件 `/tmp/worker-heartbeat`，60s 内更新即存活）。
- 容器名统一 `${COMPOSE_PROJECT_NAME:-texforge}-<role>`，在中文目录名下也可 `docker compose up -d`。
- 首次启动会拉取/构建镜像，并等 MySQL 初始化；backend 启动时建表 + seed（失败只记日志不阻塞）。
- 查看 worker 日志：`docker compose logs -f worker`；重置数据库：`docker compose down -v`（会删除 `mysql_data` 与全部产物）。
- 生成任务若在 60 秒内未完成，backend 内置 watchdog 会同步补算，保证演示不断链。

---

## 本地开发

```bash
# 前端
cd frontend && pnpm install && pnpm dev

# 后端
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                # 或依赖启动时的 create_all
uvicorn app.main:app --reload --port 19111

# worker
celery -A app.config.celery_app worker -l info
```

本地前端 `vite` 已配置 `/api` → `http://localhost:19111`（`rewrite` 去掉 `/api` 前缀，与 Nginx 行为一致）。

---

## 核心实体（贯穿表 → model → schema → service → controller → route → 前端 api → store → 页面/组件）

| 实体 | 关键文件 |
|---|---|
| User | `models/user.py` → `schemas/auth.py` → `services/auth_service.py` → `controllers/auth_controller.py` → `routes/auth.py` → `api/auth.ts` → `stores/authStore.ts` → `LoginPage.vue` / `AppShell.vue` |
| MaterialRecipe | `models/material_recipe.py` → `schemas/recipe.py` → `services/recipe_service.py` → `controllers/recipe_controller.py` → `routes/recipe.py` → `api/recipe.ts` → `stores/recipeStore.ts` → `RecipesPage.vue` |
| RecipeNode | `models/recipe_node.py` → `schemas/node.py` → `services/node_service.py` → `controllers/node_controller.py` → `routes/node.py` → `api/node.ts` → `stores/nodeGraphStore.ts` → `RecipeEditorPage.vue` |
| TextureVariant | `models/texture_variant.py` → `schemas/variant.py` → `services/variant_service.py` → `controllers/variant_controller.py` → `routes/variant.py` → `tasks/generate_texture.py` → `api/variant.ts` → `stores/recipeStore.ts` → `VariantsPage.vue` |
| ChannelPack | `models/channel_pack.py` → `schemas/pack.py` → `services/pack_service.py` → `controllers/pack_controller.py` → `routes/pack.py` → `tasks/pack_channels.py` → `api/pack.ts` → `stores/packStore.ts` → `PacksPage.vue` |

## 核心页面与共享组件

- `/recipes` 样本册（`StatusBadge`、`EmptyState`、`TextureThumb`）
- `/recipes/:id/editor` 节点编辑器（`NodeCard`、`ParamInspector`、`MaterialSphere`）
- `/preview` 材质球预览（`MaterialSphere`、`ChannelStrip`、`SeamScoreBar`）
- `/variants` 版本对比（`TextureThumb`、`StatusBadge`、`SeamScoreBar`）
- `/packs` 通道打包（`TextureThumb`、`EmptyState`、`ChannelStrip`）

---

## 共享枚举出现位置（前后端重复定义、多处引用）

### NoiseType（`value` / `perlin` / `worley` / `fbm`）

- 后端定义：`backend/app/constants/noise.py`
- 后端引用：`schemas/node.py` 的 Literal、`texture/noise.py` 的 `dispatch` 分派表、`texture/renderer.py` 的 `NOISE_NODE_MAP`、`constants/node_registry.py`、`constants/log_templates.py` 的生成日志字段、`constants/error_codes.py` 的生成失败文案、`utils/formatters.py`（通道/状态命中同一份中文名映射）、`scripts/seed_demo.py` 的 7/5/6 节点图
- 前端定义：`frontend/src/constants/noise.ts`
- 前端引用：`types/node.ts`、`constants/nodeRegistry.ts` 的节点库分组、`utils/nodeDefaults.ts` 的默认 octaves/persistence、`components/inspector/NoiseParams.vue`、`components/graph/NodePalette.vue` 分组、`constants/messages.ts`

### BlendMode（`normal` / `add` / `multiply` / `overlay` / `screen`）

- 后端定义：`backend/app/constants/blend.py`
- 后端引用：`texture/blend.py` 的 `BLEND_OPS`、`schemas/node.py`、`constants/node_registry.py` 的 blend 节点默认值、`services/node_service.py` 的槽位校验、`utils/formatters.py`、审计 payload、`constants/log_templates.py`
- 前端定义：`frontend/src/constants/blend.ts`
- 前端引用：`types/node.ts`、`constants/nodeRegistry.ts`、`utils/nodeDefaults.ts`、`components/inspector/BlendParams.vue`、`constants/messages.ts`、`components/graph/NodePalette.vue`

### TextureChannel（`base_color` / `normal` / `roughness` / `metallic` / `ao` / `height`）

- 后端定义：`backend/app/constants/channel.py`
- 后端引用：`texture/packer.py`、`schemas/pack.py`、`services/pack_service.py`、`schemas/variant.py` 的 `file_paths_json` 注释、`constants/node_registry.py` 的 `CHANNEL_NODE_MAP`、`texture/renderer.py` 的通道组装、`utils/formatters.py` 的中文名、`constants/log_templates.py` 的通道字段、`constants/messages.py` 的缺通道文案
- 前端定义：`frontend/src/constants/channel.ts`
- 前端引用：`types/texture.ts`、`types/pack.ts`、`utils/textureExport.ts` 的文件名规则、`utils/channelMath.ts` 预检、`components/texture/ChannelStrip.vue` 的格子数、`components/texture/TextureThumb.vue`、`components/inspector/ParamInspector.vue` 的通道页签、`pages/PreviewPage.vue`、`pages/PacksPage.vue`、`constants/messages.ts`

### RecipeStatus（`draft` / `generating` / `ready` / `failed`）

- 后端定义：`backend/app/constants/recipe_status.py`
- 后端引用：`models/material_recipe.py` 的 `status` 列、`services/recipe_service.py` 状态机、`services/variant_service.py` 的生成状态流转、`constants/log_templates.py`、`utils/formatters.py`
- 前端定义：`frontend/src/constants/recipeStatus.ts`
- 前端引用：`types/recipe.ts`、`components/common/StatusBadge.vue` 的样式映射、`hooks/useGenerationPolling.ts`、`constants/messages.ts`、`pages/RecipesPage.vue` 的筛选器

> 扩展验证：给 `TextureChannel` 新增 `emissive` 需要触达 `constants/channel.py`、`constants/channel.ts`、`types/texture.ts`、`constants/node_registry.py`、`texture/renderer.py`、`texture/packer.py`、`schemas/pack.py`、`utils/formatters.py`、`constants/log_templates.py`、`components/texture/ChannelStrip.vue`、`utils/textureExport.ts`、`constants/messages.ts` 共 12 个文件。

---

## 横切关注点

- **认证授权（JWT + 工作区归属）**：`users.role` / `users.workspace_role` 两列 + `material_recipes.owner_id` 外键；`middlewares/auth.py` 注入 `request.state.user`；`utils/jwt.py` 签发/校验（8 小时）；`routes/recipe.py` 写接口依赖 `require_roles("owner","editor")`，删除仅 owner；前端 `router/guards.ts`、`stores/authStore.ts`、`components/common/PermissionNotice.vue`。
- **操作审计日志**：`audit_logs(actor_id, action, entity_type, entity_id, payload_json, ip, created_at)`；`middlewares/audit_logger.py` 响应阶段写库 + `controllers/*` 显式记录四类必须审计的接口；`constants/log_templates.py` 提供模板；前端 `stores/recipeStore.ts` 删除后提示、`components/common/ActivityTrail.vue` 展示最近 10 条。
- **生成配额与接口限流**：`users.daily_generation_quota` / `quota_used_date` / `quota_used_count`；`middlewares/quota.py` 用 Redis 滑动窗口（`rl:texforge:{user_id}:{route}`），`services/variant_service.py` 用 `SETNX qlock:{recipe_id}` 保证同一配方不并行生成；前端 `stores/previewStore.ts`、`components/common/QuotaMeter.vue`、`hooks/useGenerationPolling.ts` 退避轮询。

---

## 同 seed 复现的验证方法

```bash
# 1) 对同一配方连续两次生成（seed 与 resolution 不变）
docker compose exec backend python - <<'PY'
from app.config.database import SessionLocal
from app.services.variant_service import perform_generation
from app.models.material_recipe import MaterialRecipe
from app.models.texture_variant import TextureVariant
db = SessionLocal()
r = db.query(MaterialRecipe).filter(MaterialRecipe.slug == 'prj-2611-terracotta').first()
for _ in range(2):
    v = TextureVariant(recipe_id=r.id, revision=999, seed_used=r.seed, status='generating', file_paths_json={})
    db.add(v); db.commit(); db.refresh(v)
    perform_generation(db, v.id)
    print(v.id, v.checksum)
PY

# 2) 比对两次 sha256：应完全一致
docker compose exec backend python -c "from app.config.database import SessionLocal; from app.models.texture_variant import TextureVariant; db=SessionLocal(); rows=[v.checksum for v in db.query(TextureVariant).filter(TextureVariant.revision==999).all()]; print(rows); assert len(set(rows))==1, 'checksum mismatch'; print('reproducible OK')"
```

也可以直接看 `GET /api/variants/{id}` 响应里的 `checksum` 字段。

---

## 必须真实实现的计算

- `texture/noise.py`：value / perlin / worley（F1 距离）三种向量化噪声，fbm 5 个 octave 叠加；`texture/warp.py` 两层噪声偏移采样坐标做 domain warp
- `texture/normal_map.py`：高度图经 Sobel 求梯度生成切线空间法线，`normal_scale` 参与强度
- `texture/derive.py`：由高度与噪声派生 roughness / metallic / ao（AO 用局部均值遮蔽近似）
- `texture/seam.py`：比对左右边缘列与上下边缘行的像素差与梯度差，归一化成 0~100 的 `seam_score` 写入 `TextureVariant`
- `texture/packer.py`：按 `channel_mapping_json` 合成 RGBA 四通道并输出 8bit PNG，字节数写 `byte_size`
- `texture/renderer.py`：解析 `RecipeNode` DAG、逐节点求值、组装六通道、numpy 球体着色生成预览

前端只做展示与交互：`<MaterialSphere>` 仅加载后端产出的贴图 URL，不使用 canvas shader 伪造纹理。

---

## 已知取舍

- 参数修改采用「400ms 防抖保存 + 显式提交生成」，没有在每次参数变更后自动触发生成（避免演示时误耗配额）；生成请求本身仍走异步 Celery + watchdog 兜底。
- 接缝评分是后端真实计算值，不一定正好落在剧本示例的 92 / 88 / 71，页面与 README 均不硬编码该数值。
- 节点连线在前端通过槽位下拉/端口点击完成，画布上的连线端口操作采用简化实现（支持成环与槽位类型校验）。

MIT License
