#!/usr/bin/python3
from pyrogram.errors import BadRequest
from pyrogram.filters import create
from bot import admins, owner, group, LOGGER
from pyrogram.enums import ChatMemberStatus


# async def owner_filter(client, update):
#     """
#     过滤 owner
#     :param client:
#     :param update:
#     :return:
#     """
#     user = update.from_user or update.sender_chat
#     uid = user.id
#     return uid == owner

# 三个参数给on用
async def admins_on_filter(filt, client, update) -> bool:
    """
    过滤admins中id，包括owner
    :param client:
    :param update:
    :return:
    """
    user = update.from_user or update.sender_chat
    uid = user.id
    return bool(uid == owner or uid in admins or uid in group)


async def admins_filter(update):
    """
    过滤admins中id，包括owner
    """
    user = update.from_user or update.sender_chat
    uid = user.id
    return bool(uid == owner or uid in admins)


async def user_in_group_filter(client, update):
    """
    过滤在授权组中的人员
    :param client:
    :param update:
    :return:
    """
    try:
        uid = update.from_user or update.sender_chat
        uid = uid.id
        for i in group:
            try:
                u = await client.get_chat_member(chat_id=int(i), user_id=uid)
                if u.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER, ChatMemberStatus.OWNER]:
                    return True
            except BadRequest as e:
                if e.ID == 'USER_NOT_PARTICIPANT':
                    LOGGER.info(f"{uid}不在{group}中，USER_NOT_PARTICIPANT")
                    return False
                elif e.ID == 'CHAT_ADMIN_REQUIRED':
                    LOGGER.error(f"bot不能在 {i} 中工作，请检查bot是否在群组及其权限设置")
                    return False
                else:
                    LOGGER.info(f"查询{uid}是否在{group}中，发生错误: {str(e)}, continue")
                    continue
            else:
                LOGGER.info(f"{uid}不在{group}中，continue")
                continue

        LOGGER.info(f"已确定{uid}不在{group}中")
        return False
    except Exception as e:
        LOGGER.error(f"过滤在授权组中的人员发生错误: {str(e)}")
        return False


async def user_in_group_on_filter(filt, client, update):
    """
    过滤在授权组中的人员
    :param filt:
    :param client:
    :param update:
    :return:
    """
    try:
        uid = update.from_user or update.sender_chat
        uid = uid.id
        for i in group:
            try:
                u = await client.get_chat_member(chat_id=int(i), user_id=uid)
                if u.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER, ChatMemberStatus.OWNER]:
                    return True
            except BadRequest as e:
                if e.ID == 'USER_NOT_PARTICIPANT':
                    LOGGER.info(f"{uid}不在{group}中，USER_NOT_PARTICIPANT")
                    return False
                elif e.ID == 'CHAT_ADMIN_REQUIRED':
                    LOGGER.error(f"bot不能在 {i} 中工作，请检查bot是否在群组及其权限设置")
                    return False
                else:
                    LOGGER.info(f"查询{uid}是否在{group}中，发生错误: {str(e)}, continue")
                    continue
            else:
                LOGGER.info(f"{uid}不在{group}中，continue")
                continue

        LOGGER.info(f"已确定{uid}不在{group}中")
        return False
    except Exception as e:
        LOGGER.error(f"过滤在授权组中的人员发生错误: {str(e)}")
        return False


async def judge_uid_ingroup(client, uid):
    for i in group:
        try:
            u = await client.get_chat_member(chat_id=int(i), user_id=uid)
            if u.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER,
                            ChatMemberStatus.OWNER]:  # 移除了 'ChatMemberStatus.RESTRICTED' 防止有人进群直接注册不验证
                return True
        except BadRequest as e:
            if e.ID == 'USER_NOT_PARTICIPANT':
                return False
            elif e.ID == 'CHAT_ADMIN_REQUIRED':
                LOGGER.error(f"bot不能在 {i} 中工作，请检查bot是否在群组及其权限设置")
                return False
            else:
                return False
    return False


# 过滤 on_message or on_callback 的admin
admins_on_filter = create(admins_on_filter)
admins_filter = create(admins_filter)

# 过滤 是否在群内
user_in_group_f = create(user_in_group_filter)
user_in_group_on_filter = create(user_in_group_on_filter)
