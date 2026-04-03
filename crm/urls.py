from django.urls import path
from . import views

app_name = "crm"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("password/", views.ChangePasswordView.as_view(), name="password_change"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("customers/new/", views.CustomerCreateView.as_view(), name="customer_create"),
    path("customers/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("customers/<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="customer_edit"),
    path("customers/<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="customer_delete"),
    path("customers/<int:pk>/purchase/new/", views.PurchaseCreateView.as_view(), name="purchase_create"),
    path("customers/<int:pk>/followup/new/", views.FollowUpCreateView.as_view(), name="followup_create"),
    path("sell/new/", views.SellCreateView.as_view(), name="sell_create"),
    path("sell/<int:pk>/thank-you/", views.SaleThankYouView.as_view(), name="sale_thank_you"),
    path("sell/<int:pk>/thank-you/<str:token>/", views.PublicSaleThankYouView.as_view(), name="sale_thank_you_public"),
    path("purchase/<int:pk>/delete/", views.PurchaseDeleteView.as_view(), name="purchase_delete"),
    path("followup/<int:pk>/complete/", views.FollowUpCompleteView.as_view(), name="followup_complete"),
    path("followup/<int:pk>/delete/", views.FollowUpDeleteView.as_view(), name="followup_delete"),
]
