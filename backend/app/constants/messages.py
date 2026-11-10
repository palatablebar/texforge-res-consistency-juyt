"""API 返回文案 / 审计文案 / 任务失败文案共用。前端 constants/messages.ts 镜像面向用户的 12 条。"""

MSG_RECIPE_CREATED = "配方已创建"
MSG_RECIPE_COPIED = "配方已复制，节点坐标已随配方一起复制"
MSG_RECIPE_DELETED = "配方已删除，操作已记录"
MSG_RECIPE_UPDATED = "配方已更新"
MSG_NODES_SAVED = "节点图已保存"
MSG_NODE_CYCLE_REJECTED = "连线会形成环，已拒绝"
MSG_GENERATION_QUEUED = "生成任务已入队，请稍候"
MSG_GENERATION_FAILED = "生成失败，已保留上一个成功版本"
MSG_PACK_CREATED = "通道包已生成，可以下载"
MSG_PACK_DUPLICATE_CHANNEL = "同一通道被重复占用，请重新选择"
MSG_PACK_CHANNEL_MISSING = "所选版本缺少部分通道，无法打包"
MSG_QUOTA_EXHAUSTED = "今日生成配额已用尽"
MSG_RATE_LIMITED = "操作过于频繁，请稍后再试"
MSG_VARIANT_CURRENT = "已设为当前版本"
MSG_VARIANT_DELETED = "变体已删除，共享卷文件已清理"
MSG_VIEWER_READONLY = "只读账号不能触发生成"
MSG_AUDIT_RECORDED = "操作已记录到审计日志"

TASK_FAILED_GENERATE = "纹理生成任务失败：{error}"
TASK_FAILED_PACK = "通道打包任务失败：{error}"

AUDIT_ACTIONS = {
    "recipe_create": "配方创建",
    "recipe_copy": "配方复制",
    "recipe_delete": "配方删除",
    "variant_delete": "变体删除",
    "pack_download": "打包下载",
}
