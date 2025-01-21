from django.http import Http404,HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at index.")

