from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="ShopHome"),
    path('about/', views.about, name="AboutUs"),
    path('contact/', views.contact, name="Contact"),
    path('tracker/', views.tracker, name="Tracker"),
    path('search/', views.search, name="Search"),
    path('products/<int:myid>/', views.prod_view, name="Productview"),
    path('checkout/', views.checkout, name="Checkout"),
    path('invoice/<str:token>/', views.order_invoice, name="OrderInvoice"),

]
