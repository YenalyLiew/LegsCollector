import os
import re
import time
from enum import Enum
from ssl import SSLEOFError

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, MaxRetryError
from requests.exceptions import SSLError, ProxyError
import urllib3
from urllib3.exceptions import InsecureRequestWarning


class SearchTypeEnum(Enum):
    DEFAULT = "1"
    TAG = "2"
    ACTOR = "3"
    PUBLICATION = "4"


def search_legs(search_key: str, only_load_first_page: bool, search_type: SearchTypeEnum = SearchTypeEnum.DEFAULT):
    requests.adapters.DEFAULT_RETRIES = 20
    urllib3.disable_warnings(InsecureRequestWarning)
    session = requests.Session()
    session.verify = False
    page = 1
    headers = {"Connection": "close",
               "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ("
                             "KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"}
    reload_err = 0
    while True:
        try:
            match search_type:
                case SearchTypeEnum.DEFAULT:
                    request = session.get(f'https://www.beatifulleg.com/page/{page}?s={search_key}',
                                          headers=headers)
                case SearchTypeEnum.TAG:
                    request = session.get(f'https://www.beatifulleg.com/tag/{search_key}/page/{page}',
                                          headers=headers)
                case SearchTypeEnum.ACTOR:
                    request = session.get(f'https://www.beatifulleg.com/actor/{search_key}/page/{page}',
                                          headers=headers)
                case SearchTypeEnum.PUBLICATION:
                    request = session.get(f'https://www.beatifulleg.com/publication/{search_key}/page/{page}',
                                          headers=headers)
                case _:
                    break
            if request.status_code == 404:
                print('全部加载完成！')
                break
            soup = BeautifulSoup(request.text, features="html.parser")
            post_ids = soup.find_all('div', attrs={'id': re.compile('post-')})
            for post_id in post_ids:
                img_title = post_id.find_next('img')['title']
                img_url = post_id.find_next('a')['href']
                img_code = img_url[28:]
                print(f'图集代号：{img_code} ({img_title} => {img_url})')
            if only_load_first_page:
                break
            page += 1
        except (MaxRetryError, SSLEOFError, SSLError, ProxyError):
            if reload_err == 20:
                break
            reload_err += 1


def give_me_legs(leg_code: str, save: bool) -> bool:
    requests.adapters.DEFAULT_RETRIES = 20
    urllib3.disable_warnings(InsecureRequestWarning)
    session = requests.Session()
    session.verify = False
    headers = {"Connection": "close",
               "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ("
                             "KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"}
    request = session.get(f'https://www.beatifulleg.com/{leg_code}', headers=headers)
    soup = BeautifulSoup(request.text, features="html.parser")
    figure_classes = soup.select('figure[class="album-photo"]')
    if len(figure_classes) == 0:
        print('涩图代号有误，请重新搜索')
        return False
    title = figure_classes[0].select('img')[0]['title']
    new_path = ''
    if save:
        _path = os.getcwd()
        new_path = os.path.join(_path, title)
        if not os.path.isdir(new_path):
            os.mkdir(new_path)
    for figure_class in figure_classes:
        img_src = figure_class.select('img')[0]['src']
        img_desc = figure_class.select('figcaption')[0].text
        print(f'{img_desc}: {img_src}')
        if save:
            pic_err = 1
            web_err = 1
            while True:
                try:
                    img_get = requests.get(img_src)
                    img_content = img_get.content
                    file_path = f'{new_path}\\{img_desc}.jpg'
                    with open(file=file_path, mode='wb') as f:
                        f.write(img_content)
                        if os.path.getsize(file_path) != 10_2400:
                            print(f'{img_desc} <= 已成功保存！')
                            break
                        else:
                            print(f'{img_desc} <= 第{pic_err}次加载图片失败')
                            pic_err += 1
                            if pic_err == 20:
                                print(f'{img_desc} <= 彻底加载图片失败')
                                break
                            time.sleep(0.5)
                except (MaxRetryError, SSLEOFError, SSLError, ProxyError):
                    print(f'{img_desc} <= 第{web_err}次加载网页失败')
                    web_err += 1
                    if web_err == 20:
                        print(f'{img_desc} <= 彻底加载网页失败')
                        break
                    time.sleep(0.5)
    return True


if __name__ == '__main__':
    print('\033[33mBeautiful Legs Search Engine\033[0m')
    print('\033[34m0. 跳过搜索\033[0m')
    print('1. 普通搜索')
    print('2. TAG搜索')
    print('3. 演员搜索')
    print('4. 出版商搜索')
    print('\033[34mQ. 退出\033[0m')
    while True:
        _search_type = input('输入查询类型代号：')
        match _search_type:
            case "0":
                break
            case SearchTypeEnum.DEFAULT.value:
                search_legs(input('请输入关键词：'), only_load_first_page=False, search_type=SearchTypeEnum.DEFAULT)
            case SearchTypeEnum.TAG.value:
                search_legs(input('请输入TAG：'), only_load_first_page=False, search_type=SearchTypeEnum.TAG)
            case SearchTypeEnum.ACTOR.value:
                search_legs(input('请输入演员：'), only_load_first_page=False, search_type=SearchTypeEnum.ACTOR)
            case SearchTypeEnum.PUBLICATION.value:
                search_legs(input('请输入出版商'), only_load_first_page=False, search_type=SearchTypeEnum.PUBLICATION)
            case _:
                exit(0)
        continue_search = input('要继续搜索吗？(Y/N): ')
        if continue_search != 'Y' or 'y':
            break
    while True:
        _leg_code = input('请输入涩图代号：')
        is_save = input('是否保存于根目录(Y/N)：')
        if is_save == 'Y' or 'y':
            need_not_reload = give_me_legs(_leg_code, save=True)
        else:
            need_not_reload = give_me_legs(_leg_code, save=False)
        if need_not_reload:
            need_quit = input('是否要退出(Y/N)：')
            if need_quit != 'Y' or 'y':
                exit(0)
