import requests
import re
import sqlite3

from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio

import time
import aiohttp
import asyncio

from urllib.parse import quote as encode_url


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


def harvest_urls(wiki_page,path):
    #cache
    
    cmd = cursor.execute(f'SELECT links from pages where name= "{wiki_page}" ') #bro if i get sql injected by a FUCKING WIKIPEDIA ARTICLE :sob:
    response = cmd.fetchone()
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
    else:
        return []

local_cache = {
    'Main_Page' : True, #anticheat,
    '' : True

}
def harvest_data(start_page,path,end_page):
    global local_cache
    if start_page.count(':') != 0:
        return False,[] #NO CHEATING!!!

    if local_cache.get(start_page):
        return False,[] #prune because we already scanned it
    
    data = harvest_urls(start_page,path)

    for page_name, path in data:
        if page_name == end_page:
            return page_name, path
        
    local_cache[start_page] = True
    return False, data

def hunt(start_page,end_page):

    data = []
    
    response = None
    data = [[start_page,[]]]
    while not response:

        print('checking values:')

        if len(data) == 0:
            print('Nothing stored in database.')
            response = []

        temp_data = []
        print('harvesting page data..')

        for page_name, path in tqdm(data):
            match_found, new_data = harvest_data(page_name,path,end_page)
            
            if match_found:
                print('match found!')
                return new_data
            
            temp_data += new_data


        print('Nothing found, searching deeper...')
        if len(data) == 0:
            print('nothing found in the database :c')
            return None
        
        data = temp_data

        

    return response
        

        

            

#NASA -> Lie
def main():
    start = time.time()
    print(hunt('Cat','Institut_Florimont'))
    print(time.time() - start)

main()