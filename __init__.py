"""
starts at 2/01/2009
saturdays and sundays there are not publications
some special days like national holidays there are not publications
base url: https://www.boe.es/diario_borme/
calendar uri: https://www.boe.es/diario_borme/calendarios.php
sample calendar uri: https://www.boe.es/borme/dias/2019/01/17/ y/m/d
TODO:
    download one document  in a day
    download all documents in a week
    download all documents in a month
    download all documents in a year
    UTC should be configurable
"""

import os
import datetime
from urllib.parse import urljoin
from functools import reduce
import aiohttp
import asyncio


class Doc:
    url_base = 'https://www.boe.es/borme/dias/'

    def __init__(self, date):
        self.__date = date

    @property
    def url(self):
        """
        ex.:
        https://www.boe.es/borme/dias/2019/01/17/ y/m/d
        """
        return reduce(urljoin, [
            self.url_base,
            self.__date.strftime('%Y/%m/%d') + '/',
            'pdfs/BORME-A-2019-31-28.pdf'
        ])

    async def __fetch(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                filename = os.path.basename(self.url)
                with open(filename, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break;
                        f.write(chunk)

    def fetch(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__fetch())


doc = Doc(datetime.date(2019, 2, 14))
print(doc.fetch())