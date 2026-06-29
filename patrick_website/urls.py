"""
URL configuration for patrick_website project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from store import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('women/', views.women, name='women'),
    path('men/', views.men, name='men'),
    path('about-us/', views.about_us, name='about_us'),
    path('Jew/', views.Jew, name='Jew'),
    path('product/<slug:slug>/', views.product_detail, name='Product_Detail'),
    path('category/<str:category>/', views.category_products, name='category_products'),
    path('shorts/', views.shorts, name='shorts'),
    path('pants/', views.pants, name='pants'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('search/', views.search_products, name='search_products'),
    
    
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)