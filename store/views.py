from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Category, SiteImage, Product
from django.core.paginator import Paginator


def home(request):
    images = {img.name: img for img in SiteImage.objects.all()}
    products = Product.objects.filter(show_on_home=True)
    featured_product = products.first()

    return render(request, 'store/index.html', {
        'images': images,
        'products': products,
        'featured_product': featured_product,
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


def category_products(request, category):
    images = {img.name: img for img in SiteImage.objects.all()}
    products = Product.objects.filter(category=category)

    return render(request, 'store/Jew.html', {
        'images': images,
        'products': products,
        'category': category,
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

    products = Product.objects.filter(category=category)

    paginator = Paginator(products, 5)  # 5 products per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'store/Jew.html', {
        'images': images,
        'page_obj': page_obj,
        'category': category,
    })