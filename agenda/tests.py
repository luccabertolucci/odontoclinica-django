from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
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
        hoje = timezone.localdate()
        self.hoje = Consulta.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            data_hora=timezone.make_aware(datetime.combine(hoje, time(12, 0))),
        )
        self.futuro = Consulta.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            data_hora=timezone.make_aware(
                datetime.combine(hoje + timedelta(days=3), time(12, 0))
            ),
        )
        self.passado = Consulta.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            data_hora=timezone.make_aware(
                datetime.combine(hoje - timedelta(days=20), time(12, 0))
            ),
        )

    def _aplicar(self, valor):
        request = RequestFactory().get("/", {"periodo": valor})
        filtro = PeriodoFilter(request, request.GET.copy(), Consulta, None)
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


class ConsultaConflictTests(TestCase):
    def setUp(self):
        self.especialidade = Especialidade.objects.create(nome="Clínico Geral")
        self.dentista = Dentista.objects.create(
            nome="Dra. Ana", cro="CRO-2", especialidade=self.especialidade
        )
        self.paciente = Paciente.objects.create(
            nome="João", cpf="222.333.444-55", data_nascimento="1985-03-20"
        )
        self.inicio = timezone.make_aware(datetime(2026, 11, 20, 10, 0))
        self.consulta = Consulta.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            data_hora=self.inicio,
            duracao_min=60,
        )

    def _consulta(self, data_hora, **kwargs):
        return Consulta(
            paciente=self.paciente,
            dentista=self.dentista,
            data_hora=data_hora,
            duracao_min=30,
            **kwargs,
        )

    def test_rejects_overlapping_consultation(self):
        consulta = self._consulta(self.inicio + timedelta(minutes=30))

        with self.assertRaises(ValidationError) as error:
            consulta.full_clean()

        self.assertIn("data_hora", error.exception.message_dict)

    def test_allows_adjacent_consultation(self):
        consulta = self._consulta(self.inicio + timedelta(minutes=60))

        consulta.full_clean()

    def test_cancelled_consultation_does_not_block_interval(self):
        self.consulta.status = Consulta.Status.CANCELADA
        self.consulta.save(update_fields=["status"])
        consulta = self._consulta(self.inicio + timedelta(minutes=30))

        consulta.full_clean()

    def test_editing_consultation_does_not_conflict_with_itself(self):
        self.consulta.full_clean()

    def test_database_trigger_rejects_direct_overlapping_insert(self):
        consulta = self._consulta(self.inicio + timedelta(minutes=30))

        with self.assertRaises(IntegrityError), transaction.atomic():
            Consulta.objects.bulk_create([consulta])

    def test_database_trigger_rejects_overlapping_update(self):
        outra_consulta = Consulta.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            data_hora=self.inicio + timedelta(hours=2),
            duracao_min=30,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Consulta.objects.filter(pk=outra_consulta.pk).update(
                data_hora=self.inicio + timedelta(minutes=30)
            )
