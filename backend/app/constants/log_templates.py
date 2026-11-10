"""日志模板集中定义（>=22 条），service/controller/celery task 只准通过 utils.logger.log_event 使用。"""

LOG_TEMPLATES = {
    "AUTH_LOGIN_SUCCESS": "登录成功 email={email} role={role} workspace_role={workspace_role}",
    "AUTH_LOGIN_FAILED": "登录失败 email={email} reason={reason}",
    "RECIPE_CREATE": "配方创建 recipe_id={recipe_id} owner_id={owner_id} resolution={resolution} seed={seed}",
    "RECIPE_COPY": "配方复制 source_recipe_id={recipe_id} new_recipe_id={new_recipe_id} node_count={node_count}",
    "RECIPE_DELETE": "配方软删 recipe_id={recipe_id} actor_id={actor_id}",
    "RECIPE_UPDATE": "配方更新 recipe_id={recipe_id} fields={fields}",
    "NODE_BATCH_UPDATE": "节点批量更新 recipe_id={recipe_id} node_count={node_count} duration_ms={duration_ms}",
    "NODE_CREATE": "节点新增 recipe_id={recipe_id} node_type={node_type} label={label}",
    "NODE_CONNECT": "节点连线 recipe_id={recipe_id} from_node_id={from_node_id} to_node_id={to_node_id} slot={slot}",
    "NODE_CONNECT_REJECTED": "连线被拒 recipe_id={recipe_id} reason={reason} slot={slot}",
    "NODE_PARAM_PATCH": "节点参数修改 recipe_id={recipe_id} node_id={node_id} changed={changed}",
    "GENERATION_ENQUEUED": "生成入队 recipe_id={recipe_id} variant_id={variant_id} resolution={resolution} seed={seed}",
    "GENERATION_START": "生成开始 recipe_id={recipe_id} variant_id={variant_id} revision={revision}",
    "GENERATION_DONE": "生成完成 recipe_id={recipe_id} variant_id={variant_id} duration_ms={duration_ms} seam_score={seam_score} algo_version={algo_version}",
    "GENERATION_FAILED": "生成失败 recipe_id={recipe_id} variant_id={variant_id} error={error}",
    "QUOTA_REJECTED": "配额拒绝 user_id={user_id} route={route} used={used} quota={quota}",
    "RATE_LIMIT_HIT": "限流命中 user_id={user_id} route={route} retry_after={retry_after}",
    "LOCK_REJECTED": "配方生成互斥锁命中 recipe_id={recipe_id} user_id={user_id}",
    "PACK_CREATE": "通道打包创建 pack_id={pack_id} recipe_id={recipe_id} preset={preset} mapping={mapping}",
    "PACK_DONE": "通道打包完成 pack_id={pack_id} byte_size={byte_size} duration_ms={duration_ms}",
    "PACK_DOWNLOAD": "打包下载 pack_id={pack_id} actor_id={actor_id} file={file_name}",
    "PACK_PRECHECK_FAILED": "打包预检失败 recipe_id={recipe_id} reason={reason} preset={preset}",
    "VARIANT_DELETE": "变体删除 variant_id={variant_id} recipe_id={recipe_id} revision={revision}",
    "VARIANT_SET_CURRENT": "设为当前版本 variant_id={variant_id} recipe_id={recipe_id} revision={revision}",
    "AUDIT_WRITE_FAILED": "审计写入失败 action={action} entity_type={entity_type} error={error}",
    "SEED_DEMO_DONE": "演示数据完成 users={users} recipes={recipes} variants={variants} packs={packs}",
    "SEED_DEMO_FAILED": "演示数据失败 error={error}",
    "CLEANUP_ORPHAN_FILES": "清理孤儿文件 removed={removed} kept={kept}",
}

REQUIRED_TEMPLATE_KEYS = list(LOG_TEMPLATES.keys())
