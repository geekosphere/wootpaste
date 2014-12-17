"""add a spam field

Revision ID: 41804fbf1862
Revises: 4d7d5b95ddef
Create Date: 2014-12-17 19:04:09.190962

"""

# revision identifiers, used by Alembic.
revision = '41804fbf1862'
down_revision = '4d7d5b95ddef'

from alembic import op
import sqlalchemy as sa


from os.path import join, dirname, abspath, realpath
import sys
sys.path.append(realpath(join(dirname(abspath(__file__)), '..')))
import wootpaste.models

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('paste', sa.Column('spam', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('paste', 'spam')
    ### end Alembic commands ###
