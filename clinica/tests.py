from django.contrib.admin.sites import site
from django.test import TestCase

from clinica.admin import ConvenioAdmin, DentistaAdmin, EspecialidadeAdmin, PacienteAdmin
from clinica.models import Convenio, Dentista, Especialidade, Paciente


class ClinicaModelTests(TestCase):
    def test_str_especialidade(self):
        self.assertEqual(str(Especialidade(nome="Ortodontia")), "Ortodontia")

    def test_str_paciente(self):
        self.assertEqual(str(Paciente(nome="Maria")), "Maria")

    def test_str_dentista(self):
        self.assertEqual(str(Dentista(nome="Dr. Rafael")), "Dr. Rafael")

    def test_paciente_convenio_opcional(self):
        paciente = Paciente.objects.create(
            nome="João", cpf="111.222.333-44", data_nascimento="1990-05-10"
        )
        self.assertIsNone(paciente.convenio)

    def test_ordering(self):
        self.assertEqual(Paciente._meta.ordering, ["nome"])
        self.assertEqual(Dentista._meta.ordering, ["nome"])


class ClinicaAdminTests(TestCase):
    def test_models_registrados_no_admin(self):
        self.assertIsInstance(site._registry[Especialidade], EspecialidadeAdmin)
        self.assertIsInstance(site._registry[Convenio], ConvenioAdmin)
        self.assertIsInstance(site._registry[Paciente], PacienteAdmin)
        self.assertIsInstance(site._registry[Dentista], DentistaAdmin)

    def test_search_fields(self):
        self.assertIn("nome", PacienteAdmin.search_fields)
        self.assertIn("cpf", PacienteAdmin.search_fields)
        self.assertIn("nome", DentistaAdmin.search_fields)
