from flask import Flask, request, render_template_string, jsonify
import requests
import base64
import os
from datetime import datetime

app = Flask(__name__)

# Daraja Sandbox settings
SHORTCODE = "174379"

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Wi-Fi Payment</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial;
            background: #f2f2f2;
            text-align: center;
            padding: 40px 20px;
        }

        .box {
            background: white;
            max-width: 400px;
            margin: auto;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 2px 10px #ccc;
        }

        input, button {
            width: 90%;
            padding: 14px;
            margin: 10px;
            border-radius: 8px;
            border: 1px solid #ccc;
            box-sizing: border-box;
        }

        button {
            background: #168a3d;
            color: white;
            border: none;
            font-size: 16px;
        }
    </style>
</head>

<body>

<div class="box">
    <h2>📶 Wi-Fi Payment</h2>

    <p>Enter your M-Pesa number and amount</p>

    <input id="phone" type="tel" placeholder="2547XXXXXXXX">

    <input id="amount" type="number" placeholder="Amount">

    <button onclick="pay()">Pay with M-Pesa</button>

    <p id="message"></p>
</div>

<script>
async function pay() {

    const phone = document.getElementById("phone").value;
    const amount = document.getElementById("amount").value;

    document.getElementById("message").innerText =
        "Sending M-Pesa request...";

    const response = await fetch("/pay", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            phone: phone,
            amount: amount
        })
    });

    const result = await response.json();

    document.getElementById("message").innerText =
        result.message;
}
</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


def get_access_token():

    consumer_key = os.environ.get("CONSUMER_KEY")
    consumer_secret = os.environ.get("CONSUMER_SECRET")

    url = (
        "https://sandbox.safaricom.co.ke/"
        "oauth/v1/generate?grant_type=client_credentials"
    )

    response = requests.get(
        url,
        auth=(consumer_key, consumer_secret)
    )

    response.raise_for_status()

    return response.json()["access_token"]


@app.route("/pay", methods=["POST"])
def pay():

    data = request.get_json()

    phone = data.get("phone")
    amount = int(data.get("amount"))

    passkey = os.environ.get("PASSKEY")
    callback_url = os.environ.get("CALLBACK_URL")

    access_token = get_access_token()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password_string = SHORTCODE + passkey + timestamp

    password = base64.b64encode(
        password_string.encode()
    ).decode()

    url = (
        "https://sandbox.safaricom.co.ke/"
        "mpesa/stkpush/v1/processrequest"
    )

    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": "WIFI",
        "TransactionDesc": "WiFi Payment"
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers
    )

    result = response.json()

    if response.ok:
        return jsonify({
            "message": "M-Pesa request sent. Check your phone.",
            "result": result
        })

    return jsonify({
        "message": "M-Pesa request failed.",
        "result": result
    }), 400


@app.route("/callback", methods=["POST"])
def callback():

    data = request.get_json()

    print("M-PESA CALLBACK:")
    print(data)

    return jsonify({
        "ResultCode": 0,
        "ResultDesc": "Accepted"
    })


@app.route("/health")
def health():
    return "Wi-Fi Payment Server is running!"


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
