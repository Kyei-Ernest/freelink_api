from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProposalListCreateView.as_view(), name='proposal-list-create'),
    path('<int:pk>/', views.ProposalRetrieveView.as_view(), name='proposal-detail'),
    path('<int:pk>/status/', views.ProposalUpdateStatusView.as_view(), name='proposal-update-status'),
]