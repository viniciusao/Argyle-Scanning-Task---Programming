import asyncio
from datetime import datetime
import json
import logging
import os
import pathlib
import re
import sqlite3
from typing import Mapping, Sequence
import aiosqlite
from aiosqlite import Connection
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import httpx
from httpx import AsyncClient
from pydantic import ValidationError
from bypass_antiscraping_methods import ByPass
from validade_scraped_data import ScrapedData

load_dotenv()


class ScrapingUpWork:
    def __init__(self):
        self.db_path = str(pathlib.Path(__file__).parent.resolve())+'/argyle_test.db'
        self.cookie = None
        self.user_agent = None
        self.header = eval(os.environ['DEFAULT_H'])
        self.retry_count = 0
        self.task_id = None
        self.url_login = 'https://www.upwork.com/ab/account-security/login'
        self.url_home = 'https://www.upwork.com/home/'
        self.url_profile_details = 'https://www.upwork.com/freelancers/api/v1/freelancer/profile/{}/details'

    async def get_xsfr_token(self, credential: Sequence):
        async with aiosqlite.connect(self.db_path) as db:
            j = await db.execute(f'INSERT INTO tasks (login_id, status, created) VALUES ({credential[0]}, "pending", "{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}")')
            self.task_id: int = j.lastrowid
            await db.commit()
            query = await db.execute('SELECT cookie, user_agent from cookie')
            query_result = await query.fetchone()
            if query_result:
                self.cookie, self.user_agent = query_result
                self.header['User-Agent'] = self.user_agent
            async with httpx.AsyncClient(cookies={'_px3': self.cookie}) as c:
                r = await c.get(url=self.url_login, headers=self.header, timeout=40)
                if r.status_code == 200:
                    cookies = r.headers.get('set-cookie')
                    cookie = cookies[cookies.index('XSRF-TOKEN'):].split(';', 1)[0].split('=').pop()
                    await self.login(c, cookie, credential, db)
                elif r.status_code in (403, 429) and self.retry_count < 2:
                    await self.retry_request(credential, db)
                else:
                    await db.execute(f'UPDATE tasks SET status="Unknown Error! HTTP Status Code: {r.status_code}" WHERE task_id={self.task_id}')
                    await db.commit()

    async def retry_request(self, credential: Sequence, db_con: Connection):
        logging.error('AntiScraping detected... Bypassing.')
        self.retry_count += 1
        await db_con.execute(f'UPDATE tasks SET status="Got by AntiScraping Mechanisms" WHERE task_id={self.task_id}')
        await db_con.commit()
        ByPass().bypass_perimeterx()
        await self.get_xsfr_token(credential)

    async def login(self, client: AsyncClient, xsrf_token: str, credential: Sequence, db_con: Connection):
        client.cookies.set('XSRF-TOKEN', xsrf_token)
        self.header.update({
            'content-type': 'application/json',
            'referer': self.url_login,
            'x-requested-with': 'XMLHttpRequest',
            'x-odesk-csrf-token': xsrf_token,

        })
        r = await client.post(
            url=self.url_login, headers=self.header, timeout=40,
            json={
                "login": {"password": f"{credential[2]}",
                          "mode": "password",
                          "username": f"{credential[1]}"}}
        )
        if r.status_code in (403, 429) and self.retry_count < 2:
            await self.retry_request(credential, db_con)
        else:
            await self.get_user_profile_details(client, credential[1], db_con)

    async def get_user_profile_details(self, client: AsyncClient, username: str, db_con: Connection):
        r = await client.get(url=self.url_home, headers=eval(os.environ['DEFAULT_H']))
        soup = BeautifulSoup(r.text, 'html.parser')
        login_id = soup.find(string=re.compile('~'))
        id_ = login_id[login_id.index('~'):login_id.index('~') + 19]
        r = await client.get(url=self.url_profile_details.format(id_), headers=self.header)
        await self.validate_scraped_data_and_serialize(r.json(), id_, username, db_con)

    async def validate_scraped_data_and_serialize(self, json_: Mapping, user_id: str, username: str, db_con: Connection):
        d = {
            "id": user_id.lstrip('~'),
            "employers": json_.get('profile', {}).get('employmentHistory'),
            "created_at": json_.get('person', {}).get('creationDate'),
            "full_name": json_.get('profile', {}).get('profile', {}).get('name'),
            "picture_url": json_.get('person', {}).get('photoUrl'),
            "address": json_.get('person', {}).get('location')
        }
        await db_con.execute(f'UPDATE tasks SET status="Success!" WHERE task_id={self.task_id}')
        await db_con.commit()
        try:
            ScrapedData(**d)
        except ValidationError as e:
            logging.error(f'Scraped profile info data from username: {username} ')
            logging.error(e)
            print('\n----------------------\n')
        finally:
            with open(f'{username}_profile_info.json', 'w') as f:
                json.dump(d, f)
                f.flush()


async def go():
    await asyncio.gather(*[ScrapingUpWork().get_xsfr_token(login) for login in logins])

if __name__ == '__main__':
    formatter = "[%(asctime)s] %(name)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=formatter)
    con_s = sqlite3.connect(str(pathlib.Path(__file__).parent.resolve())+'/argyle_test.db')
    cursor = con_s.cursor()
    logins = cursor.execute('SELECT id, username, password from logins').fetchall()
    cursor.close()
    con_s.close()
    asyncio.run(go())
