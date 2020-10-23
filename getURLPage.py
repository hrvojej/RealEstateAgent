import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from timedelta import getDuration

class GetPage:
    def __init__(self, url, store_path, fileName):
        fileNameSuffix = str(time.time())
        self.fileNameSuffix = fileNameSuffix
        self.url = url
        if "https://www.njuskalo.hr/prodaja-stanova" not in self.url:
            self.soup = "NemaPraznaKriva"
        else:
            self.store_path = store_path
            self.fileName = fileName
            headers = [{'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'},
                       {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0'}]
            self.headers = headers

            #File path and name
            current_path = os.getcwd()
            self.store_path = store_path
            self.fileName = fileName
            pageNameFull = os.path.join(current_path, self.store_path, self.fileName+ self.fileNameSuffix)
            self.pageNameFull = pageNameFull
            self.soup = self.getPage()
            if self.soup == "NemaPraznaKriva":
                return
            else: self.getAdInfo()

    def getPage(self):
        session = requests.Session()
        retry = Retry(connect=7, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        while True:
            try:
                r = requests.get(self.url, headers=self.headers[1], timeout=5)
            except requests.ConnectionError as e:
                print("Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
                print(str(e))
                continue
            except requests.Timeout as e:
                print("Timeout Error")
                print(str(e))
                continue
            except requests.RequestException as e:
                print("General Error")
                print(str(e))
                continue
            except KeyboardInterrupt:
                print("Someone closed the program")
            break
        self.soup = BeautifulSoup(r.text, "lxml")
        for tag in self.soup.find_all("script"): self.soup.script.decompose()
        for tag in self.soup.find_all("style"): self.soup.style.decompose()
        print(self.soup.title.text)
        if "nepostoje" in self.soup.title.text:
            self.soup = "NemaPraznaKriva"
            return self.soup
        else: return self.soup

    def getAdInfo(self):
        adBasicInfo = {}
        adBasicList = []
        if self.soup == "NemaPraznaKriva":
            return pd.DataFrame()
        # Get all regular and paid ads
        if self.soup.findAll('li', attrs={'class': 'EntityList-item--Regular'}):
            adsRegular = self.soup.findAll('li', attrs={'class': 'EntityList-item--Regular'})
            for li in adsRegular:
                adBasicInfo = {
                    # u'ThumbSlika': li.img['data-src'],
                    u'ID': li.a['name'],
                    u'Naslov': li.a.get_text(),
                    u'Tip': li.select(".entity-description-main")[0].get_text().splitlines()[1].replace('\n', '').replace(
                                   '\r', '').replace(".", "").strip(),
                    u'Kvadratura': li.select(".entity-description-main")[0].get_text().splitlines()[2].replace(
                                   '\n',
                                   '').replace(
                                   '\r', '').replace("Stambena površina: ", "").strip(),
                    u'Lokacija': li.select(".entity-description-main")[0].get_text().splitlines()[3].replace(
                                   '\n',
                                   '').replace(
                                   '\r', '').replace("Lokacija: ", "").strip(),
                    u'CijenaKN': li.select(".price-item .price--hrk")[0].get_text().replace('\n', '').replace(
                                   '\r', '').replace(".", "").strip(),
                    u'CijenaEUR': li.select(".price-item .price--eur")[0].get_text().replace('\n', '').replace(
                                   '\r', '').replace(".", "").strip(),
                    u'VrijemeObjave': li.time['datetime'],
                    u'URL': li['data-href'],
                    u'TipOglasa': 'običan'}
                adBasicList.append(adBasicInfo)
            self.adBasicDF = pd.DataFrame(data=adBasicList)
            # Get all promoted ads
        if self.soup.findAll('li', attrs={'class': 'EntityList-item--VauVau'}):
            adsVauVau = self.soup.findAll('li', attrs={'class': 'EntityList-item--VauVau'})
            for li in adsVauVau:
                adBasicInfo = {
                # u'ThumbSlika': li.img['data-src'],
                u'ID': li.a['name'],
                u'Naslov': li.a.get_text(),
                u'Tip': li.select(".entity-description-main")[0].get_text().splitlines()[1].replace('\n',
                                                                                                                   '').replace(
                                   '\r', '').replace(".", "").strip(),
                u'Kvadratura': li.select(".entity-description-main")[0].get_text().splitlines()[2].replace(
                                   '\n',
                                   '').replace(
                                   '\r', '').replace("Stambena površina: ", "").strip(),
                u'Lokacija': li.select(".entity-description-main")[0].get_text().splitlines()[3].replace(
                                   '\n',
                                   '').replace(
                                   '\r', '').replace("Lokacija: ", "").strip(),
                u'CijenaKN': li.select(".price-item .price--hrk")[0].get_text().replace('\n', '').replace(
                                   '\r', '').replace(".", "").strip(),
                u'CijenaEUR': li.select(".price-item .price--eur")[0].get_text().replace('\n', '').replace(
                                   '\r', '').replace(".", "").strip(),
                u'VrijemeObjave': li.time['datetime'],
                u'URL': li['data-href'],
                u'TipOglasa': 'istaknut'}
            adBasicList.append(adBasicInfo)
        self.adBasicDF = pd.DataFrame(data=adBasicList)
        # self.adBasicDF['VrijemeDohvata'] = datetime.datetime.now()
        # self.adBasicDF['ThumbSlika'] = 'https:' + self.adBasicDF['ThumbSlika']
        # self.adBasicDF.drop(['ThumbSlika'], axis=1, inplace=True)
        self.adBasicDF['VrijemeObjave'] = pd.to_datetime(self.adBasicDF['VrijemeObjave'].replace('T', ' ', regex=True).str.split('+').str[
            0]).dt.strftime('%d.%m.%Y %H:%M:%S')
        self.adBasicDF['ObjavljenPrije'] = self.adBasicDF.apply(lambda row: getDuration(row.VrijemeObjave), axis=1)
        self.adBasicDF['CijenaKN'] = self.adBasicDF['CijenaKN'].str.replace(u'\xa0', u'')
        self.adBasicDF['CijenaKN'] = self.adBasicDF['CijenaKN'].str.replace(u'kn', u'').astype(int)
        self.adBasicDF['CijenaEUR'] = self.adBasicDF['CijenaEUR'].str.replace(u'\xa0', u'')
        self.adBasicDF['CijenaEUR'] = self.adBasicDF['CijenaEUR'].str.replace(u'€ ~', u'').astype(int)
        self.adBasicDF['Kvadratura'] = self.adBasicDF['Kvadratura'].str.replace(u'\xa0', u'')
        self.adBasicDF['Kvadratura'] = round(self.adBasicDF['Kvadratura'].str.replace(u'm2', u'').astype(float)).astype(int)
        self.adBasicDF['URL']="https://njuskalo.hr" + self.adBasicDF['URL']
        #self.adBasicDF.to_csv(self.pageNameFull + ".csv", sep='|', encoding='utf-8', index=False)
        # self.adBasicDF.to_excel(self.pageNameFull + ".xlsx", encoding='utf-8', index=False)
        return self.adBasicDF

# getPage = GetPage("https://www.njuskalo.hr/prodaja-stanova/zagreb",
#         "data",
#         "page")
# pageDF = getPage.getAdInfo()
# print(pageDF)
# print(pageDF.VrijemeObjave)
# print(pageDF.ObjavljenPrije)



