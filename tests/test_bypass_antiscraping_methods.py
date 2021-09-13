import os
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
import unittest
from src.bypass_antiscraping_methods import ByPass

load_dotenv()


class TestByPass(unittest.TestCase, ByPass):

    def setUp(self) -> None:
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
        self.test_cookie_user_agent_exists()
        self.test_cookie_user_agent_values()

    def test_cookie_user_agent_exists(self):
        cookie, user_agent = self.get_cookie_and_useragent('https://scrapfly.io/dashboard/monitoring/log/d432f656-77a1-4595-ab8f-29148e630064')
        self.assertTrue(cookie)
        self.assertTrue(user_agent)
        self.cookie = cookie
        self.user_agent = user_agent

    def test_cookie_user_agent_values(self):
        self.assertTrue(self.cookie.endswith('=='))
        self.assertIn('user-agent', self.user_agent)

    def get_cookie_and_useragent(self, canonical_link: str):
        response = requests.request('GET', canonical_link, headers=self.header)
        soup = BeautifulSoup(response.text, 'html.parser')
        redirect_login_url = soup.find(attrs={'rel': 'canonical'}).attrs.get('href')
        self.header['Referer'] = redirect_login_url
        response = requests.request("POST", redirect_login_url, headers=self.header,
                                    data=os.environ['PERIMETERX_BYPASS_PAYLOAD'])
        soup = BeautifulSoup(response.text, 'html.parser')
        cookie = soup.find(string=re.compile('_px3')).parent.parent.nextSibling.nextSibling.text
        ua = soup.find(string=re.compile('user-agent')).parent.parent.parent.parent.text.strip()
        user_agent = ua[ua.index('t') + 1:].strip()
        return cookie, ua


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestByPass)
    unittest.TextTestRunner(verbosity=2).run(suite)
