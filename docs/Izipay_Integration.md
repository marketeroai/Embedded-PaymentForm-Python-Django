# Izipay Django Integration Guide

This guide documents the correct implementation of Izipay payment integration in Django applications, based on lessons learned from debugging common issues.

## Project Structure

The repository provides three implementations:
- `Demo` - Original complex form (may have issues)
- `payments` - Production-ready full-featured app
- `PaymentDemo` - Ultra-simple demo with multiple payment amounts

## Prerequisites

1. **Django Project Setup**
   ```bash
   django-admin startproject yourproject
   cd yourproject
   python manage.py startapp payments
   ```

2. **Required Packages**
   ```bash
   pip install requests
   ```

3. **Directory Structure**
   ```
   yourproject/
   ├── payments/
   │   ├── static/
   │   ├── templates/payments/
   │   ├── models.py (Payment, Transaction)
   │   ├── views.py
   │   ├── urls.py
   │   └── apps.py
   ├── Keys/
   │   └── keys.py (store securely)
   └── templates/base.html
   ```

## Key Implementation Details

### 1. Credentials Configuration

Create `Keys/keys.py` with your Izipay credentials:
```python
keys = {
    "USERNAME": "your_username",
    "PASSWORD": "your_password",
    "PUBLIC_KEY": "your_public_key",
    "HMACSHA256": "your_signature_key"
}
```

### 2. API Integration Pattern

#### Correct View Implementation

```python
from django.shortcuts import render
import base64, requests
from Keys.keys import keys

def checkout(request):
    # Use production API (not sandbox unless for testing)
    url = 'https://api.micuentaweb.pe/api-payment/V4/Charge/CreatePayment'

    auth = 'Basic ' + base64.b64encode(
        f"{keys['USERNAME']}:{keys['PASSWORD']}".encode('utf-8')
    ).decode('utf-8')

    headers = {'Content-Type': 'application/json', 'Authorization': auth}

    # Critical: Include successURL, failureURL, notificationURL
    data = {
        "amount": int(payment_amount * 100),  # Convert to cents
        "currency": "PEN",
        "orderId": str(order_id),
        "successURL": f"{request.scheme}://{request.get_host()}/payments/success/",
        "failureURL": f"{request.scheme}://{request.get_host()}/payments/failed/",
        "notificationURL": f"{request.scheme}://{request.get_host()}/payments/ipn/",
        "customer": {"email": customer_email}  # Minimum required
    }

    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()

    if response_data['status'] != 'SUCCESS':
        raise Exception(f"Payment creation failed: {response_data['answer'].get('errorMessage')}")

    return render(request, 'payments/checkout.html', {
        'token': response_data['answer']['formToken'],
        'publickey': keys['PUBLIC_KEY'],
        'payment': payment  # Optional: for display
    })
```

### 3. Template Implementation

#### HTML Structure
```html
{% extends 'base.html' %}

{% block content %}
<section class="container">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">Payment Form</div>
                <div class="card-body">
                    Amount: ${{ payment.amount }}
                    <div id="micuentawebstd_rest_wrapper">
                        <div class="kr-embedded" kr-form-token="{{ token }}"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>
{% endblock %}
```

#### JavaScript Scripts (in head)
```html
<!-- Load Bootstrap if using -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootswatch@4.5.2/dist/journal/bootstrap.min.css">
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>

<!-- Izipay KR Payment Form Script -->
<script type="text/javascript"
    src="https://static.micuentaweb.pe/static/js/krypton-client/V4.0/stable/kr-payment-form.min.js"
    kr-public-key="{{ publickey }}"
    kr-post-url-success="{% url 'payments:success' %}"
    kr-post-url-refused="{% url 'payments:failed' %}"
    kr-language="es-ES"
>
</script>

<!-- Izipay Styles -->
<link rel="stylesheet" href="https://static.micuentaweb.pe/static/js/krypton-client/V4.0/ext/classic.css">
<script src="https://static.micuentaweb.pe/static/js/krypton-client/V4.0/ext/classic.js"></script>
```

#### JavaScript Error Handling (at end of body)
```html
<script>
setTimeout(function() {
    if (typeof KR !== 'undefined') {
        KR.onError(function(event) {
            var code = event.errorCode;
            var message = event.errorMessage;
            console.error(code + ": " + message);
            // Display error in UI
            document.getElementById('kr-error').innerText = code + ": " + message;
            document.getElementById('kr-error').style.display = 'block';
        });
    } else {
        console.error("KR not defined after timeout");
        document.getElementById('kr-error').innerText = "Payment form failed to load";
        document.getElementById('kr-error').style.display = 'block';
    }
}, 1000);
</script>
```

## Common Issues & Solutions

### 1. "KR is not defined" Error

**Symptoms:** JavaScript error, form doesn't load

**Cause:** Script loading timing issue or CORB blocking

**Solutions:**
- Ensure scripts are loaded in correct order
- Add timeout delay for KR.onError
- Check network tab for blocked requests
- Use production environment (sandbox may have restrictions)

### 2. "NoReverseMatch" Error

**Symptoms:** Template URL reversal fails

**Cause:** Missing app_name in urls.py

**Solution:**
```python
# In payments/urls.py
app_name = 'payments'  # Add this line
```

### 3. API "SUCCESS" but Token Invalid

**Symptoms:** API returns SUCCESS but form fails

**Cause:** Incomplete API payload (missing URLs or customer data)

**Solution:** Always include successURL, failureURL, notificationURL in payload

### 4. Form Loads But Doesn't Submit

**Symptoms:** Form appears but payment doesn't process

**Cause:** Invalid kr-post-url-success URL

**Solution:** Use `{% url %}` template tag or absolute URLs

### 5. CORS/CORB Blocking

**Symptoms:** KR script doesn't load, CORB errors in console

**Cause:** Browser blocking cross-origin scripts

**Solution:** Use production environment, check network permissions

## Success/Error Handling

### Success View
```python
@csrf_exempt
def payment_success(request):
    if request.POST and checkHash(request.POST, keys["HMACSHA256"]):
        kr_answer = json.loads(request.POST['kr-answer'])
        # Process successful payment
        return render(request, 'payments/success.html', {
            'payment_data': kr_answer
        })
    return HttpResponse("Invalid signature", status=400)
```

### IPN Handler
```python
@csrf_exempt
def payment_ipn(request):
    if checkHash(request.POST, keys["PASSWORD"]):
        kr_answer = json.loads(request.POST['kr-answer'])
        order_status = kr_answer['orderStatus']
        # Update order status in database
        if order_status == 'PAID':
            # Mark as paid
            pass
    return HttpResponse("OK", status=200)
```

## Security Best Practices

1. **Store Keys Securely:** Never commit keys.py to version control
2. **Verify Signatures:** Always check HMAC signatures on callbacks
3. **HTTPS Only:** Use HTTPS in production
4. **Environment Variables:** Use environment variables for sensitive data
5. **CSRF Protection:** Use {% csrf_token %} in forms

## Testing Checklist

- [ ] API credentials configured correctly
- [ ] Webhook URLs accessible from Izipay
- [ ] SSL certificate valid for HTTPS
- [ ] Error pages handle failures gracefully
- [ ] Payment amounts and currencies validated
- [ ] Order IDs unique and tracked

## Debugging Tools

1. **Browser Console:** Check for JavaScript errors
2. **Network Tab:** Verify API calls and resource loading
3. **Django Logs:** Enable DEBUG mode for detailed logs
4. **Webhook Tester:** Use tools like webhook.site to test callbacks

## Production Deployment

1. Update keys to production credentials
2. Configure webhooks in Izipay dashboard
3. Set up proper error handling and logging
4. Test with small amounts before scale

## Reference URLs

- Demo: `/demo/` - Simple implementation
- Full App: `/payments/` - Production-ready
- Izipay Documentation: https://docs.izipay.pe/

## Version Info

This implementation uses Izipay V4 API with KR (Krypton) embedded forms.
