#! /usr/bin/python3
# -*- coding:utf-8 -*-
"""
emby的api操作方法
"""
from datetime import datetime, timedelta, timezone

from cacheout import Cache
import requests as r
from bot import emby_url, emby_api, _open, emby_block, schedall, extra_emby_libs, LOGGER
from bot.sql_helper.sql_emby import sql_update_emby, Emby
from bot.sql_helper.sql_emby2 import sql_add_emby2, sql_delete_emby2
from bot.func_helper.utils import pwd_create, convert_runtime

cache = Cache()


def create_policy(admin=False, disable=False, limit: int = 5, block: list = None):
    """
    :param admin: bool 是否开启管理员
    :param disable: bool 是否禁用
    :param limit: int 同时播放流的默认值，修改2 -> 3 any都可以
    :param block: list 默认将 播放列表 屏蔽
    :return: plocy 用户策略
    """
    if block is None:
        block = ['播放列表'] + extra_emby_libs
        
    policy = {
        "IsAdministrator": admin,
        "IsHidden": True,
        "IsHiddenRemotely": True,
        "IsDisabled": disable,
        "EnableRemoteControlOfOtherUsers": False,
        "EnableSharedDeviceControl": False,
        "EnableRemoteAccess": True,
        "EnableLiveTvManagement": False,
        "EnableLiveTvAccess": True,
        "EnableMediaPlayback": True,
        "EnableAudioPlaybackTranscoding": False,
        "EnableVideoPlaybackTranscoding": False,
        "EnablePlaybackRemuxing": False,
        "EnableContentDeletion": False,
        "EnableContentDownloading": False,
        "EnableSubtitleDownloading": False,
        "EnableSubtitleManagement": False,
        "EnableSyncTranscoding": False,
        "EnableMediaConversion": False,
        "EnableAllDevices": True,
        "SimultaneousStreamLimit": limit,
        "BlockedMediaFolders": block
    }
    return policy


def pwd_policy(embyid, stats=False, new=None):
    """
    :param embyid: str 修改的emby_id
    :param stats: bool 是否重置密码
    :param new: str 新密码
    :return: plocy 密码策略
    """
    if new is None:
        policy = {
            "Id": f"{embyid}",
            "ResetPassword": stats,
        }
    else:
        policy = {
            "Id": f"{embyid}",
            "NewPw": f"{new}",
        }
    return policy


class Embyservice:
    """
    初始化一个类，接收url和api_key，params作为参数
    计划是将所有关于emby api的使用方法放进来
    """

    def __init__(self, url, api_key):
        """
        必要参数
        :param url: 网址
        :param api_key: embyapi
        """
        self.url = url
        self.api_key = api_key
        self.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'X-Emby-Token': self.api_key,
            'X-Emby-Client': 'Sakura BOT',
            'X-Emby-Device-Name': 'Sakura BOT',
            'X-Emby-Client-Version': '1.0.0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82'
        }

    async def emby_create(self, tg: int, name, pwd2, us: int, stats):
        """
        创建账户
        :param tg: tg_id
        :param name: emby_name
        :param pwd2: pwd2 安全码
        :param us: us 积分
        :param stats: plocy 策略
        :return: bool
        """
        if _open["tem"] >= int(_open["all_user"]):
            return 403
        # name = escape_html_special_chars(name)
        ex = (datetime.now() + timedelta(days=us))
        name_data = ({"Name": name})
        new_user = r.post(f'{self.url}/emby/Users/New',
                          headers=self.headers,
                          json=name_data)
        if new_user.status_code == 200 or 204:
            try:
                id = new_user.json()["Id"]
                pwd = await pwd_create(8) if stats != 'o' else 5210
                pwd_data = pwd_policy(id, new=pwd)
                _pwd = r.post(f'{self.url}/emby/Users/{id}/Password',
                              headers=self.headers,
                              json=pwd_data)
            except:
                return 100
            else:
                policy = create_policy(False, False)
                _policy = r.post(f'{self.url}/emby/Users/{id}/Policy',
                                 headers=self.headers,
                                 json=policy)  # .encode('utf-8')
                if _policy.status_code == 200 or 204:
                    if stats == 'y':
                        sql_update_emby(Emby.tg == tg, embyid=id, name=name, pwd=pwd, pwd2=pwd2, lv='b',
                                        cr=datetime.now(), ex=ex)
                    elif stats == 'n':
                        sql_update_emby(Emby.tg == tg, embyid=id, name=name, pwd=pwd, pwd2=pwd2, lv='b',
                                        cr=datetime.now(), ex=ex,
                                        us=0)
                    elif stats == 'o':
                        sql_add_emby2(embyid=id, name=name, cr=datetime.now(), ex=ex)

                    if schedall["check_ex"]:
                        ex = ex.strftime("%Y-%m-%d %H:%M:%S")
                    elif schedall["low_activity"]:
                        ex = '__若21天无观看将封禁__'
                    else:
                        ex = '__无需保号，放心食用__'
                    return pwd, ex
        elif new_user.status_code == 400:
            return 400

    async def emby_del(self, id, stats=None):
        """
        删除账户
        :param id: emby_id
        :return: bool
        """
        res = r.delete(f'{self.url}/emby/Users/{id}', headers=self.headers)
        if res.status_code == 200 or 204:
            if stats is None:
                if sql_update_emby(Emby.embyid == id, embyid=None, name=None, pwd=None, pwd2=None, lv='d', cr=None,
                                   ex=None):
                    return True
                else:
                    return False
            else:
                if sql_delete_emby2(embyid=id):
                    return True
                else:
                    return False
        else:
            return False

    async def emby_reset(self, id, new=None):
        """
        重置密码
        :param id: emby_id
        :param new: new_pwd
        :return: bool
        """
        pwd = pwd_policy(embyid=id, stats=True, new=None)
        _pwd = r.post(f'{self.url}/emby/Users/{id}/Password',
                      headers=self.headers,
                      json=pwd)
        # print(_pwd.status_code)
        if _pwd.status_code == 200 or 204:
            if new is None:
                if sql_update_emby(Emby.embyid == id, pwd=None) is True:
                    return True
                return False
            else:
                pwd2 = pwd_policy(id, new=new)
                new_pwd = r.post(f'{self.url}/emby/Users/{id}/Password',
                                 headers=self.headers,
                                 json=pwd2)
                if new_pwd.status_code == 200 or 204:
                    if sql_update_emby(Emby.embyid == id, pwd=new) is True:
                        return True
                    return False
        else:
            return False

    async def emby_block(self, id, stats=0, block=emby_block):
        """
        显示、隐藏媒体库
        :param id: emby_id
        :param stats: plocy
        :return:bool
        """
        result, user_config = self.user(id)
        policy = None

        if result and user_config:
            policy = user_config.get('Policy')

        if policy:
            if stats == 0:
                policy["BlockedMediaFolders"] = block
            else:
                policy["BlockedMediaFolders"] = ['播放列表']
        else:
            if stats == 0:
                policy = create_policy(False, False, block=block)
            else:
                policy = create_policy(False, False)

        _policy = r.post(f'{self.url}/emby/Users/{id}/Policy',
                         headers=self.headers,
                         json=policy)

        if _policy.status_code in (200, 204):
            return True

        return False

    @cache.memoize(ttl=120)
    def get_current_playing_count(self) -> int:
        """
        最近播放数量
        :return: int NowPlayingItem
        """
        response = r.get(f"{self.url}/emby/Sessions", headers=self.headers)
        sessions = response.json()
        # print(sessions)
        count = 0
        for session in sessions:
            try:
                if session["NowPlayingItem"] is not None:
                    count += 1
            except KeyError:
                pass
        # print(count)
        return count

    async def emby_change_policy(self, id=id, admin=False, method=False):
        """
        :param id:
        :param admin:
        :param method: 默认False允许播放
        :return:
        """
        policy = create_policy(admin=admin, disable=method)
        _policy = r.post(self.url + f'/emby/Users/{id}/Policy',
                         headers=self.headers,
                         json=policy)
        if _policy.status_code == 200 or 204:
            return True
        return False

    async def authority_account(self, tg, username, password=None):
        data = {"Username": username, "Pw": password, }
        if password == 'None':
            data = {"Username": username}
        res = r.post(self.url + '/emby/Users/AuthenticateByName', headers=self.headers, json=data)
        if res.status_code == 200:
            embyid = res.json()["User"]["Id"]
            return True, embyid
        return False, 0

    async def emby_cust_commit(self, user_id=None, days=7, method=None):
        _url = f'{self.url}/emby/user_usage_stats/submit_custom_query'
        sub_time = datetime.now(timezone(timedelta(hours=8)))
        start_time = (sub_time - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        end_time = sub_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = ''
        if method == 'sp':
            sql += "SELECT UserId, SUM(PlayDuration - PauseDuration) AS WatchTime FROM PlaybackActivity "
            sql += f"WHERE DateCreated >= '{start_time}' AND DateCreated < '{end_time}' GROUP BY UserId ORDER BY WatchTime DESC LIMIT 10"
        elif user_id != 'None':
            sql += "SELECT MAX(DateCreated) AS LastLogin,SUM(PlayDuration - PauseDuration) / 60 AS WatchTime FROM PlaybackActivity "
            sql += f"WHERE UserId = '{user_id}' AND DateCreated >= '{start_time}' AND DateCreated < '{end_time}' GROUP BY UserId"
        data = {"CustomQueryString": sql, "ReplaceUserId": True}  # user_name
        # print(sql)
        resp = r.post(_url, headers=self.headers, json=data, timeout=30)
        if resp.status_code == 200:
            # print(resp.json())
            rst = resp.json()["results"]
            return rst
        else:
            return None

    async def users(self):
        """
        Asynchronously retrieves the list of users from the Emby server.

        Returns:
            - If the request is successful, returns a tuple with the first element as True and the second element as a dictionary containing the response JSON.
            - If the request is unsuccessful, returns a tuple with the first element as False and the second element as a dictionary containing an 'error' key with an error message.

        Raises:
            - Any exception that occurs during the request.
        """
        try:
            _url = f"{self.url}/emby/Users"
            resp = r.get(_url, headers=self.headers)
            if resp.status_code != 204 and resp.status_code != 200:
                return False, {'error': "🤕Emby 服务器连接失败!"}
            return True, resp.json()
        except Exception as e:
            return False, {'error': e}

    def user(self, embyid):
        """
        通过id查看该账户配置信息
        :param embyid:
        :return:
        """
        try:
            _url = f"{self.url}/emby/Users/{embyid}"
            resp = r.get(_url, headers=self.headers)
            if resp.status_code != 204 and resp.status_code != 200:
                return False, {'error': "🤕Emby 服务器连接失败!"}
            return True, resp.json()
        except Exception as e:
            return False, {'error': e}

    async def add_favotire_items(self, user_id, item_id):
        try:
            _url = f"{self.url}/emby/Users/{user_id}/FavoriteItems/{item_id}"
            resp = r.post(_url, headers=self.headers)
            if resp.status_code != 204 and resp.status_code != 200:
                return False
            return True
        except Exception as e:
            LOGGER.error(f'添加收藏失败 {e}')
            return False

    async def item_id_namme(self, user_id, item_id):
        try:
            req = f"{self.url}/emby/Users/{user_id}/Items/{item_id}"
            reqs = r.get(req, headers=self.headers, timeout=3)
            if reqs.status_code != 204 and reqs.status_code != 200:
                return ''
            title = reqs.json().get("Name")
            # print(reqs.json())
            return title
        except Exception as e:
            LOGGER.error(f'获取title失败 {e}')
            return ''

    async def primary(self, item_id, width=200, height=300, quality=90):
        try:
            _url = f"{self.url}/emby/Items/{item_id}/Images/Primary?maxHeight={height}&maxWidth={width}&quality={quality}"
            resp = r.get(_url, headers=self.headers)
            if resp.status_code != 204 and resp.status_code != 200:
                return False, {'error': "🤕Emby 服务器连接失败!"}
            return True, resp.content
        except Exception as e:
            return False, {'error': e}

    async def backdrop(self, item_id, width=300, quality=90):
        try:
            _url = f"{self.url}/emby/Items/{item_id}/Images/Backdrop?maxWidth={width}&quality={quality}"
            resp = r.get(_url, headers=self.headers)
            if resp.status_code != 204 and resp.status_code != 200:
                return False, {'error': "🤕Emby 服务器连接失败!"}
            return True, resp.content
        except Exception as e:
            return False, {'error': e}

    async def items(self, user_id, item_id):
        try:
            _url = f"{self.url}/emby/Users/{user_id}/Items/{item_id}"
            resp = r.get(_url, headers=self.headers)
            if resp.status_code != 204 and resp.status_code != 200:
                return False, {'error': "🤕Emby 服务器连接失败!"}
            return True, resp.json()
        except Exception as e:
            return False, {'error': e}

    async def get_emby_report(self, types='Movie', user_id=None, days=7, end_date=None, limit=10):
        try:
            if not end_date:
                end_date = datetime.now(timezone(timedelta(hours=8)))
            start_time = (end_date - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            end_time = end_date.strftime('%Y-%m-%d %H:%M:%S')
            sql = "SELECT UserId, ItemId, ItemType, "
            if types == 'Episode':
                sql += " substr(ItemName,0, instr(ItemName, ' - ')) AS name, "
            else:
                sql += "ItemName AS name, "
            sql += "COUNT(1) AS play_count, "
            sql += "SUM(PlayDuration - PauseDuration) AS total_duarion "
            sql += "FROM PlaybackActivity "
            sql += f"WHERE ItemType = '{types}' "
            sql += f"AND DateCreated >= '{start_time}' AND DateCreated <= '{end_time}' "
            sql += "AND UserId not IN (select UserId from UserList) "
            if user_id:
                sql += f"AND UserId = '{user_id}' "
            sql += "GROUP BY name "
            sql += "ORDER BY total_duarion DESC "
            sql += "LIMIT " + str(limit)
            _url = f'{self.url}/emby/user_usage_stats/submit_custom_query'
            data = {
                "CustomQueryString": sql,
                "ReplaceUserId": False
            }
            # print(sql)
            resp = r.post(_url, headers=self.headers, json=data)
            if resp.status_code != 204 and resp.status_code != 200:
                return False, {'error': "🤕Emby 服务器连接失败!"}
            ret = resp.json()
            if len(ret["colums"]) == 0:
                return False, ret["message"]
            return True, ret["results"]
        except Exception as e:
            return False, {'error': e}

    @staticmethod
    def get_medias_count():
        """
        获得电影、电视剧、音乐媒体数量
        :return: MovieCount SeriesCount SongCount
        """
        req_url = f"{emby_url}/emby/Items/Counts?api_key={emby_api}"
        try:
            res = r.get(url=req_url)
            if res:
                result = res.json()
                # print(result)
                movie_count = result.get("MovieCount") or 0
                tv_count = result.get("SeriesCount") or 0
                episode_count = result.get("EpisodeCount") or 0
                music_count = result.get("SongCount") or 0
                txt = f'🎬 电影数量：{movie_count}\n' \
                      f'📽️ 剧集数量：{tv_count}\n' \
                      f'🎵 音乐数量：{music_count}\n' \
                      f'🎞️ 总集数：{episode_count}\n'
                return txt
            else:
                LOGGER.error(f"Items/Counts 未获取到返回数据")
                return None
        except Exception as e:
            LOGGER.error(f"连接Items/Counts出错：" + str(e))
            return e

    async def get_movies(self, title: str, start: int = 0, limit: int = 5):
        """
        根据标题和年份，检查是否在Emby中存在，存在则返回列表
        :param limit: x限制条目
        :param title: 标题
        :param start: 从何处开始
        :return: 返回信息列表
        """
        if start != 0: start = start
        # Options: Budget, Chapters, DateCreated, Genres, HomePageUrl, IndexOptions, MediaStreams, Overview, ParentId, Path, People, ProviderIds, PrimaryImageAspectRatio, Revenue, SortName, Studios, Taglines
        req_url = f"{self.url}/emby/Items?IncludeItemTypes=Movie,Series&Fields=ProductionYear,Overview,OriginalTitle,Taglines,ProviderIds,Genres,RunTimeTicks,ProductionLocations" \
                  f"&StartIndex={start}&Recursive=true&SearchTerm={title}&Limit={limit}&IncludeSearchTypes=false"
        try:
            res = r.get(url=req_url, headers=self.headers, timeout=3)
            if res:
                res_items = res.json().get("Items")
                if res_items:
                    ret_movies = []
                    for res_item in res_items:
                        # print(res_item)
                        item_tmdbid = res_item.get("ProviderIds", {}).get("Tmdb")
                        runtime = convert_runtime(res_item.get("RunTimeTicks")) if res_item.get(
                            "RunTimeTicks") else '数据缺失'
                        ns = ", ".join(res_item.get("Genres"))
                        od = ", ".join(res_item.get("ProductionLocations")) if res_item.get(
                            "ProductionLocations") else '普遍'
                        title = res_item.get("Name") if res_item.get("Name") == res_item.get(
                            "OriginalTitle") else f'{res_item.get("Name")} - {res_item.get("OriginalTitle")}'
                        mediaserver_item = dict(ServerId=res_item.get("ServerId"),
                                                library=res_item.get("ParentId"),
                                                item_id=res_item.get("Id"),
                                                photo=f'{self.url}/emby/Items/{res_item.get("Id")}/Images/Primary?maxHeight=400&maxWidth=600&quality=90',
                                                item_type=res_item.get("Type"),
                                                title=title,
                                                genres=ns,
                                                runtime=runtime,
                                                od=od,
                                                year=res_item.get("ProductionYear"),
                                                overview=res_item.get("Overview"),
                                                taglines='' if not res_item.get("Taglines") else res_item.get(
                                                    "Taglines")[0],
                                                tmdbid=int(item_tmdbid) if item_tmdbid else None,
                                                # imdbid=res_item.get("ProviderIds", {}).get("Imdb"),
                                                # tvdbid=res_item.get("ProviderIds", {}).get("Tvdb"),
                                                # path=res_item.get("Path")
                                                )
                        ret_movies.append(mediaserver_item)
                    return ret_movies
        except Exception as e:
            LOGGER.error(f"连接Items出错：" + str(e))
            return []

    async def get_audios(self, ids: str, start: int = 0, limit: int = 5):
        """
        根据标题和年份，检查是否在Emby中存在，存在则返回列表
        :param limit: x限制条目
        :param ids: 音乐的id，如果多个id以英文逗号分割
        :param start: 从何处开始
        :return: 返回信息列表
        """
        if start != 0: start = start
        req_url = f"{self.url}/emby/Items?&StartIndex={start}&Limit={limit}&Recursive=true&Ids={ids}"
        try:
            res = r.get(url=req_url, headers=self.headers, timeout=3)
            if res:
                res_items = res.json().get("Items")
                if res_items:
                    ret_movies = []
                    for res_item in res_items:
                        runtime = convert_runtime(res_item.get("RunTimeTicks")) if res_item.get(
                            "RunTimeTicks") else '数据缺失'
                        mediaserver_item = dict(ServerId=res_item.get("ServerId"),
                                                albumId=res_item.get("AlbumId"),
                                                photo=f'{self.url}/emby/Items/{res_item.get("AlbumId")}/Images/Primary?maxHeight=400&maxWidth=600&quality=90',
                                                item_type=res_item.get("Type"),
                                                title=res_item.get("Name"),
                                                runtime=runtime
                                                )
                        ret_movies.append(mediaserver_item)
                    return ret_movies
        except Exception as e:
            LOGGER.error(f"连接Items出错：" + str(e))
            return []

# 实例
emby = Embyservice(emby_url, emby_api)
