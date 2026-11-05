from django.contrib import admin

from .models import Convenio, Dentista, Especialidade, Paciente


@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(Convenio)
class ConvenioAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "telefone", "convenio", "ativo", "criado_em")
    list_filter = ("ativo", "convenio")
    search_fields = ("nome", "cpf", "email", "telefone")
    list_select_related = ("convenio",)
    ordering = ("nome",)


@admin.register(Dentista)
class DentistaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cro", "especialidade", "telefone", "ativo")
    list_filter = ("ativo", "especialidade")
    search_fields = ("nome", "cro", "email")
    list_select_related = ("especialidade",)
    ordering = ("nome",)
