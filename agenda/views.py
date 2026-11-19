import calendar
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db.models.functions import ExtractHour, TruncMonth
from django.shortcuts import redirect, render
from django.utils import timezone

from clinica.models import Dentista, Paciente

from .forms import (
    ConsultaForm,
    ConvenioForm,
    DentistaForm,
    EspecialidadeForm,
    PacienteForm,
)
from .models import Consulta


@login_required(login_url="login")
def dashboard(request):
    hoje = timezone.localdate()
    inicio_mes = hoje.replace(day=1)
    inicio_proximo_mes = (inicio_mes + timedelta(days=32)).replace(day=1)
    consultas = Consulta.objects.select_related("paciente", "dentista")
    mes_atual = consultas.filter(data_hora__date__gte=inicio_mes, data_hora__date__lt=inicio_proximo_mes)

    status_map = dict(Consulta.Status.choices)
    status_counts = mes_atual.values("status").annotate(total=Count("id"))
    status_chart = [{"label": status_map.get(item["status"], item["status"]), "value": item["total"], "key": item["status"].lower()} for item in status_counts]

    inicio_historico = (inicio_mes - timedelta(days=150)).replace(day=1)
    meses = []
    cursor = inicio_historico
    while cursor < inicio_proximo_mes:
        meses.append(cursor)
        cursor = (cursor + timedelta(days=32)).replace(day=1)
    historico = consultas.filter(data_hora__date__gte=inicio_historico, data_hora__date__lt=inicio_proximo_mes).annotate(mes=TruncMonth("data_hora")).values("mes").annotate(total=Count("id"), faturamento=Sum("valor", filter=Q(status=Consulta.Status.REALIZADA)))
    por_mes = {item["mes"].date().replace(day=1): item for item in historico}
    tendencia = [{"label": calendar.month_abbr[mes.month].capitalize(), "appointments": por_mes.get(mes, {}).get("total", 0), "revenue": float(por_mes.get(mes, {}).get("faturamento") or 0)} for mes in meses]

    horarios_qs = mes_atual.annotate(hora=ExtractHour("data_hora")).values("hora").annotate(total=Count("id")).order_by("hora")
    horarios = [{"label": f"{item['hora']:02d}h", "value": item["total"]} for item in horarios_qs]
    recorrentes = consultas.values("paciente__nome").annotate(total=Count("id")).filter(total__gt=1).order_by("-total", "paciente__nome")[:5]

    total_mes = mes_atual.count()
    realizadas_mes = mes_atual.filter(status=Consulta.Status.REALIZADA)
    faturamento_mes = realizadas_mes.aggregate(total=Sum("valor"))["total"] or Decimal("0")
    ticket_medio = (faturamento_mes / realizadas_mes.count()) if realizadas_mes.exists() else Decimal("0")
    proxima = consultas.filter(data_hora__gte=timezone.now(), status__in=[Consulta.Status.AGENDADA, Consulta.Status.CONFIRMADA]).order_by("data_hora").first()
    cancelamentos = mes_atual.filter(status=Consulta.Status.CANCELADA).count()
    receita_prevista = mes_atual.filter(status__in=[Consulta.Status.AGENDADA, Consulta.Status.CONFIRMADA]).aggregate(total=Sum("valor"))["total"] or Decimal("0")
    maior_dentista = realizadas_mes.values("dentista__nome").annotate(total=Sum("valor")).order_by("-total").first()
    melhor_horario = realizadas_mes.annotate(hora=ExtractHour("data_hora")).values("hora").annotate(total=Sum("valor"), consultas=Count("id")).order_by("-total").first()
    dias_mes = calendar.monthrange(hoje.year, hoje.month)[1]
    dias_uteis_decorridos = len([day for day in range(1, min(hoje.day, dias_mes) + 1) if (inicio_mes + timedelta(days=day - 1)).weekday() < 5])

    nomes_meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    context = {
        "hoje": hoje,
        "mes_nome": nomes_meses[hoje.month - 1].capitalize(),
        "status_chart": status_chart,
        "tendencia": tendencia,
        "horarios": horarios,
        "recorrentes": recorrentes,
        "total_mes": total_mes,
        "realizadas_mes": realizadas_mes.count(),
        "faturamento_mes": faturamento_mes,
        "ticket_medio": ticket_medio,
        "proxima": proxima,
        "cancelamentos": cancelamentos,
        "receita_prevista": receita_prevista,
        "maior_dentista": maior_dentista,
        "melhor_horario": melhor_horario,
        "media_diaria": round(total_mes / dias_uteis_decorridos, 1) if dias_uteis_decorridos else 0,
    }
    return render(request, "dashboard/index.html", context)


@login_required(login_url="login")
def agendamentos(request):
    if request.method == "POST":
        form = ConsultaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "O agendamento foi salvo com sucesso.")
            return redirect("agendamentos")
    else:
        form = ConsultaForm()

    proximas_consultas = (
        Consulta.objects.select_related("paciente", "dentista")
        .filter(
            data_hora__gte=timezone.now(),
            status__in=[Consulta.Status.AGENDADA, Consulta.Status.CONFIRMADA],
        )
        .order_by("data_hora")[:6]
    )
    return render(
        request,
        "agenda/agendamentos.html",
        {
            "form": form,
            "hoje": timezone.localdate(),
            "proximas_consultas": proximas_consultas,
            "pacientes_ativos": Paciente.objects.filter(ativo=True).count(),
            "dentistas_ativos": Dentista.objects.filter(ativo=True).count(),
        },
    )


def _cadastro(request, form_class, titulo, descricao, active_page, redirect_name):
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"{titulo} cadastrado com sucesso.")
            return redirect(redirect_name)
    else:
        form = form_class()

    return render(
        request,
        "cadastros/formulario.html",
        {
            "form": form,
            "titulo": titulo,
            "descricao": descricao,
            "active_page": active_page,
            "hoje": timezone.localdate(),
        },
    )


@login_required(login_url="login")
def cadastrar_paciente(request):
    return _cadastro(
        request,
        PacienteForm,
        "Novo paciente",
        "Adicione os dados de contato e identificação do paciente.",
        "pacientes",
        "cadastrar_paciente",
    )


@login_required(login_url="login")
def cadastrar_dentista(request):
    return _cadastro(
        request,
        DentistaForm,
        "Novo dentista",
        "Cadastre o profissional e vincule sua especialidade.",
        "dentistas",
        "cadastrar_dentista",
    )


@login_required(login_url="login")
def cadastrar_convenio(request):
    return _cadastro(
        request,
        ConvenioForm,
        "Novo convênio",
        "Inclua um convênio para associá-lo aos pacientes.",
        "convenios",
        "cadastrar_convenio",
    )


@login_required(login_url="login")
def cadastrar_especialidade(request):
    return _cadastro(
        request,
        EspecialidadeForm,
        "Nova especialidade",
        "Cadastre uma especialidade disponível na clínica.",
        "especialidades",
        "cadastrar_especialidade",
    )
