from models.model_utils import *


async def check_permission(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    permissions = await get_permissions_from_db(ctx)
    perm_roles_id = list(map(lambda perm: perm.role_id, permissions))
    roles = [i for i in ctx.author.roles]

    cross = list(set(roles) & set(perm_roles_id))

    return True if cross else False

