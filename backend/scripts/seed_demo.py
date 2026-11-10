"""演示数据 seed：3 个账号 / 3 条 PRJ-2611 配方（7/5/6 节点）/ 每配方 2 个变体 / 1 条 ORM 打包。
幂等：按 email / slug 自然键 upsert，重复执行不追加记录、不覆盖用户改过的节点参数。"""
import sys
import traceback

from app.config.database import Base, SessionLocal, engine
from app.config.settings import settings
from app.constants.node_registry import (
    NODE_TYPE_AO,
    NODE_TYPE_BLEND,
    NODE_TYPE_FBM,
    NODE_TYPE_HEIGHT,
    NODE_TYPE_NORMAL,
    NODE_TYPE_NOISE_PERLIN,
    NODE_TYPE_NOISE_VALUE,
    NODE_TYPE_NOISE_WORLEY,
    NODE_TYPE_WARP,
)
from app.constants.recipe_status import RecipeStatus
from app.models.channel_pack import ChannelPack
from app.models.material_recipe import MaterialRecipe
from app.models.recipe_node import RecipeNode
from app.models.texture_variant import TextureVariant
from app.models.user import User
from app.services.pack_service import pack_filename, perform_pack
from app.services.variant_service import perform_generation
from app.utils.logger import log_event
from app.utils.password import hash_password

DEMO_PASSWORD = "TexForge@2026"

ACCOUNTS = [
    {
        "email": "ta@qike-vision.com",
        "display_name": "林知远（TA）",
        "role": "admin",
        "workspace_role": "owner",
        "daily_generation_quota": 60,
    },
    {
        "email": "artist@qike-vision.com",
        "display_name": "沈嘉禾（材质美术）",
        "role": "member",
        "workspace_role": "editor",
        "daily_generation_quota": 60,
    },
    {
        "email": "pm@qike-vision.com",
        "display_name": "周倩（外包 PM）",
        "role": "member",
        "workspace_role": "viewer",
        "daily_generation_quota": 0,
    },
]


def upsert_user(db, account: dict) -> User:
    """唯一账号分支：新建或按 email 更新角色字段（不重置密码与配额）。"""
    user = db.query(User).filter(User.email == account["email"]).first()
    if user is None:
        user = User(
            email=account["email"],
            password_hash=hash_password(DEMO_PASSWORD),
            display_name=account["display_name"],
            role=account["role"],
            workspace_role=account["workspace_role"],
            daily_generation_quota=account["daily_generation_quota"],
        )
        db.add(user)
    else:
        user.display_name = account["display_name"]
        user.role = account["role"]
        user.workspace_role = account["workspace_role"]
    db.commit()
    db.refresh(user)
    return user


def N(node_type: str, label: str, x: float, y: float, params: dict, inputs: dict | None = None) -> dict:
    return {
        "node_type": node_type,
        "label": label,
        "position_x": float(x),
        "position_y": float(y),
        "params_json": params,
        "inputs": inputs or {},
    }


RECIPES = [
    {
        "slug": "prj-2611-terracotta",
        "name": "PRJ-2611-陶土外墙",
        "description": "栖刻视觉 · PRJ-2611 哑光陶土外墙。客户 brief：暖灰陶土、颗粒感明显、粗糙度高。",
        "resolution": 1024,
        "seed": 2611001,
        "owner_email": "ta@qike-vision.com",
        "nodes": [
            N(NODE_TYPE_NOISE_VALUE, "Value-01", 60, 130, {"frequency": 7.0, "seed_offset": 0, "contrast": 1.0}),
            N(NODE_TYPE_FBM, "FBM-02", 250, 130, {"octaves": 5, "persistence": 0.5, "lacunarity": 2.0,
                                                  "frequency": 3.5, "seed_offset": 11, "grayness": 0.45}, {"a": 0}),
            N(NODE_TYPE_NOISE_WORLEY, "Worley-03", 440, 130, {"cells": 11, "jitter": 0.9, "seed_offset": 7,
                                                             "contrast": 1.1}, {"a": 1}),
            N(NODE_TYPE_WARP, "Warp-04", 630, 130, {"strength": 0.34, "scale": 3.0, "iterations": 2,
                                                    "seed_offset": 5}, {"a": 2}),
            N(NODE_TYPE_HEIGHT, "Height-05", 820, 130, {"contrast": 1.25, "invert": False, "palette": "terracotta",
                                                         "levels": 8}, {"a": 3}),
            N(NODE_TYPE_NORMAL, "Normal-06", 1010, 40, {"normal_scale": 1.05, "flip_y": False}, {"a": 4}),
            N(NODE_TYPE_AO, "AO-07", 1010, 240, {"radius": 6, "strength": 0.8}, {"a": 4}),
        ],
    },
    {
        "slug": "prj-2611-brushed-metal",
        "name": "PRJ-2611-拉丝金属",
        "description": "栖刻视觉 · PRJ-2611 电梯轿厢拉丝不锈钢。横向拉丝、低粗糙度、高金属度。",
        "resolution": 512,
        "seed": 2612007,
        "owner_email": "artist@qike-vision.com",
        "nodes": [
            N(NODE_TYPE_NOISE_PERLIN, "Perlin-01", 70, 150, {"frequency": 8.0, "seed_offset": 3, "contrast": 1.2}),
            N(NODE_TYPE_FBM, "FBM-02", 260, 150, {"octaves": 4, "persistence": 0.55, "lacunarity": 2.4,
                                                  "frequency": 5.0, "seed_offset": 11, "grayness": 0.55}, {"a": 0}),
            N(NODE_TYPE_WARP, "Warp-03", 450, 150, {"strength": 0.18, "scale": 9.0, "iterations": 2,
                                                    "seed_offset": 5}, {"a": 1}),
            N(NODE_TYPE_HEIGHT, "Height-04", 640, 150, {"contrast": 1.05, "invert": False, "palette": "metal",
                                                        "levels": 6}, {"a": 2}),
            N(NODE_TYPE_NORMAL, "Normal-05", 830, 150, {"normal_scale": 0.8, "flip_y": False}, {"a": 3}),
        ],
    },
    {
        "slug": "prj-2611-fabric",
        "name": "PRJ-2611-织物",
        "description": "栖刻视觉 · PRJ-2611 展厅织物软包。粗经纬、强漫反射、接近零金属度。",
        "resolution": 512,
        "seed": 2613043,
        "owner_email": "artist@qike-vision.com",
        "nodes": [
            N(NODE_TYPE_NOISE_WORLEY, "Worley-01", 60, 120, {"cells": 18, "jitter": 0.7, "seed_offset": 7}),
            N(NODE_TYPE_NOISE_VALUE, "Value-02", 60, 300, {"frequency": 32.0, "seed_offset": 0}),
            N(NODE_TYPE_BLEND, "Blend-03", 250, 210, {"mode": "overlay", "opacity": 0.58},
              {"a": 0, "b": 1}),
            N(NODE_TYPE_WARP, "Warp-04", 440, 210, {"strength": 0.12, "scale": 6.0, "iterations": 1,
                                                    "seed_offset": 5}, {"a": 2}),
            N(NODE_TYPE_HEIGHT, "Height-05", 630, 210, {"contrast": 1.1, "invert": False, "palette": "fabric",
                                                        "levels": 7}, {"a": 3}),
            N(NODE_TYPE_NORMAL, "Normal-06", 820, 210, {"normal_scale": 0.9, "flip_y": False}, {"a": 4}),
        ],
    },
]


def ensure_nodes(db, recipe: MaterialRecipe, spec: dict) -> list[RecipeNode]:
    existing = db.query(RecipeNode).filter(RecipeNode.recipe_id == recipe.id).count()
    if existing:
        return db.query(RecipeNode).filter(RecipeNode.recipe_id == recipe.id).order_by(RecipeNode.order_index).all()
    created: list[RecipeNode] = []
    for order_index, item in enumerate(spec["nodes"]):
        node = RecipeNode(
            recipe_id=recipe.id,
            node_type=item["node_type"],
            label=item["label"],
            position_x=item["position_x"],
            position_y=item["position_y"],
            params_json=item["params_json"],
            input_refs_json=[],
            order_index=order_index,
        )
        db.add(node)
        db.flush()
        created.append(node)
    # 第二遍按 order_index 的输入解析成真实节点 id，保证 DAG 连接完整
    for order_index, item in enumerate(spec["nodes"]):
        node = created[order_index]
        refs = []
        for slot, source_index in item["inputs"].items():
            refs.append({"slot": slot, "from_node_id": created[source_index].id})
        node.input_refs_json = refs
        db.add(node)
    db.commit()
    return created


def seed_recipe(db, spec: dict, owner: User) -> tuple[MaterialRecipe, int]:
    recipe = db.query(MaterialRecipe).filter(MaterialRecipe.slug == spec["slug"]).first()
    created_variants = 0
    if recipe is None:
        recipe = MaterialRecipe(
            owner_id=owner.id,
            name=spec["name"],
            slug=spec["slug"],
            description=spec["description"],
            resolution=spec["resolution"],
            seed=spec["seed"],
            status=RecipeStatus.DRAFT.value,
        )
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
    ensure_nodes(db, recipe, spec)

    ready = (
        db.query(TextureVariant)
        .filter(TextureVariant.recipe_id == recipe.id, TextureVariant.status == "ready")
        .order_by(TextureVariant.revision)
        .all()
    )
    if not ready:
        for index in range(2):
            variant = TextureVariant(
                recipe_id=recipe.id,
                revision=index + 1,
                seed_used=(spec["seed"] + index * 137) % 2147483647,
                status="generating",
                file_paths_json={},
            )
            db.add(variant)
            db.commit()
            db.refresh(variant)
            perform_generation(db, variant.id)
            created_variants += 1
        ready = (
            db.query(TextureVariant)
            .filter(TextureVariant.recipe_id == recipe.id, TextureVariant.status == "ready")
            .order_by(TextureVariant.revision)
            .all()
        )
    if ready:
        current = ready[0]
        recipe.status = RecipeStatus.READY.value
        if not recipe.current_variant_id:
            recipe.current_variant_id = current.id
            current.is_current = 1
            recipe.thumbnail_path = current.preview_path
        db.add(recipe)
        db.add(current)
        db.commit()
    return recipe, created_variants


def seed_pack(db, recipe: MaterialRecipe, user: User) -> int:
    exists = (
        db.query(ChannelPack)
        .filter(ChannelPack.recipe_id == recipe.id, ChannelPack.preset == "orm")
        .first()
    )
    if exists:
        return 0
    variant = (
        db.query(TextureVariant)
        .filter(TextureVariant.recipe_id == recipe.id, TextureVariant.status == "ready")
        .order_by(TextureVariant.revision)
        .first()
    )
    if not variant:
        return 0
    preset = "orm"
    filename = pack_filename(recipe, preset, "png")
    pack = ChannelPack(
        recipe_id=recipe.id,
        variant_id=variant.id,
        name=filename.rsplit(".", 1)[0],
        channel_mapping_json={"r": "roughness", "g": "metallic", "b": "ao", "a": "height"},
        output_format="png",
        preset=preset,
        file_path=f"packs/{filename}",
        status="pending",
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)
    perform_pack(db, pack.id)
    return 1


def seed_demo() -> dict:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    stats = {"users": 0, "recipes": 0, "variants": 0, "packs": 0}
    try:
        users: dict[str, User] = {}
        for account in ACCOUNTS:
            users[account["email"]] = upsert_user(db, account)
            stats["users"] = len(users)
        for spec in RECIPES:
            owner = users[spec["owner_email"]]
            recipe, created = seed_recipe(db, spec, owner)
            stats["recipes"] += 1
            stats["variants"] += created
        terracotta = db.query(MaterialRecipe).filter(MaterialRecipe.slug == "prj-2611-terracotta").first()
        if terracotta:
            stats["packs"] += seed_pack(db, terracotta, users["ta@qike-vision.com"])
        log_event("SEED_DEMO_DONE", users=stats["users"], recipes=stats["recipes"],
                  variants=stats["variants"], packs=stats["packs"])
        return stats
    finally:
        db.close()


if __name__ == "__main__":
    try:
        result = seed_demo()
        print(f"seed done: {result}")
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(1)
