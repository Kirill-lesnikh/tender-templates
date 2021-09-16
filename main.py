import requests
import json
import re
from lxml import etree
from os import mkdir, listdir, rename, walk


# setup
re_date = re.compile('(\d{4}-\d{2}-\d{2})')
re_time = re.compile('(\d{2}:\d{2}:\d{2})')
re_url = re.compile('https://smarttender.biz/.*/\d{8}/')
re_tender_folder = re.compile('\d{4}-\d{2}-\d{2}__\d{2}-\d{2}__\d{8}__.*')
re_tender_index = re.compile('\d{8}')
companies_arr = ["СУ24", "ДАККАР", "СПЕЦТЕХ ОСНАСТКА", "ЕЛЕКТРОСВІТЛОМОНТАЖ", "ФАБРИКА", "СВІТЛОЕЛЕКТРОБУД"]
usb_path = 'E:'
working_directory_name = 'Тендера'
key_file = 'scriptKeyCode'
usb_key = {key_file: 'iouwegjnrvktfmuerhwbnveikwjlrnviolwnvjkwr'}


# check given url
def parse_url(url: str):
    if url == '':
        print('String is empty')
        return None
    if url[-1] != '/':
        url = url + '/'
    print(url)
    try:
        result = re.search(re_url, url).group()
    except AttributeError:
        print("Link is not valid.")
    else:
        return result


def check_usb_device():
    file_key_value = open(f"{usb_path}/{key_file}.txt", 'r').read()
    if file_key_value != usb_key[key_file]:
        raise Exception("Check USB device. Keys doesn't match.")


def get_url():
    target_url = None
    counter = 0
    while target_url is None and counter < 3:
        target_url = parse_url(input('Link: '))
        if target_url is not None:
            break
        print(f"Attempt: #{counter + 1}")
        counter += 1
    if target_url is None:
        raise ValueError("No URL")
    return target_url


def get_general_data():
    re_index = re.compile('№\d{8}')
    url = get_url()
    response = requests.get(url)
    tree = etree.HTML(response.content)
    description = tree.xpath('//*[@name="keywords"]')[0].get('content')
    return {
            'general_data': json.loads(tree.xpath('//*[@type="application/ld+json"]')[0].text)['offers'],
            'description': description,
            'tender_index': re.search(re_index, description).group()[1:],
            'url': url
            }


def check_folder_system():
    usb_folders = sorted(listdir(f"{usb_path}/{working_directory_name}/"))
    if usb_folders != sorted(companies_arr):
        raise Exception("Check companies folders. They don't match")


def check_company_index(index):
    try:
        index = int(index)
    except ValueError:
        return print('Should be an Integer')
    companies_count = len(companies_arr)
    if index not in range(companies_count):
        return print(f"Index should be in range of 0 and {companies_count}")
    return index


def get_company_index_from_list():
    print("Companies list:")
    for index, company in enumerate(companies_arr):
        print(f"{index} - {company}")
    print("Select company by index:")
    chosen_company_index = None
    counter = 0
    while type(chosen_company_index) is not int and counter < 3:
        chosen_company_index = check_company_index(input())
        counter += 1
    return chosen_company_index


# constructs the year folder path
def get_year_folder(company_folder, year):
    folders = listdir(company_folder)
    for folder in folders:
        if int(folder[slice(4)]) == int(year):
            return f"{company_folder}/{folder}"
    return f"{company_folder}/{year} [0]"


def get_list_of_tender_folders(year_folder):
    tender_dirs = []
    for (dirpath, dirnames, filenames) in walk(year_folder):
        for dirname in dirnames:
            if re.search(re_tender_folder, dirname) is not None:
                tender_dirs.append(dirname)
        break
    return tender_dirs


# create tender template with all needed fodlers
def create_template():
    general_data = get_general_data()
    start_datetime = general_data['general_data']['availabilityStarts']
    end_datetime = general_data['general_data']['availabilityEnds']
    time_slice = slice(0, 5)
    start_date = re.search(re_date, start_datetime).group()
    # start_time = re.search(re_time, start_datetime).group()[time_slice].replace(':', '-')
    end_date = re.search(re_date, end_datetime).group()
    end_time = re.search(re_time, end_datetime).group()[time_slice].replace(':', '-')
    tender_name = input('Set tender name: ')
    tender_index = general_data['tender_index']

    # select company by index
    try:
        company_folder_name = companies_arr[get_company_index_from_list()]
        company_folder = f"{usb_path}/{working_directory_name}/{company_folder_name}"
    except TypeError:
        raise TypeError("Valid company index wasn't chosen")

    year_folder = get_year_folder(company_folder, start_date[slice(4)])

    # create year folder if it's not exist
    try:
        mkdir(year_folder)
    except FileExistsError:
        pass
    # create tender folder
    for folder in get_list_of_tender_folders(year_folder):
        if re.search(re_tender_index, folder).group() == tender_index:
            print('Tender with such index already exists. Check it out')
    tender_folder = f"{year_folder}/{end_date}__{end_time}__{tender_index}__{tender_name}"
    mkdir(tender_folder)
    mkdir(f"{tender_folder}/Закидка")
    mkdir(f"{tender_folder}/Подготовка")
    # create general data file
    f = open(f"{tender_folder}/Закупівля.txt", 'w')
    f.write(f"#{general_data['description']}\n{general_data['url']}")
    f.close()
    # TODO: implement shortcut file creation to open the tender link

    # update tender counter value on the folder
    tenders_in_folder_count = len(get_list_of_tender_folders(year_folder))
    rename(year_folder, re.sub('\[\d*]$', f"[{tenders_in_folder_count}]", year_folder))


def main():
    check_usb_device()
    check_folder_system()
    create_template()


if __name__ == '__main__':
    main()
