import datetime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup


class DateInRange:
    """
    check date_from <= date_to
    """
    date_from = datetime.date(2009, 1, 1)

    date_to = datetime.date.today()

    def __init__(self, date):
        if self.date_from <= date <= self.date_to:
            self.__date = date
        else:
            raise ValueError('date must be in {}..{}'.format(self.date_from, self.date_to))

    def __get__(self):
        return self.__date


class DocPDF:
    url_base = 'https://boe.es/'

    def __init__(self, url):
        self.__url = urljoin(self.url_base, url)

    @property
    def content(self):
        return requests.get(self.__url).content


class SummaryXML:
    url_base = 'https://boe.es/diario_borme/xml.php'

    date_from = datetime.date(2009, 1, 1)

    date_to = datetime.date.today()

    def __init__(self, date):
        if self.date_from <= date <= self.date_to:
            self.__date = date
        else:
            raise ValueError('date must be in {}..{}'.format(self.date_from, self.date_to))

    @property
    def content(self):
        params = {'id': 'BORME-S-' + self.__date.strftime('%Y%m%d')}
        r = requests.get(self.url_base, params=params)
        return r.content

    @property
    def content1(self):
        with open('files/summary.xml', 'rb') as f:
            return f.read()


class Province:

    def __init__(self, name, url, size):
        self.__name = name
        self.__url = url
        self.__size = size

    @property
    def name(self):
        return self.__name.strip().lower()

    @property
    def url(self):
        return self.__url

    @property
    def size(self):
        return int(self.__size)


class SummaryParsed:

    def __init__(self, summaryXML):
        self.__summaryXML = summaryXML

    @property
    def __soup(self):
        return BeautifulSoup(self.__summaryXML.content, 'xml')

    @property
    def date_next(self):
        if self.__soup.sumario.meta.fechaSig.string:
            day, month, year = map(
                lambda x: int(x.lstrip('0')),
                self.__soup.sumario.meta.fechaSig.string.split('/')
            )
            return datetime.date(year, month, day)
        else:
            return None

    def province_by_name(self, name):
        province_xml = self.__soup.find('titulo', string=name).parent
        if province_xml:
            return Province(
                name=province_xml.titulo.string,
                url=province_xml.urlPdf.string,
                size=province_xml.urlPdf['szBytes']
            )
        else:
            return None


class Summary:

    def __init__(self, summaryParsed):
        self.__summaryParsed = summaryParsed

    @property
    def date_next(self):
        return self.__summaryParsed.date_next

    def doc_by_province(self, name):
        province = self.__summaryParsed.province_by_name(name)
        if province:
            return DocPDF(url=province.url)
        else:
            return None


class DocsPDF:

    def __init__(self, province, date_start, date_end=datetime.date.today()):
        self.__province = province
        self.__date_start = date_start
        self.__date_end = date_end
        self.__date_next = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.__date_next is None:
            self.__date_next = self.__date_start

        summary = Summary(SummaryParsed(SummaryXML(self.__date_next)))
        if summary.date_next is None or summary.date_next > self.__date_end:
            raise StopIteration
        else:
            self.__date_next = summary.date_next

        doc = summary.doc_by_province(self.__province)
        if doc:
            return doc.content
        else:
            return self.__next__()


# summary = Summary(SummaryParsed(SummaryXML(datetime.date(2019, 2, 22))))
# print(summary.date_next)

date_start = datetime.date(2019, 2, 20)
date_end = datetime.date(2019, 2, 22)
docs = DocsPDF('MADRID', date_start, date_end)

i = 0
for doc in docs:
    with open('pdfs/' + str(i), 'wb') as f:
        f.write(doc)
    i += 1
