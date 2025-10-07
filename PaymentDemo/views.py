from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import base64
import json
import requests
import hashlib
import hmac
from django.http import HttpResponse
from Keys.keys import keys


def index(request):
    return render(request,'PaymentDemo/index.html')

def checkout(request):
    #URL de Web Service REST
    url = 'https://api.micuentaweb.pe/api-payment/V4/Charge/CreatePayment'

    #Encabezado Basic con concatenación de "usuario:contraseña" en base64
    auth = 'Basic ' + base64.b64encode(f"{keys["USERNAME"]}:{keys["PASSWORD"]}".encode('utf-8')).decode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': auth,
    }

    # Get data from POST or use defaults for demo
    data = {
        "amount": int(float(request.POST.get('amount', 100.00)) * 100),
        "currency": request.POST.get('currency', 'PEN'),
        "orderId": request.POST.get('orderId', 'DEMO-001'),
        "customer": {
            "email": request.POST.get('email', 'demo@email.com'),
            "firstName": request.POST.get('firstName', 'Demo'),
            "lastName": request.POST.get('lastName', 'User'),
            "phoneNumber": request.POST.get('phoneNumber', '999999999'),
            "identityType": request.POST.get('identityType', 'DNI'),
            "identityCode": request.POST.get('identityCode', '12345678'),
            "address": request.POST.get('address', 'Demo Address'),
            "country": request.POST.get('country', 'PE'),
            "state": request.POST.get('state', 'LIMA'),
            "city": request.POST.get('city', 'LIMA'),
            "zipCode": request.POST.get('zipCode', '15001'),
        }
    }

    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()

    if response_data['status'] != 'SUCCESS':
        #raise Exception
        raise Exception(f"Payment creation failed: {response_data.get('answer', {}).get('errorMessage', 'Unknown error')}")
    
    token = response_data['answer']['formToken']
    return render(request, 'PaymentDemo/checkout.html', {'token': token, 'publickey': keys['PUBLIC_KEY']})

@csrf_exempt
def result(request):
    if not request.POST: 
        raise Exception("No post data received!")

    #Validación de firma
    if not checkHash(request.POST, keys["HMACSHA256"]) : 
        raise Exception("Invalid signature")

    answer_json = json.loads(request.POST['kr-answer'])
    krAnswerData = json.dumps(answer_json, indent=2)
    postData = json.dumps(request.POST, indent=4)

    answer_json["orderDetails"]["orderTotalAmount"] = answer_json["orderDetails"]["orderTotalAmount"] / 100

    return render(request, 'PaymentDemo/result.html', {'answer': answer_json, 'postData': postData, 'krAnswerData': krAnswerData})

@csrf_exempt
def ipn(request):
    if not request.POST: 
        raise Exception("No post data received!")

    #Validación de firma en IPN
    if not checkHash(request.POST, keys["PASSWORD"]) : 
        raise Exception("Invalid signature")
    
    answer = json.loads(request.POST['kr-answer']) 
    transaction = answer['transactions'][0]

    #Verificar orderStatus: PAID / UNPAID
    orderStatus = answer['orderStatus']
    orderId = answer['orderDetails']['orderId']
    transactionUuid = transaction['uuid']

    return HttpResponse(status=200, content=f"OK! OrderStatus is {orderStatus} ")

def checkHash(response, key):

    answer = response['kr-answer'].encode('utf-8')

    calculateHash = hmac.new(key.encode('utf-8'), answer, hashlib.sha256).hexdigest()

    return calculateHash == response['kr-hash']
