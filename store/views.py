from django.shortcuts import render
from .models import SiteImage
from .models import Product

def home(request):
    images = {img.name: img for img in SiteImage.objects.all()}
    products = Product.objects.filter(show_on_home=True)

    featured_product = Product.objects.filter(show_on_home=True).first()

    return render(request, 'store/index.html', {
        'images': images,
        'products': products,
        'featured_product': featured_product,
    })


def women(request):
    images = {img.name: img for img in SiteImage.objects.all()}
    products = Product.objects.filter(category='women')

    return render(request, 'store/women.html', {
        'images': images,
        'products': products
    })


def men(request):
    products = Product.objects.filter(category='men')

    return render(request, 'store/men.html', {
        'products': products
    })


def Jew(request):
    products = Product.objects.filter(category='jewelry')

    return render(request, 'store/Jew.html', {
        'products': products
    })


def pants(request):
    products = Product.objects.filter(category='pants')

    return render(request, 'store/Pants.html', {
        'products': products
    })


def category_products(request, category):
    products = Product.objects.filter(category=category)

    return render(request, 'store/Pants.html', {
        'products': products,
        'category': category
    })



def tshirt(request):
    products = Product.objects.filter(category='t-shirt')

    return render(request, 'store/T-Shirt.html', {
        'products': products
    })


def about_us(request):
    return render(request, 'store/about_us.html')


def contact_us(request):
    return render(request, 'store/contact_us.html')

def product_detail(request, slug):
    product = Product.objects.get(slug=slug)
    return render(request, 'store/Product_Detail.html', {'product': product})


def category_products(request, category):
    images = {img.name: img for img in SiteImage.objects.all()}
    products = Product.objects.filter(category=category)

    return render(request, 'store/Jew.html', {
        'images': images,
        'products': products,
        'category': category,
    })


def shorts(request):
    products = Product.objects.filter(category='shorts')

    return render(request, 'store/Jew.html', {
        'products': products,
        'category': 'shorts'
    })