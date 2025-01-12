# Create your views here.
from django.shortcuts import render
from rest_framework import generics, viewsets, status
from django.db.models import Sum
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from django.db import transaction
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CartItemSerializer, CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer, UserGroupSerializer, UserSerializer
from decimal import Decimal

class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return []
        return [IsAdminUser()]

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return []
        return [IsAdminUser()]

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            return []
        return [IsAdminUser()]

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminUser]
    
    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            return []
        return [IsAdminUser()]
    
    def get_queryset(self):
        queryset = MenuItem.objects.all()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset.order_by('price')

class CartView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        menuitem = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']
        unit_price = menuitem.price
        price = unit_price * quantity
        serializer.save(user=self.request.user, unit_price=unit_price, price=price)

class CartView(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        menuitem = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']
        unit_price = Decimal(str(menuitem.price))
        price = unit_price * Decimal(str(quantity))
        serializer.save(
            user=self.request.user,
            unit_price=unit_price,
            price=price
        )

class CartItemView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
        
    def update(self, request, *args, **kwargs):
        cart_item = self.get_object()
        
        # Get quantity from request data or use current quantity
        try:
            quantity = int(request.data.get('quantity', cart_item.quantity))
            if quantity < 1:
                return Response(
                    {'quantity': 'Quantity must be at least 1'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (TypeError, ValueError):
            return Response(
                {'quantity': 'Invalid quantity value'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update price based on new quantity
        unit_price = Decimal(str(cart_item.unit_price))
        cart_item.quantity = quantity
        cart_item.price = unit_price * Decimal(str(quantity))
        cart_item.save()
        
        serializer = self.get_serializer(cart_item)
        return Response(serializer.data)
class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(delivery_crew=user)
        return Order.objects.filter(user=user)
    
    @transaction.atomic
    def perform_create(self, serializer):
        cart_items = Cart.objects.filter(user=self.request.user)
        
        if not cart_items.exists():
            raise ValidationError("Cart is empty")
            
        total = sum(item.price for item in cart_items)
        
        order = serializer.save(user=self.request.user, total=total)
        
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=cart_item.menuitem,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                price=cart_item.price
            )
        
        cart_items.delete()

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(delivery_crew=user)
        return Order.objects.filter(user=user)
    
    def perform_update(self, serializer):
        user = self.request.user
        if user.groups.filter(name='Delivery Crew').exists():
            serializer.save(status=serializer.validated_data['status'])
        else:
            serializer.save()


class ManagerGroupListView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only return users in Manager group
        manager_group = Group.objects.get(name='Manager')
        return User.objects.filter(groups=manager_group)
    
    def post(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='Manager').exists():
            return Response(
                {'message': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        username = request.data.get('username')
        if not username:
            return Response(
                {'message': 'Username is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.get(username=username)
            manager_group = Group.objects.get(name='Manager')
            manager_group.user_set.add(user)
            return Response(
                UserSerializer(user).data, 
                status=status.HTTP_201_CREATED
            )
        except User.DoesNotExist:
            return Response(
                {'message': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ManagerGroupDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        manager_group = Group.objects.get(name='Manager')
        return User.objects.filter(groups=manager_group)
    
    def delete(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='Manager').exists():
            return Response(
                {'message': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        user = self.get_object()
        manager_group = Group.objects.get(name='Manager')
        manager_group.user_set.remove(user)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class OrderListView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(delivery_crew=user)
        return Order.objects.filter(user=user)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Get current user's cart items
        cart_items = Cart.objects.filter(user=request.user)
        
        if not cart_items.exists():
            return Response(
                {'detail': 'No items in cart'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Calculate total from cart items
        total = cart_items.aggregate(
            total=Sum('price')
        )['total']
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total=total,
            status=False  # Initial status as not delivered
        )
        
        # Create OrderItem entries
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=cart_item.menuitem,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                price=cart_item.price
            )
        
        # Clear user's cart
        cart_items.delete()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class OrderDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(delivery_crew=user)
        return Order.objects.filter(user=user)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)  # Set to True to allow PATCH
        instance = self.get_object()
        
        if not request.user.groups.filter(name='Manager').exists():
            return Response({'message': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
        delivery_crew_username = request.data.get('delivery_crew')
        if delivery_crew_username:
            delivery_crew = get_object_or_404(User, username=delivery_crew_username)
            instance.delivery_crew = delivery_crew
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
            
        return Response({'message': 'No delivery crew specified'}, status=status.HTTP_400_BAD_REQUEST)


class OrderManagementView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(delivery_crew=user)
        return Order.objects.filter(user=user)
    
    def get(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def patch(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        if request.user.groups.filter(name='Manager').exists():
            delivery_crew_username = request.data.get('delivery_crew')
            if delivery_crew_username:
                delivery_crew = get_object_or_404(User, username=delivery_crew_username)
                order.delivery_crew = delivery_crew
                order.save()
                serializer = self.get_serializer(order)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'message': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    
class ManagerUserView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        username = request.data.get('username')
        if username:
            user = get_object_or_404(User, username=username)
            delivery_crew = Group.objects.get(name='Delivery Crew')
            delivery_crew.user_set.add(user)
            return Response({'message': 'User added to delivery crew'}, status=status.HTTP_200_OK)
        return Response({'message': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        username = request.data.get('username')
        if username:
            user = get_object_or_404(User, username=username)
            delivery_crew = Group.objects.get(name='Delivery Crew')
            delivery_crew.user_set.remove(user)
            return Response({'message': 'User removed from delivery crew'}, status=status.HTTP_200_OK)
        return Response({'message': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

class DeliveryCrewGroupView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        username = request.data.get('username')
        if username:
            user = get_object_or_404(User, username=username)
            delivery_crew = Group.objects.get(name='Delivery Crew')
            delivery_crew.user_set.add(user)
            return Response({'message': 'User added to delivery crew group'}, status=status.HTTP_200_OK)
        return Response({'message': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        username = request.data.get('username')
        if username:
            user = get_object_or_404(User, username=username)
            delivery_crew = Group.objects.get(name='Delivery Crew')
            delivery_crew.user_set.remove(user)
            return Response({'message': 'User removed from delivery crew group'}, status=status.HTTP_200_OK)
        return Response({'message': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

class DeliveryCrewUserView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        username = request.data.get('username')
        if username:
            user = get_object_or_404(User, username=username)
            delivery_crew = Group.objects.get(name='Delivery Crew')
            delivery_crew.user_set.add(user)
            return Response({'message': 'User added to delivery crew'}, status=status.HTTP_200_OK)
        return Response({'message': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        username = request.data.get('username')
        if username:
            user = get_object_or_404(User, username=username)
            delivery_crew = Group.objects.get(name='Delivery Crew')
            delivery_crew.user_set.remove(user)
            return Response({'message': 'User removed from delivery crew'}, status=status.HTTP_200_OK)
        return Response({'message': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

class GroupManagementView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request, group_name):
        user = get_object_or_404(User, username=request.data.get('username'))
        group = get_object_or_404(Group, name=group_name)
        group.user_set.add(user)
        return Response({'message': f'User added to {group_name} group'}, status=status.HTTP_200_OK)
    
    def delete(self, request, group_name):
        user = get_object_or_404(User, username=request.data.get('username'))
        group = get_object_or_404(Group, name=group_name)
        group.user_set.remove(user)
        return Response({'message': f'User removed from {group_name} group'}, status=status.HTTP_200_OK)