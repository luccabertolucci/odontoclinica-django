from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from agenda.models import Consulta
from clinica.models import Convenio, Dentista, Especialidade, Paciente


class Command(BaseCommand):
    help = "Popula o banco com dados de demonstração para a apresentação."

    def handle(self, *args, **options):
        especialidades = [
            ("Ortodontia", "Correção do alinhamento dos dentes."),
            ("Endodontia", "Tratamento de canal."),
            ("Implantodontia", "Implantes dentários."),
            ("Clínico Geral", "Atendimento geral e prevenção."),
        ]
        esp = {}
        for nome, desc in especialidades:
            obj, _ = Especialidade.objects.get_or_create(nome=nome, defaults={"descricao": desc})
            esp[nome] = obj

        convenios = ["Amil", "Unimed", "Bradesco Saúde"]
        conv = {}
        for nome in convenios:
            obj, _ = Convenio.objects.get_or_create(nome=nome)
            conv[nome] = obj

        dentistas = [
            ("Dra. Beatriz Souza", "CRO-SP 12345", "Ortodontia"),
            ("Dr. Rafael Lima", "CRO-SP 23456", "Endodontia"),
            ("Dra. Camila Rocha", "CRO-SP 34567", "Implantodontia"),
            ("Dr. Marcos Alves", "CRO-SP 45678", "Clínico Geral"),
        ]
        dent = {}
        for nome, cro, especialidade in dentistas:
            obj, _ = Dentista.objects.get_or_create(
                cro=cro,
                defaults={"nome": nome, "especialidade": esp[especialidade]},
            )
            dent[nome] = obj

        pacientes = [
            ("João da Silva", "111.222.333-44", "Amil"),
            ("Maria Oliveira", "222.333.444-55", "Unimed"),
            ("Pedro Santos", "333.444.555-66", "Bradesco Saúde"),
            ("Ana Costa", "444.555.666-77", "Amil"),
            ("Lucas Pereira", "555.666.777-88", None),
            ("Julia Almeida", "666.777.888-99", "Unimed"),
            ("Carlos Mendes", "777.888.999-00", None),
            ("Fernanda Lima", "888.999.000-11", "Bradesco Saúde"),
        ]
        pac = []
        for nome, cpf, convenio in pacientes:
            obj, _ = Paciente.objects.get_or_create(
                cpf=cpf,
                defaults={
                    "nome": nome,
                    "convenio": conv[convenio] if convenio else None,
                    "data_nascimento": "1990-05-10",
                    "telefone": "(35) 99999-0000",
                    "email": nome.split()[0].lower() + "@example.com",
                },
            )
            pac.append(obj)

        agora = timezone.localtime().replace(minute=0, second=0, microsecond=0)
        consultas = [
            (pac[0], "Dra. Beatriz Souza", agora.replace(hour=9), "CONFIRMADA", 250.00),
            (pac[1], "Dr. Rafael Lima", agora.replace(hour=10), "AGENDADA", 180.00),
            (pac[2], "Dra. Camila Rocha", agora.replace(hour=11), "REALIZADA", 1500.00),
            (pac[3], "Dr. Marcos Alves", agora + timedelta(days=1, hours=9), "AGENDADA", 120.00),
            (pac[4], "Dra. Beatriz Souza", agora + timedelta(days=2, hours=14), "CONFIRMADA", 200.00),
            (pac[5], "Dr. Rafael Lima", agora + timedelta(days=3, hours=8), "CANCELADA", 0.00),
            (pac[6], "Dra. Camila Rocha", agora + timedelta(days=4, hours=16), "AGENDADA", 900.00),
            (pac[7], "Dr. Marcos Alves", agora + timedelta(days=6, hours=10), "AGENDADA", 130.00),
            (pac[0], "Dra. Beatriz Souza", agora - timedelta(days=15), "REALIZADA", 250.00),
            (pac[1], "Dr. Rafael Lima", agora - timedelta(days=10), "REALIZADA", 180.00),
        ]
        for paciente, dentista_nome, data_hora, status, valor in consultas:
            Consulta.objects.get_or_create(
                paciente=paciente,
                dentista=dent[dentista_nome],
                data_hora=data_hora,
                defaults={"status": status, "valor": valor, "duracao_min": 30},
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Dados de demonstração prontos: "
                f"{Consulta.objects.count()} consultas, "
                f"{Paciente.objects.count()} pacientes, "
                f"{Dentista.objects.count()} dentistas."
            )
        )
