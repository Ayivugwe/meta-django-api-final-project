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
   path('cart/menu-items/', views.CartManagementView.as_view(), {
       'methods': ['GET', 'POST', 'DELETE']
   }),
   # Order endpoints
   path('orders/', views.OrderManagementView.as_view(), {
       'methods': ['GET', 'POST']
   }),
   path('orders/<int:orderId>/', views.OrderDetailView.as_view(), {
       'methods': ['GET', 'PUT', 'PATCH', 'DELETE']
   }),
   # User group endpoints
   path('groups/manager/users/', views.ManagerGroupView.as_view(), {
       'methods': ['GET', 'POST']
   }),
   path('groups/manager/users/<int:userId>/', views.ManagerUserView.as_view(), {
       'methods': ['DELETE']
   }),
   path('groups/delivery-crew/users/', views.DeliveryCrewGroupView.as_view(), {
       'methods': ['GET', 'POST']
   }), 
   path('groups/delivery-crew/users/<int:userId>/', views.DeliveryCrewUserView.as_view(), {
       'methods': ['DELETE']
   })
]