#!/usr/bin/python3

import argparse
import datetime
import os
import sys
import time

from bs4 import BeautifulSoup
import lxml.html
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

court_list = ["芝公園", "日比谷公園", "木場公園", "猿江恩賜公園"]
court_list2 = ['大井ふ頭海浜公園Ａ']
court_list3 = ["有明テニスの森公園イン"]

time_slot_list = [9, 11, 13, 15, 17, 19]
time_slot_list2 = [7, 9, 11, 13, 15, 17, 19]

try:
    Linetoken = os.environ["LINE_TOKEN"]
    ID = os.environ["ReserveWebID"]
    passwd = os.environ["ReserveWebPass"]
except KeyError:
    print("Please set the environment variable.")
    sys.exit()


class Reservation:
    def __init__(self):
        options = Options()
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--proxy-server="direct://"')
        options.add_argument('--proxy-bypass-list=*')
        # options.add_argument('--start-maximized')
        options.add_argument('--headless')

        DRIVER_PATH = '/usr/local/bin/chromedriver'
        self.driver = webdriver.Chrome(executable_path=DRIVER_PATH, chrome_options=options)
        url = 'https://yoyaku.sports.metro.tokyo.lg.jp/user/view/user/homeIndex.html'
        self.driver.get(url)

    def click_button(self, selector):
        self.driver.find_element_by_css_selector(selector).click()

    def input_text(self, selector, text):
        self.driver.find_element_by_css_selector(selector).send_keys(text)

    def click_specified_calendar_day(self, reserv_day):
        now = datetime.datetime.now()
        diff_month = int(reserv_day[4:6]) - int(now.month)
        if diff_month > 0:
            for i in range(diff_month):
                if i == 0:
                    self.click_button('#calendar > table:nth-child(1) > tbody > tr > td > div > a')
                else:
                    self.click_button('#calendar > table:nth-child(1) > tbody > tr > td > div > a:nth-child(2)')
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'lxml')  # または、'html.parser'
        results = soup.find_all("a", class_='calclick')
        for result in results:
            if result.attrs["onclick"].find(
                    reserv_day[0:4] + "," + str(int(reserv_day[4:6])) + "," + str(int(reserv_day[6:8]))) != -1:
                element = self.driver.find_element_by_link_text(result.string)
                element.click()
                return 0
        return 1

    def select_tennis_court(self, i):
        if i == 0:
            self.driver.find_elements_by_css_selector("#checked")[3].click()  # 人工芝コート
        else:
            self.driver.find_elements_by_css_selector("#checked")[2].click()  # ハードコート
            self.driver.find_elements_by_css_selector("#checked")[3].click()  # 人工芝コート

    def get_park_button_list(self, court_list):
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        buttons = self.driver.find_elements_by_css_selector('#srchBtn')
        places = soup.select('#bnamem')
        button_index_list = []
        for i, (place, button) in enumerate(zip(places, buttons)):
            if place.string in court_list:
                button_index_list.append(i)
        return button_index_list

    def login(self, ID, passwd):
        # self.click_button('#login')
        self.input_text("#userid", ID)
        self.input_text("#passwd", passwd)
        time.sleep(3)  # 秒
        self.click_button('#login')

    def get_timeslot_index_list(self, from_time, to_time, time_slot_list):
        timeslot_index_list = []
        for i, timeslot in enumerate(time_slot_list):
            if from_time <= timeslot and timeslot <= to_time:
                timeslot_index_list.append(i)
        return timeslot_index_list

    def search_vacant_timeslot(self, i, timeslot_index_list, dom):
        for timeslot_index in timeslot_index_list:
            xpath = "/html/body/div/form[2]/table/tbody/tr/td[2]/div/table[1]/tbody/tr[2]/td/div/div/table[" + \
                    str(i + 1) + "]/tbody/tr[4]/td[" + str(timeslot_index + 1) + "]/div/div/img"
            element_of_dom = dom.xpath(xpath)
            if element_of_dom[0].attrib["alt"] == "空き":
                self.click_button('#doReserve')
                self.login(ID, passwd)
                self.driver.find_element_by_xpath(xpath).click()
                return 1, timeslot_index
        return 0, None

    def search_vacant_place_and_timeslot(self, timeslot_index_list, court_list):
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        results = soup.select('#bnamem')  # 場所の名前を一覧化
        dom = lxml.html.fromstring(html)

        for court_name in court_list:  # 探したい場所配列をスキャン
            for index, result in enumerate(results):
                if court_name in result.contents[0]:
                    is_clicked, timeslot_index = self.search_vacant_timeslot(index, timeslot_index_list, dom)
                    if is_clicked:
                        return 1, court_name, timeslot_index
        return 0, None, None

    def close_driver(self):
        self.driver.quit()

    def refresh_page(self):
        self.driver.refresh()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='set time and reserve date.')
    parser.add_argument('-fr', type=int, help='予約したい開始時間帯　ここから')
    parser.add_argument('-to', type=int, help='予約したい開始時間帯　ここまで')
    parser.add_argument('-date', type=str, nargs='+', help='予約したい日付　yyyymmdd 複数指定可能')
    parser.add_argument('-inter', type=int, default=60, help='webを見に行くInterval秒数')

    args = parser.parse_args()
    from_time = args.fr
    to_time = args.to
    reserve_date_list = args.date
    interval = args.inter

    if not from_time or not to_time or not reserve_date_list:
        print("Please set the argument.")
        sys.exit()

    url = "https://notify-api.line.me/api/notify"
    headers = {'Authorization': 'Bearer ' + Linetoken}

    resevation_ = Reservation()
    timeslot_index_list = resevation_.get_timeslot_index_list(from_time, to_time, time_slot_list)
    timeslot_index_list2 = resevation_.get_timeslot_index_list(from_time, to_time, time_slot_list2)

    date_index = 0
    while 1:
        try:
            reserve_date = reserve_date_list[date_index]
            reserve_date_format = "{}年{}月{}日".format(reserve_date[0:4], reserve_date[4:6], reserve_date[6:8])

            # ここで種目を探す画面遷移が正常に行われない場合あり。時間が開くと画面遷移がうまくいかなくなる模様
            resevation_.click_button('#purposeSearch')  # 種目から探す
            if resevation_.click_specified_calendar_day(reserve_date):
                print("{} is not available datetime".format(reserve_date_format))
                del reserve_date_list[date_index]

            for i in range(2):
                resevation_.select_tennis_court(i)
                resevation_.click_button('#srchBtn')  # 上記の内容で検索する

                if i == 0:
                    is_clicked, court_name, timeslot_index = resevation_.search_vacant_place_and_timeslot(
                        timeslot_index_list, court_list)  # 芝コート予約検索
                else:
                    is_clicked, court_name, timeslot_index = resevation_.search_vacant_place_and_timeslot(
                        timeslot_index_list, court_list2)  # ハードコート予約検索 大井ふ頭海浜公園Ａ用
                    # is_clicked, court_name, timeslot_index = resevation_.search_vacant_place_and_timeslot(
                    #     timeslot_index_list2, court_list3)  # 有明テニス森用検索
                if is_clicked:
                    break
                resevation_.driver.back()

            if is_clicked:
                resevation_.click_button('#doReserve')
                resevation_.click_button('#apply')
                message = "{}のアカウント : {}で{} {}時から予約できました".format(ID, court_name, reserve_date_format,
                                                                 str(time_slot_list[timeslot_index]))
                r = requests.post(url, headers=headers, params={'message': message}, )
                print(message)
                resevation_.click_button('#doLogout')

                is_clicked = False
                del reserve_date_list[date_index]
            else:
                resevation_.click_button('#goBtn > img')

            if not reserve_date_list:
                resevation_.close_driver()
                exit()

            date_index += 1
            if date_index >= len(reserve_date_list):
                date_index = 0

            time.sleep(interval)
        # except NoSuchElementException:
        except Exception as e:
            dt_now = datetime.datetime.now()
            message = "{} / {} プログラムがストップしました".format(dt_now, e)
            r = requests.post(url, headers=headers, params={'message': message}, )
            print(message)
            resevation_.close_driver()
            exit()

##################################################
# 場所から探す -> 場所によってテニスだけではないので、個別対応になり、難しい。 -> テニスというワードで検索すればよかったか?
# click_button('#nameSearch > img')
# button_index_list = get_park_button_list(court_list)
# for button_index in button_index_list:
#     buttons = driver.find_elements_by_css_selector('#srchBtn')
#     buttons[button_index].click()
#     if get_vacant_timeslot(timeslot_index_list):
#         break
#     else:
#         driver.back()
