"""节点控制器。"""
from sqlalchemy.orm import Session

from app.models.recipe_node import RecipeNode
from app.services import node_service


def serialize(node: RecipeNode) -> dict:
    return {
        "id": node.id, "recipe_id": node.recipe_id, "node_type": node.node_type, "label": node.label,
        "position_x": node.position_x, "position_y": node.position_y, "params_json": node.params_json or {},
        "input_refs_json": node.input_refs_json or [], "order_index": node.order_index, "is_disabled": node.is_disabled,
    }


def list_nodes(db: Session, recipe_id: int) -> list[dict]:
    return [serialize(node) for node in node_service.list_nodes(db, recipe_id)]


def create_node(db: Session, user: dict, recipe_id: int, payload) -> dict:
    return serialize(node_service.create_node(db, user, recipe_id, payload))


def update_node(db: Session, user: dict, node_id: int, payload) -> dict:
    return serialize(node_service.update_node(db, user, node_id, payload))


def batch_update(db: Session, user: dict, recipe_id: int, payload) -> dict:
    count = node_service.batch_update(db, user, recipe_id, payload)
    return {"message": "节点图已保存", "updated": count}
