from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, JSON, String

from app.config.database import Base


class RecipeNode(Base):
    __tablename__ = "recipe_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("material_recipes.id"), nullable=False, index=True)
    node_type = Column(String(40), nullable=False)
    label = Column(String(80), nullable=False)
    position_x = Column(Float, nullable=False, default=0.0)
    position_y = Column(Float, nullable=False, default=0.0)
    params_json = Column(JSON, nullable=False, default=dict)
    input_refs_json = Column(JSON, nullable=False, default=list)
    order_index = Column(Integer, nullable=False, default=0)
    is_disabled = Column(Boolean, nullable=False, default=False)
