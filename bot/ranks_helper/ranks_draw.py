import os
import pytz
import random
import logging
from io import BytesIO
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from datetime import datetime
from bot.func_helper.emby import emby

"""
日榜周榜海报样式
你可以根据你的需求自行封装或更改为你自己的周榜海报样式！
"""


class RanksDraw:

    def __init__(self, embyname=None, weekly=False, backdrop=False):
        # 绘图文件路径初始化
        bg_path = os.path.join('bot', 'ranks_helper', "resource", "bg")
        if weekly:
            mask_path = os.path.join('bot', 'ranks_helper', "resource", "week_ranks_mask_backdrop.png")
        else:
            mask_path = os.path.join('bot', 'ranks_helper', "resource", "day_ranks_mask_backdrop.png")
        font_path = os.path.join('bot', 'ranks_helper', "resource", 'font', "PingFang Bold.ttf")
        logo_font_path = os.path.join('bot', 'ranks_helper', 'resource', 'font', 'Provicali.otf')
        # 随机调取背景
        bg_list = os.listdir(bg_path)
        bg_path = os.path.join(bg_path, random.choice(bg_list))
        # 初始绘图对象
        self.bg = Image.open(bg_path)
        mask = Image.open(mask_path)
        self.bg = self.bg.resize(mask.size)
        self.bg.paste(mask, (0, 0), mask)
        self.font = ImageFont.truetype(font_path, 18)
        self.font_small = ImageFont.truetype(font_path, 14)
        self.font_count = ImageFont.truetype(font_path, 12)
        self.font_logo = ImageFont.truetype(logo_font_path, 100)
        self.embyname = embyname
        self.backdrop = backdrop

    # backdrop_image 使用横版封面图绘制
    # draw_text 绘制item_name和播放次数
    async def draw(self, movies=[], tvshows=[], audios=[], draw_text=False):
        text = ImageDraw.Draw(self.bg)
        # 合并绘制
        index = 0
        font_offset_y = 190
        resize = (0, 0)
        xy = (0, 0)

        # 剧集Y偏移
        index = 0
        # 名称显示偏移
        font_offset_y = 193
        for i in tvshows[:5]:
            # 榜单项数据
            user_id, item_id, item_type, name, count, duarion = tuple(i)
            if not item_id:
                continue
            # 图片获取，剧集主封面获取
            # 获取剧ID
            success, data = await emby.items(user_id, item_id)
            if success:
                item_id = data["SeriesId"]
            else:
                logging.error(f'【ranks_draw】获取剧集ID失败 {item_id} {name},根据名称开始搜索。')
                # ID错误时根据剧名搜索得到正确的ID
                ret_media = await emby.get_movies(title=name, start=0, limit=1)
                if ret_media:
                    item_id = ret_media[0]['item_id']
                    logging.info(f'{name} 已更新使用正确ID：{item_id}')

            # 封面图像获取
            resize = (242, 160)
            xy = (103 + 302 * index, 140)
            logging.info(f'【ranks_draw】正在处理剧集封面图 {item_id} {name}')
            prisuccess, data = await emby.backdrop(item_id)
            if not prisuccess:
                prisuccess, data = await emby.primary(item_id)
                resize = (110, 160)
                xy = (169 + 302 * index, 140)

            if not prisuccess:
                logging.error(f'【ranks_draw】获取剧集ID失败 {item_id} {name} {data}')
                continue
            temp_font = self.font
            # 名称超出长度缩小省略
            name = name[:7]
            try:
                # 绘制封面
                if prisuccess:
                    cover = Image.open(BytesIO(data))
                    cover = cover.resize(resize)
                    self.bg.paste(cover, xy)
            except Exception as e:
                prisuccess = False
                logging.error(f'【ranks_draw】绘制剧集封面图失败 {item_id} {name} {e}')
                pass

            if not prisuccess:
                # 如果没有封面图，使用name来代替
                draw_text_psd_style(text, (123 + 302 * index, 140), name, temp_font, 126)

            # 绘制 播放次数、影片名称
            if draw_text:
                draw_text_psd_style(text, (601 + 130, 163 + (230 * index)), str(count), self.font_count, 126)
                draw_text_psd_style(text, (601, 163 + font_offset_y + (230 * index)), name, temp_font, 126)

            index += 1

        # 剧集Y偏移
        index = 0
        # 名称显示偏移
        font_offset_y = 190
        for i in movies[:5]:
            # 榜单项数据
            user_id, item_id, item_type, name, count, duarion = tuple(i)
            if not item_id:
                continue
            # 封面图像获取
            logging.info(f'【ranks_draw】正在处理电影封面图 {item_id} {name}')
            prisuccess, data = await emby.backdrop(item_id)
            resize = (242, 160)
            xy = (408 + 302 * index, 444)
            if not prisuccess:
                prisuccess, data = await emby.primary(item_id)
                resize = (110, 160)
                xy = (474 + 302 * index, 444)

            if not prisuccess:
                logging.error(f'【ranks_draw】获取电影封面图失败 {item_id} {name}')
            # 名称显示偏移
            temp_font = self.font
            # 名称超出长度缩小省略
            name = name[:7]
            try:
                # 绘制封面
                if prisuccess:
                    cover = Image.open(BytesIO(data))
                    cover = cover.resize(resize)
                    self.bg.paste(cover, xy)
            except Exception as e:
                prisuccess = False
                logging.error(f'【ranks_draw】绘制电影封面图失败 {item_id} {name} {e}')
                pass

            if not prisuccess:
                # 如果没有封面图，使用name来代替
                draw_text_psd_style(text, (428 + 302 * index, 444), name, temp_font, 126)

            # 绘制 播放次数、影片名称
            if draw_text:
                draw_text_psd_style(text, (770 + 130, 990 - (232 * index)), str(count), self.font_count, 126)
                draw_text_psd_style(text, (770, 990 + font_offset_y - (232 * index)), name, temp_font, 126)

            index += 1

        # 剧集Y偏移
        index = 0
        # 名称显示偏移
        font_offset_y = 193
        for i in audios[:5]:
            # 榜单项数据
            user_id, item_id, item_type, name, count, duarion = tuple(i)
            if not item_id:
                continue
            # 封面图像获取
            logging.info(f'【ranks_draw】正在处理音乐封面图 {item_id} {name}')
            ret_media = await emby.get_audios(ids=item_id, start=0, limit=1)
            if ret_media:
                item_id = ret_media[0]['albumId']
                logging.info(f'{name} 已更新使用正确ID：{item_id}')
            prisuccess, data = await emby.backdrop(item_id)
            resize = (242, 160)
            xy = (103 + 302 * index, 780)
            if not prisuccess:
                prisuccess, data = await emby.primary(item_id)
                resize = (110, 160)
                xy = (169 + 302 * index, 780)

            if not prisuccess:
                logging.error(f'【ranks_draw】获取音乐专辑封面图失败 {item_id} {name}')
            # 名称显示偏移
            temp_font = self.font
            # 名称超出长度缩小省略
            name = name[:7]
            try:
                # 绘制封面
                if prisuccess:
                    cover = Image.open(BytesIO(data))
                    cover = cover.resize(resize)
                    self.bg.paste(cover, xy)
            except Exception as e:
                prisuccess = False
                logging.error(f'【ranks_draw】绘制电影封面图失败 {item_id} {name} {e}')
                pass

            if not prisuccess:
                # 如果没有封面图，使用name来代替
                draw_text_psd_style(text, (123 + 302 * index, 780), name, temp_font, 126)

            # 绘制 播放次数、影片名称
            if draw_text:
                draw_text_psd_style(text, (601 + 130, 163 + (230 * index)), str(count), self.font_count, 126)
                draw_text_psd_style(text, (601, 163 + font_offset_y + (230 * index)), name, temp_font, 126)

            index += 1

    def save(self,
             save_path=os.path.join('log', 'img',
                                    datetime.now(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d.jpg"))):
        if not os.path.exists('log/img'): os.makedirs('log/img')
        if self.bg.mode in ("RGBA", "P"): self.bg = self.bg.convert("RGB")
        self.bg.save(save_path)
        return save_path

def draw_text_psd_style(draw, xy, text, font, tracking=0, leading=None, **kwargs):
    """
    usage: draw_text_psd_style(draw, (0, 0), "Test", 
                tracking=-0.1, leading=32, fill="Blue")

    Leading is measured from the baseline of one line of text to the
    baseline of the line above it. Baseline is the invisible line on which most
    letters—that is, those without descenders—sit. The default auto-leading
    option sets the leading at 120% of the type size (for example, 12‑point
    leading for 10‑point type).

    Tracking is measured in 1/1000 em, a unit of measure that is relative to 
    the current type size. In a 6 point font, 1 em equals 6 points; 
    in a 10 point font, 1 em equals 10 points. Tracking
    is strictly proportional to the current type size.
    """

    def stutter_chunk(lst, size, overlap=0, default=None):
        for i in range(0, len(lst), size - overlap):
            r = list(lst[i:i + size])
            while len(r) < size:
                r.append(default)
            yield r

    x, y = xy
    font_size = font.size
    lines = text.splitlines()
    if leading is None:
        leading = font.size * 1.2
    for line in lines:
        for a, b in stutter_chunk(line, 2, 1, ' '):
            w = font.getlength(a + b) - font.getlength(b)
            draw.text((x, y), a, font=font, **kwargs)
            x += w + (tracking / 1000) * font_size
        y += leading
        x = xy[0]
