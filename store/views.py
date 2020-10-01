from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import datetime
import random
from .models import *
from .utils import cookieCart, cartData, guestOrder
from django.contrib.auth.forms import UserCreationForm
from .forms import CreateUserForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout


# Create your views here.
def login_user(request):
    if request.user.is_authenticated:
        return redirect('store')
    else:
        pass

    if request.method == 'POST':
        user = authenticate(username=request.POST['username'],
                            password=request.POST['password'])
        if user is not None:
            login(request, user)
            return redirect('store')
        else:
            messages.info(request, 'Username or Password Incorrect!')

    context = {}
    return render(request, 'store/login.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('store')
    else:
        pass

    form = CreateUserForm()

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        else:
            messages.info(request, 'Register Error, Try Again')

    context = {'form': form}
    return render(request, 'store/register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('store')


def store(request):

    data = cartData(request)
    cartItems = data['cartItems']

    products = Product.objects.all()
    context = {
        'products': products,
        'cartItems': cartItems,
        'active_store': 'true',
    }
    return render(request, 'store/store.html', context)


def cart(request):

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {
        'items': items,
        'order': order,
        'cartItems': cartItems,
        'active_cart': 'true',
    }
    return render(request, 'store/cart.html', context)


def checkout(request):

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)


def viewProducts(request, pk):
    data = cartData(request)
    cartItems = data['cartItems']

    products = Product.objects.get(id=pk)
    context = {
        'products': products,
        'cartItems': cartItems,
    }
    return render(request, 'store/view.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    # print('ProductId :', productId, 'Action :', action)
    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer,
                                                 complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order,
                                                         product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer,
                                                     complete=False)

    else:
        print(data)
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == float(order.get_cart_total):
        order.complete = True

    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment Complete', safe=False)
