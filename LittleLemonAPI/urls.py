from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.CategoryViewSet)
router.register('menu-items', views.MenuItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('cart/menu-items/', views.CartView.as_view()),
    path('cart/menu-items/<int:pk>/', views.CartItemView.as_view()),
    path('orders/', views.OrderView.as_view()),
    path('orders/<int:pk>/', views.OrderDetailView.as_view()),
    path('groups/manager/users/', views.GroupManagementView.as_view(), {'group_name': 'Manager'}),
    path('groups/delivery-crew/users/', views.GroupManagementView.as_view(), {'group_name': 'Delivery Crew'}),
]