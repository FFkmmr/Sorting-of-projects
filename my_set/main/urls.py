from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('project_list/', views.project_filter_view, name='project_list'),
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('import-csv/', views.import_csv_view, name='import_csv'),
    path('add-project/', views.add_project, name="add_project"),
    path('delete-project/<int:project_id>/', views.delete_project, name="delete_project"),
    path('edit-project/<int:project_id>/', views.edit_project, name='edit_project'),
    path('add-project-set', views.add_set, name='add_set'),
    path('set/<int:set_id>/', views.project_set, name='set'),
    path('edit-set/<int:set_id>/', views.edit_project_set, name='edit_set'),
    path('accept-invitation/<str:token>/', views.accept_invitation, name='accept_invitation'),
    path('add-user-for-set/<int:set_id>/', views.generate_invitation_token, name='add-user-set'),
    path('send_message/', views.send_message, name='email_invitation'),
    path('oauth/', include('social_django.urls', namespace='social')),
]