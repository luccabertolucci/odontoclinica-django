from datetime import timedelta

from django.test import RequestFactory, TestCase
from django.utils import timezone

from agenda.admin import PeriodoFilter
from agenda.models import Consulta
from clinica.models import Dentista, Especialidade, Paciente


class PeriodoFilterTests(TestCase):
    def setUp(self):
        self.especialidade = Especialidade.objects.create(nome="Ortodontia")
        self.dentista = Dentista.objects.create(
            nome="Dra. Beatriz", cro="CRO-1", especialidade=self.especialidade
        )
        self.paciente = Paciente.objects.create(
            nome="Maria", cpf="111.222.333-44", data_nascimento="1990-05-10"
        )
        self.agora = timezone.now()
        self.hoje = Consulta.objects.create(
            paciente=self.paciente, dentista=self.dentista, data_hora=self.agora
        )
        self.futuro = Consulta.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            data_hora=self.agora + timedelta(days=3),
        )
        self.passado = Consulta.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            data_hora=self.agora - timedelta(days=20),
        )

    def _aplicar(self, valor):
        request = RequestFactory().get("/", {"periodo": valor})
        filtro = PeriodoFilter(request, {"periodo": valor}, Consulta, None)
        return filtro.queryset(request, Consulta.objects.all())

    def test_hoje(self):
        resultado = self._aplicar("hoje")
        self.assertIn(self.hoje, resultado)
        self.assertNotIn(self.futuro, resultado)
        self.assertNotIn(self.passado, resultado)

    def test_proximos_7_dias(self):
        resultado = self._aplicar("7")
        self.assertIn(self.futuro, resultado)
        self.assertNotIn(self.passado, resultado)

    def test_ultimos_30_dias(self):
        resultado = self._aplicar("30")
        self.assertIn(self.hoje, resultado)
        self.assertIn(self.passado, resultado)
