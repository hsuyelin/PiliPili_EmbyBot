import uuid

import pytz

from bot import _open, save_config, owner, admins, bot_name, ranks, schedall, group
from bot.sql_helper.sql_code import sql_add_code
from bot.sql_helper.sql_emby import sql_get_emby

wh_msg = ['谁都无法相信未来，谁都无法接受未来。', 
          '如果每个人都能为自己所爱的事情付诸努力，那崭新的地方定是梦想的终点。',
          '所谓的觉悟、就是在黑暗的荒野中开辟前行的道路。', 
          '如果能在六十亿分之一的概率下次与你相遇，即使你那时候你还是身体无法动弹，我也会和你结婚。', 
          '即使交不到100个朋友也没有关系，只要交到一个比100个朋友更重要的朋友。', 
          '我喜欢你。对君之爱，胜于世上万千，思君之意，亙古如斯，唯有这份心意不输给任何人。纵使此身魂去魄散，消失离散于世间，若有来生，我心依旧。',
          '九月露湿，待君之前。',
          '双鱼合分波雷理，狂骨逍遥枕乱花。',
          '你不在的世界里，我无法找到任何意义。',
          '不要把生杀予夺大权交给别人!',
          '过于认真的人总是无法将责任推给别人，所以只能自己埋怨自己，让自己很痛苦。',
          '那天，彗星划过天际的那一天，那就像，就像梦幻的景色一般，那真是无与伦比，美到极致的风景。',
          '世界不完美，所以才显得美丽。',
          '不管前方的路有多苦，只要走的方向正确，不管多么崎岖不平，都比站在原地更接近幸福。',
          '听说，樱花花瓣飘落的速度，是每秒5厘米。…思念的距离到底有多远……樱花下落的速度是秒速5厘米。如果樱花下落时是有声音的，你会不会听到我对你的思念。',
          '天空仿佛触手可及。所以，我喜欢雨，因它带来了天空的气味。我经常在下雨的早晨，不转乘地铁，转身走出车站。',
          '我——撒了一个谎，宫园薰，喜欢渡亮太的，这样的一个谎。这个谎把你——有马公生君，命运般地带到了我的面前。马上，春天就要来了，与你相遇的春天，一个没有你的春天。']


def judge_admins(uid):
    """
    判断是否admin
    :param uid: tg_id
    :return: bool
    """
    if uid != owner and uid not in admins and uid not in group:
        return False
    else:
        return True


# @cache.memoize(ttl=60)
async def members_info(tg=None, name=None):
    """
    基础资料 - 可传递 tg,emby_name
    :param tg: tg_id
    :param name: emby_name
    :return: name, lv, ex, us, embyid, pwd2
    """
    if tg is None:
        tg = name
    data = sql_get_emby(tg)
    if data is None:
        return None
    else:
        name = data.name or '无账户信息'
        pwd2 = data.pwd2
        embyid = data.embyid
        us = [data.us, data.iv]
        lv_dict = {'a': '白名单', 'b': '**正常**', 'c': '**已禁用**', 'd': '未注册'}  # , 'e': '**21天未活跃/无信息**'
        lv = lv_dict.get(data.lv, '未知')
        if lv == '白名单':
            ex = '+ ∞'
        elif data.name is not None and schedall["low_activity"] and not schedall["check_ex"]:
            ex = '__若21天无观看将封禁__'
        elif data.name is not None and not schedall["low_activity"] and not schedall["check_ex"]:
            ex = ' __无需保号，放心食用__'
        else:
            ex = data.ex or '无账户信息'
        return name, lv, ex, us, embyid, pwd2


async def open_check():
    """
    对config查询open
    :return: open_stats, all_user, tem, timing
    """
    open_stats = _open["stat"]
    all_user = _open["all_user"]
    tem = _open["tem"]
    timing = _open["timing"]
    allow_code = _open["allow_code"]
    return open_stats, all_user, tem, timing, allow_code


async def tem_alluser():
    _open["tem"] = int(_open["tem"] + 1)
    if _open["tem"] >= _open["all_user"]:
        _open["stat"] = False
    save_config()


from random import choice
import string


async def pwd_create(length=8, chars=string.ascii_letters + string.digits):
    """
    简短地生成随机密码，包括大小写字母、数字，可以指定密码长度
    :param length: 长度
    :param chars: 字符 -> python3中为string.ascii_letters,而python2下则可以使用string.letters和string.ascii_letters
    :return: 密码
    """
    return ''.join([choice(chars) for i in range(length)])


async def cr_link_one(tg: int, times, count, days: int, method: str):
    """
    创建连接
    :param tg:
    :param times:
    :param count:
    :param days:
    :param method:
    :return:
    """
    links = ''
    code_list = []
    i = 1
    if method == 'code':
        while i <= count:
            p = await pwd_create(10)
            uid = f'{ranks["logo"]}-{times}-{p}'
            code_list.append(uid)
            link = f'`{uid}`\n'
            links += link
            i += 1
    elif method == 'link':
        while i <= count:
            p = await pwd_create(10)
            uid = f'{ranks["logo"]}-{times}-{p}'
            code_list.append(uid)
            link = f't.me/{bot_name}?start={uid}\n'
            links += link
            i += 1
    if sql_add_code(code_list, tg, days) is False:
        return None
    return links


async def cr_link_two(tg: int, times, days: int):
    code_list = []
    p = uuid.uuid4()
    uid = f'{ranks["logo"]}-{times}-{str(p).replace("-", "")}'
    code_list.append(uid)
    link = f't.me/{bot_name}?start={uid}'
    if sql_add_code(code_list, tg, days) is False:
        return None
    return link


from datetime import datetime, timedelta


async def convert_s(seconds):
    # 创建一个时间间隔对象，换算以后返回计算出的字符串
    secondsIntValue = 1
    try:
        secondsIntValue = int(seconds)
    except Exception as e:
        pass
    duration = timedelta(seconds=secondsIntValue)
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} 天 {hours % 24} 小时 {minutes % 60} 分钟"
    elif hours > 0:
        return f"{hours} 小时 {minutes % 60} 分钟"
    elif minutes > 0:
        return f"{minutes} 分钟"
    else:
        return "1 分钟"


def convert_runtime(runTimeTicks):
    # 创建一个时间间隔对象，换算以后返回计算出的字符串
    secondsIntValue = 1
    try:
        secondsIntValue = int(runTimeTicks) // 10000000
    except Exception as e:
        pass
    duration = timedelta(seconds=secondsIntValue)
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} 天 {hours % 24} 小时 {minutes % 60} 分钟"
    elif hours > 0:
        return f"{hours} 小时 {minutes % 60} 分钟"
    elif minutes > 0:
        return f"{minutes} 分钟"
    else:
        return "1 分钟"


def convert_to_beijing_time(original_date):
    original_date = original_date.split(".")[0].replace('T', ' ')
    dt = datetime.strptime(original_date, "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)
    # 使用pytz.timezone函数获取北京时区对象
    beijing_tz = pytz.timezone("Asia/Shanghai")
    # 使用beijing_tz.localize函数将dt对象转换为有时区的对象
    dt = beijing_tz.localize(dt)
    return dt

# 定义一个函数，将北京时间转换成utc时间'%Y-%m-%dT%H:%M:%S.%fZ'
# def convert_to_utc_time(beijing_time):
#     dt = datetime.strptime(beijing_time, '%Y-%m-%d %H:%M:%S')
#     dt = dt - timedelta(hours=8)
#     return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


# import random
# import grequests


# def err_handler(request, exception):
#     get_bot_wlc()


# def random_shici_data(data_list, x):
#     try:
#         # 根据不同的url返回的数据结构，获取相应的字段
#         if x == 0:
#             ju, nm = data_list[0]["content"], f'{data_list[0]["author"]}《{data_list[0]["origin"]}》'
#         elif x == 1:
#             ju, nm = data_list[1]["hitokoto"], f'{data_list[1]["from_who"]}《{data_list[1]["from"]}》'
#         elif x == 2:
#             ju, nm = data_list[2]["content"], data_list[2]["source"]
#             # 如果没有作者信息，就不显示
#         return ju, nm
#     except:
#         return False


# # 请求每日诗词
# def get_bot_shici():
#     try:
#         urls = ['https://v1.jinrishici.com/all.json', 'https://international.v1.hitokoto.cn/?c=i',
#                 'http://yijuzhan.com/api/word.php?m=json']
#         reqs = [grequests.get(url) for url in urls]
#         res_list = grequests.map(reqs)  # exception_handler=err_handler
#         data_list = [res.json() for res in res_list]
#         # print(data_list)
#         seq = [0, 1, 2]
#         x = random.choice(seq)
#         seq.remove(x)
#         e = random.choice(seq)
#         ju, nm = random_shici_data(data_list, x=x)
#         e_ju, e_nm = random_shici_data(data_list, x=e)
#         e_ju = random.sample(e_ju, 6)
#         T = ju
#         t = random.sample(ju, 2)
#         e_ju.extend(t)
#         random.shuffle(e_ju)
#         for i in t:
#             ju = ju.replace(i, '░')  # ░
#         print(T, e_ju, ju, nm)
#         return T, e_ju, ju, nm
#     except Exception as e:
#         print(e)
#         # await get_bot_shici()
