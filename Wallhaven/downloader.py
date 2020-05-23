#!/usr/bin/env python3
# -*-coding:utf-8-*-

from tqdm import tqdm
from bs4 import BeautifulSoup
from time import time
import aiohttp
import asyncio
import os


class Wallhaven():
    def __init__(self):
        self.urls = []  # urls to download
        self.failed = []  # failed urls
        self.unique_urls = []  # unique urls        
        self.link = input('Please input the URL to donwload from:\n')
        if self.link.find("&page") != -1:
            self.link = self.link[0:self.link.find('&page') + 1]
        self.n = int(input('Please input the number of pages to download:\n'))
        self.nsfw = int(input('Please indicate whether to download NSFW wallpapers:\n1. YES, I will provide username and password\n2. NO\n'))
        self.num = ''
        self.date = ''
        self.pages = list(range(1, self.n + 1))
        self.dir_name = f'{self.pages[0]}-{self.pages[-1]}'
        self.header = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36' }
        self.dir_path = os.path.abspath('.') + os.sep + self.dir_name + os.sep
        self.run()

    async def main(self):                
        async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True) as tc:
            async with aiohttp.ClientSession(connector=tc) as session:
                if self.nsfw == 1:
                    await self.login(session)

                await self.get_url(self.pages, session)

                self.check_txt()

                self.write_url()

                self.new_dir()

                ten = asyncio.Semaphore(10)
                tasks = [self.download(url, session, ten) for url in self.unique_urls]
                await asyncio.gather(*tasks)
                print(f'Failed to download {len(self.failed)} wallpapers\nstart downloading again...')

                for _ in range(3):
                    if self.failed:
                        tasks = [self.download(url, session, ten, fail=True) for url in self.failed]
                        await asyncio.gather(*tasks)
                    else:
                        break

                self.write_fail_url()
                print(f'Successfully downloaded {len(self.unique_urls) - len(self.failed)} wallpapers')

    async def login(self, session):        
        print('Start logging in...')
        login_index_url = 'https://wallhaven.cc/login'
        response = await session.get(login_index_url, headers=self.header)
        html = await response.text()
        bf = BeautifulSoup(html, 'lxml')
        hidden = bf.find_all('input', {'type': 'hidden'})
        for i in hidden:
            _token = i['value']
        data = {
            '_token': _token,
            'username': input('Please input username：'),
            'password': input('Please input password：')
        }
        login_url = 'https://wallhaven.cc/auth/login'
        response = await session.post(login_url, headers=self.header, data=data)
        if response.status == 200:
            print('Successfully logged in!')
        else:
            print(f'Login failed! HTTP:{response.status}')

    async def get_url(self, pages, session):        
        pbar = tqdm(pages, ncols=85)
        for i in pbar:
            pbar.set_description(f'Fetching urls for page {i}')
            if i == 1:
                url = f'{self.link}&page'
            else:
                url = f'{self.link}&page={i}'
            print(url)
            response = await session.get(url, headers=self.header)
            html = await response.text()
            bf = BeautifulSoup(html, 'lxml')
            targets_url = bf.find_all('figure')
            for each in targets_url:
                page_url = each.a.get('href')
                small_name = page_url.split('/')[-1]
                little_name = small_name[0:2]
                full_url = 'https://w.wallhaven.cc/full/' + little_name + \
                    '/wallhaven-' + small_name + '.jpg'
                self.urls.append(full_url)

    def check_txt(self):
        if not os.path.exists('all-url.txt'):
            with open('all-url.txt', 'w'):
                pass

    def write_url(self):        
        with open('all-url.txt', 'r') as f:
            all_list = f.read().splitlines()
            print(f'Got urls for {len(all_list)} wallpapers')
            for i in self.urls:
                if i not in all_list:
                    self.unique_urls.append(i)
            print(f'Removed {len(self.urls)-len(self.unique_urls)} duplicate urls')

        if self.unique_urls:
            with open('all-url.txt', 'a') as f:
                for i in self.unique_urls:
                    f.write(i + '\n')
                print(f'Add {len(self.unique_urls)} urls')
        else:
            print('No new url found!')

    def new_dir(self):        
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)

    async def download(self, url, session, ten, fail=False):        
        async with ten:
            name = url.split('/')
            filename = self.dir_path + name[-1]
            response = await session.get(url, headers=self.header)
            try:
                file_size = int(response.headers['content-length']) 
            except:
                if not fail:                    
                    self.failed.append(url)
                return
            else:
                if os.path.exists(filename):
                    first_byte = os.path.getsize(filename) 
                else:
                    first_byte = 0
                if first_byte >= file_size:
                    print(f'{name[-1]} exists')
                    return
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
                    'Range': f'bytes={first_byte}-{file_size}'}
                try:
                    response = await session.get(url, headers=headers)
                    with open(filename, 'ab') as f:                        
                        with tqdm(total=file_size, initial=first_byte, unit='B', unit_scale=True, desc=name[-1], ncols=85) as pbar:
                            while True:
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                                pbar.update(len(chunk))
                    if fail:
                        self.failed.remove(url)
                except:
                    print(f'Failed to download：{name[-1]}')
                    if not fail:
                        self.failed.append(url)

    def write_fail_url(self):        
        if self.failed:
            with open('fail.txt', 'a') as f:
                for i in self.failed:
                    f.write(i + '\n')

    def run(self):
        start = time()
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self.main())
        loop.run_until_complete(future)
        print(f'Spent {int((time()-start) // 60)} minutes and {int((time()-start) % 60)} seconds')


if __name__ == "__main__":    
    Wallhaven()
