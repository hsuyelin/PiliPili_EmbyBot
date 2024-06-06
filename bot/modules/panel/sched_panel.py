import threading
import asyncio
import os
import traceback
import json

from pyrogram import filters
from bot import bot, sakura_b, schedall, save_config, prefixes, _open, owner, LOGGER
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.fix_bottons import sched_buttons
from bot.func_helper.msg_utils import callAnswer, editMessage, deleteMessage
from bot.func_helper.scheduler import Scheduler
from bot.modules.schedme import *

# 实例化
scheduler = Scheduler()

# 开机检查重启
timer = threading.Timer(1, check_restart)
timer.start()  # 重启

# 初始化命令
loop = asyncio.get_event_loop()
loop.call_later(5, lambda: loop.create_task(BotCommands.set_commands(client=bot)))

# 启动定时任务
auto_backup_db = DbBackupUtils.auto_backup_db


async def user_day_plays(): await Uplaysinfo.user_plays_rank(days=1)


async def user_week_plays(): await Uplaysinfo.user_plays_rank(days=7)


async def user_total_plays(): await Uplaysinfo.user_plays_rank(days=65535)


async def user_total_coins(): await Uplaysinfo.user_coins_rank(num=10)


# 写优雅点
# 字典，method相应的操作函数
action_dict = {
    "dayrank": day_ranks,
    "weekrank": week_ranks,
    "dayplayrank": user_day_plays,
    "weekplayrank": user_week_plays,
    "totalplayrank": user_total_plays,
    "totalcoinsrank": user_total_coins,
    # "check_ex": check_expired,
    # "low_activity": check_low_activity,
    "backup_db": auto_backup_db
}

# 字典，对应的操作函数的参数和id
args_dict = {
    "dayrank": {'hour': 21, 'minute': 00, 'id': 'day_ranks'},
    "weekrank": {'day_of_week': "sun", 'hour': 23, 'minute': 59, 'id': 'week_ranks'},
    "dayplayrank": {'hour': 21, 'minute': 30, 'id': 'user_day_plays'},
    "weekplayrank": {'day_of_week': "sun", 'hour': 23, 'minute': 0, 'id': 'user_week_plays'},
    "totalplayrank": {'hour': 22, 'minute': 00, 'id': 'user_total_plays'},
    "totalcoinsrank": {'hour': 22, 'minute': 30, 'id': 'user_total_coins'},
    # "check_ex": {'hour': 1, 'minute': 30, 'id': 'check_expired'},
    # "low_activity": {'hour': 8, 'minute': 30, 'id': 'check_low_activity'},
    "backup_db": {'hour': 2, 'minute': 30, 'id': 'backup_db'}
}


def set_all_sche():
    try:
        if not isinstance(schedall, dict):
            LOGGER.error(f"计划任务不是字典类型")
            return

        schedall_str = json.dumps(schedall, indent=4, ensure_ascii=False, sort_keys=True)
        LOGGER.info(f"计划任务: {schedall_str}")

        for key, value in action_dict.items():
            if not key in schedall:
                continue
            if not schedall[key]:
                continue
            action = action_dict[key]
            args = args_dict[key]
            scheduler.add_job(action, 'cron', **args)
    except Exception as e:
        traceback.print_exc()
        LOGGER.error(f"设置计划任务发生错误: {str(e)}")


set_all_sche()


async def sched_panel(_, msg):
    # await deleteMessage(msg)
    await editMessage(msg,
                      text=f'🎮 **管理定时任务面板**\n\n默认关闭**看片榜单**，开启请在日与周中二选一，谨慎',
                      buttons=sched_buttons())


@bot.on_callback_query(filters.regex('sched') & admins_on_filter)
async def sched_change_policy(_, call):
    try:
        method = call.data.split('-')[1]
        # 根据method的值来添加或移除相应的任务
        action = action_dict[method]
        args = args_dict[method]
        if schedall[method]:
            scheduler.remove_job(job_id=args['id'], jobstore='default')
        else:
            scheduler.add_job(action, 'cron', **args)
        schedall[method] = not schedall[method]
        save_config()
        await asyncio.gather(callAnswer(call, f'⭕️ {method} 更改成功'), sched_panel(_, call.message))
    except IndexError:
        await sched_panel(_, call.message)


@bot.on_message(filters.command('check_ex', prefixes) & admins_on_filter)
async def check_ex_admin(_, msg):
    send = await msg.reply("🍥 正在运行 【到期检测】。。。")
    await check_expired()
    await asyncio.gather(msg.delete(), send.edit("✅ 【到期检测结束】"))


# bot数据库手动备份
@bot.on_message(filters.command('backup_db', prefixes) & filters.user(owner))
async def manual_backup_db(_, msg):
    await asyncio.gather(deleteMessage(msg), DbBackupUtils.auto_backup_db())


@bot.on_message(filters.command('days_ranks', prefixes) & admins_on_filter)
async def day_r_ranks(_, msg):
    await asyncio.gather(msg.delete(), day_ranks(pin_mode=False))


@bot.on_message(filters.command('week_ranks', prefixes) & admins_on_filter)
async def week_r_ranks(_, msg):
    await asyncio.gather(msg.delete(), week_ranks(pin_mode=False))


@bot.on_message(filters.command('low_activity', prefixes) & admins_on_filter)
async def run_low_ac(_, msg):
    await deleteMessage(msg)
    send = await msg.reply(f"⭕ 不活跃检测运行ing···")
    await asyncio.gather(Uplaysinfo.check_low_activity(), send.delete())


@bot.on_message(filters.command('uranks', prefixes) & admins_on_filter)
async def shou_dong_uplayrank(_, msg):
    await deleteMessage(msg)
    try:
        days = int(msg.command[1])
        LOGGER.info(f"手动获取用户播放时长排行榜 - 天数: {days}")
        await Uplaysinfo.user_plays_rank(days=days)
    except Exception as e:
        try:
            await Uplaysinfo.user_plays_rank(days=65535)
        except Exception as e:
            pass


@bot.on_message(filters.command('coinranks', prefixes) & admins_on_filter)
async def shou_dong_coinrank(_, msg):
    await deleteMessage(msg)
    try:
        nums = int(msg.command[1])
        LOGGER.info(f"手动获取硬币排行榜 - 个数: {nums}")
        await Uplaysinfo.user_coins_rank(num=nums)
    except Exception as e:
        try:
            await Uplaysinfo.user_coins_rank()
        except Exception as e:
            pass


@bot.on_message(filters.command('restart', prefixes) & admins_on_filter)
async def restart_bot(_, msg):
    await msg.delete()
    send = await msg.reply("Restarting，等待几秒钟。")
    schedall.update({"restart_chat_id": int(send.chat.id), "restart_msg_id": int(send.id)})
    save_config()
    try:
        # some code here
        LOGGER.info("重启")
        os.execl('/bin/systemctl', 'systemctl', 'restart', 'embyboss')  # 用当前进程执行systemctl命令，重启embyboss服务
    except FileNotFoundError:
        exit(1)
