import requests
import re
import sqlite3

from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio

from last_downloaded_index import last_downloaded

import aiohttp
import asyncio

from urllib.parse import quote as encode_url

clientTimeout = aiohttp.ClientTimeout(total=60*60*60) #timeout of 1 hour

limiter = asyncio.Semaphore(5000)

connection = sqlite3.connect('cache.db')
cursor = connection.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS pages
                   (
                    name TEXT PRIMARY KEY,
                    links TEXT
                   )''')


regex = '<a href="\/wiki\/.{1,50}" title=".{1,50}">.{1,50}<\/a>'

connection.commit()

session = requests.Session()

# session.trust_env = True #FUCK FLORIMONT
# session.verify = False

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

async def harvest_urls(wiki_page,async_session):
    #cache
    wiki_page = wiki_page.replace('"','""')
    cmd = cursor.execute(f'SELECT links from pages where name= "{wiki_page}" ') #bro if i get sql injected by a FUCKING WIKIPEDIA ARTICLE :sob:
    response = cmd.fetchone()
    # response = False
    if response:
        return


    async with async_session.get(ssl=False,url=f'https://en.wikipedia.org/wiki/{wiki_page}') as response:
        content = await response.text()
        res = re.findall(regex,str(content))
        
        
        cache = []


        for html in res:
            url = html.split('"')[1][6:]
            urllabel = html.replace('"',"_").split('>')[1][:-3]

            cache.append(url + '@@' + urllabel)

        cache = '::;'.join(cache)
        cursor.execute(f'INSERT OR IGNORE INTO pages VALUES( "{wiki_page}", "{ cache}" )')
        


local_cache = {
    'Main_Page' : True, #anticheat,
    '' : True

}
async def harvest_data(start_page,session):
    async with limiter:
        global local_cache
        if start_page.count(':') != 0:
            return 

        if local_cache.get(start_page):
            return
    
        await harvest_urls(start_page,session)
        local_cache[start_page] = True


        

            

MAX_TASKS = 5000
async def main():
    tasks = []
    with open('all_wikipedia_urls.txt') as file:
        async with aiohttp.ClientSession(timeout=clientTimeout) as session:
            for index,line in enumerate(file):

                if index <= last_downloaded:
                    continue

                rstrip = line.rstrip()
                tasks.append(harvest_data(rstrip,session))
                if len(tasks) >= MAX_TASKS:
                    await tqdm_asyncio.gather(*tasks)
                    connection.commit()
                    tasks = []
                    print(index/18137703)
                    with open('last_downloaded_index.py','w') as file2:
                        file2.write(f'last_downloaded={index}')
            

asyncio.run(main())
