'''This program is aimed at performing works on the state task
in terms of updating and monitoring the completeness of information on projects
on the site fcpir.ru'''


import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import os

#---------------------------------Functions-------------------------------------------------


# Function finds max page for parsing
def max_page():
    items_list = []
    url = 'http://fcpir.ru/participation_in_program/contracts/'
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, features='html.parser')
    for items in soup.findAll('a', {'class':'pagination__item'}):
        items_list.append(items.string)

    items_list = list(set(items_list))
    pages = []
    for i in items_list:
        if i.isdigit():
            pages.append(int(i))
    return max(pages)


# Function finds links with projects, then returns list with project number and etap number with missing files
def trade_spider():
    list_of_contracts = []
    page = 1
    last_page = max_page()
    while page <= last_page:

        url = "http://fcpir.ru/participation_in_program/contracts/?PAGEN_1=" +str(page)
        source_code = requests.get(url)
        plain_text = source_code.text
        soup = BeautifulSoup(plain_text, features="html.parser")
        for link in soup.table("a"):
            if link.get("href").startswith("#"):
                continue
            else:
                href = "http://fcpir.ru" + link.get("href")         # Get link of project
                etap = get_single_item_data(href)                   # Get dictionary key - number of project
                for key, value in etap.items():                     # value - list of etaps
                    if len(value) < 1:
                        continue
                    else:
                        for v in value:
                            list_of_contracts.append([key, v])



        page+=1
    return list_of_contracts


# Function finds project number and etap numbers, then returns dictionary
def get_single_item_data(item_url):
    global contract_count

    l_1 = []
    l_2 = []
    dict = {}

    source_code = requests.get(item_url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, features="html.parser")
    for item1 in soup.tbody.findAll('p'):
        l_1.append(item1.string)                                                # List of project numbers
    for item2 in soup.tbody('tr', class_='tr-hr-dashed'):
        i_1 = item2.find_all('td')[0].string
        i_2 = item2.find('span').string[3:]
        i_3 = item2.find_all('div')[1].contents
        if (i_2 == "Этап принят") and (len(i_3) == 1):
            l_2.append(i_1)                                                     # List of etap numbers

    for item_name in soup.table("a", {'class':'panel-some-doc preview'}):
        contract_count += 1                                                     # Additional task to count project files

    dict[l_1[1]] =l_2
    return dict

#-----------------------------------------MAIN--------------------------------------------------------------

contract_count = 0

data = pd.read_excel('Contracts.xlsx')
data.rename(columns={'Номер': 'Project', 'Ответственный сотрудник дирекции' : 'Specialist'}, inplace=True)

features = np.array(trade_spider())
columns = ['Project', 'Etap']
frame = pd.DataFrame(data = features, columns = columns)


df = pd.merge(frame, data, on='Project', how='left')                            # Final dataframe to Excel



writer = pd.ExcelWriter('Missing_files.xlsx', engine='xlsxwriter')
df.to_excel(writer, sheet_name='Sheet1', index=False)

worksheet = writer.sheets['Sheet1']

worksheet.set_column(0,0,width=16)
worksheet.set_column(1,1,width=10)
worksheet.set_column(2,2,width=35)

writer.save()
print('There are ',contract_count, ' files in projects')
print('File with dataframe of missing files in projects completed!')

