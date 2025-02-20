import requests
import re
import sqlite3

from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio


import aiohttp
import asyncio

from urllib.parse import quote as encode_url

from ai_heuristic import score_word_similarity

clientTimeout = aiohttp.ClientTimeout(total=60*60*60) #timeout of 1 hour

limiter = asyncio.Semaphore(100)

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

async def harvest_urls(wiki_page,path,async_session):
    #cache
    
    cmd = cursor.execute(f'SELECT links from pages where name= "{wiki_page}" ') #bro if i get sql injected by a FUCKING WIKIPEDIA ARTICLE :sob:
    response = cmd.fetchone()
    # response = False
    if response:
        res = response[0].split('::;')
        parsed_response = []
        
        for split_response in res:
            splitter = split_response.split('@@')
            url = splitter[0]

            urllabel = '[UNKNOWN TITLE]'
            if len(splitter) == 2:
                urllabel = splitter[1]

            newpath = path + [ [wiki_page,urllabel ] ]
            parsed_response.append([url,newpath])

        return parsed_response


    async with async_session.get(ssl=False,url=f'https://en.wikipedia.org/wiki/{wiki_page}') as response:
        content = await response.text()
        res = re.findall(regex,str(content))
        
        
        cache = []

        parsed_response = []

        for html in res:
            url = html.split('"')[1][6:]
            urllabel = html.replace('"',"_").split('>')[1][:-3]
            newpath = path + [ [wiki_page,urllabel ] ]

            parsed_response.append([url,newpath])
            cache.append(url + '@@' + urllabel)

        cache = '::;'.join(cache)
        cursor.execute(f'INSERT OR IGNORE INTO pages VALUES( "{wiki_page}", "{ cache}" )')
        connection.commit()
        return parsed_response

local_cache = {
    'Main_Page' : True, #anticheat,
    '' : True

}
async def harvest_data(start_page,path,session):
    async with limiter:
        global local_cache
        if start_page.count(':') != 0:
            return [] #NO CHEATING!!!

        if local_cache.get(start_page):
            return [] #prune because we already scanned it
    
        data = await harvest_urls(start_page,path,session)
        local_cache[start_page] = data
        return data

async def hunt(start_page,end_page,max_pages_to_check):

    data = []
    heuristic_scores = []
    recursions = 0
    response = None
    data = [[start_page,[]]]
    while not response:

        print('checking values:')
        for page_name, path in tqdm(data):
            if page_name == end_page:
                response = path
                break

        if response:
            break
        
        print('scoring data...')

        for page_name, path in tqdm(data):
            heuristic_scores.append([page_name,path,score_word_similarity(page_name,end_page)])

        tasks = []
        task_response = []
        print('harvesting page data..')
        print('pages to check: ',len(data))
        # await asyncio.sleep(1)
        # print(data)

        if recursions >= 2:
            print('pruning')
            recursions = 0
            print(len(heuristic_scores))
            heuristic_scores.sort(reverse=True,key = lambda data: data[2])
            print('top survivor:',heuristic_scores[0][0],heuristic_scores[0][2])
            #ai optimisation: it picks the best path to route on based on what it already explored.
            data = [pagedata[:-1] for pagedata in heuristic_scores[:10]]
            heuristic_scores = []

        print(len(data))
        async with aiohttp.ClientSession(timeout=clientTimeout) as session:
            chunks = chunker(data,max_pages_to_check)
            for chunk in tqdm(chunks,total=len(data)//max_pages_to_check): #this nonesense ensures that tasks doesnt get too long
                for page_name, path in chunk:
                    new_data = harvest_data(page_name,path,session)
                    tasks.append(new_data)
                task_response += await asyncio.gather(*tasks)
                tasks = []
        print('saving...')
        connection.commit()

        print('parsing...')
        data = []
        for data_slice in tqdm(task_response):
            data += data_slice

        recursions += 1

    return response
        

        

            


async def main():
    print(await hunt('Associazione_Nazionale_Felina_Italiana','Lie',5000))

asyncio.run(main())

from itertools import islice