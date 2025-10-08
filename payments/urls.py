from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('create/', views.create_payment, name='create_payment'),
    path('checkout/<int:payment_id>/', views.checkout, name='checkout'),
    path('ipn/', views.ipn_handler, name='ipn_handler'),
    path('success/', views.payment_success, name='success'),
    path('failed/', views.payment_failed, name='failed'),
    # ...existing paths...
    path('result/', views.result, name='result'),  # Add this if not present

    # Workshop registration URLs
    path('taller/', views.workshop_landing, name='workshop_landing'),
    path('taller/registro/', views.register_workshop, name='register_workshop'),
    path('taller/checkout/<int:payment_id>/', views.workshop_checkout, name='workshop_checkout'),

]
