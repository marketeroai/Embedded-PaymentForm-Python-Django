from django.urls import path
from PaymentDemo import views

app_name = 'PaymentDemo'

urlpatterns = [
    path('', views.index, name='index'),
    path('checkout', views.checkout, name='checkout'),
    path('result', views.result, name='result'),
    path('ipn', views.ipn, name='ipn')
]
