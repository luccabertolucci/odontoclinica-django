from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from agenda.views import (
    agendamentos,
    cadastrar_convenio,
    cadastrar_dentista,
    cadastrar_especialidade,
    cadastrar_paciente,
    dashboard,
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("agendamentos/", agendamentos, name="agendamentos"),
    path("pacientes/novo/", cadastrar_paciente, name="cadastrar_paciente"),
    path("dentistas/novo/", cadastrar_dentista, name="cadastrar_dentista"),
    path("convenios/novo/", cadastrar_convenio, name="cadastrar_convenio"),
    path("especialidades/nova/", cadastrar_especialidade, name="cadastrar_especialidade"),
    path("admin/", admin.site.urls),
]
