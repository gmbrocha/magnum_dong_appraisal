import json
import requests as requests
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/appraisal', methods=['POST'])
def get_appraisal():

    if request.method == 'POST':
        # read in form data
        items_text = request.form.get("appraisal-items")

        # request prices from the controller/api
        response = requests.post(f'http://localhost:5001/get-prices/{items_text}')

        # if response from REST is good, return appraisal
        if response.status_code == 200:
            items_dct = json.loads(response.text)

            contract_price = 0
            for key, dct in items_dct.items():
                num = dct["sell_price"]
                dct["sell_price"] = f'{num:,}'
                num = dct["buy_price"]
                dct["buy_price"] = f'{num:,}'
                num = dct["total_price"]
                contract_price += num
                dct["total_price"] = f'{num:,}'
            contract_price = f'{contract_price:,}'
            return render_template('price_disp.html', items=items_dct, total=contract_price)
        else:
            print(f'Error: {response.status_code}')
            redirect(url_for('index'))
    else:
        return redirect(url_for('index.html'))


if __name__ == '__main__':

    # make calls to /post-db first to update the db file
    # requests.post('http://localhost:5001/post-db')

    # run the app on 5000
    app.run(host='0.0.0.0', port=5000)
