from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import node_controller
from app.middlewares.auth import get_current_user, require_roles
from app.schemas.node import NodeBatchUpdate, NodeCreate, NodeOut, NodePatch

router = APIRouter(tags=["nodes"])


@router.get("/recipes/{recipe_id}/nodes", response_model=list[NodeOut])
def list_nodes(recipe_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return node_controller.list_nodes(db, recipe_id)


@router.post("/recipes/{recipe_id}/nodes", response_model=NodeOut,
             dependencies=[Depends(require_roles("owner", "editor"))])
def create_node(recipe_id: int, payload: NodeCreate, db: Session = Depends(get_db),
                user: dict = Depends(get_current_user)):
    return node_controller.create_node(db, user, recipe_id, payload)


@router.put("/recipes/{recipe_id}/nodes", dependencies=[Depends(require_roles("owner", "editor"))])
def batch_update(recipe_id: int, payload: NodeBatchUpdate, db: Session = Depends(get_db),
                 user: dict = Depends(get_current_user)):
    return node_controller.batch_update(db, user, recipe_id, payload)


@router.patch("/nodes/{node_id}", response_model=NodeOut, dependencies=[Depends(require_roles("owner", "editor"))])
def patch_node(node_id: int, payload: NodePatch, db: Session = Depends(get_db),
               user: dict = Depends(get_current_user)):
    return node_controller.update_node(db, user, node_id, payload)
