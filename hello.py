import atexit
import json
import os

from cloudant import Cloudant
from flask import Flask, render_template, request

app = Flask(__name__, static_url_path='')

db_name = 'mydb'
client = None
db = None

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
elif "CLOUDANT_URL" in os.environ:
    client = Cloudant(os.environ['CLOUDANT_USERNAME'], os.environ['CLOUDANT_PASSWORD'], url=os.environ['CLOUDANT_URL'], connect=True)
    db = client.create_database(db_name, throw_on_exists=False)
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)

port = int(os.getenv('PORT', 8000))

@app.route('/')
def index():
    db = client.create_database(db_name, throw_on_exists=False)
    orders = db['Orders']['data']
    customers = db['Customers']['data']
    return render_template(
        'index.html', 
        orders=orders,
        query_orders=orders, 
        customers=customers,
        city=""
    )

@app.route('/queryOrders', methods=["POST"])
def query_orders():
    db = client.create_database(db_name, throw_on_exists=False)
    city = request.form['city']
    orders = db['Orders']['data']
    customers = db['Customers']['data']
    customers_from_city_ids = list(map(
        lambda c: c['id'], 
        filter(lambda c: c['CustTown'] == city, customers))
    )
    if city != "":
        query_orders = list(filter(lambda order: order['id'] in customers_from_city_ids, orders))
    else:
        query_orders = orders

    return render_template(
        'index.html', 
        orders=orders,
        query_orders=query_orders, 
        customers=customers,
        city=city
    )


@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
