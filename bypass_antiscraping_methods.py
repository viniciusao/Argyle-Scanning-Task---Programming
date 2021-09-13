from datetime import datetime
import os
import re
from bs4 import BeautifulSoup
import requests
import sqlite3
from dotenv import load_dotenv
from scrapfly import ScrapeConfig, ScrapflyClient, ScrapeApiResponse


load_dotenv()


class ByPass:

    def __init__(self):
        self.con = sqlite3.connect('argyle_test.db')
        self.cursor = self.con.cursor()
        self.header = {
          'Connection': 'keep-alive',
          'Cache-Control': 'max-age=0',
          'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
          'sec-ch-ua-mobile': '?0',
          'Upgrade-Insecure-Requests': '1',
          'Origin': 'https://scrapfly.io',
          'Content-Type': 'application/x-www-form-urlencoded',
          'User-Agent': eval(os.environ['DEFAULT_H']).get('User-Agent'),
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
          'Sec-Fetch-Site': 'same-origin',
          'Sec-Fetch-Mode': 'navigate',
          'Sec-Fetch-User': '?1',
          'Sec-Fetch-Dest': 'document',
          'Referer': None,
          'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def bypass_perimeterx(self):
        now = datetime.strptime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "%d/%m/%Y %H:%M:%S")
        query_result = self.cursor.execute('select created from cookie').fetchone()
        seconds_elapsed = (now - datetime.strptime(query_result[0], "%d/%m/%Y %H:%M:%S")).total_seconds() if query_result else None
        if not query_result or (seconds_elapsed > 60):
            scrapfly = ScrapflyClient(key=os.environ['API_KEY'], max_concurrency=3)
            with scrapfly as client:
                api_response: ScrapeApiResponse = client.scrape(
                    scrape_config=ScrapeConfig(
                        url='https://www.upwork.com/ab/account-security/login', render_js=True
                    )
                )
            self.get_cookie_and_useragent(api_response.headers.get('Link'))

    def get_cookie_and_useragent(self, canonical_link: str):
        pattern = r'(?:https://)?\w+\.\S*[^.\s]'
        result = re.search(pattern, canonical_link)
        # TODO: Tracking this process would be good.
        if result:
            url = result.group()[:-2]     # doesn't get `>;`
            response = requests.request('GET', url, headers=self.header)
            soup = BeautifulSoup(response.text, 'html.parser')
            redirect_login_url = soup.find(attrs={'rel': 'canonical'}).attrs.get('href')
            self.header['Referer'] = redirect_login_url
            response = requests.request("POST", redirect_login_url, headers=self.header, data=os.environ['PERIMETERX_BYPASS_PAYLOAD'])
            soup = BeautifulSoup(response.text, 'html.parser')
            cookie = soup.find(string=re.compile('_px3')).parent.parent.nextSibling.nextSibling.text
            ua = soup.find(string=re.compile('user-agent')).parent.parent.parent.parent.text.strip()
            user_agent = ua[ua.index('t')+1:].strip()
            self.store(cookie, user_agent)

    def store(self, cookie, user_agent):
        if not self.cursor.execute('select * from cookie').fetchone():
            self.cursor.execute(f'INSERT INTO cookie (cookie, user_agent, created) VALUES ("{cookie}", "{user_agent}", "{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}")')
        else:
            self.cursor.execute(
                f'UPDATE cookie SET cookie="{cookie}", user_agent="{user_agent}", '
                f'created="{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}" WHERE id=1')
        self.con.commit()
        self.cursor.close()
        self.con.close()
