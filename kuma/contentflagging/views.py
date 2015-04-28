from django.shortcuts import render

from .models import ContentFlag, FLAG_STATUS_FLAGGED


def flagged(request):
    flag_status = request.GET.get('status',
                                  FLAG_STATUS_FLAGGED)
    flag_dict = ContentFlag.objects.flags_by_type(flag_status)
    return render(request,
                  'contentflagging/flags.html',
                  {'flag_dict': flag_dict})
