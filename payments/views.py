import base64
import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import requests
from .models import Payment, Transaction
from Keys.keys import keys


from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import base64
import json
import requests
import hashlib
import hmac
from django.http import HttpResponse
from Keys.keys import keys




logger = logging.getLogger(__name__)

def dashboard(request):
    logger.info('Accessing payment dashboard')
    return render(request, 'payments/dashboard.html')

def create_payment(request):
    amount = request.POST.get('amount')
    logger.info(f'Creating payment for amount: {amount}')
    try:
        payment = Payment.objects.create(amount=amount)
        logger.info(f'Payment created successfully with ID: {payment.id}')
        return redirect('payments:checkout', payment_id=payment.id)
    except Exception as e:
        logger.error(f'Error creating payment: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


def checkout(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)

    url = 'https://api.micuentaweb.pe/api-payment/V4/Charge/CreatePayment'
    auth = 'Basic ' + base64.b64encode(f"{keys['USERNAME']}:{keys['PASSWORD']}".encode('utf-8')).decode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': auth,
    }

    data = {
        "amount": int(float(payment.amount) * 100),
        "currency": "PEN",
        "orderId": str(payment.id),
        "customer": {
            "email": "example@gmail.com",
            "firstName": "John",
            "lastName": "Doe",
            "phoneNumber": "999999999",
            "identityType": "DNI",
            "identityCode": "12345678",
            "address": "Example Address",
            "country": "PE",
            "state": "LIMA",
            "city": "LIMA",
            "zipCode": "15001"
        }
    }

    logger.debug(f'Sending payment request: {data}')
    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()
    logger.debug(f'Payment response: {response_data}')

    if response_data['status'] != 'SUCCESS':
        raise Exception(f"Payment creation failed: {response_data.get('answer', {}).get('errorMessage', 'Unknown error')}")

    token = response_data['answer']['formToken']
    return render(request, 'payments/checkout.html', {
        'token': token,
        'publickey': keys['PUBLIC_KEY']
    })


"""
def checkout(request, payment_id):
    try:
        payment = get_object_or_404(Payment, id=payment_id)
        
        #URL de Web Service REST
        url = 'https://api.micuentaweb.pe/api-payment/V4/Charge/CreatePayment'

        # Encabezado Basic con concatenación de "usuario:contraseña" en base64
        #Encabezado Basic con concatenación de "usuario:contraseña" en base64
        auth = 'Basic ' + base64.b64encode(f"{keys["USERNAME"]}:{keys["PASSWORD"]}".encode('utf-8')).decode('utf-8')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': auth,
        }

        # Datos del formulario de pago
        data = {
            "amount": int(float(payment.amount) * 100),
            "currency": "PEN",
            "orderId": str(payment.id),
            "customer": {
                "email": "example@gmail.com"
            },
            "formAction": "PAYMENT",
            "formId": "1",
            "notificationURL": "http://127.0.0.1:8000/payments/ipn/",
            "successURL": "http://127.0.0.1:8000/payments/success",
            "failureURL": "http://127.0.0.1:8000/payments/failed"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()
        
        if response_data['status'] != 'SUCCESS':
            raise Exception(f"Payment creation failed: {response_data.get('answer', {}).get('errorMessage', 'Unknown error')}")
        
        context = {
            'payment': payment,
            'token': response_data['answer']['formToken'],
            'publickey': keys['PUBLIC_KEY']
        }
        #return render(request, 'payments/checkout.html', context)
    
        token = response_data['answer']['formToken']
        return render(request, 'Demo/checkout.html', {'payment': payment, 'token': token, 'publickey': keys['PUBLIC_KEY']})

        
    except Exception as e:
        logger.error(f'Error in checkout: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)

"""



@csrf_exempt
def ipn_handler(request):
    logger.info('Received IPN notification')
    try:
        data = json.loads(request.body)
        logger.debug(f'IPN data received: {data}')
        
        # Get the payment ID from the order ID
        order_id = data.get('orderDetails', {}).get('orderId')
        if not order_id:
            raise ValueError('No order ID in IPN data')
            
        payment = Payment.objects.get(id=order_id)
        
        # Create transaction record
        Transaction.objects.create(
            payment=payment,
            transaction_id=data.get('orderDetails', {}).get('orderReference', ''),
            amount=float(data.get('orderDetails', {}).get('orderAmount', 0)) / 100,
            response_code=data.get('orderStatus', ''),
            response_message=json.dumps(data)
        )
        
        # Update payment status
        if data.get('orderStatus') == 'PAID':
            payment.status = Payment.COMPLETED
        else:
            payment.status = Payment.FAILED
        payment.save()
        
        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f'Error processing IPN: {str(e)}')
        return HttpResponse(status=500)

@csrf_exempt  # Only if you need to bypass CSRF for Izipay callbacks
def payment_success(request):
    if not request.POST: 
        raise Exception("No post data received!")

    #Validación de firma
    if not checkHash(request.POST, keys["HMACSHA256"]) : 
        raise Exception("Invalid signature")

    answer_json = json.loads(request.POST['kr-answer'])
    krAnswerData = json.dumps(answer_json, indent=2)
    postData = json.dumps(request.POST, indent=4)

    answer_json["orderDetails"]["orderTotalAmount"] = answer_json["orderDetails"]["orderTotalAmount"] / 100

    return render(request, 'payments/success.html', {'answer': answer_json, 'postData': postData, 'krAnswerData': krAnswerData})

    
@csrf_exempt  # Only if you need to bypass CSRF for Izipay callbacks
def payment_failed(request):
    logger.info('Payment failed')
    logger.debug(f'Failure parameters: {request.GET}')
    return render(request, 'payments/failed.html')










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

    return render(request, 'Demo/result.html', {'answer': answer_json, 'postData': postData, 'krAnswerData': krAnswerData})

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
