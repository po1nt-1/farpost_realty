import sys
from pprint import pprint
from time import time

import pymongo
import selenium
from pymongo import MongoClient
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options


client = MongoClient()
db = client["db"]
collection = db["farpost"]


with Firefox() as driver:
    print("Подготовка...")
    driver.get("https://www.farpost.ru/vladivostok/"
               "realty/sell_flats/?page=1")
    max_pages = -1
    while max_pages == -1:
        try:
            max_pages = driver.find_element_by_css_selector(
                'span.pageCount').text.split(' ')[2]
            max_pages = int(max_pages)
        except IndexError:
            max_pages == -1
        except selenium.common.exceptions.NoSuchElementException:
            max_pages == -1

    print("Начало парсинга")
    total_start = time()
    for i in range(1, max_pages + 1):
        local_start = time()

        driver.get(
            "https://www.farpost.ru/vladivostok/"
            f"realty/sell_flats/?page={i}")
        raw_data = driver.find_element_by_class_name(
            'native').find_elements_by_tag_name('td')[1:]

        ads = []
        for raw_ad in raw_data:
            ad = {"url": "", "address": "", "price": "",
                  "district": "", "type_": "", "area": ""}

            try:
                url = raw_ad.find_element_by_css_selector(
                    'a[href^="/vladivostok/realty"]').get_attribute('href')
                ad.update({"url": url})
            except selenium.common.exceptions.NoSuchElementException:
                pass

            try:
                address = raw_ad.find_element_by_css_selector(
                    'a[class$="bull-item__self-link '
                    'auto-shy"]').text.split(', ')
                if len(address) == 2:
                    ad.update({"address": address[1]})
            except selenium.common.exceptions.NoSuchElementException:
                pass

            try:
                price = raw_ad.find_element_by_css_selector(
                    'span.price-block__price').text
                ad.update({"price": price.replace(
                    ' ', '').replace('₽', '')})
            except selenium.common.exceptions.NoSuchElementException:
                pass

            try:
                district = raw_ad.find_element_by_css_selector(
                    'div.bull-item__annotation-row').text
                district = district[::-1].replace(' ,', ';', 2)[::-1]
                ad.update({"district": district.split(';')[0]})
            except selenium.common.exceptions.NoSuchElementException:
                pass

            try:
                type_ = raw_ad.find_element_by_css_selector(
                    'a[class$="bull-item__self-link '
                    'auto-shy"]').text.split(', ')
                if len(address) == 2:
                    ad.update({"type_": type_[0]})
            except selenium.common.exceptions.NoSuchElementException:
                pass

            try:
                area = raw_ad.find_element_by_css_selector(
                    'div.bull-item__annotation-row').text
                area = area[::-1].replace(' ,', ';', 2)[::-1]
                area = area.split(';')[-1]
                ad.update({"area": area.replace(' кв. м.', '')})
            except selenium.common.exceptions.NoSuchElementException:
                pass

            data = [i for i in collection.find(ad)]
            if len(data) != 0:
                print("skipped. ", end="")
                continue

            ads.append(ad)

        try:
            collection.insert_many(ads)
        except TypeError:
            pass
        local_stop = time()

        print(f'Страница {i} из {max_pages + 1}', '\tОбъявлений: ', len(ads),
              '\tВремя в этой странице: ', local_stop - local_start)
    total_stop = time()

    print(
        f"Всего затраченно времени: {(total_stop - total_start) / 60} минут")
