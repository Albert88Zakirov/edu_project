import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import csv

#HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
#        'accept': '*/*'}
userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'

options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
#options.add_argument("user-data-dir=./chromeprofile")
options.add_argument(f"user-agent={userAgent}")
options.add_argument('--disable-extensions')
options.add_argument("--incognito")
options.add_argument("--disable-plugins-discovery")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)

driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
     "source": """
          const newProto = navigator.__proto__
          delete newProto.webdriver
          navigator.__proto__ = newProto
          """
    })

#driver = webdriver.Chrome()

urls = open('urls_new.csv')
num_lines = sum(1 for line in open('urls_new.csv'))
inum = 0
for URL in urls:
    inum += 1
    print('Парсинг {} из {} веб-страниц'.format(inum, num_lines))

    try:
        driver.get(URL)
    except Exception:
        print('Парсинг {} веб-страницы не удался'.format(URL))

    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    while True:
        try:
            show_more_btn = driver.find_element(By.CSS_SELECTOR, '.event__more.event__more--static')
            show_more_btn.click()
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        except Exception:
            break

    container = driver.find_element(By.CSS_SELECTOR, 'div[id=live-table]').get_attribute('innerHTML')
    soup = BeautifulSoup(container, 'html.parser')
    matches = soup.select('.event__match.event__match--static.event__match--twoLine')
    years = driver.find_element(By.CSS_SELECTOR, '.heading__info').text
    years_par = years.split('/')
    if len(years_par) == 1:
        years_changed = years_par[0]
    else:
        years_changed = years_par[0] + '-' + years_par[1]
    how_much_years = len(years_par)

    country = driver.find_element(By.CSS_SELECTOR, '.breadcrumb').get_attribute('innerHTML')
    country_soup = BeautifulSoup(country, 'html.parser')
    country_name = country_soup.select('.breadcrumb__link')[1].text
    league = driver.find_element(By.CSS_SELECTOR, '.heading__name').text

    FILE = '{}_{}_games {}.csv'.format(country_name, league, years_changed)

    games = []
    for match in matches:
        if how_much_years == 1:
            addyear = years_par[0]
        elif int(match.select_one('div.event__time').text.split('.')[1]) in [7, 8, 9, 10, 11, 12]:
            addyear = years_par[0]
        else:
            addyear = years_par[1]

        if match.select_one('div.event__part.event__part--home.event__part--2') is None:
            score_home_main_time = match.select_one('div.event__score.event__score--home').text
            score_away_main_time = match.select_one('div.event__score.event__score--away').text
        else:
            score_home_main_time = match.select_one('div.event__part.event__part--home.event__part--2').text
            score_away_main_time = match.select_one('div.event__part.event__part--away.event__part--2').text

        games.append({
            'match_type': match.find_previous('div', 'event__header--noExpand').select_one('span.event__title--name').text,
            # 'match_type_stage': match.find_previous('div', 'event__round--static').text,
            'match_type_stage': '',
            'match_date': match.select_one('div.event__time').text.replace('. ', '.'+ str(addyear) + ' '),
            'match_time': match.select_one('div.event__time').text,
            'team_home': match.select_one('div.event__participant.event__participant--home').text,
            'team_away': match.select_one('div.event__participant.event__participant--away').text,
            'score_home': match.select_one('div.event__score.event__score--home').text,
            'score_away': match.select_one('div.event__score.event__score--away').text,
            'score_home_main_time': score_home_main_time,
            'score_away_main_time': score_away_main_time,
            'season': years,
            'country': country_name,
            'league': league
        })


    with open(FILE, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['match_type', 'match_type_stage', 'match_date', 'match_time', 'team_home', 'team_away',
                         'score_home', 'score_away', 'score_home_main_time', 'score_away_main_time',
                         'season', 'country', 'league'])
        for game in games:
            writer.writerow([game['match_type'], game['match_type_stage'], game['match_date'],
                             game['match_time'], game['team_home'], game['team_away'],
                             game['score_home'], game['score_away'], game['score_home_main_time'],
                             game['score_away_main_time'], game['season'], game['country'],
                             game['league']])

    time.sleep(3)
