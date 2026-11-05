from django.contrib import admin

from .models import Consulta


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ("paciente", "dentista", "data_hora", "status", "valor")
    list_display_links = ("paciente", "dentista")
    search_fields = ("paciente__nome", "paciente__cpf", "dentista__nome")
    date_hierarchy = "data_hora"
    autocomplete_fields = ("paciente", "dentista")
    list_select_related = ("paciente", "dentista")
    ordering = ("-data_hora",)
    list_per_page = 20
    readonly_fields = ("criado_em",)
    fieldsets = (
        ("Agendamento", {"fields": ("paciente", "dentista", "data_hora", "duracao_min", "status")}),
        ("Financeiro", {"fields": ("valor",)}),
        ("Observações", {"fields": ("observacoes",)}),
        ("Registro", {"fields": ("criado_em",)}),
    )
