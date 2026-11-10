"""0002: texture_variants 增加 algo_version（生成算法版本）。

历史变体（本次升级前生成的所有记录）统一回填为 1 = 按像素梯度/AO 半径的旧实现；
新变体由应用层写入 GENERATION_ALGO_VERSION=2（UV 空间分辨率补偿）。
历史文件与 checksum 不重算、不覆盖。
"""
import sqlalchemy as sa
from alembic import op

revision = "0002_variant_algo_version"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("texture_variants") as batch:
        batch.add_column(sa.Column("algo_version", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    with op.batch_alter_table("texture_variants") as batch:
        batch.drop_column("algo_version")
