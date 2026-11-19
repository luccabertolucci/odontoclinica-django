from datetime import datetime, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from agenda.models import Consulta
from clinica.models import Dentista, Especialidade, Paciente


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
