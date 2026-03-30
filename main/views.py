from django.shortcuts import render

def home(request):
    return render(request, "main/home.html")

def dashboard(request):
    return render(request, "base.html")
