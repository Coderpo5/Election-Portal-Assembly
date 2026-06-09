"""
URL configuration for ELECTION_ASSEMBLY_PORTAL project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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

from django.shortcuts import render

from django.contrib import admin
from django.urls import include, path
from members import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('partywiseresult-U01', views.index, name = "Index-Page"),
    path('', views.home, name = "Home-Page"),
    path('candidatewise-U01-<str:constituency_id>/', views.candidate_wise, name = "candidate-wise"),
    path('api/constituencies/', views.constituency_data, name='constituency_data'),
    path('votesconstituencywise-U01-<str:constituency_id>/', views.votes, name = "Votes"),
    path('partywisewinresult-U01-<str:party_acronym>', views.party, name = "Party"),
    path('partywiseleads-U01-<str:party_acronym>', views.partyLeads, name = "PartyLeads"),
    path('statewise-U01-<int:set_number>/', views.statewise, name = "Statewise"),
    path('roundwise-U01-<str:constituency_id>/', views.roundwise, name = "roundwise"),
]
# /<str:constituency_id>/

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

