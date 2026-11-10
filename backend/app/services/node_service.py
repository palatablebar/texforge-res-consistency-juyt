"""节点服务：DAG 校验（成环/槽位）、增删改、批量坐标保存。"""
import time

from sqlalchemy.orm import Session

from app.constants.error_codes import ERROR_MESSAGES, NODE_CYCLE, RECIPE_NOT_FOUND, SLOT_TYPE_MISMATCH
from app.constants.node_registry import NODE_REGISTRY
from app.models.material_recipe import MaterialRecipe
from app.models.recipe_node import RecipeNode
from app.services.recipe_service import get_recipe, require_write
from app.utils.errors import AppError
from app.utils.logger import log_event


def list_nodes(db: Session, recipe_id: int) -> list[RecipeNode]:
    return db.query(RecipeNode).filter(RecipeNode.recipe_id == recipe_id).order_by(RecipeNode.order_index).all()


def _validate_refs(nodes: list[RecipeNode], extra: dict[int, list[dict]] | None = None) -> None:
    """校验槽位类型与成环。extra 用于批量更新时尚未落库的 input_refs。"""
    known = {n.id: n for n in nodes}
    refs_map = {n.id: list(n.input_refs_json or []) for n in nodes}
    if extra:
        for node_id, refs in extra.items():
            if node_id in refs_map:
                refs_map[node_id] = refs
    graph: dict[int, list[int]] = {nid: [] for nid in known}
    for node_id, refs in refs_map.items():
        node = known[node_id]
        allowed = set(NODE_REGISTRY.get(node.node_type, {}).get("inputs", []))
        seen_slots: set[str] = set()
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            slot = ref.get("slot", "a")
            from_id = ref.get("from_node_id")
            if from_id not in known:
                raise AppError(SLOT_TYPE_MISMATCH, f"连线引用了不存在的节点 {from_id}", http_status=422)
            if allowed and slot not in allowed:
                raise AppError(SLOT_TYPE_MISMATCH, f"节点 {node.label} 没有槽位 {slot}", http_status=422)
            if slot in seen_slots:
                raise AppError(SLOT_TYPE_MISMATCH, f"节点 {node.label} 的槽位 {slot} 被重复连线", http_status=422)
            seen_slots.add(slot)
            graph[from_id].append(node_id)
    visiting: set[int] = set()
    visited: set[int] = set()

    def dfs(node_id: int) -> None:
        if node_id in visited:
            return
        if node_id in visiting:
            raise AppError(NODE_CYCLE, ERROR_MESSAGES[NODE_CYCLE], http_status=422)
        visiting.add(node_id)
        for nxt in graph.get(node_id, []):
            dfs(nxt)
        visiting.discard(node_id)
        visited.add(node_id)

    for node_id in list(graph.keys()):
        dfs(node_id)


def create_node(db: Session, user: dict, recipe_id: int, payload) -> RecipeNode:
    require_write(user)
    get_recipe(db, recipe_id)
    spec = NODE_REGISTRY.get(payload.node_type)
    if not spec:
        raise AppError(SLOT_TYPE_MISMATCH, f"未知节点类型 {payload.node_type}", http_status=422)
    params = dict(spec["defaults"])
    params.update(payload.params_json or {})
    node = RecipeNode(
        recipe_id=recipe_id,
        node_type=payload.node_type,
        label=(payload.label or spec["label"]).strip(),
        position_x=float(payload.position_x),
        position_y=float(payload.position_y),
        params_json=params,
        input_refs_json=payload.input_refs_json or [],
        order_index=db.query(RecipeNode).filter(RecipeNode.recipe_id == recipe_id).count(),
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    log_event("NODE_CREATE", recipe_id=recipe_id, node_type=node.node_type, label=node.label)
    return node


def update_node(db: Session, user: dict, node_id: int, payload) -> RecipeNode:
    require_write(user)
    node = db.get(RecipeNode, node_id)
    if not node:
        raise AppError(RECIPE_NOT_FOUND, f"节点 {node_id} 不存在", http_status=404)
    data = payload.model_dump(exclude_unset=True)
    changed = []
    for field in ("label", "position_x", "position_y", "params_json", "is_disabled"):
        if field in data and data[field] is not None:
            setattr(node, field, data[field])
            changed.append(field)
    if "input_refs_json" in data and data["input_refs_json"] is not None:
        nodes = list_nodes(db, node.recipe_id)
        _validate_refs(nodes, extra={node.id: data["input_refs_json"]})
        node.input_refs_json = data["input_refs_json"]
        changed.append("input_refs_json")
    db.add(node)
    db.commit()
    db.refresh(node)
    log_event("NODE_PARAM_PATCH", recipe_id=node.recipe_id, node_id=node.id, changed=",".join(changed))
    return node


def batch_update(db: Session, user: dict, recipe_id: int, payload) -> int:
    require_write(user)
    get_recipe(db, recipe_id)
    started = time.perf_counter()
    nodes = list_nodes(db, recipe_id)
    known = {n.id: n for n in nodes}
    extras: dict[int, list[dict]] = {}
    for item in payload.nodes:
        node = known.get(item.id)
        if not node:
            raise AppError(RECIPE_NOT_FOUND, f"节点 {item.id} 不属于该配方", http_status=404)
        if item.position_x is not None:
            node.position_x = float(item.position_x)
        if item.position_y is not None:
            node.position_y = float(item.position_y)
        if item.params_json is not None:
            merged = dict(node.params_json or {})
            merged.update(item.params_json)
            node.params_json = merged
        if item.is_disabled is not None:
            node.is_disabled = bool(item.is_disabled)
        if item.input_refs_json is not None:
            extras[node.id] = item.input_refs_json
    if extras:
        _validate_refs(nodes, extra=extras)
        for node_id, refs in extras.items():
            known[node_id].input_refs_json = refs
    db.commit()
    duration_ms = int((time.perf_counter() - started) * 1000)
    log_event("NODE_BATCH_UPDATE", recipe_id=recipe_id, node_count=len(payload.nodes), duration_ms=duration_ms)
    return len(payload.nodes)
