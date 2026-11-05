from django.test import TestCase
from django.utils import timezone

from agenda.models import Consulta
from clinica.models import Dentista, Especialidade, Paciente


class ConsultaModelTests(TestCase):
    def setUp(self):
        self.especialidade = Especialidade.objects.create(nome="Ortodontia")
        self.dentista = Dentista.objects.create(
            nome="Dra. Beatriz", cro="CRO-1", especialidade=self.especialidade
        )
        self.paciente = Paciente.objects.create(
            nome="Maria", cpf="111.222.333-44", data_nascimento="1990-05-10"
        )

    def test_status_padrao(self):
        consulta = Consulta.objects.create(
            paciente=self.paciente, dentista=self.dentista, data_hora=timezone.now()
        )
        self.assertEqual(consulta.status, Consulta.Status.AGENDADA)

    def test_duracao_padrao(self):
        consulta = Consulta.objects.create(
            paciente=self.paciente, dentista=self.dentista, data_hora=timezone.now()
        )
        self.assertEqual(consulta.duracao_min, 30)

    def test_str(self):
        data = timezone.datetime(2026, 5, 11, 14, 30, tzinfo=timezone.utc)
        consulta = Consulta.objects.create(
            paciente=self.paciente, dentista=self.dentista, data_hora=data
        )
        self.assertIn("11/05/2026 14:30", str(consulta))

    def test_ordering(self):
        self.assertEqual(Consulta._meta.ordering, ["-data_hora"])
