import logging
import os
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import (
    SiteImage,
    Category,
    Product,
    ProductImage,
    ProductOption,
    Order,
    OrderItem,
)

logger = logging.getLogger(__name__)
GCT_RATE = Decimal('0.15')


# -------------------------
# Cart format helpers
# -------------------------
def _normalise_cart(cart):
    """
    Normalize session cart into canonical list-of-lines:
    [
        {'product_id': 12, 'quantity': 2, 'selected_options': {'Size': 'M'}},
        ...
    ]

    Accept both the older dict mapping format {product_id_str: quantity_int}
    and the newer list-of-lines format.
    """
    if isinstance(cart, list):
        entries = cart
    elif isinstance(cart, dict):
        entries = []
        for product_id, value in cart.items():
            if isinstance(value, dict):
                entries.append({
                    'product_id': product_id,
                    'quantity': value.get('quantity', 1),
                    'selected_options': value.get('selected_options', {}),
                })
            else:
                entries.append({
                    'product_id': product_id,
                    'quantity': value,
                    'selected_options': {},
                })
    else:
        return []

    normalized = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        try:
            product_id = int(entry.get('product_id'))
            quantity = int(entry.get('quantity', 1))
        except (TypeError, ValueError):
            continue
        if product_id <= 0 or not 1 <= quantity <= 99:
            continue

        options = entry.get('selected_options')
        if not isinstance(options, dict):
            options = {}
        selected_options = {
            name.strip(): value.strip()
            for name, value in options.items()
            if isinstance(name, str) and isinstance(value, str)
            and name.strip() and value.strip()
        }
        existing = next((
            item for item in normalized
            if item['product_id'] == product_id
            and item['selected_options'] == selected_options
        ), None)
        if existing:
            existing['quantity'] = min(99, existing['quantity'] + quantity)
        else:
            normalized.append({
                'product_id': product_id,
                'quantity': quantity,
                'selected_options': selected_options,
            })
    return normalized


def _cart_products(request):
    """
    Convert canonical cart into detailed items and compute subtotal.
    Also rewrites session cart to canonical list-of-lines for consistency.
    Returns (items, subtotal)
    """
    raw_cart = request.session.get('cart', {})
    cart = _normalise_cart(raw_cart)

    items = []
    subtotal = Decimal('0.00')

    for entry in cart:
        product = Product.objects.filter(pk=entry['product_id']).first()
        if not product:
            # Skip invalid product ids
            continue
        qty = max(1, min(int(entry.get('quantity', 1)), 99))
        line_total = (product.price * qty).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        subtotal += line_total
        items.append({
            'product': product,
            'quantity': qty,
            'line_total': line_total,
            'selected_options': entry.get('selected_options', {}) or {},
            'line_index': len(items),
        })

    # canonicalize session cart as list-of-lines
    request.session['cart'] = [
        {
            'product_id': item['product'].pk,
            'quantity': item['quantity'],
            'selected_options': item['selected_options'],
        }
        for item in items
    ]
    request.session.modified = True

    return items, subtotal.quantize(Decimal('0.01'))


# -------------------------
# Pricing helpers
# -------------------------
def _delivery_cost():
    """
    Read DELIVERY_COST from env; fallback to 0.00
    """
    try:
        cost = Decimal(os.environ.get('DELIVERY_COST', '0'))
    except InvalidOperation:
        logger.exception('Invalid DELIVERY_COST environment value')
        return Decimal('0.00')
    if not cost.is_finite():
        logger.error('DELIVERY_COST must be finite')
        return Decimal('0.00')
    return max(cost, Decimal('0.00')).quantize(Decimal('0.01'))


def _discount_for(subtotal, promo_code):
    """
    Only promo supported: ISLAND10 -> 10% off subtotal
    """
    if promo_code == 'ISLAND10':
        return (subtotal * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return Decimal('0.00')


def _gct_for(subtotal, discount):
    taxable_subtotal = max(subtotal - discount, Decimal('0.00'))
    return (taxable_subtotal * GCT_RATE).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )


def _checkout_context(request, **extra):
    """
    Build common context for checkout template.
    """
    items, subtotal = _cart_products(request)
    promo_code = request.session.get('promo_code', '')
    discount = _discount_for(subtotal, promo_code)
    delivery_cost = _delivery_cost()

    delivery_type = 'island'
    gct_amount = _gct_for(subtotal, discount)
    total = max(subtotal - discount + delivery_cost + gct_amount, Decimal('0.00'))

    context = {
        'cart_items': items,
        'subtotal': subtotal,
        'discount': discount,
        'delivery_cost': delivery_cost,
        'gct_amount': gct_amount,
        'delivery_type': delivery_type,
        'total': total,
        'promo_code': promo_code,
        'promo_notice': request.session.pop('promo_notice', ''),
    }
    context.update(extra)
    return context


# -------------------------
# Public views referenced by URLs
# -------------------------
def home(request):
    """
    Homepage: show products flagged to show on home, or latest products.
    """
    products = Product.objects.filter(show_on_home=True).order_by('-pk')[:12]
    if not products:
        products = Product.objects.all().order_by('-pk')[:12]

    top_seller_products = list(
        Product.objects.filter(show_on_home=True, image__gt='')
        .order_by('-pk')[:3]
    )
    if len(top_seller_products) < 3:
        existing_ids = [product.pk for product in top_seller_products]
        additional_products = Product.objects.filter(image__gt='').exclude(
            pk__in=existing_ids
        ).order_by('-pk')[:3 - len(top_seller_products)]
        top_seller_products.extend(additional_products)

    categories = (
        Category.objects.filter(parent__isnull=True)
        .prefetch_related('children')
        .order_by('name')
    )
    homepage_categories = categories
    images = {image.name: image for image in SiteImage.objects.all()}
    return render(request, 'store/index.html', {
        'products': products,
        'categories': categories,
        'homepage_categories': homepage_categories,
        'top_seller_products': top_seller_products,
        'images': images,
    })


def women(request):
    products = Product.objects.filter(category='women').order_by('-pk')
    paginator = Paginator(products, 24)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request, 'store/women.html', {'page_obj': page_obj})


def men(request):
    products = Product.objects.filter(category='men').order_by('-pk')
    paginator = Paginator(products, 24)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request, 'store/men.html', {'page_obj': page_obj})


def shorts(request):
    products = Product.objects.filter(category__icontains='shorts').order_by('-pk')
    paginator = Paginator(products, 24)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request, 'store/men.html', {'page_obj': page_obj})


def pants(request):
    products = Product.objects.filter(category__icontains='pants').order_by('-pk')
    paginator = Paginator(products, 24)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request, 'store/men.html', {'page_obj': page_obj})


def Jew(request):
    """
    Special page (keeps existing template name in repository).
    """
    return render(request, 'store/Jew.html', {})


def about_us(request):
    return render(request, 'store/index.html', {})  # reuse index if no separate template


def contact_us(request):
    return render(request, 'store/contact_us.html', {})


def category_products(request, category):
    """
    Show a category, its child categories, and products assigned within its
    subtree. Legacy product categories remain available without Category rows.
    """
    category_record = Category.objects.filter(slug=category).first()
    legacy_category_name = dict(Product.CATEGORY_CHOICES).get(category)
    if category_record is None and legacy_category_name is None:
        raise Http404

    category_slugs = [category]
    if category_record:
        seen_ids = {category_record.pk}
        pending_ids = [category_record.pk]
        while pending_ids:
            descendants = list(
                Category.objects.filter(parent_id__in=pending_ids)
                .exclude(pk__in=seen_ids)
                .values_list('pk', 'slug')
            )
            pending_ids = [pk for pk, _slug in descendants]
            seen_ids.update(pending_ids)
            category_slugs.extend(slug for _pk, slug in descendants)

    page = request.GET.get('page')
    products = Product.objects.filter(category__in=category_slugs).order_by('-pk')
    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(page)
    return render(request, 'store/category_products.html', {
        'category_record': category_record,
        'category_name': (
            category_record.name if category_record else legacy_category_name
        ),
        'subcategories': (
            Category.objects.filter(parent=category_record)
            .select_related('parent')
            .order_by('name')
            if category_record else ()
        ),
        'page_obj': page_obj,
        'products': page_obj.object_list,
    })


def product_detail(request, slug):
    """
    Product detail page by slug.
    """
    product = get_object_or_404(Product, slug=slug)
    images = product.gallery_images.all() if hasattr(product, 'gallery_images') else ProductImage.objects.filter(product=product)
    options = list(
        product.options.filter(values__isnull=False)
        .distinct()
        .prefetch_related('values')
        .order_by('position', 'pk')
    )
    return render(request, 'store/Product_Detail.html', {
        'product': product,
        'images': images,
        'product_options': options,
    })


# -------------------------
# Cart endpoints
# -------------------------
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    try:
        quantity = int(request.POST.get('quantity', '1'))
    except (TypeError, ValueError):
        quantity = 0

    if quantity < 1 or quantity > 99:
        messages.error(request, 'Choose a quantity between 1 and 99 per product.')
        return redirect('Product_Detail', slug=product.slug)

    # Validate product options
    selected_options = {}
    product_options = list(
        ProductOption.objects.filter(
            product=product,
            values__isnull=False,
        ).distinct().prefetch_related('values').order_by('position', 'pk')
    )
    expected_option_fields = {f'option_{option.pk}' for option in product_options}
    submitted_option_fields = {
        field_name
        for field_name in request.POST
        if field_name.startswith('option_')
    }
    if submitted_option_fields - expected_option_fields:
        messages.error(request, 'One or more selected options are not valid for this product.')
        return redirect('Product_Detail', slug=product.slug)

    for opt in product_options:
        field_name = f'option_{opt.pk}'
        value = (request.POST.get(field_name) or '').strip()
        if not value:
            if opt.is_required:
                messages.error(request, f'Please choose a valid {opt.name}.')
                return redirect('Product_Detail', slug=product.slug)
            continue
        valid_values = opt.value_list
        if value not in valid_values:
            messages.error(request, f'Invalid selection for {opt.name}.')
            return redirect('Product_Detail', slug=product.slug)
        selected_options[opt.name] = value

    cart = _normalise_cart(request.session.get('cart', []))

    # If same product + same options exists, increase quantity; else append as separate line
    existing_index = None
    for i, entry in enumerate(cart):
        if entry['product_id'] == product.id and entry.get('selected_options', {}) == selected_options:
            existing_index = i
            break

    if existing_index is not None:
        if cart[existing_index]['quantity'] + quantity > 99:
            messages.error(request, 'Choose a quantity between 1 and 99 per product variation.')
            return redirect('Product_Detail', slug=product.slug)
        cart[existing_index]['quantity'] += quantity
    else:
        cart.append({
            'product_id': product.id,
            'quantity': quantity,
            'selected_options': selected_options,
        })

    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, f'{product.name} was added to your cart.')
    return redirect('checkout')


@require_POST
def change_cart(request, product_id):
    """Change one variation line, or the first product line for older clients."""
    action = request.POST.get('action')
    cart = _normalise_cart(request.session.get('cart', []))

    try:
        line_index = int(request.POST.get('line_index', ''))
    except (TypeError, ValueError):
        line_index = None

    matching_indexes = [
        index for index, entry in enumerate(cart)
        if entry['product_id'] == int(product_id)
    ]
    if line_index not in matching_indexes:
        line_index = matching_indexes[0] if matching_indexes else None

    if line_index is not None:
        if action == 'increase' and cart[line_index]['quantity'] < 99:
            cart[line_index]['quantity'] += 1
        elif action == 'decrease':
            cart[line_index]['quantity'] = max(1, cart[line_index]['quantity'] - 1)
        elif action == 'remove':
            cart.pop(line_index)

    request.session['cart'] = cart
    request.session.modified = True
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
    request.session.modified = True
    return redirect('checkout')


def checkout(request):
    return render(request, 'store/checkout.html', _checkout_context(request))


# -------------------------
# Order creation and WhatsApp data
# -------------------------
def _whatsapp_order_data(order):
    """
    Structure order info for the checkout template's WhatsApp payload.
    """
    items = []
    for it in order.items.all():
        line_total = (it.unit_price * it.quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        items.append({
            'name': it.product_name,
            'quantity': it.quantity,
            'unit_price': f'{it.unit_price:.2f}',
            'line_total': f'{line_total:.2f}',
            'selected_options': it.selected_options or {},
        })
    return {
        'customer_name': order.customer_name,
        'phone': order.phone,
        'delivery_address': order.delivery_address,
        'room': order.room or '',
        'delivery_time': order.delivery_time,
        'delivery_notes': order.delivery_notes or '',
        'cash_note': order.cash_note or '',
        'items': items,
        'subtotal': f'{order.subtotal:.2f}',
        'discount': f'{order.discount:.2f}',
        'delivery_cost': f'{order.delivery_cost:.2f}',
        'gct_amount': f'{order.gct_amount:.2f}',
        'total': f'{order.total:.2f}',
        'order_id': order.pk,
    }


@require_POST
def submit_order(request):
    items, subtotal = _cart_products(request)
    if not items:
        messages.error(request, 'Your cart is empty.')
        return redirect('checkout')

    # Extract and validate form fields
    customer_name = (request.POST.get('customer_name') or '').strip()
    phone = (request.POST.get('phone') or '').strip()
    delivery_address = (request.POST.get('delivery_address') or '').strip()
    room = (request.POST.get('room') or '').strip()
    delivery_time = (request.POST.get('delivery_time') or '').strip()
    cash_note = (request.POST.get('cash_note') or '').strip()
    delivery_notes = (request.POST.get('delivery_notes') or '').strip()
    delivery_type = 'island'

    errors = []
    if not customer_name or len(customer_name) > 160:
        errors.append('Enter your name (up to 160 characters).')
    if not re.fullmatch(r'[0-9+().\-\s]{7,40}', phone):
        errors.append('Enter a valid phone or WhatsApp number.')
    if not delivery_address or len(delivery_address) > 255:
        errors.append('Enter your hotel or delivery address (up to 255 characters).')
    if len(room) > 80:
        errors.append('Room or unit must be 80 characters or fewer.')
    if delivery_time not in {'ASAP', 'Morning (9-12)', 'Afternoon (12-4)', 'Evening (4-7:30)'}:
        errors.append('Select a valid delivery time.')
    if cash_note not in {'Exact amount', '$20 bill', '$50 bill', '$100 bill'}:
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

    gct_amount = _gct_for(subtotal, discount)

    total = max(subtotal - discount + delivery_cost + gct_amount, Decimal('0.00'))

    order = Order.objects.create(
        customer_name=customer_name,
        phone=phone,
        delivery_address=delivery_address,
        room=room,
        delivery_time=delivery_time,
        cash_note=cash_note,
        delivery_notes=delivery_notes,
        promo_code=promo_code,
        subtotal=subtotal,
        discount=discount,
        delivery_cost=delivery_cost,
        gct_amount=gct_amount,
        delivery_type=delivery_type,
        total=total,
    )

    order_items = []
    for it in items:
        order_items.append(OrderItem(
            order=order,
            product=it['product'],
            product_reference_id=it['product'].pk,
            product_name=it['product'].name,
            product_image=it['product'].image.name if it['product'].image else '',
            unit_price=it['product'].price,
            quantity=it['quantity'],
            selected_options=it.get('selected_options', {}),
        ))
    OrderItem.objects.bulk_create(order_items)

    # Do not clear cart: app intends to keep cart after order per tests
    return render(request, 'store/checkout.html', _checkout_context(
        request,
        whatsapp_order=order,
        whatsapp_order_data=_whatsapp_order_data(order),
    ))


# -------------------------
# Search helper
# -------------------------
def search_products(request):
    q = (request.GET.get('q') or '').strip()
    products = Product.objects.none()
    if q:
        products = Product.objects.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q)
        ).order_by('-pk')
    paginator = Paginator(products, 24)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request, 'store/search_results.html', {
        'q': q,
        'page_obj': page_obj,
    })