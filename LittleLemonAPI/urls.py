from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('menu-items', views.MenuItemViewSet)

urlpatterns = [
   path('', include(router.urls)),
   # Djoser auth endpoints
   path('', include('djoser.urls')),
   path('', include('djoser.urls.authtoken')),
   path('categories/', views.CategoryListView.as_view(), name='category-list'),
   path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
   # Cart endpoints  
   path('cart/menu-items/', views.CartView.as_view(), name='cart-list'),
   path('cart/menu-items/<int:pk>/', views.CartItemView.as_view(), name='cart-detail'),
   # Order endpoints
   path('orders/', views.OrderListView.as_view(), name='order-list'),  
   path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
   # User group endpoints
   path('groups/manager/users/', views.ManagerGroupListView.as_view(), name='manager-users-list'),
   path('groups/manager/users/<int:pk>/', views.ManagerGroupDetailView.as_view(), name='manager-users-detail'),
   path('groups/delivery-crew/users/', views.DeliveryCrewGroupView.as_view(), {
       'methods': ['GET', 'POST']
   }), 
   path('groups/delivery-crew/users/<int:userId>/', views.DeliveryCrewUserView.as_view(), {
       'methods': ['DELETE']
   })
]