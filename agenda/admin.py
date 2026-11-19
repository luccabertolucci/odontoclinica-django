from datetime import timedelta

from django.contrib import admin
from django.utils import timezone

from .models import Consulta


class PeriodoFilter(admin.SimpleListFilter):
    title = "Período"
    parameter_name = "periodo"

    def lookups(self, request, model_admin):
        return (
            ("hoje", "Hoje"),
            ("7", "Próximos 7 dias"),
            ("30", "Últimos 30 dias"),
        )

    def queryset(self, request, queryset):
        agora = timezone.now()
        if self.value() == "hoje":
            return queryset.filter(data_hora__date=timezone.localdate())
        if self.value() == "7":
            return queryset.filter(
                data_hora__gte=agora, data_hora__lte=agora + timedelta(days=7)
            )
        if self.value() == "30":
            return queryset.filter(data_hora__gte=agora - timedelta(days=30))
        return queryset


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ("paciente", "dentista", "data_hora", "status", "valor")
    list_display_links = ("paciente", "dentista")
    list_filter = ("status", "dentista", ("data_hora", admin.DateFieldListFilter), PeriodoFilter)
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
