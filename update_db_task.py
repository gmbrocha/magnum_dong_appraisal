import json
import sqlite3

import requests
from celery import Celery
import os

#  celery -A update_db_task worker --loglevel=INFO

os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

app = Celery('tasks', broker='amqp://guest@localhost//')


@app.task
def update_db():
    """
            This function is to be run twice or three times daily to keep an updated ab containing all the eve orders (buys
            and sells) in Jita 4-4
            """
    response = requests.get(f"https://esi.evetech.net/latest/markets/10000002/orders/?order_type=all")

    # get the number of pages remaining - each request only responds with 1000 items max
    num_pages = response.headers.get('X-Pages')

    if response.status_code == 200:

        orders = json.loads(response.text)

        # make succeeding calls up to the total number of pages starting at the second page
        for i in range(2, int(num_pages) + 1):
            response = requests.get(
                f"https://esi.evetech.net/latest/markets/10000002/orders/?order_type=all&page={i}")
            if i % 50 == 0:  # update on progress, it can be up to 350 calls or more
                print(f'call # {i}')
            if response.status_code == 200:
                temp_orders = json.loads(response.text)
                orders += temp_orders
            else:
                print(f'Error {response.status_code}')
                continue
    else:
        print(f'Error {response.status_code}')
        return  # unsure what to return here

    # gets a list of type id (ints) to pass to get_item_names --> this needs to be cleaned up
    type_ids = orders_to_type_id_list(orders)
    names_w_id = get_item_names(type_ids)  # returns tuples with names and type id

    items = {}
    for item in orders:
        type_id = item['type_id']
        item_price = item['price']

        # check if item in item_prices already or not
        if type_id not in items:
            if item['is_buy_order'] is True:
                items[type_id] = {'max_buy': item_price}
            elif item['is_buy_order'] is False:
                items[type_id] = {'min_sell': item_price}
        # if item already entered into the dict, check buy or sell and -
        if type_id in items:
            if item['is_buy_order'] is True:
                # if a sell order was entered first for this id prior, this conditional cleans that up - otherwise
                # the max_buy key won't exist, and it will throw an error
                if items[type_id].get('max_buy') is None:
                    items[type_id]['max_buy'] = item_price
                else:
                    curr_price = items[type_id]['max_buy']
                    items[type_id]['max_buy']: max(item_price, curr_price)
            elif item['is_buy_order'] is False:
                # same as above, this conditional handles the case where a buy order was entered for the id first
                if items[type_id].get('min_sell') is None:
                    items[type_id]['min_sell'] = item_price
                else:
                    curr_price = items[type_id]['min_sell']
                    items[type_id]['min_sell'] = min(item_price, curr_price)

    # iterate the tuples containing ('item name', type id) and add the names of the items into the dict
    for tup in names_w_id:
        items[tup[1]]['name'] = tup[0]  # add name as key with the item name as value

    # this may be unnecessary - it adds either min_sell or max_buy keys so that the sqlite logic doesn't fail
    for item in items:
        if items[item].get("min_sell") is None:
            items[item]['min_sell'] = None
        if items[item].get("max_buy") is None:
            items[item]['max_buy'] = None

    try:
        sqliteConnection = sqlite3.connect('C:\\Users\\gmbro\\OneDrive\\Desktop\\esiDBtest\\db\\item-prices.db')
        cur = sqliteConnection.cursor()
        cur.execute("DROP TABLE IF EXISTS ITEM_PRICES")
        cur.execute("CREATE TABLE IF NOT EXISTS ITEM_PRICES("
                    "ITEM_NAME TEXT, "
                    "TYPE_ID INTEGER, "
                    "BUY_PRICE INTEGER, "
                    "SELL_PRICE INTEGER"
                    ")")
        for type_id, dct in items.items():
            insert_query = "INSERT INTO ITEM_PRICES(ITEM_NAME, TYPE_ID, BUY_PRICE, SELL_PRICE) VALUES(?,?,?,?)"
            cur.execute(insert_query, (
                dct['name'],
                type_id,
                dct['max_buy'],
                dct['min_sell']
            ))
            # commit changes to db
            sqliteConnection.commit()

    except sqlite3.Error as error:
        print('Error while connecting to sqlite', error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print('connection closed')
    return 'task completed'


def orders_to_type_id_list(dict_list: list):
    """
    USED BY POST_DB
    """
    type_ids = []
    for dct in dict_list:
        if dct['type_id'] not in type_ids:
            type_ids.append(dct['type_id'])
    return type_ids


def get_item_names(type_ids: list):
    """
    USED BY POST_DB
    """
    # make sub lists because the post request can only accept up to 1000 ids
    range_multiple = len(type_ids) // 1000
    copy_type_ids = type_ids.copy()  # in case?
    resp_package = []
    for i in range(range_multiple):
        temp_ids = []
        for j in range(1000):
            temp_id = copy_type_ids[j]
            temp_ids.append(temp_id)
        copy_type_ids = copy_type_ids[1000:]
        response = requests.post(f"https://esi.evetech.net/latest/universe/names/", json=temp_ids)
        if response.status_code == 200:
            resp_package += json.loads(response.text)
        else:
            print(f'Error {response.status_code}')
            continue

    # then the leftovers, make last call
    response = requests.post(f"https://esi.evetech.net/latest/universe/names/", json=type_ids[range_multiple*1000:])

    if response.status_code == 200:
        resp_package += json.loads(response.text)
    else:
        print(f'Error {response.status_code}')
        return # not sure how to handle errors or what to return

    name_w_id = []

    # iterate type id ints and also the response package (list of dicts) and find the names corresponding to each id
    for idx in type_ids:
        for dct in resp_package:
            if dct['category'] == 'inventory_type' and dct['id'] == idx:
                name_w_id.append((dct['name'], dct['id']))
    return name_w_id