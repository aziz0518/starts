from django.shortcuts import render
from .models import Product, Category

def web_app_shop(request):
    products = Product.objects.filter(is_sold=False)
    categories = Category.objects.all()
    return render(request, 'shop/webapp.html', {
        'products': products,
        'categories': categories
    })