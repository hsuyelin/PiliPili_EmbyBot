"""
对用户分数调整
score +-

对用户sakura_b币调整
coins +-
"""
import math
import asyncio

from pyrogram import filters
from pyrogram.errors import BadRequest
from bot import bot, prefixes, LOGGER, sakura_b, owner, coin_admins
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import sendMessage, deleteMessage
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby
from bot.func_helper.fix_bottons import group_f


async def get_user_input(msg):
    if msg.reply_to_message is None:
        try:
            uid = int(msg.command[1])
            b = int(math.ceil(float(msg.command[2])))
            enableAdmin = bool(int(msg.command[3])) if len(msg.command) > 3 else False
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest, ValueError):
            try:
                await deleteMessage(msg)
            except Exception as e:
                pass
            return None, None, None, None
    else:
        try:
            uid = msg.reply_to_message.from_user.id
            b = int(math.ceil(float(msg.command[1])))
            enableAdmin = bool(int(msg.command[2])) if len(msg.command) > 2 else False
            first = await bot.get_chat(uid)
        except (IndexError, ValueError):
            try:
                await deleteMessage(msg)
            except Exception as e:
                pass
            return None, None, None, None
    return uid, b, enableAdmin, first


@bot.on_message(filters.command('score', prefixes=prefixes) & admins_on_filter)
async def score_user(_, msg):
    uid, b, enableAdmin, first = await get_user_input(msg)
    if not first:
        return await sendMessage(msg,
                                 "🔔 **使用格式：**[命令符]score [id] [加减分数]\n\n或回复某人[命令符]score [+/-分数] 请确认tg_id输入正确",
                                 timer=60)
    e = sql_get_emby(tg=uid)
    if not e:
        return await sendMessage(msg, f"数据库中没有[ta](tg://user?id={uid}) 。请先私聊我", buttons=group_f)

    us = e.us + b
    try:
        us = int(math.ceil(float(us)))
        us = 0 if us < 0 else us
    except Exception as e:
        pass

    content = ""
    if b == 0:
        content = f"🎯 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 拍了拍 [{first.first_name}](tg://user?id={uid}) 什么都没有做"
    elif b > 0:
        content = f"🎯 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 赏赐了 [{first.first_name}](tg://user?id={uid}) {b} 积分"
    else:
        content = f"🎯 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 偷走了 [{first.first_name}](tg://user?id={uid}) {abs(b)} 积分"

    if msg.from_user.id != owner or not enableAdmin:
        await asyncio.gather(sendMessage(msg, content), msg.delete())
        LOGGER.info(f"【用户】[积分]: {content}")
        return

    content += f"\n· 🎟️ 实时积分: **{us}**"
    if sql_update_emby(Emby.tg == uid, us=us):
        await asyncio.gather(sendMessage(msg, content), msg.delete())
        LOGGER.info(f"【admin】[积分]: 管理员 {content} 数据操作成功")
    else:
        await sendMessage(msg, '⚠️ 数据库操作失败，请检查')
        LOGGER.info(f"【admin】[积分]: 管理员 {content} 数据操作失败")


@bot.on_message(filters.command('coins', prefixes=prefixes) & admins_on_filter)
async def coins_user(_, msg):
    uid, b, enableAdmin, first = await get_user_input(msg)
    if not first:
        return await sendMessage(msg,
                                 "🔔 **使用格式：**[命令符]coins [id] [+/-币]\n\n或回复某人[命令符]coins [+/-币] 请确认tg_id输入正确",
                                 timer=60)

    e = sql_get_emby(tg=uid)
    if not e:
        return await sendMessage(msg, f"数据库中没有[ta](tg://user?id={uid}) 。请先私聊我", buttons=group_f)

    us = e.iv + b
    try:
        us = int(math.ceil(float(us)))
        us = 0 if us < 0 else us
    except Exception as e:
        pass

    content = ""
    if b == 0:
        content = f"🎯 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 拍了拍 [{first.first_name}](tg://user?id={uid}) 什么都没有做"
    elif b > 0:
        content = f"🎯 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 赏赐了 [{first.first_name}](tg://user?id={uid}) {b} {sakura_b}"
    else:
        content = f"🎯 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 偷走了 [{first.first_name}](tg://user?id={uid}) {abs(b)} {sakura_b}"

    if not enableAdmin:
        await asyncio.gather(sendMessage(msg, content), msg.delete())
        LOGGER.info(f"【用户】[{sakura_b}]: {content}")
        return
        
    if msg.from_user.id != owner and msg.from_user.id not in coin_admins:
        await asyncio.gather(sendMessage(msg, content), msg.delete())
        LOGGER.info(f"【用户】[{sakura_b}]: {content}")
        return

    content += f"\n· 🎟️ 实时{sakura_b}: **{us}**"

    if sql_update_emby(Emby.tg == uid, iv=us):
        await asyncio.gather(sendMessage(msg, content), msg.delete())
        LOGGER.info(f"【admin】[{sakura_b}]: {content} 数据操作成功")
    else:
        await sendMessage(msg, '⚠️ 数据库操作失败，请检查')
        LOGGER.info(f"【admin】[{sakura_b}]: {content} 数据操作失败")
