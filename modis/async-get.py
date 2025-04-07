#!/usr/bin/env python3

import asyncio
import aiohttp
import tomllib
import json
import datetime
import sys
import re
from pathlib import Path

from gibs_wmts import GIBS_WMTS

async def get(src_url, dest_path):
    '''Get url to file.
    '''
    async with aiohttp.ClientSession() as session:
        async with session.get(src_url) as response:

            print('<', src_url, datetime.datetime.now())

            print("Content-type:", response.headers['content-type'], "Status:", response.status)

            body = await response.read()
            if response.status == 200:
                # savepath = Path(f'img/{d.strftime('%Y-%m-%d')}/best/{z}/{y}/{x}.{wmts.Format}')
                Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
                with open(dest_path, 'wb') as f:
                    f.write(body)

    print('>', dest_path, datetime.datetime.now())

async def main(tomlfile, d, z):
    '''Get a tileset for the Northern Hemisphere.
    '''

    with open(tomlfile, 'rb') as f:
        params = tomllib.load(f)
        print(json.dumps(params['wmts'], indent=2), file=sys.stderr)
        wmts = GIBS_WMTS(**params['wmts'])

    xmax = 2**z
    ymax = 2**(z-1)
    xskip = min(xmax, 16)
    for y in range(ymax):
        for x in range(0, xmax, xskip):
            async with asyncio.TaskGroup() as tg:
                for dx in range(xskip):
                    src_url = wmts.tile(d, z, y, x+dx)
                    tg.create_task(get(src_url, f'{params['output']['Prefix']}{d.strftime('%Y-%m-%d')}/{z}/{y}/{x+dx}.{wmts.Format}'))

if __name__ == '__main__':

    for x in sys.argv[1:]:
        if re.search('toml$', x):
            tomlfile = x
        elif re.match(r'\d{8}', x):
            d = datetime.datetime.strptime(x, '%Y%m%d')
        elif re.match(r'\d', x):
            z = int(x)
    print((tomlfile, d, z))

    asyncio.run(main(tomlfile, d, z))
