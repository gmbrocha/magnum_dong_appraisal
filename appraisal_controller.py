import json

import requests
from flask import Flask, render_template, redirect, url_for, jsonify

app = Flask(__name__)


@app.route('/post-db', methods=['POST'])
def post_db():
    response = requests.post(f'http://localhost:5002/post-db')
    if response.status_code == 200:
        print('db updated successfully.')
        return
    else:
        return redirect(url_for('index'))


@app.route('/get-prices/<item_text>', methods=['POST'])
def get_prices(item_text):
    # get type ids from db service
    # response = requests.get(f'http://localhost:5002/get-type-ids/{item_text}')
    # type_ids = json.loads(response.text)

    # call to db service get_prices (actual appraisal) -- response will be a dict once loaded
    response = requests.get(f'http://localhost:5002/get-prices/{item_text}')

    if response.status_code == 200:
        items_dct = json.loads(response.text)
        return jsonify(items_dct)
    else:
        print(f'Error: {response.status_code}')
        redirect(url_for('index'))


if __name__ == '__main__':

    # run on port 5001
    app.run(host='0.0.0.0', port=5001)