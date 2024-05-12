import requests as r
from base64 import b64encode
from bot.sql_helper.sql_manga import Manga, sql_add_manga, sql_delete_manga, sql_get_manga
from bot import manga_url, manga_authorization


class MangaService:

    def __init__(self, url, authorization):
        self.url = url
        self.authorization = authorization
        self.headers = {
            'Authorization': self.authorization,
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': url,
            'priority': 'u=1, i',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15'
        }

    async def manga_create(self, embyid, email, pwd):
        if not embyid or not email or not pwd:
            return 404
        parameter = {
            'email': email,
            'password': pwd,
            'roles': [
                'USER',
                'PAGE_STREAMING'
            ]
        }
        new_user = r.post(f'{self.url}/api/v2/users', headers=self.headers, json=parameter)
        status_code = new_user.status_code
        try:
            if (status_code == 200 or status_code == 201) and new_user.json():
                new_user_data = new_user.json()
                manga_id = new_user_data.get('id')
                name = new_user_data.get('email')
                manga_info = Manga(manga_id=manga_id, embyid=embyid, name=name, pwd=pwd)
                sql_add_manga(manga_info)
                return manga_info
            elif status_code == 400:
                return 400
            else:
                return status_code
        except:
            return 403

    async def manga_del(self, manga_id):
        if not manga_id:
            return False

        res = r.delete(f'{self.url}/api/v2/users/{manga_id}', headers=self.headers)
        status_code = res.status_code
        if status_code == 200 or status_code == 201 or status_code == 204:
            if sql_delete_manga(embyid=None, manga_id=manga_id):
                return True
            else:
                return False
        else:
            return False

    async def manga_reset(self, manga_info, new_pwd):
        if not manga_info or not isinstance(manga_info, Manga) or not new_pwd or not isinstance(new_pwd, str):
            return False

        authorization = 'Basic ' + b64encode(f'{manga_info.name}:{manga_info.pwd}'.encode('utf-8')).decode()
        headers = self.headers.copy()
        headers['Authorization'] = authorization
        parameter = {
            'password': new_pwd
        }
        res = r.patch(f'{self.url}/api/v2/users/{manga_info.manga_id}/password', headers=headers, json=parameter)
        status_code = res.status_code
        if status_code == 200 or status_code == 201 or status_code == 204:
            return True
        else:
            return False


# 实例
manga = MangaService(manga_url, manga_authorization)

