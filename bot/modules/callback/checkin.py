import asyncio
import random
from datetime import datetime, timezone, timedelta

from pyrogram import filters

from bot import bot, _open, sakura_b
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.fix_bottons import checkin_button
from bot.func_helper.msg_utils import callAnswer, editMessage, callListen, sendMessage
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby


def generate_expression():
    operators = ['+', '-', '*', '/']
    op = random.choice(operators)
    
    if op == '+':
        a = random.randint(0, 100)
        b = random.randint(0, 100 - a)
        expression_str = f"{a} + {b} ="
        result = (a + b, expression_str)
    elif op == '-':
        a = random.randint(0, 100)
        b = random.randint(0, a)
        expression_str = f"{a} - {b} ="
        result = (a - b, expression_str)
    elif op == '*':
        a = random.randint(0, 10)
        b = random.randint(0, 10)
        expression_str = f"{a} * {b} ="
        result = (a * b, expression_str)
    elif op == '/':
        b = random.randint(1, 10)
        a = random.randint(0, 100)
        a = a - (a % b)
        result = (a // b, f"{a} / {b} =")
    
    return result


def simulate_event():
    rand_num = random.randint(1, 40)
    
    if rand_num == 1:
        hit = True
    else:
        hit = False
    
    result_value, expression_str = generate_expression()
    
    return hit, expression_str, result_value


def is_kfc_crazy_thursday():
    return datetime.today().weekday() == 3


@bot.on_callback_query(filters.regex('checkin') & user_in_group_on_filter)
async def user_in_checkin(_, call):
    now = datetime.now(timezone(timedelta(hours=8)))
    now_i = now.strftime("%Y-%m-%d")
    if _open["checkin"]:
        e = sql_get_emby(tg=call.from_user.id)
        if e.ch is None or e.ch.strftime("%Y-%m-%d") < now_i:
            hit, expression_str, result_value = simulate_event()
            expression_str = expression_str.replace('/', '÷')
            is_kfc_day = is_kfc_crazy_thursday()
            reward = random.randint(6, 18)

            await editMessage(call, 
                f'🎯 **签到说明**：\n\n' +
                f'在120s内计算出 {expression_str} ? \n' +
                f'结果正确你将会随机获得6 ~ 18 {sakura_b}(概率获得88 {sakura_b})\n'+
                f'结果错误你将会随机扣除6 ~ 18 {sakura_b}(概率扣除88 {sakura_b}), 请谨慎回答\n\n')
            text = await callListen(call, timer=120, buttons=checkin_button)
            if isinstance(text, bool):
                iv = e.iv - int(reward)
                sql_update_emby(Emby.tg == call.from_user.id, iv=iv, ch=now)
                await callAnswer(call, '❌ 发生未知错误，请联系管理员！', True)
                return

            texts = text.text.split('|')
            textValue = texts[0]
            eggshellValue = texts[1] if len(texts) >= 2 else ""
            isHitEggshell = eggshellValue and eggshellValue == "大哥好帅"
            randomEggshellValue = random.randint(1, 6)
            answer_result = True
            try:
                if int(textValue) == int(result_value):
                    reward = 88 if hit else reward
                    reward = random.randint(18, 68) if is_kfc_day and reward < 88 else reward
                    reward = reward + randomEggshellValue if isHitEggshell else reward
                    iv = e.iv + int(reward)
                else:
                    answer_result = False
                    iv = e.iv - int(reward)
            except Exception as e:
                answer_result = False
                iv = e.iv - int(reward)

            sql_update_emby(Emby.tg == call.from_user.id, iv=iv, ch=now)
            message = ""
            if answer_result:
                message = f'🎉 **签到完成** | 本次签到你获得了 {reward} {sakura_b}\n💴 **当前{sakura_b}余额** | {iv}\n⏳ **签到日期** | {now_i}'

                if is_kfc_day:
                    message = f'🎉 **签到完成** | 本次签到你获得了 {reward} {sakura_b}\n💴 **当前{sakura_b}余额** | {iv}\n⏳ **签到日期** | {now_i} (疯狂星期四)'

                if isHitEggshell:
                    message += f"\n\nPS: 由于你诚实的性格，额外奖励你 {randomEggshellValue} {sakura_b}"
            else:
                message = f'🎉 **签到完成** | 本次签到回答错误，扣除 {reward} {sakura_b}\n💴 **当前{sakura_b}余额** | {iv}\n⏳ **签到日期** | {now_i}'
            await asyncio.gather(call.message.delete(), sendMessage(call, text=message))
        else:
            await callAnswer(call, '⭕ 您今天已经签到过了！签到是无聊的活动哦。', True)
    else:
        await callAnswer(call, '❌ 未开启签到系统，等待！', True)
