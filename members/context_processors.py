from .models import Constituency

def dropdown_context(request):
    constituencies = Constituency.objects.all()
    return {'constituencies': constituencies}