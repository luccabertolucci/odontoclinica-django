from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from agenda.models import Consulta
from clinica.models import Convenio, Dentista, Especialidade, Paciente


class DashboardRegistrationIntegrationTests(TestCase):
    """Exercise the real Django Admin registration forms and dashboard together."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_superuser(
            username="dashboard-test-admin",
            email="dashboard-test@example.com",
            password="test-password-123",
        )
        cls.specialty = Especialidade.objects.create(nome="Clínico Geral")
        cls.dentist = Dentista.objects.create(
            nome="Dra. Integração",
            cro="CRO-TEST-9001",
            especialidade=cls.specialty,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def _register_patient(self, cpf="900.111.222-33", name="Paciente de Integração"):
        response = self.client.post(
            reverse("admin:clinica_paciente_add"),
            {
                "nome": name,
                "cpf": cpf,
                "data_nascimento": "1990-05-10",
                "telefone": "11999990000",
                "email": "paciente@example.com",
                "convenio": "",
                "ativo": "on",
                "_save": "Salvar",
            },
        )
        self.assertEqual(response.status_code, 302, response.context)
        return Paciente.objects.get(cpf=cpf)

    def _register_consultation(self, patient, status, value):
        local_datetime = timezone.make_aware(
            datetime.combine(timezone.localdate(), time(10, 0))
        )
        response = self.client.post(
            reverse("admin:agenda_consulta_add"),
            {
                "paciente": str(patient.pk),
                "dentista": str(self.dentist.pk),
                "data_hora_0": local_datetime.strftime("%d/%m/%Y"),
                "data_hora_1": local_datetime.strftime("%H:%M:%S"),
                "duracao_min": "30",
                "status": status,
                "valor": str(value),
                "observacoes": "Criada pelo teste de integração",
                "_save": "Salvar",
            },
        )
        self.assertEqual(response.status_code, 302, response.context)
        return Consulta.objects.get(paciente=patient, dentista=self.dentist)

    def test_admin_patient_registration_keeps_dashboard_available(self):
        patient = self._register_patient()

        self.assertEqual(patient.nome, "Paciente de Integração")
        dashboard = self.client.get(reverse("dashboard"))

        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.context["total_mes"], 0)
        self.assertContains(dashboard, reverse("admin:index"))

    def test_admin_consultation_registration_updates_operational_dashboard(self):
        patient = self._register_patient()
        consultation = self._register_consultation(
            patient, Consulta.Status.CONFIRMADA, Decimal("185.50")
        )

        self.assertEqual(consultation.status, Consulta.Status.CONFIRMADA)
        dashboard = self.client.get(reverse("dashboard"))

        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.context["total_mes"], 1)
        self.assertEqual(dashboard.context["cancelamentos"], 0)
        self.assertEqual(dashboard.context["receita_prevista"], Decimal("185.50"))
        self.assertIn(
            {"label": "Confirmada", "value": 1, "key": "confirmada"},
            dashboard.context["status_chart"],
        )

    def test_admin_patient_and_realized_consultation_update_financial_dashboard(self):
        patient = self._register_patient()
        consultation = self._register_consultation(
            patient, Consulta.Status.REALIZADA, Decimal("320.00")
        )

        self.assertEqual(consultation.valor, Decimal("320.00"))
        dashboard = self.client.get(reverse("dashboard"))

        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.context["realizadas_mes"], 1)
        self.assertEqual(dashboard.context["faturamento_mes"], Decimal("320.00"))
        self.assertEqual(dashboard.context["ticket_medio"], Decimal("320.00"))
        self.assertEqual(dashboard.context["melhor_horario"]["total"], Decimal("320.00"))


class UserFacingAppointmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="clinica-user", password="test-pass-123")
        specialty = Especialidade.objects.create(nome="Odontologia Geral")
        cls.dentist = Dentista.objects.create(
            nome="Dra. Portal",
            cro="CRO-PORTAL-1",
            especialidade=specialty,
        )
        cls.patient = Paciente.objects.create(
            nome="Paciente do Portal",
            cpf="901.111.222-33",
            data_nascimento="1990-05-10",
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_portal_pages_are_available_without_admin_access(self):
        dashboard = self.client.get(reverse("dashboard"))
        appointments = self.client.get(reverse("agendamentos"))

        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(appointments.status_code, 200)
        self.assertContains(dashboard, reverse("agendamentos"))
        self.assertNotContains(dashboard, reverse("admin:index"))
        for route_name in (
            "cadastrar_paciente",
            "cadastrar_dentista",
            "cadastrar_convenio",
            "cadastrar_especialidade",
        ):
            self.assertContains(dashboard, reverse(route_name))
        self.assertTemplateUsed(appointments, "agenda/agendamentos.html")
        self.assertEqual(
            self.client.get(reverse("admin:index")).status_code,
            302,
        )

    def test_user_can_create_appointment_from_portal(self):
        scheduled_at = timezone.localtime(timezone.now() + timedelta(days=1))
        response = self.client.post(
            reverse("agendamentos"),
            {
                "paciente": self.patient.pk,
                "dentista": self.dentist.pk,
                "data_hora": scheduled_at.strftime("%Y-%m-%dT%H:%M"),
                "duracao_min": 45,
                "valor": "250.00",
                "observacoes": "Cadastro pelo portal",
            },
        )

        self.assertRedirects(response, reverse("agendamentos"))
        consulta = Consulta.objects.get(paciente=self.patient, dentista=self.dentist)
        self.assertEqual(consulta.status, Consulta.Status.AGENDADA)
        self.assertEqual(consulta.valor, Decimal("250.00"))
        self.assertEqual(consulta.duracao_min, 45)

    def test_portal_rejects_overlapping_appointment_for_same_dentist(self):
        scheduled_at = timezone.localtime(timezone.now() + timedelta(days=1)).replace(
            minute=0, second=0, microsecond=0
        )
        Consulta.objects.create(
            paciente=self.patient,
            dentista=self.dentist,
            data_hora=scheduled_at,
            duracao_min=60,
        )

        response = self.client.post(
            reverse("agendamentos"),
            {
                "paciente": self.patient.pk,
                "dentista": self.dentist.pk,
                "data_hora": (scheduled_at + timedelta(minutes=30)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "duracao_min": 30,
                "valor": "250.00",
                "observacoes": "Deve ser rejeitada",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Consulta.objects.count(), 1)
        self.assertContains(response, "já possui uma consulta nesse intervalo")

    def test_calendar_groups_all_month_appointments_by_day(self):
        first_appointment = timezone.make_aware(datetime(2026, 3, 5, 9, 0))
        second_appointment = timezone.make_aware(datetime(2026, 3, 5, 11, 30))
        outside_month = timezone.make_aware(datetime(2026, 4, 2, 10, 0))
        Consulta.objects.create(
            paciente=self.patient,
            dentista=self.dentist,
            data_hora=first_appointment,
            duracao_min=30,
            status=Consulta.Status.AGENDADA,
        )
        Consulta.objects.create(
            paciente=self.patient,
            dentista=self.dentist,
            data_hora=second_appointment,
            duracao_min=30,
            status=Consulta.Status.CANCELADA,
        )
        Consulta.objects.create(
            paciente=self.patient,
            dentista=self.dentist,
            data_hora=outside_month,
            duracao_min=30,
        )

        response = self.client.get(
            reverse("agendamentos"),
            {"mes": "3", "ano": "2026"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Março de 2026")
        self.assertContains(response, "09:00")
        self.assertContains(response, "11:30")
        self.assertContains(response, "Agendada")
        self.assertContains(response, "Cancelada")
        self.assertNotContains(response, "10:00")
        self.assertEqual(response.context["total_consultas_mes"], 2)

    def test_calendar_navigation_links_neighboring_months(self):
        response = self.client.get(
            reverse("agendamentos"),
            {"mes": "1", "ano": "2026"},
        )

        self.assertContains(response, 'href="?mes=12&amp;ano=2025#calendario"')
        self.assertContains(response, 'href="?mes=2&amp;ano=2026#calendario"')
        self.assertContains(response, 'aria-label="Mês anterior"')
        self.assertContains(response, 'aria-label="Próximo mês"')

    def test_portal_login_page_is_separate_from_admin_login(self):
        self.client.logout()

        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_user_can_create_clinic_records_from_portal(self):
        for route_name in (
            "cadastrar_convenio",
            "cadastrar_especialidade",
            "cadastrar_paciente",
            "cadastrar_dentista",
        ):
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "cadastros/formulario.html")

        response = self.client.post(
            reverse("cadastrar_convenio"),
            {"nome": "Convênio Portal", "ativo": "on"},
        )
        self.assertRedirects(response, reverse("cadastrar_convenio"))
        convenio = Convenio.objects.get(nome="Convênio Portal")

        response = self.client.post(
            reverse("cadastrar_especialidade"),
            {
                "nome": "Especialidade Portal",
                "descricao": "Cadastro realizado pelo portal",
                "ativo": "on",
            },
        )
        self.assertRedirects(response, reverse("cadastrar_especialidade"))
        specialty = Especialidade.objects.get(nome="Especialidade Portal")

        response = self.client.post(
            reverse("cadastrar_paciente"),
            {
                "nome": "Paciente Novo Portal",
                "cpf": "902.111.222-33",
                "data_nascimento": "1988-04-12",
                "telefone": "11988887777",
                "email": "novo.paciente@example.com",
                "convenio": convenio.pk,
                "ativo": "on",
            },
        )
        self.assertRedirects(response, reverse("cadastrar_paciente"))
        patient = Paciente.objects.get(cpf="902.111.222-33")

        response = self.client.post(
            reverse("cadastrar_dentista"),
            {
                "nome": "Dr. Novo Portal",
                "cro": "CRO-PORTAL-2",
                "especialidade": specialty.pk,
                "telefone": "11977776666",
                "email": "dentista.portal@example.com",
                "ativo": "on",
            },
        )
        self.assertRedirects(response, reverse("cadastrar_dentista"))

        self.assertEqual(patient.convenio, convenio)
        self.assertTrue(Dentista.objects.filter(cro="CRO-PORTAL-2", especialidade=specialty).exists())

    def test_registration_pages_require_login(self):
        self.client.logout()
        for route_name in (
            "cadastrar_paciente",
            "cadastrar_dentista",
            "cadastrar_convenio",
            "cadastrar_especialidade",
        ):
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertRedirects(
                    response,
                    f"{reverse('login')}?next={reverse(route_name)}",
                )
