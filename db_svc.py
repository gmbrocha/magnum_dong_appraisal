import json
import sqlite3
from flask import Flask, jsonify
import requests


app = Flask(__name__)


@app.route('/get-prices/<item_text>', methods=['GET'])
def get_prices(item_text):
    """
    """
    item_w_quant = split_textbox_str_quant(item_text)
    # call to db with filter from form data
    sqliteConnection = sqlite3.connect('./db/item-prices.db')
    cur = sqliteConnection.cursor()
    item_names = []
    for tup in item_w_quant:
        item_names.append(tup[0])

    placehold = ','.join('?' for _ in item_names)
    query = f"SELECT ITEM_NAME, BUY_PRICE, SELL_PRICE FROM ITEM_PRICES WHERE ITEM_NAME IN ({placehold})"
    cur.execute(query, item_names)

    result = cur.fetchall()

    response_buy_prices = {}
    for item_name, buy_price, sell_price in result:
        response_buy_prices[item_name] = {"buy_price": buy_price, "sell_price": sell_price}

    for el in item_w_quant:
        total_buy_at_ninety = round(float(response_buy_prices[el[0]]["buy_price"] * int(el[1])) * .9)
        response_buy_prices[el[0]]["total_price"] = total_buy_at_ninety
    return jsonify(response_buy_prices)


@app.route('/get-type-ids/<item_text>', methods=['GET'])
def get_type_ids(item_text):
    """
    """
    item_w_quant = split_textbox_str_quant(item_text)

    # item_names will be a list of names without the quantity
    item_names = []
    for item in item_w_quant:
        item_names.append(item[0])

    esi_response = requests.post(f"https://esi.evetech.net/latest/universe/ids/?datasource=tranquility&language=en",
                                 json=item_names)
    if esi_response.status_code == 200:
        esi_response_text = json.loads(esi_response.text)

    esi_response_ids = []
    for dct in esi_response_text['inventory_types']:
        esi_response_ids.append(dct['id'])

    return jsonify(esi_response_ids)


def split_textbox_str_quant(text):
    """
    USED BY GET_PRICES
    """
    # initialize empty list to hold the item and quantity; split the text
    item_w_quant = []
    items_no_ids_lst = text.splitlines()

    # iterate textarea list and split single string into list with a numeric quantity at the end
    for el in items_no_ids_lst:
        temp = el.split()
        quant = temp.pop()
        temp_rejoin = (' '.join(temp), quant)
        # append item name and quantity as a tuple, to the running list
        item_w_quant.append(temp_rejoin)
    return item_w_quant


if __name__ == '__main__':

    # update db
    # post_db()
    # run on port 5002
    app.run(host='0.0.0.0', port=5002)
