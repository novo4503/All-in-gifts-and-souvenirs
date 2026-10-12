import logging
import os
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import Category, SiteImage, Product, Order, OrderItem
from django.core.paginator import Paginator


logger = logging.getLogger(__name__)


def home(request):
    images = {img.name: img for img in SiteImage.objects.all()}
    category_groups = {
        category.slug: category
        for category in Category.objects.filter(
            slug__in=['liquor', 'coffee', 'cake']
        ).prefetch_related('children')
    }
    products = Product.objects.filter(show_on_home=True)
    featured_product = products.first()

    return render(request, 'store/index.html', {
        'images': images,
        'products': products,
        'featured_product': featured_product,
        'category_groups': category_groups,
    })


def search_products(request):
    query = request.GET.get('q', '')

    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(category__icontains=query)
    ) if query else Product.objects.none()

    return render(request, 'store/search_results.html', {
        'products': products,
        'query': query,
    })


def contact_us(request):
    images = {img.name: img for img in SiteImage.objects.all()}

    return render(request, 'store/contact_us.html', {
        'images': images,
    })


def about_us(request):
    return render(request, 'store/about_us.html')


def women(request):
    images = {img.name: img for img in SiteImage.objects.all()}
    products = Product.objects.filter(category='women')

    return render(request, 'store/women.html', {
        'images': images,
        'products': products,
    })


def men(request):
    products = Product.objects.filter(category='men')

    return render(request, 'store/men.html', {
        'products': products,
    })


def Jew(request):
    images = {img.name: img for img in SiteImage.objects.all()}

    products = Product.objects.filter(category='jewelry').order_by("-id")

    paginator = Paginator(products, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'store/Jew.html', {
        'images': images,
        'page_obj': page_obj,
        'category': 'jewelry',
    })


def pants(request):
    products = Product.objects.filter(category='pants')

    return render(request, 'store/Pants.html', {
        'products': products,
    })


def shorts(request):
    images = {img.name: img for img in SiteImage.objects.all()}

    products = Product.objects.filter(category='shorts').order_by("-id")

    paginator = Paginator(products, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'store/Jew.html', {
        'images': images,
        'page_obj': page_obj,
        'category': 'shorts',
    })


def tshirt(request):
    products = Product.objects.filter(category='t-shirt')

    return render(request, 'store/T-Shirt.html', {
        'products': products,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id).order_by('?')[:4]

    return render(request, 'store/Product_Detail.html', {
        'product': product,
        'related_products': related_products,
    })



def category_products(request, category):
    images = {img.name: img for img in SiteImage.objects.all()}
    category_record = Category.objects.filter(slug=category).prefetch_related(
        'children'
    ).first()
    category_slugs = [category]
    if category_record:
        category_slugs.extend(
            category_record.children.values_list('slug', flat=True)
        )
        category_title = category_record.name
    else:
        category_title = category

    products = Product.objects.filter(category__in=category_slugs).order_by('name')

    paginator = Paginator(products, 5)  # 5 products per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'store/Jew.html', {
        'images': images,
        'page_obj': page_obj,
        'category': category_title,
    })


def _cart_products(request):
    cart = request.session.get('cart', {})
    valid_cart = {}
    for product_id, quantity in cart.items():
        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue
        if product_id > 0 and 1 <= quantity <= 99:
            valid_cart[str(product_id)] = quantity

    products = Product.objects.filter(pk__in=valid_cart)
    items = []
    subtotal = Decimal('0.00')
    for product in products:
        quantity = valid_cart[str(product.pk)]
        line_total = (product.price * quantity).quantize(Decimal('0.01'))
        subtotal += line_total
        items.append({
            'product': product,
            'quantity': quantity,
            'line_total': line_total,
        })

    if valid_cart != cart or len(items) != len(valid_cart):
        request.session['cart'] = {
            str(item['product'].pk): item['quantity'] for item in items
        }
    return items, subtotal.quantize(Decimal('0.01'))


def _delivery_cost():
    try:
        cost = Decimal(os.environ.get('DELIVERY_COST', '0'))
    except InvalidOperation:
        logger.exception('Invalid DELIVERY_COST environment value')
        return Decimal('0.00')
    if not cost.is_finite():
        logger.error('DELIVERY_COST must be a finite decimal value')
        return Decimal('0.00')
    return max(cost, Decimal('0.00')).quantize(Decimal('0.01'))


def _discount_for(subtotal, promo_code):
    if promo_code == 'ISLAND10':
        return (subtotal * Decimal('0.10')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    return Decimal('0.00')


def _checkout_context(request, **extra):
    items, subtotal = _cart_products(request)
    promo_code = request.session.get('promo_code', '')
    discount = _discount_for(subtotal, promo_code)
    delivery_cost = _delivery_cost()
    context = {
        'cart_items': items,
        'subtotal': subtotal,
        'discount': discount,
        'delivery_cost': delivery_cost,
        'total': max(subtotal - discount + delivery_cost, Decimal('0.00')),
        'promo_code': promo_code,
        'promo_notice': request.session.pop('promo_notice', ''),
    }
    context.update(extra)
    return context


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    try:
        quantity = int(request.POST.get('quantity', '1'))
    except (TypeError, ValueError):
        quantity = 0
    cart = request.session.get('cart', {})
    current_quantity = int(cart.get(str(product.pk), 0))
    if quantity < 1 or current_quantity + quantity > 99:
        messages.error(request, 'Choose a quantity between 1 and 99 per product.')
        return redirect('Product_Detail', slug=product.slug)
    cart[str(product.pk)] = current_quantity + quantity
    request.session['cart'] = cart
    messages.success(request, f'{product.name} was added to your cart.')
    return redirect('checkout')


@require_POST
def change_cart(request, product_id):
    get_object_or_404(Product, pk=product_id)
    cart = request.session.get('cart', {})
    product_key = str(product_id)
    try:
        quantity = int(cart.get(product_key, 0))
    except (TypeError, ValueError):
        quantity = 0
    action = request.POST.get('action')
    if action == 'increase' and quantity < 99:
        quantity += 1
        cart[product_key] = quantity
    elif action == 'decrease' and quantity > 1:
        cart[product_key] = quantity - 1
    elif action == 'remove':
        cart.pop(product_key, None)
    request.session['cart'] = cart
    return redirect('checkout')


@require_POST
def apply_promo(request):
    code = request.POST.get('promo_code', '').strip().upper()
    if code == 'ISLAND10':
        request.session['promo_code'] = code
        request.session['promo_notice'] = 'Promo applied: 10% off.'
    else:
        request.session.pop('promo_code', None)
        request.session['promo_notice'] = 'Invalid promo code.'
    return redirect('checkout')


def checkout(request):
    return render(request, 'store/checkout.html', _checkout_context(request))


def _whatsapp_order_data(order):
    return {
        'customer_name': order.customer_name,
        'phone': order.phone,
        'delivery_address': order.delivery_address,
        'room': order.room or 'Not provided',
        'delivery_time': order.delivery_time,
        'delivery_notes': order.delivery_notes or 'None',
        'cash_note': order.cash_note,
        'items': [
            {
                'name': item.product_name,
                'quantity': item.quantity,
                'unit_price': f'{item.unit_price:.2f}',
                'line_total': f'{item.unit_price * item.quantity:.2f}',
            }
            for item in order.items.all()
        ],
        'subtotal': f'{order.subtotal:.2f}',
        'discount': f'{order.discount:.2f}',
        'delivery_cost': f'{order.delivery_cost:.2f}',
        'total': f'{order.total:.2f}',
        'order_id': order.pk,
    }


@require_POST
def submit_order(request):
    items, subtotal = _cart_products(request)
    if not items:
        messages.error(request, 'Your cart is empty.')
        return redirect('checkout')

    customer_name = request.POST.get('customer_name', '').strip()
    phone = request.POST.get('phone', '').strip()
    address = request.POST.get('delivery_address', '').strip()
    room = request.POST.get('room', '').strip()
    delivery_time = request.POST.get('delivery_time', '').strip()
    cash_note = request.POST.get('cash_note', '').strip()
    delivery_notes = request.POST.get('delivery_notes', '').strip()
    delivery_times = {'ASAP', 'Morning (9-12)', 'Afternoon (12-4)', 'Evening (4-7:30)'}
    cash_notes = {'Exact amount', '$20 bill', '$50 bill', '$100 bill'}
    errors = []
    if not customer_name or len(customer_name) > 160:
        errors.append('Enter your name (up to 160 characters).')
    if not re.fullmatch(r'[0-9+().\-\s]{7,40}', phone):
        errors.append('Enter a valid phone or WhatsApp number.')
    if not address or len(address) > 255:
        errors.append('Enter your hotel or delivery address (up to 255 characters).')
    if len(room) > 80:
        errors.append('Room or unit must be 80 characters or fewer.')
    if delivery_time not in delivery_times:
        errors.append('Select a valid delivery time.')
    if cash_note not in cash_notes:
        errors.append('Select a valid cash note.')
    if len(delivery_notes) > 2000:
        errors.append('Delivery notes must be 2,000 characters or fewer.')
    if errors:
        return render(request, 'store/checkout.html', _checkout_context(
            request,
            form_data=request.POST,
            form_errors=errors,
        ), status=400)

    promo_code = request.session.get('promo_code', '')
    discount = _discount_for(subtotal, promo_code)
    delivery_cost = _delivery_cost()
    total = max(subtotal - discount + delivery_cost, Decimal('0.00'))
    order = Order.objects.create(
        customer_name=customer_name,
        phone=phone,
        delivery_address=address,
        room=room,
        delivery_time=delivery_time,
        cash_note=cash_note,
        delivery_notes=delivery_notes,
        promo_code=promo_code,
        subtotal=subtotal,
        discount=discount,
        delivery_cost=delivery_cost,
        total=total,
    )
    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            product=item['product'],
            product_reference_id=item['product'].pk,
            product_name=item['product'].name,
            product_image=item['product'].image.name if item['product'].image else '',
            unit_price=item['product'].price,
            quantity=item['quantity'],
            selected_options={},
        )
        for item in items
    ])

    return render(request, 'store/checkout.html', _checkout_context(
        request,
        whatsapp_order=order,
        whatsapp_order_data=_whatsapp_order_data(order),
    ))