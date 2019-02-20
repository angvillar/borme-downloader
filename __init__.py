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
from bs4 import BeautifulSoup


class SummaryResource:
    url_base = 'https://boe.es/diario_borme/xml.php'

    def __init__(self, date):
        """
        date should be from 2009/01/01 to today
        """
        self.__date = date

    @property
    def content(self):
        """
        remove the file write part, this class should just
        download documents
        check status code
        """

        async def _fetch():
            params = {'id': 'BORME-S-' + self.__date.strftime('%Y%m%d')}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url_base, params=params) as response:
                    return await response.read()

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_fetch())

    @property
    def content1(self):
        with open('summary.xml', 'rb') as f:
            return f.read()


class Summary:

    def __init__(self, summary):
        self.__summary = summary

    @property
    def __parsed(self):
        """
        memoize
        check exceptions
        :return:
        """
        return BeautifulSoup(self.__summary.content1, 'xml')

    def __parse_meta(self):
        parsed = self.__parsed
        meta = parsed.sumario.meta
        return {'date_next': meta.fechaSig.string}

    def __parse_provinces(self):
        parsed = self.__parsed
        provinces = parsed.sumario.diario.find('seccion', {'num': 'A'}).findAll('item')

        result = {}
        for province in provinces:
            result[province.titulo.string] = {
                'size': province.urlPdf['szBytes'],
                'url': province.urlPdf.string
            }
        return result

    @property
    def content(self):
        meta = self.__parse_meta()
        provinces = self.__parse_provinces()

        return {**meta, **provinces}


# summary = Summary(SummaryResource(datetime.date(2014, 1, 2)))
# print(summary.content)


class Doc:
    url_base = 'https://www.boe.es/'

    def __init__(self, date, province):
        self.__date = date
        self.__province = province

    @property
    def __summary(self):
        return Summary(SummaryResource(self.__date))

    @property
    def __url(self):
        return urljoin(self.url_base, self.__summary.content[self.__province]['url'])

    def fetch(self):
        """
        remove the file write part, this class should just
        download documents
        """

        async def _fetch():
            async with aiohttp.ClientSession() as session:
                async with session.get(self.__url) as response:
                    filename = os.path.basename(self.__url)
                    with open(filename, 'wb') as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break;
                            f.write(chunk)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(_fetch())

# doc = Doc(datetime.date(2019, 2, 14), 'MADRID')
# doc.fetch()
