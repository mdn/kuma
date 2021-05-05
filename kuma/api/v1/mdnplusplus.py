from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def landing_page_survey(request):
    context = {}
    if request.method == "POST":

        from pprint import pprint

        print("Gotto store this somewhere...")
        pprint(request.POST)
        context["ok"] = True
    return JsonResponse(context)
