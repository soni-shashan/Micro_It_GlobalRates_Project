from flask import Flask, render_template, request, jsonify
import requests
import json
from country_correncies import CURRENCY_COUNTRY_MAP
from datetime import datetime
import pytz

app = Flask(__name__)

API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

def get_exchange_rates():
    """Fetch the latest exchange rates from the API"""
    try:
        response = requests.get(API_URL)
        response.raise_for_status() 
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching exchange rates: {e}")
        return None

@app.route('/')
def index():
    exchange_data = get_exchange_rates()
    
    if not exchange_data:
        return render_template('error.html', message="Failed to fetch exchange rates")
    
    currencies = [(currency, f"{currency} - {CURRENCY_COUNTRY_MAP.get(currency, currency)}") 
                  for currency in sorted(exchange_data['rates'].keys())]
    timestamp = exchange_data.get('time_last_updated', 0)
    utc_time = datetime.fromtimestamp(timestamp, tz=pytz.UTC)

    ist = pytz.timezone('Asia/Kolkata')
    ist_time = utc_time.astimezone(ist)

    formatted_date = ist_time.strftime('%B %d, %Y, %I:%M:%S %p IST')
    
    return render_template('index.html', currencies=currencies, last_updated=formatted_date)

@app.route('/convert', methods=['POST'])
def convert():
    data = request.get_json()
    amount = float(data.get('amount', 0))
    from_currency = data.get('from_currency')
    to_currency = data.get('to_currency')
    
    if not all([amount, from_currency, to_currency]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    exchange_data = get_exchange_rates()
    
    if not exchange_data:
        return jsonify({'error': 'Failed to fetch exchange rates'}), 500
    
    rates = exchange_data['rates']
    
    if from_currency != 'USD':
        amount = amount / rates[from_currency]
    
    converted_amount = amount * rates[to_currency]
    
    return jsonify({
        'amount': amount if from_currency == 'USD' else amount * rates['USD'],
        'from_currency': from_currency,
        'to_currency': to_currency,
        'converted_amount': converted_amount,
        'rate': rates[to_currency] / (1 if from_currency == 'USD' else rates[from_currency])
    })

if __name__ == '__main__':
    app.run(debug=True)