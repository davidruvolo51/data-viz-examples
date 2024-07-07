
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from tqdm import tqdm
from datatable import dt, f, fread
import time


def pace_to_time(value):
    """Convert pace MM:SS to minutes as an int"""
    pace = [int(d) for d in value.split(',')]
    return datetime(2023, 12, 3, 0, *pace)


def time_to_datetime(value):
    """Convert time (HH:MM:SS) to datetime"""
    time = [int(d) for d in value.split(':')]
    return datetime(2023, 12, 3, *time)


URL = "https://resultados.valenciaciudaddelrunning.com/en/maraton-clasificados.php?y=2023"

BROWSER = webdriver.Firefox()
BROWSER.get(URL)

# ///////////////////////////////////////////////////////////////////////////////

# ~ 1 ~
# Retrieve race results by Men and Women

# extract column headers
table = BROWSER.find_element(by=By.CSS_SELECTOR, value='table#tabModulos')
theaders = table.find_elements(by=By.CSS_SELECTOR, value='thead tr th span')
headers = [th.text for th in theaders]


# get pagination buttons
firstPageBtn = BROWSER.find_element(
    By.CSS_SELECTOR, 'a.paginate_button[data-dt-idx="1"]')

firstPageBtn.click()


# prepare to extract top 250 men and women
views = {2: 'Women Ranking', 1: 'Men Ranking'}
pages = range(1, 6, 1)
results = []

for view in views.keys():
    print('Extracting data from view', views[view])

    selectInput = BROWSER.find_element(
        By.CSS_SELECTOR, f'#selgeneral option[value="{view}"]')
    selectInput.click()

    time.sleep(1)

    print('Pulling results from view....')
    for page in tqdm(pages):
        table = BROWSER.find_element(By.CSS_SELECTOR, 'table#tabModulos')
        trows = table.find_elements(By.CSS_SELECTOR, 'tbody tr')
        for row in trows:
            cells = row.find_elements(By.CSS_SELECTOR, 'td')
            row_data = {}
            for index, cell in enumerate(cells):
                try:
                    cell_href = cell.find_element(By.CSS_SELECTOR, 'a')
                    row_data[headers[index]] = cell_href.text
                except NoSuchElementException:
                    row_data[headers[index]] = cell.text
            results.append(row_data)

        nextPageBtn = BROWSER.find_element(
            By.CSS_SELECTOR, 'a.paginate_button.next')
        nextPageBtn.click()


results_dt = dt.Frame(results)
results_dt.to_csv('datasets/results.csv')

# ///////////////////////////////////////

# ~ 2 ~
# Retrieve splits
# Using race numbers, search for runners and retreive splits

results_dt = fread('datasets/results.csv')
race_numbers = results_dt['RACE NUMBER'].to_list()[0]

split_headers = ['DISTANCE', 'TIEMPO', 'PARTIAL', 'PACE']
splits_data = []


for rnum in tqdm(race_numbers):
    BROWSER.get(URL)
    time.sleep(3)

    search_btn = BROWSER.find_element(
        By.CSS_SELECTOR,
        'ul.nav.nav-tabs li:nth-child(3) a'
    )
    search_btn.click()

    # ///////////////////////////////////////

    # search for runner by race number
    race_number_input = BROWSER.find_element(
        By.CSS_SELECTOR, 'input[name="txtdorsal"]'
    )

    race_number_input.send_keys(rnum)

    form_submit_btn = BROWSER.find_element(
        By.CSS_SELECTOR,
        'input[type="submit"]'
    )
    form_submit_btn.click()

    time.sleep(3)

    # ///////////////////////////////////////

    # click entry in results table
    try:
        racer_link = BROWSER.find_element(
            By.CSS_SELECTOR,
            'table tbody tr td a.blnk'
        )
        racer_link.click()
        time.sleep(3)

        # retrieve splits data
        splits = BROWSER.find_element(
            By.CSS_SELECTOR, 'table.table')

        splits_rows = splits.find_elements(
            By.CSS_SELECTOR, 'tbody tr')

        for split_row in splits_rows:
            split_row_cells = split_row.find_elements(
                By.CSS_SELECTOR, 'td')

            splits_row_data = {'RACE NUMBER': rnum}
            for sindex, split_cell in enumerate(split_row_cells):
                splits_row_data[
                    split_headers[sindex]] = split_cell.text
            splits_data.append(splits_row_data)

    except NoSuchElementException:
        print('Race number cannot be found')

splits_dt = dt.Frame(splits_data)
splits_dt.to_csv('./datasets/splits.csv')


# ///////////////////////////////////////////////////////////////////////////////

# PREPARE DATA

results_dt = fread('data/results.csv')
splits_dt = fread('data/splits.csv')

# set column names of results_dt
results_dt.names = {
    'OFFICIAL POS.': 'OFFICIAL_POSITION',
    'RACE NUMBER': 'RACE_NUMBER',
    'OFFICIAL TIME': 'OFFICIAL_TIME',
    'REAL AVERAGE': 'REAL_AVERAGE',
    'REAL TIME': 'REAL_TIME'
}

# set column names of splits data
splits_dt.names = {
    'RACE NUMBER': 'RACE_NUMBER',
    'TIEMPO': 'TIME'
}

results_dt['GENDER'] = dt.Frame([
    value.split('-')[0] if bool(value) else value
    for value in results_dt['CATEGORY'].to_list()[0]
])

# join runner information
runners_dt = results_dt[
    :, (f.RACE_NUMBER, f.NAME, f.GENDER, f.OFFICIAL_POSITION)]
runners_dt.key = 'RACE_NUMBER'

splits_dt = splits_dt[:, :, dt.join(runners_dt)]

# group runners by top 10 finishers
splits_dt['POSITION_GROUPING'] = dt.Frame([
    'Top 10' if value <= 10 else (
        'Top 25' if 25 <= value >= 11 else 'Other'
    )
    for value in splits_dt['OFFICIAL_POSITION'].to_list()[0]
])

# convert PACE to int
splits_dt['PACE_DATETIME'] = dt.Frame([
    pace_to_time(value) if bool(value) else None
    for value in splits_dt['PACE'].to_list()[0]
])

# bin times to datetime

splits_dt['TIME_DATETIME'] = dt.Frame([
    time_to_datetime(value) if bool(value) else None
    for value in splits_dt['TIME'].to_list()[0]
])

splits_dt['PARTIAL_DATETIME'] = dt.Frame([
    time_to_datetime(value) if value else None
    for value in splits_dt['PARTIAL'].to_list()[0]
])


results_dt.to_csv('./viz/src/data/marathon_results.csv')
splits_dt.to_csv('./viz/src/data/marathon_splits.csv')
