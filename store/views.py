# --- CLEAN IMPORTS ---
import json
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.conf import settings
import razorpay

# Local Imports
from .models import Product, Order, OrderItem, Customer, ShippingAddress
from .utils import cookieCart, cartData, guestOrder
from .forms import ProductForm, CreateUserForm
# ---------------------


# --- 1. HELPER FUNCTION: GET CART DATA ---
def get_cart_data(request):
    if request.user.is_authenticated:
        # 1. Get or Create Customer
        customer, created = Customer.objects.get_or_create(
            user=request.user,
            defaults={'name': request.user.first_name, 'email': request.user.email}
        )
        
        # 2. Get or Create Order
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        
        # 3. CLEANUP: Delete items where the product no longer exists
        # This fixes the "Item Unavailable" issue automatically
        for item in order.orderitem_set.all():
            if item.product is None:
                item.delete()

        # 4. Refresh items list after cleanup
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        # Guest User Logic
        cookieData = cookieCart(request)
        cartItems = cookieData['cartItems']
        order = cookieData['order']
        items = cookieData['items']
        
    return {'items':items, 'order':order, 'cartItems':cartItems}

# --- 2. MAIN STORE VIEW (Restored) ---
def store(request):
    data = get_cart_data(request)
    cartItems = data['cartItems']
    
    products = Product.objects.all()

    # --- NEW SEARCH LOGIC ---
    # Check if there is a 'q' parameter in the URL (e.g., ?q=burger)
    query = request.GET.get('q')
    if query:
        # Filter products where the name contains the query (case-insensitive)
        products = products.filter(name__icontains=query)
    # ------------------------

    context = {'products':products, 'cartItems':cartItems}
    return render(request, 'store/store.html', context)

# --- 3. PRODUCT & CART PAGES ---

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    data = get_cart_data(request)
    context = {'product': product, 'cartItems': data['cartItems']}
    return render(request, 'store/product_detail.html', context)

@login_required(login_url='login')
def cart(request):
    data = get_cart_data(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    # --- 🧹 GHOST ITEM CLEANUP SCRIPT ---
    if request.user.is_authenticated:
        # Loop through items and delete any that have a missing (deleted) product
        for item in items:
            if not item.product:
                item.delete()
        
        # Refresh the items list after deleting the ghosts
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request):
    data = get_cart_data(request)
    context = {'items':data['items'], 'order':data['order'], 'cartItems':data['cartItems']}
    return render(request, 'store/checkout.html', context)

# --- 4. CART API (The Engine) ---

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    print('Action:', action)
    print('Product:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)

# --- 5. FALLBACK CART ACTIONS (Optional) ---

def add_cart(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
        order_item.quantity += 1
        order_item.save()
    return redirect('cart')

def remove_cart(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        customer = request.user.customer
        order = Order.objects.get(customer=customer, complete=False)
        try:
            order_item = OrderItem.objects.get(order=order, product=product)
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order_item.delete()
        except OrderItem.DoesNotExist:
            pass
    return redirect('cart')

def remove_cart_item(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        customer = request.user.customer
        order = Order.objects.get(customer=customer, complete=False)
        try:
            order_item = OrderItem.objects.get(order=order, product=product)
            order_item.delete()
        except OrderItem.DoesNotExist:
            pass
    return redirect('cart')

# --- 6. ORDER PROCESSING & PAYMENT ---

@login_required(login_url='login')
def processOrder(request):
    if request.method == 'POST':
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        
        email = request.POST.get('email')
        if email:
            customer.email = email
            customer.save()

        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=request.POST['address'],
            city=request.POST['city'],
            state=request.POST['state'],
            zipcode=request.POST['zipcode']
        )
        return redirect('payment')
    return redirect('store')

@login_required(login_url='login')
def payment(request):
    data = get_cart_data(request)
    order = data['order']
    amount = int(order.get_cart_total * 100) 
    
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    payment_order = client.order.create({
        'amount': amount, 
        'currency': 'INR', 
        'payment_capture': '1'
    })
    
    context = {
        'order': order,
        'razorpay_order_id': payment_order['id'],
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'razorpay_amount': amount,
        'currency': 'INR',
        'callback_url': '/payment_success/' 
    }
    return render(request, 'store/payment.html', context)

@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            client.utility.verify_payment_signature(params_dict)
            
            customer = request.user.customer
            order = Order.objects.get(customer=customer, complete=False)
            order.complete = True
            order.transaction_id = payment_id
            order.save()
            
            return render(request, 'store/success.html')
            
        except Exception as e:
            return HttpResponse(f"Payment Verification Failed: {e}")
            
    return redirect('store')

# --- 7. USER ACCOUNTS ---

def registerPage(request):
    form = CreateUserForm()
    
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create Customer Profile safely
            Customer.objects.create(
                user=user, 
                name=user.first_name, 
                email=user.email
            )
            
            # Log in using our custom Email Backend
            login(request, user, backend='store.backends.EmailBackend')
            return redirect('store')
            
    context = {'form':form}
    return render(request, 'store/register.html', context)

@login_required(login_url='login')
def myOrders(request):
    customer = request.user.customer
    orders = Order.objects.filter(customer=customer, complete=True).order_by('-date_ordered')
    context = {'orders':orders}
    return render(request, 'store/my_orders.html', context)

# --- 8. ADMIN DASHBOARD & MANAGEMENT ---

@staff_member_required
def dashboard(request):
    orders = Order.objects.filter(complete=True).order_by('-date_ordered')

    # Search Logic
    search_query = request.GET.get('search_query')
    if search_query:
        clean_query = search_query.replace('#', '').strip()
        orders = orders.filter(transaction_id__icontains=clean_query)

    # Date Filter Logic
    date_query = request.GET.get('filter_date')
    if date_query:
        orders = orders.filter(date_ordered__date=date_query)

    total_revenue = sum(order.get_cart_total for order in orders)
    total_orders = orders.count()
    
    products = Product.objects.all()

    context = {
        'orders': orders,
        'products': products,
        'total_revenue': total_revenue, 
        'total_orders': total_orders,
        'current_date': date_query, 
        'current_search': search_query, 
    }
    return render(request, 'store/dashboard.html', context)

@staff_member_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        order.status = status
        order.save()
    return redirect('dashboard')

@staff_member_required
def createProduct(request):
    form = ProductForm()
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('dashboard')

    context = {'form':form, 'title': 'Add New Product'}
    return render(request, 'store/product_form.html', context)

@staff_member_required
def updateProduct(request, pk):
    product = get_object_or_404(Product, id=pk)
    form = ProductForm(instance=product)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('dashboard')

    context = {'form':form, 'title': 'Edit Product'}
    return render(request, 'store/product_form.html', context)

@staff_member_required
def deleteProduct(request, pk):
    product = get_object_or_404(Product, id=pk)
    
    # Delete immediately
    product.delete()
    
    # Go back to dashboard
    return redirect('dashboard')

# --- BOT INITIALIZATION ---
# We set it to None initially so the server starts fast.
# It will load the first time you send a message.
health_bowl_agent = None

def get_bot():
    global health_bowl_agent
    if health_bowl_agent is None:
        # Note: No dot here either!
        from bot import build_local_health_bowl_bot 
        health_bowl_agent = build_local_health_bowl_bot()
    return health_bowl_agent

@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            user_msg_lower = user_message.lower().strip()

            # 1. Handle Memory (Last 4 messages)
            if 'chat_history' not in request.session:
                request.session['chat_history'] = []
            history = request.session['chat_history']
            formatted_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-4:]])

            # 2. Smart Data Filter (Only fetch private data if keywords are present)
            keywords = ['order', 'cart', 'delivery', 'status', 'track', 'where', 'my', 'price', 'cost']
            needs_user_data = any(word in user_msg_lower for word in keywords)

            # 3. Build the Secret Prompt
            user_name = request.user.first_name if request.user.is_authenticated else "there"
            
            if request.user.is_authenticated and needs_user_data:
                customer = request.user.customer
                active_order = Order.objects.filter(customer=customer, complete=False).first()
                cart_status = f"{active_order.get_cart_items} items (Total: ₹{active_order.get_cart_total})" if active_order else "Empty"
                
                last_completed = Order.objects.filter(customer=customer, complete=True).order_by('-id').first()
                order_status = f"Order #{last_completed.id} is out for delivery." if last_completed else "No past orders."

                context_data = f"- Customer Name: {user_name}\n- Cart: {cart_status}\n- Last Order: {order_status}"
            else:
                context_data = f"- Customer Name: {user_name}"

            # 4. Construct the Final Prompt for Phi-3.5
            # We tell the AI exactly what to do with "hi" here
            # 4. Construct the Final Prompt
            # 4. Construct the Final Prompt
            # 4. Construct the Final Prompt
            # 4. Construct the Final Prompt
            final_input = f"""
            [INST] You are a support assistant for 'Health Bowl'. 
            
            CRITICAL RULES:
            1. You can ONLY PROVIDE INFORMATION. 
            2. You CANNOT perform actions (like adding/removing items, changing orders, or processing refunds).
            3. If a user asks to change or remove something, say: "Maaf kijiye, main order change nahi kar sakta. Please Cart page par jaakar manually remove karein."
            4. Use the HIDDEN DATA to check status, don't guess.
            5. Max 15 words.
            [/INST]

            HIDDEN DATA: {context_data}
            USER QUESTION: {user_message}
            """
            # 5. Invoke the Bot (Using the helper to avoid NoneType error)
            bot_instance = get_bot()
            ai_response = bot_instance.invoke(final_input)

            # 6. Save to Memory
            history.append({'role': 'Customer', 'content': user_message})
            history.append({'role': 'HealthBowl AI', 'content': ai_response})
            request.session['chat_history'] = history
            request.session.modified = True

            return JsonResponse({'response': ai_response})
            
        except Exception as e:
            print(f"Chat Error: {e}") # This prints the error to your terminal for debugging
            return JsonResponse({'response': "I'm having a bit of trouble connecting to my brain. Please try again in a moment!"})
            
    return JsonResponse({'response': 'Invalid request'})