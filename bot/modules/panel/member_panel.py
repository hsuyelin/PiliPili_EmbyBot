"""
用户区面板代码
先检测有无账户
无 -> 创建账户、换绑tg

有 -> 账户续期，重置密码，删除账户，显隐媒体库
"""
import asyncio
import datetime
import random
import re
from datetime import timedelta, datetime

from pyrogram.errors import BadRequest

from bot import bot, LOGGER, _open, emby_line, sakura_b, ranks, config, group, extra_emby_libs, emby_block, manga_url
from pyrogram import filters
from bot.func_helper.emby import emby
from bot.func_helper.manga import manga
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.utils import members_info, tem_alluser, wh_msg
from bot.func_helper.fix_bottons import members_ikb, back_members_ikb, re_create_ikb, del_me_ikb, re_delme_ikb, \
    re_reset_ikb, re_changetg_ikb, emby_block_ikb, user_emby_block_ikb, user_emby_unblock_ikb, re_exchange_b_ikb, \
    store_ikb, re_store_renew, re_bindtg_ikb, manga_ikb, back_manga_ikb, re_create_manga_ikb, re_delme_manga_ikb, \
    del_me_manga_ikb, re_reset_manga_ikb
from bot.func_helper.msg_utils import callAnswer, editMessage, callListen, sendMessage
from bot.modules.commands.exchange import rgs_code
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby, sql_delete_emby, sql_change_emby_tg
from bot.sql_helper.sql_emby2 import sql_get_emby2, sql_delete_emby2
from bot.sql_helper.sql_manga import Manga, sql_add_manga, sql_delete_manga, sql_update_manga_password, sql_get_manga


# 创号函数
async def create_user(_, call, us, stats):
    same = await editMessage(call,
                             text='🤖**注意：您已进入注册状态:\n\n• 请在2min内输入 `[用户名][空格][安全码]`\n• 举个例子🌰：`苏苏 1234`**\n\n• 用户名中不限制中/英文/emoji，🚫**特殊字符**'
                                  '\n• 安全码为敏感操作时附加验证，请填入最熟悉的数字4~6位；退出请点 /cancel')
    if same is False:
        return

    txt = await callListen(call, 120, buttons=back_members_ikb)
    if isinstance(txt, bool):
        return

    elif txt.text == '/cancel':
        return await asyncio.gather(txt.delete(),
                                    editMessage(call, '__您已经取消输入__ **会话已结束！**', back_members_ikb))
    else:
        try:
            await txt.delete()
            emby_name, emby_pwd2 = txt.text.split()
        except (IndexError, ValueError):
            await editMessage(call, f'⚠️ 输入格式错误\n【`{txt.text}`】\n **会话已结束！**', re_create_ikb)
        else:
            await editMessage(call,
                              f'🆗 会话结束，收到设置\n\n用户名：**{emby_name}**  安全码：**{emby_pwd2}** \n\n__正在为您初始化账户，更新用户策略__......')
            try:
                x = int(emby_name)
            except ValueError:
                pass
            else:
                try:
                    await bot.get_chat(x)
                except BadRequest:
                    pass
                else:
                    return await editMessage(call, "🚫 根据银河正义法，您创建的用户名不得与任何 tg_id 相同",
                                             re_create_ikb)
            await asyncio.sleep(1)

            # emby api操作
            pwd1 = await emby.emby_create(call.from_user.id, emby_name, emby_pwd2, us, stats)
            if pwd1 == 403:
                await editMessage(call, '**🚫 很抱歉，注册总数已达限制。**', back_members_ikb)
            elif pwd1 == 100:
                await editMessage(call,
                                  '**- ❎ 已有此账户名，请重新输入注册\n- ❎ 或检查有无特殊字符\n- ❎ 或emby服务器连接不通，会话已结束！**',
                                  re_create_ikb)
                LOGGER.error("【创建账户】：重复账户 or 未知错误！")
            else:
                await editMessage(call,
                                  f'**▎创建用户成功🎉**\n\n'
                                  f'· 用户名称 | `{emby_name}`\n'
                                  f'· 用户密码 | `{pwd1[0]}`\n'
                                  f'· 安全密码 | `{emby_pwd2}`（仅发送一次）\n'
                                  f'· 到期时间 | `{pwd1[1]}`\n'
                                  f'· 当前线路：\n'
                                  f'{emby_line}\n\n'
                                  f'**·【服务器】 - 查看线路和密码**')
                if stats == 'y':
                    LOGGER.info(f"【创建账户】[开注状态]：{call.from_user.id} - 建立了 {emby_name} ")
                elif stats == 'n':
                    LOGGER.info(f"【创建账户】：{call.from_user.id} - 建立了 {emby_name} ")
                await tem_alluser()


# 键盘中转
@bot.on_callback_query(filters.regex('members') & user_in_group_on_filter)
async def members(_, call):
    data = await members_info(tg=call.from_user.id)
    if not data:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)

    await callAnswer(call, f"✅ 用户界面")
    name, lv, ex, us, embyid, pwd2 = data
    text = f"▎__欢迎进入用户面板！{call.from_user.first_name}__\n\n" \
           f"**· 🆔 用户ID** | `{call.from_user.id}`\n" \
           f"**· 📊 当前状态** | {lv}\n" \
           f"**· 🍒 积分{sakura_b}** | {us[0]} · {us[1]}\n" \
           f"**· 💠 账号名称** | [{name}](tg://user?id={call.from_user.id})\n" \
           f"**· 🚨 到期时间** | {ex}"
    if not embyid:
        await editMessage(call, text, members_ikb(False))
    else:
        await editMessage(call, text, members_ikb(True))


# 创建账户
@bot.on_callback_query(filters.regex('create') & user_in_group_on_filter)
async def create(_, call):
    e = sql_get_emby(tg=call.from_user.id)
    if not e:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)

    if e.embyid:
        await callAnswer(call, '💦 你已经有账户啦！请勿重复注册。', True)
    elif not _open["stat"] and int(e.us) <= 0:
        await callAnswer(call, f'🤖 自助注册已关闭，等待开启。', True)
    elif not _open["stat"] and int(e.us) > 0:
        send = await callAnswer(call, f'🪙 积分满足要求，请稍后。', True)
        if send is False:
            return
        else:
            await create_user(_, call, us=e.us, stats='n')
    elif _open["stat"]:
        send = await callAnswer(call, f"🪙 开放注册，免除积分要求。", True)
        if send is False:
            return
        else:
            await create_user(_, call, us=65535, stats='y')


# 换绑tg
@bot.on_callback_query(filters.regex('changetg') & user_in_group_on_filter)
async def change_tg(_, call):
    d = sql_get_emby(tg=call.from_user.id)
    if not d:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    if d.embyid:
        return await callAnswer(call, '⚖️ 您已经拥有账户，请不要钻空子', True)

    await callAnswer(call, '⚖️ 更换绑定的TG')
    send = await editMessage(call,
                             '🔰 **【更换绑定emby的tg】**\n'
                             '须知：\n'
                             '- **请确保您之前用其他tg账户注册过**\n'
                             '- **请确保您注册的其他tg账户呈已注销状态**\n'
                             '- **请确保输入正确的emby用户名，安全码/密码**\n\n'
                             '您有120s回复 `[emby用户名] [安全码/密码]`\n例如 `苏苏 5210` ，若密码为空则填写“None”，退出点 /cancel')
    if send is False:
        return

    m = await callListen(call, 120, buttons=back_members_ikb)
    if isinstance(m, bool):
        return

    elif m.text == '/cancel':
        await m.delete()
        await editMessage(call, '__您已经取消输入__ **会话已结束！**', back_members_ikb)
    else:
        try:
            await m.delete()
            emby_name, emby_pwd = m.text.split()
        except (IndexError, ValueError):
            return await editMessage(call, f'⚠️ 输入格式错误\n【`{m.text}`】\n **会话已结束！**', re_changetg_ikb)

        await editMessage(call,
                          f'✔️ 会话结束，收到设置\n\n用户名：**{emby_name}** 正在检查码 **{emby_pwd}**......')

        pwd = '空（直接回车）', 5210 if emby_pwd == 'None' else emby_pwd, emby_pwd
        e = sql_get_emby(tg=emby_name)
        if e is None:
            # 在emby2中，验证安全码 或者密码
            e2 = sql_get_emby2(name=emby_name)
            if e2 is None:
                return await editMessage(call, f'❓ 未查询到bot数据中名为 {emby_name} 的账户，请使用 **绑定TG** 功能。',
                                         buttons=re_bindtg_ikb)
            if emby_pwd != e2.pwd2:
                success, embyid = await emby.authority_account(call.from_user.id, emby_name, emby_pwd)
                if not success:
                    return await editMessage(call,
                                             f'💢 安全码or密码验证错误，请检查输入\n{emby_name} {emby_pwd} 是否正确。',
                                             buttons=re_changetg_ikb)
                sql_update_emby(Emby.tg == call.from_user.id, embyid=embyid, name=e2.name, pwd=emby_pwd,
                                pwd2=e2.pwd2, lv=e2.lv, cr=e2.cr, ex=e2.ex)
                sql_delete_emby2(embyid=e2.embyid)
                text = f'⭕ 账户 {emby_name} 的密码验证成功！\n\n' \
                       f'· 用户名称 | `{emby_name}`\n' \
                       f'· 用户密码 | `{pwd[0]}`\n' \
                       f'· 安全密码 | `{e2.pwd2}`（仅发送一次）\n' \
                       f'· 到期时间 | `{e2.ex}`\n\n' \
                       f'· 当前线路：\n{emby_line}\n\n' \
                       f'**·在【服务器】按钮 - 查看线路和密码**'
                await sendMessage(call,
                                  f'⭕#TG改绑 原emby账户 #{emby_name}\n\n'
                                  f'从emby2表绑定至 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) - {call.from_user.id}',
                                  send=True)
                LOGGER.info(f'【TG改绑】 emby账户 {emby_name} 绑定至 {call.from_user.first_name}-{call.from_user.id}')
                await editMessage(call, text)

            elif emby_pwd == e2.pwd2:
                text = f'⭕ 账户 {emby_name} 的安全码验证成功！\n\n' \
                       f'· 用户名称 | `{emby_name}`\n' \
                       f'· 用户密码 | `{e2.pwd}`\n' \
                       f'· 安全密码 | `{pwd[1]}`（仅发送一次）\n' \
                       f'· 到期时间 | `{e2.ex}`\n\n' \
                       f'· 当前线路：\n{emby_line}\n\n' \
                       f'**·在【服务器】按钮 - 查看线路和密码**'
                sql_update_emby(Emby.tg == call.from_user.id, embyid=e2.embyid, name=e2.name, pwd=e2.pwd,
                                pwd2=emby_pwd, lv=e2.lv, cr=e2.cr, ex=e2.ex)
                sql_delete_emby2(embyid=e2.embyid)
                await sendMessage(call,
                                  f'⭕#TG改绑 原emby账户 #{emby_name}\n\n'
                                  f'从emby2表绑定至 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) - {call.from_user.id}',
                                  send=True)
                LOGGER.info(f'【TG改绑】 emby账户 {emby_name} 绑定至 {call.from_user.first_name}-{call.from_user.id}')
                await editMessage(call, text)

        else:
            if emby_pwd != e.pwd2:
                success, embyid = await emby.authority_account(call.from_user.id, emby_name, emby_pwd)
                if not success:
                    return await editMessage(call,
                                             f'💢 安全码or密码验证错误，请检查输入\n{emby_name} {emby_pwd} 是否正确。',
                                             buttons=re_changetg_ikb)
                text = f'⭕ 账户 {emby_name} 的密码验证成功！\n\n' \
                       f'· 用户名称 | `{emby_name}`\n' \
                       f'· 用户密码 | `{pwd[0]}`\n' \
                       f'· 安全密码 | `{e.pwd2}`（仅发送一次）\n' \
                       f'· 到期时间 | `{e.ex}`\n\n' \
                       f'· 当前线路：\n{emby_line}\n\n' \
                       f'**·在【服务器】按钮 - 查看线路和密码**'
            elif emby_pwd == e.pwd2:
                text = f'⭕ 账户 {emby_name} 的安全码验证成功！\n\n' \
                       f'· 用户名称 | `{emby_name}`\n' \
                       f'· 用户密码 | `{e.pwd}`\n' \
                       f'· 安全密码 | `{pwd[1]}`（仅发送一次）\n' \
                       f'· 到期时间 | `{e.ex}`\n\n' \
                       f'· 当前线路：\n{emby_line}\n\n' \
                       f'**·在【服务器】按钮 - 查看线路和密码**'

            f = await bot.get_users(user_ids=e.tg)
            if not f.is_deleted:
                await sendMessage(call,
                                  f'⭕#TG改绑 **用户 [{call.from_user.id}](tg://user?id={call.from_user.id}) 正在试图改绑一个状态正常的[tg用户](tg://user?id={e.tg}) - {e.name}\n\n请管理员检查。**',
                                  send=True)
                return await editMessage(call,
                                         f'⚠️ **你所要换绑的[tg](tg://user?id={e.tg}) - {e.tg}\n\n用户状态正常！无须换绑。**',
                                         buttons=back_members_ikb)

            if not e.embyid or not call.from_user.id:
                LOGGER.error(f"【TG改绑】 emby账户{emby_name} 换绑错误: embyid或者对话中tgid不存在")
                return await editMessage(call, "🍰 **【TG改绑】数据库处理出错，请联系管理！**", back_members_ikb)

            result, msg = sql_change_emby_tg(embyid=e.embyid, new_tg=call.from_user.id)
            if not result:
                await editMessage(call, "🍰 **【TG改绑】数据库处理出错，请联系管理！**", back_members_ikb)
                LOGGER.error(f"【TG改绑】 emby账户{emby_name} 换绑错误: {msg}")
            else:
                await sendMessage(call,
                                  f'⭕#TG改绑 原emby账户 #{emby_name} \n\n已绑定至 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) - {call.from_user.id}',
                                  send=True)
                LOGGER.info(
                    f'【TG改绑】 emby账户 {emby_name} 绑定至 {call.from_user.first_name}-{call.from_user.id}')
                await editMessage(call, text)


@bot.on_callback_query(filters.regex('bindtg') & user_in_group_on_filter)
async def bind_tg(_, call):
    d = sql_get_emby(tg=call.from_user.id)
    if d.embyid is not None:
        return await callAnswer(call, '⚖️ 您已经拥有账户，请不要钻空子', True)
    await callAnswer(call, '⚖️ 将账户绑定TG')
    send = await editMessage(call,
                             '🔰 **【已有emby绑定至tg】**\n'
                             '须知：\n'
                             '- **请确保您需绑定的账户不在bot中**\n'
                             '- **请确保您不是恶意绑定他人的账户**\n'
                             '- **请确保输入正确的emby用户名，密码**\n\n'
                             '您有120s回复 `[emby用户名] [密码]`\n例如 `苏苏 5210` ，若密码为空则填写“None”，退出点 /cancel')
    if send is False:
        return

    m = await callListen(call, 120, buttons=back_members_ikb)
    if isinstance(m, bool):
        return

    elif m.text == '/cancel':
        await m.delete()
        await editMessage(call, '__您已经取消输入__ **会话已结束！**', back_members_ikb)
    else:
        try:
            await m.delete()
            emby_name, emby_pwd = m.text.split()
        except (IndexError, ValueError):
            return await editMessage(call, f'⚠️ 输入格式错误\n【`{m.text}`】\n **会话已结束！**', re_bindtg_ikb)
        await editMessage(call,
                          f'✔️ 会话结束，收到设置\n\n用户名：**{emby_name}** 正在检查密码 **{emby_pwd}**......')
        e = sql_get_emby(tg=emby_name)
        if e is None:
            e2 = sql_get_emby2(name=emby_name)
            if e2 is None:
                success, embyid = await emby.authority_account(call.from_user.id, emby_name, emby_pwd)
                if not success:
                    return await editMessage(call,
                                             f'🍥 很遗憾绑定失败，您输入的账户密码不符（{emby_name} - {emby_pwd}），请仔细确认后再次尝试',
                                             buttons=re_bindtg_ikb)
                else:
                    pwd = '空（直接回车）', 5210 if emby_pwd == 'None' else emby_pwd, emby_pwd
                    ex = (datetime.now() + timedelta(days=30))
                    text = f'✅ 账户 {emby_name} 成功绑定\n\n' \
                           f'· 用户名称 | `{emby_name}`\n' \
                           f'· 用户密码 | `{pwd[0]}`\n' \
                           f'· 安全密码 | `{pwd[1]}`（仅发送一次）\n' \
                           f'· 到期时间 | `{ex}`\n\n' \
                           f'· 当前线路：\n{emby_line}\n\n' \
                           f'· **在【服务器】按钮 - 查看线路和密码**'
                    sql_update_emby(Emby.tg == call.from_user.id, embyid=embyid, name=emby_name, pwd=emby_pwd,
                                    pwd2=emby_pwd, lv='b', cr=datetime.now(), ex=ex)
                    await editMessage(call, text)
                    await sendMessage(call,
                                      f'⭕#新TG绑定 原emby账户 #{emby_name} \n\n已绑定至 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) - {call.from_user.id}',
                                      send=True)
                    LOGGER.info(
                        f'【新TG绑定】 emby账户 {emby_name} 绑定至 {call.from_user.first_name}-{call.from_user.id}')
            else:
                await editMessage(call, '🔍 数据库已有此账户，不可绑定，请使用 **换绑TG**', buttons=re_changetg_ikb)
        else:
            await editMessage(call, '🔍 数据库已有此账户，不可绑定，请使用 **换绑TG**', buttons=re_changetg_ikb)


# kill yourself
@bot.on_callback_query(filters.regex('delme') & user_in_group_on_filter)
async def del_me(_, call):
    e = sql_get_emby(tg=call.from_user.id)
    if e is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    else:
        if e.embyid is None:
            return await callAnswer(call, '未查询到账户，不许乱点！💢', True)
        await callAnswer(call, "🔴 请先进行 安全码 验证")
        edt = await editMessage(call, '**🔰账户安全验证**：\n\n👮🏻验证是否本人进行敏感操作，请对我发送您设置的安全码。倒计时 120s\n'
                                      '🛑 **停止请点 /cancel**')
        if edt is False:
            return

        m = await callListen(call, 120)
        if isinstance(m, bool):
            return

        elif m.text == '/cancel':
            await m.delete()
            await editMessage(call, '__您已经取消输入__ **会话已结束！**', buttons=back_members_ikb)
        else:
            if m.text == e.pwd2:
                await m.delete()
                await editMessage(call, '**⚠️ 如果您的账户到期，我们将封存您的账户，但仍保留数据'
                                        '而如果您选择删除，这意味着服务器会将您此前的活动数据全部删除。\n**',
                                  buttons=del_me_ikb(e.embyid))
            else:
                await m.delete()
                await editMessage(call, '**💢 验证不通过，安全码错误。**', re_delme_ikb)


@bot.on_callback_query(filters.regex('delemby') & user_in_group_on_filter)
async def del_emby(_, call):
    send = await callAnswer(call, "🎯 get，正在删除ing。。。")
    if send is False:
        return

    embyid = call.data.split('-')[1]
    if await emby.emby_del(embyid):
        send1 = await editMessage(call, '🗑️ 好了，已经为您删除...\n愿来日各自安好，山高水长，我们有缘再见！',
                                  buttons=back_members_ikb)
        if send1 is False:
            return

        LOGGER.info(f"【删除账号】：{call.from_user.id} 已删除！")
    else:
        await editMessage(call, '🥧 蛋糕辣~ 好像哪里出问题了，请向管理反应', buttons=back_members_ikb)
        LOGGER.error(f"【删除账号】：{call.from_user.id} 失败！")


# 重置密码为空密码
@bot.on_callback_query(filters.regex('reset') & user_in_group_on_filter)
async def reset(_, call):
    e = sql_get_emby(tg=call.from_user.id)
    if e is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    if e.embyid is None:
        return await bot.answer_callback_query(call.id, '未查询到账户，不许乱点！💢', show_alert=True)
    else:
        await callAnswer(call, "🔴 请先进行 安全码 验证")
        send = await editMessage(call, '**🔰账户安全验证**：\n\n 👮🏻验证是否本人进行敏感操作，请对我发送您设置的安全码。倒计时 120 s\n'
                                       '🛑 **停止请点 /cancel**')
        if send is False:
            return

        m = await callListen(call, 120, buttons=back_members_ikb)
        if isinstance(m, bool):
            return

        elif m.text == '/cancel':
            await m.delete()
            await editMessage(call, '__您已经取消输入__ **会话已结束！**', buttons=back_members_ikb)
        else:
            if m.text != e.pwd2:
                await m.delete()
                await editMessage(call, f'**💢 验证不通过，{m.text} 安全码错误。**', buttons=re_reset_ikb)
            else:
                await m.delete()
                await editMessage(call, '🎯 请在 120s内 输入你要更新的密码,不限制中英文，emoji。特殊字符部分支持，其他概不负责。\n\n'
                                        '点击 /cancel 将重置为空密码并退出。 无更改退出状态请等待120s')
                mima = await callListen(call, 120, buttons=back_members_ikb)
                if isinstance(mima, bool):
                    return

                elif mima.text == '/cancel':
                    await mima.delete()
                    await editMessage(call, '**🎯 收到，正在重置ing。。。**')
                    if await emby.emby_reset(id=e.embyid) is True:
                        await editMessage(call, '🕶️ 操作完成！已为您重置密码为 空。', buttons=back_members_ikb)
                        LOGGER.info(f"【重置密码】：{call.from_user.id} 成功重置了空密码！")
                    else:
                        await editMessage(call, '🫥 重置密码操作失败！请联系管理员。')
                        LOGGER.error(f"【重置密码】：{call.from_user.id} 重置密码失败 ！")

                else:
                    await mima.delete()
                    await editMessage(call, '**🎯 收到，正在重置ing。。。**')
                    if await emby.emby_reset(id=e.embyid, new=mima.text) is True:
                        await editMessage(call, f'🕶️ 操作完成！已为您重置密码为 `{mima.text}`。',
                                          buttons=back_members_ikb)
                        LOGGER.info(f"【重置密码】：{call.from_user.id} 成功重置了密码为 {mima.text} ！")
                    else:
                        await editMessage(call, '🫥 操作失败！请联系管理员。', buttons=back_members_ikb)
                        LOGGER.error(f"【重置密码】：{call.from_user.id} 重置密码失败 ！")


# 显示/隐藏某些库
@bot.on_callback_query(filters.regex('embyblock') & user_in_group_on_filter)
async def embyblock(_, call):
    data = sql_get_emby(tg=call.from_user.id)
    if data is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    if data.embyid is None:
        return await callAnswer(call, '❓ 未查询到账户，不许乱点!', True)
    elif data.lv == "c":
        return await callAnswer(call, '💢 账户到期，封禁中无法使用！', True)
    elif len(config["emby_block"]) == 0:
        send = await editMessage(call, '⭕ 管理员未设置。。。 快催催\no(*////▽////*)q', buttons=back_members_ikb)
        if send is False:
            return
    else:
        success, rep = emby.user(embyid=data.embyid)
        try:
            if success is False:
                stat = '💨 未知'
            else:
                blocks = rep["Policy"]["BlockedMediaFolders"]
                if set(config["emby_block"]).issubset(set(blocks)):
                    stat = '🔴 隐藏'
                else:
                    stat = '🟢 显示'
        except KeyError:
            stat = '💨 未知'
        await asyncio.gather(callAnswer(call, "✅ 到位"),
                             editMessage(call,
                                         f'🤺 用户状态：{stat}\n🎬 目前设定的库为: \n**{config["emby_block"]}**\n请选择你的操作。',
                                         buttons=emby_block_ikb(data.embyid)))


# 隐藏
@bot.on_callback_query(filters.regex('emby_block') & user_in_group_on_filter)
async def user_emby_block(_, call):
    embyid = call.data.split('-')[1]
    send = await callAnswer(call, f'🎬 正在为您关闭显示ing')
    if send is False:
        return
    success, rep = emby.user(embyid=embyid)
    currentblock = []
    if success:
        try:
            currentblock = list(set(rep["Policy"]["BlockedMediaFolders"] + emby_block + ['播放列表']))
        except KeyError:
            currentblock = ['播放列表'] + extra_emby_libs + emby_block
        re = await emby.emby_block(embyid, 0, block=currentblock)
        if re is True:
            send1 = await editMessage(call, f'🕶️ ο(=•ω＜=)ρ⌒☆\n 小尾巴隐藏好了！ ', buttons=user_emby_block_ikb)
            if send1 is False:
                return
        else:
            await editMessage(call, f'🕶️ Error!\n 隐藏失败，请上报管理检查)', buttons=back_members_ikb)


# 显示
@bot.on_callback_query(filters.regex('emby_unblock') & user_in_group_on_filter)
async def user_emby_unblock(_, call):
    embyid = call.data.split('-')[1]
    send = await callAnswer(call, f'🎬 正在为您开启显示ing')
    if send is False:
        return
    success, rep = emby.user(embyid=embyid)
    currentblock = []
    if success:
        try:
            currentblock = list(set(rep["Policy"]["BlockedMediaFolders"] + ['播放列表']))
            # 保留不同的元素
            currentblock = [x for x in currentblock if x not in emby_block] + [x for x in emby_block if
                                                                               x not in currentblock]
        except KeyError:
            currentblock = ['播放列表'] + extra_emby_libs
        re = await emby.emby_block(embyid, 0, block=currentblock)
        if re is True:
            # await embyblock(_, call)
            send1 = await editMessage(call, f'🕶️ ┭┮﹏┭┮\n 小尾巴被抓住辽！ ', buttons=user_emby_unblock_ikb)
            if send1 is False:
                return
        else:
            await editMessage(call, f'🎬 Error!\n 显示失败，请上报管理检查设置', buttons=back_members_ikb)


@bot.on_callback_query(filters.regex('exchange') & user_in_group_on_filter)
async def call_exchange(_, call):
    await callAnswer(call, '🔋 使用注册码')
    send = await editMessage(call,
                             '🔋 **【使用注册码】**：\n\n'
                             f'- 请在120s内对我发送你的注册码，形如\n`{ranks["logo"]}-xx-xxxx`\n退出点 /cancel')
    if send is False:
        return

    msg = await callListen(call, 120, buttons=re_exchange_b_ikb)
    if isinstance(msg, bool):
        return
    elif msg.text == '/cancel':
        await msg.delete()
        await editMessage(call, '__您已经取消输入__ **会话已结束！**', re_exchange_b_ikb)
    else:
        await editMessage(call, f'验证注册码 {msg.text} ing。。。')
        await rgs_code(_, msg)


@bot.on_callback_query(filters.regex('storeall') & user_in_group_on_filter)
async def do_store(_, call):
    await callAnswer(call, '✔️ 欢迎进入兑换商店')
    # e = sql_get_emby(tg=call.from_user.id)
    await editMessage(call, '🏪 请选择想要使用的服务', buttons=store_ikb())


@bot.on_callback_query(filters.regex('store-renew') & user_in_group_on_filter)
async def do_store_renew(_, call):
    if _open["exchange"]:
        await callAnswer(call, '✔️ 进入兑换时长')
        e = sql_get_emby(tg=call.from_user.id)
        if e is None:
            return
        if e.iv < 60:
            return await editMessage(call,
                                     f'**🏪 兑换规则：**\n当前兑换为 2{sakura_b} / 一天，**兑换者所持有积分不得低于60**，当前仅：{e.iv}，请好好努力。',
                                     buttons=back_members_ikb)

        await editMessage(call,
                          f'🏪 您已满足基础{sakura_b}要求，请回复您需要兑换的时长，当前兑换为 2{sakura_b} / 一天，退出请 /cancel')
        m = await callListen(call, 120, buttons=re_store_renew)
        if isinstance(m, bool):
            return

        elif m.text == '/cancel':
            await m.delete()
            await do_store(_, call)
        else:
            try:
                await m.delete()
                iv = int(m.text)
            except KeyError:
                await editMessage(call, f'❌ 请不要调戏bot，输入一个整数！！！', buttons=re_store_renew)
            else:
                new_us = e.iv - iv
                if new_us < 0:
                    sql_update_emby(Emby.tg == call.from_user.id, iv=e.iv - 10)
                    return await editMessage(call, f'🫡，西内！输入值超出你持有的{e.iv}{sakura_b}，倒扣10。')
                new_ex = e.ex + timedelta(days=iv / 2)
                sql_update_emby(Emby.tg == call.from_user.id, ex=new_ex, iv=new_us)
                await emby.emby_change_policy(id=e.embyid)
                await editMessage(call, f'🎉 您已花费 {iv}{sakura_b}\n🌏 到期时间 **{new_ex}**')
                LOGGER.info(f'【兑换续期】- {call.from_user.id} 已花费 {iv}{sakura_b}，到期时间：{new_ex}')
    else:
        await callAnswer(call, '❌ 管理员未开启此兑换', True)


@bot.on_callback_query(filters.regex('store-whitelist') & user_in_group_on_filter)
async def do_store_whitelist(_, call):
    if _open["whitelist"]:
        e = sql_get_emby(tg=call.from_user.id)
        if e is None:
            return
        if e.iv < 9999 or e.lv == 'a':
            return await callAnswer(call,
                                    f'🏪 兑换规则：\n当前兑换白名单需要 9999 {sakura_b}，已有白名单无法再次消费。勉励',
                                    True)
        await callAnswer(call, f'🏪 您已满足 9999 {sakura_b}要求', True)
        sql_update_emby(Emby.tg == call.from_user.id, lv='a', iv=e.iv - 9999)
        send = await call.message.edit(f'**{random.choice(wh_msg)}**\n\n'
                                       f'🎉 恭喜[{call.from_user.first_name}](tg://user?id={call.from_user.id}) 今日晋升，{ranks["logo"]}白名单')
        await send.forward(group[0])
        LOGGER.info(f'【兑换白名单】- {call.from_user.id} 已花费 9999{sakura_b}，晋升白名单')
    else:
        await callAnswer(call, '❌ 管理员未开启此兑换', True)


@bot.on_callback_query(filters.regex('store-invite') & user_in_group_on_filter)
async def do_store_invite(_, call):
    await callAnswer(call, '❌ 管理员未开启此兑换，等待编写', True)


@bot.on_callback_query(filters.regex('store-query') & user_in_group_on_filter)
async def do_store_query(_, call):
    await callAnswer(call, '❌ 管理员未开启此兑换，等待编写', True)


@bot.on_callback_query(filters.regex('manga') & user_in_group_on_filter)
async def manga(_, call):
    emby = sql_get_emby(tg=call.from_user.id)
    manga_info = None
    if emby and emby.embyid:
        manga_info = sql_get_manga(embyid=emby.embyid)

    await callAnswer(call, f"✅ 漫画自助服务界面")
    text = f"▎__欢迎进入漫画自助服务面板！{call.from_user.first_name}__\n\n" \
           f"**· 🆔 用户ID** | `{call.from_user.id}`\n" \
           f"**· 🍒 Emby** | `{emby.name}`\n" \
           f"**· 💠 账号** | `{manga_info.name}`\n" \
           f"**· 🚨 密码** | `{manga_info.pwd}`"
    await editMessage(call, text, manga_ikb(manga_id=manga_info.manga_id))


@bot.on_callback_query(filters.regex('manga_create') & user_in_group_on_filter)
async def manga_create(_, call):
    emby_info = sql_get_emby(tg=call.from_user.id)
    if not emby_info:
        return await callAnswer(call, '⚠️ 数据库没有你，请先创建Emby账号', True)

    manga_info = sql_get_manga(embyid=emby_info.embyid)
    if manga_info.manga_id:
        await callAnswer(call, '💦 你已经有账户啦！请勿重复注册。', True)
    else:
        await create_manga_user(_, call, emby_info.embyid)


async def create_manga_user(_, call, embyid):
    same = await editMessage(call,
                             text='🤖**注意：您已进入注册状态:\n\n• 请在2min内输入 `[邮箱][空格][密码]`\n• 举个例子🌰：`test@qq.com 123456`**\n\n• '
                                  '\n• 邮箱不要求真实邮箱，只是作为登录使用，不与其他用户重复即可；退出请点 /cancel')
    if same is False:
        return

    txt = await callListen(call, 120, buttons=back_manga_ikb)
    if isinstance(txt, bool):
        return

    elif txt.text == '/cancel':
        return await asyncio.gather(txt.delete(),
                                    editMessage(call, '__您已经取消输入__ **会话已结束！**', back_manga_ikb))
    else:
        try:
            await txt.delete()
            manga_email, manga_pwd = txt.text.split()
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            match = re.match(pattern, manga_email)
            if not match:
                await editMessage(call, f'⚠️ 输入用户名格式错误\n【`{manga_email}`】\n **会话已结束！**', re_create_ikb)
        except (IndexError, ValueError):
            await editMessage(call, f'⚠️ 输入格式错误\n【`{txt.text}`】\n **会话已结束！**', re_create_ikb)
        else:
            await editMessage(call,
                              f'🆗 会话结束，收到设置\n\n用户名：**{manga_email}**  密码：**{manga_pwd}** \n\n__正在为您初始化账户_......')
            await asyncio.sleep(1)

            # manga api操作
            manga_info = await manga.manga_create(embyid=embyid, email=manga_email, pwd=manga_pwd)
            if isinstance(manga_info, Manga) and manga_info:
                await editMessage(call,
                                  f'**▎创建用户成功🎉**\n\n'
                                  f'· 账号 | `{manga_email}`\n'
                                  f'· 密码 | `{manga_pwd}`\n'
                                  f'· 当前线路：\n'
                                  f'{manga_url}\n\n'
                                  f'**·【服务器】 - 查看线路和密码**')
                LOGGER.info(f"【创建漫画服账户】：{call.from_user.id} - 建立了 {manga_email} ")
            elif isinstance(manga_info, int) and manga_info == 403:
                await editMessage(call, '**🚫 很抱歉，该用户名已经被使用。**', back_manga_ikb)
            else:
                await editMessage(call, '**- ❎ emby服务器连接不通，会话已结束！**', re_create_manga_ikb)


@bot.on_callback_query(filters.regex('manga_delme') & user_in_group_on_filter)
async def manga_delme(_, call):
    emby_info = sql_get_emby(tg=call.from_user.id)
    if emby_info is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请先创建Emby账号', True)

    manga_info = sql_get_manga(embyid=emby_info.embyid)
    if not manga_info or not manga_info.manga_id:
        return await callAnswer(call, '未查询到账户，不许乱点！💢', True)

    edt = await editMessage(call, '**🔰账户安全验证**：\n\n👮🏻验证是否本人进行敏感操作，请对我发送您设置的漫画服密码。倒计时 120s\n'
                                  '🛑 **停止请点 /cancel**')
    if edt is False:
        return

    m = await callListen(call, 120)
    if isinstance(m, bool):
        return
    elif m.text == '/cancel':
        await m.delete()
        await editMessage(call, '__您已经取消输入__ **会话已结束！**', buttons=back_manga_ikb)
    else:
        if m.text == manga_info.pwd:
            await editMessage(call, '**⚠️ 删除漫画服账号将会丢失所有活动记录。\n**',
                              buttons=del_me_manga_ikb(manga_info.manga_id))
        else:
            await m.delete()
            await editMessage(call, '**💢 验证不通过，漫画服密码与服务器保存的密码不匹配。**', re_delme_manga_ikb)


@bot.on_callback_query(filters.regex('delmanga') & user_in_group_on_filter)
async def delmanga(_, call):
    send = await callAnswer(call, "🎯 get，正在删除ing。。。")
    if send is False:
        return

    manga_id = call.data.split('-')[1]
    if await manga.manga_del(manga_id):
        send1 = await editMessage(call, '🗑️ 好了，已经为您删除...\n愿来日各自安好，山高水长，我们有缘再见！',
                                  buttons=back_manga_ikb)
        if send1 is False:
            return

        LOGGER.info(f"【删除漫画服账号】：{call.from_user.id} 已删除！")
    else:
        await editMessage(call, '🥧 蛋糕辣~ 好像哪里出问题了，请向管理反应', buttons=back_manga_ikb)
        LOGGER.error(f"【删除漫画服账号】：{call.from_user.id} 失败！")


@bot.on_callback_query(filters.regex('manga_reset') & user_in_group_on_filter)
async def manga_reset(_, call):
    emby_info = sql_get_emby(tg=call.from_user.id)
    if emby_info is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请先创建Emby账号', True)

    manga_info = sql_get_manga(embyid=emby_info.embyid)
    if not manga_info or not manga_info.manga_id:
        return await callAnswer(call, '未查询到账户，不许乱点！💢', True)
    else:
        await callAnswer(call, "🔴 请先进行 原密码 验证")
        send = await editMessage(call, '**🔰账户安全验证**：\n\n 👮🏻验证是否本人进行敏感操作，请对我发送您上次设置的密码。倒计时 120 s\n'
                                       '🛑 **停止请点 /cancel**')
        if send is False:
            return

        m = await callListen(call, 120, buttons=back_manga_ikb)
        if isinstance(m, bool):
            return

        elif m.text == '/cancel':
            await m.delete()
            await editMessage(call, '__您已经取消输入__ **会话已结束！**', buttons=back_manga_ikb)
        else:
            if m.text != manga_info.pwd:
                await m.delete()
                await editMessage(call, f'**💢 验证不通过，{m.text} 旧密码错误。**', buttons=re_reset_manga_ikb)
            else:
                await m.delete()
                await editMessage(call, '🎯 请在 120s内 输入你要更新的密码, 仅支持英文字母和数字的组合。\n\n'
                                        '点击 /cancel 将重置为123456并退出。 无更改退出状态请等待120s')
                mima = await callListen(call, 120, buttons=back_manga_ikb)
                if isinstance(mima, bool):
                    return

                elif mima.text == '/cancel':
                    await mima.delete()
                    await editMessage(call, '**🎯 收到，正在重置ing。。。**')
                    if await manga.manga_reset(manga_info, '123456') is True:
                        await editMessage(call, '🕶️ 操作完成！已为您重置密码为 123456。', buttons=back_manga_ikb)
                        LOGGER.info(f"【重置漫画服密码】：{call.from_user.id} 成功重置了123456密码！")
                    else:
                        await editMessage(call, '🫥 重置密码操作失败！请联系管理员。')
                        LOGGER.error(f"【重置漫画服密码】：{call.from_user.id} 重置密码失败 ！")

                else:
                    await mima.delete()
                    await editMessage(call, '**🎯 收到，正在重置ing。。。**')
                    if await manga.manga_reset(manga_info, mima.text)  is True:
                        await editMessage(call, f'🕶️ 操作完成！已为您重置密码为 `{mima.text}`。',
                                          buttons=back_manga_ikb)
                        LOGGER.info(f"【重置漫画服密码】：{call.from_user.id} 成功重置了密码为 {mima.text} ！")
                    else:
                        await editMessage(call, '🫥 操作失败！请联系管理员。', buttons=back_manga_ikb)
                        LOGGER.error(f"【重置漫画服密码】：{call.from_user.id} 重置密码失败 ！")