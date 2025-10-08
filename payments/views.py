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


# Workshop Registration Views
def workshop_landing(request):
    """Landing page for the game development workshop"""
    return render(request, 'payments/workshop_landing.html')


def register_workshop(request):
    """Handle workshop registration and create payment"""
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')

        logger.info(f'Workshop registration attempt - Name: {name}, Phone: {phone}, Email: {email}')

        # Validate required fields
        if not name or not phone or not email:
            logger.warning('Missing required fields in workshop registration')
            return render(request, 'payments/workshop_landing.html', {
                'error': 'Todos los campos marcados con * son obligatorios'
            })

        # Create payment for registration (48 soles)
        try:
            logger.info('Creating payment for workshop registration...')
            payment = Payment.objects.create(amount=48.00)
            logger.info(f'Payment created successfully with ID: {payment.id}')

            logger.info(f'Redirecting to checkout: payment_id={payment.id}, name={name}, email={email}, phone={phone}')
            return redirect('payments:workshop_checkout', payment_id=payment.id, name=name, email=email, phone=phone)

        except Exception as e:
            logger.error(f'Error creating workshop registration: {str(e)}')
            logger.error(f'Error type: {type(e).__name__}')
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return render(request, 'payments/workshop_landing.html', {
                'error': f'Error al procesar la inscripción: {str(e)}'
            })

    logger.info('Redirecting to workshop landing (GET request)')
    return redirect('payments:workshop_landing')


def workshop_checkout(request, payment_id):
    """Show payment checkout for workshop registration"""
    payment = get_object_or_404(Payment, id=payment_id)

    # Get customer data from URL parameters
    name = request.GET.get('name', '')
    email = request.GET.get('email', '')
    phone = request.GET.get('phone', '')

    url = 'https://api.micuentaweb.pe/api-payment/V4/Charge/CreatePayment'
    auth = 'Basic ' + base64.b64encode(f"{keys['USERNAME']}:{keys['PASSWORD']}".encode('utf-8')).decode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': auth,
    }

    data = {
        "amount": int(float(payment.amount) * 100),  # 4800 centavos (48 soles)
        "currency": "PEN",
        "orderId": str(payment.id),
        "customer": {
            "email": email,
            "firstName": name.split()[0] if name else "Cliente",
            "lastName": " ".join(name.split()[1:]) if len(name.split()) > 1 else "Workshop",
            "phoneNumber": phone.strip(),
            "identityType": "DNI",  # Default
            "identityCode": "99999999",  # Placeholder
            "address": "Dirección por confirmar",
            "country": "PE",
            "state": "PIURA",
            "city": "PIURA",
            "zipCode": "20001"
        }
    }

    logger.debug(f'Creating workshop payment request: {data}')
    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()
    logger.debug(f'Workshop payment response: {response_data}')

    if response_data.get('status') != 'SUCCESS':
        error_msg = response_data.get('answer', {}).get('errorMessage', 'Error desconocido')
        logger.error(f'Payment creation failed: {error_msg}')
        return render(request, 'payments/workshop_landing.html', {
            'error': f'Error al procesar el pago: {error_msg}'
        })

    token = response_data['answer']['formToken']
    return render(request, 'payments/workshop_checkout.html', {
        'token': token,
        'publickey': keys['PUBLIC_KEY'],
        'payment': payment,
        'customer_name': name,
        'customer_email': email,
        'customer_phone': phone
    })
