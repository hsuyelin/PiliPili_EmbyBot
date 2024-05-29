import asyncio
import random
from datetime import datetime, timezone, timedelta

from pyrogram import filters

from bot import bot, _open, sakura_b
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.fix_bottons import checkin_button
from bot.func_helper.msg_utils import callAnswer, editMessage, callListen, sendMessage
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby


def generate_random_expression():
    if random.random() < 0.01:
        while True:
            num1 = random.randint(1, 999)
            op = random.choice(['+', '-', '*', '/'])
            if op == '+':
                num2 = 88 - num1
            elif op == '-':
                num2 = num1 - 88
            elif op == '*':
                if num1 == 0 or 88 % num1 != 0:
                    continue
                num2 = 88 // num1
            elif op == '/':
                if num1 == 0 or 88 * num1 > 999:
                    continue
                num2 = num1 * 88
                
            if 1 <= num2 <= 999:
                expression = f"{num1} {op} {num2}"
                return (expression, 88)
            
    while True:
        num1 = random.randint(1, 999)
        num2 = random.randint(1, 999)
        op = random.choice(['+', '-', '*', '/'])
        
        if op == '/':
            if num2 == 0:
                continue
            result = num1 / num2
            if result != int(result):
                continue
            result = int(result)
        else:
            if op == '+':
                result = num1 + num2
            elif op == '-':
                result = num1 - num2
            elif op == '*':
                result = num1 * num2
                
        if 0 <= result <= 1000:
            expression = f"{num1} {op} {num2}"
            return (expression, result)


@bot.on_callback_query(filters.regex('checkin') & user_in_group_on_filter)
async def user_in_checkin(_, call):
    now = datetime.now(timezone(timedelta(hours=8)))
    now_i = now.strftime("%Y-%m-%d")
    if _open["checkin"]:
        e = sql_get_emby(tg=call.from_user.id)
        if e.ch is None or e.ch.strftime("%Y-%m-%d") < now_i:
            expression, result = generate_random_expression()
            reward = 88 if result == 88 else random.randint(6, 18)

            await editMessage(call,
                              f'🎯 **签到说明**：\n\n在120s内发送 {expression} 的值。随机获得6~18 {sakura_b}(概率获得88 {sakura_b})')
            text = await callListen(call, timer=120, buttons=checkin_button)
            if isinstance(text, bool):
                await callAnswer(call, '❌ 发生未知错误，请联系管理员！', True)
                return

            if text.text == str(result):
                iv = e.iv + int(reward)
            else:
                await callAnswer(call, '💢 哥们，你就是九年义务教育的漏网之鱼吧！', True)
                return
                
            sql_update_emby(Emby.tg == call.from_user.id, iv=iv, ch=now)
            await asyncio.gather(call.message.delete(), sendMessage(call,
                                                                    text=f'🎉 **签到成功** | {reward} {sakura_b}\n'
                                                                         f'💴 **当前状态** | {iv} {sakura_b}\n'
                                                                         f'⏳ **签到日期** | {now_i}'))
        else:
            await callAnswer(call, '⭕ 您今天已经签到过了！签到是无聊的活动哦。', True)
    else:
        await callAnswer(call, '❌ 未开启签到系统，等待！', True)
