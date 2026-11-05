from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from agenda.models import Consulta
from clinica.models import Convenio, Dentista, Especialidade, Paciente

PERFIS = {
    "Administrador": {
        Especialidade: ["add", "change", "delete", "view"],
        Convenio: ["add", "change", "delete", "view"],
        Paciente: ["add", "change", "delete", "view"],
        Dentista: ["add", "change", "delete", "view"],
        Consulta: ["add", "change", "delete", "view"],
    },
    "Dentista": {
        Consulta: ["add", "change", "view"],
        Paciente: ["view"],
        Dentista: ["view"],
        Especialidade: ["view"],
    },
    "Atendente": {
        Consulta: ["add", "change", "view"],
        Paciente: ["add", "change", "view"],
        Dentista: ["view"],
        Especialidade: ["view"],
        Convenio: ["view"],
    },
}


class Command(BaseCommand):
    help = "Cria os grupos de perfil e define as permissões no admin."

    def handle(self, *args, **options):
        for nome, modelos in PERFIS.items():
            grupo, criado = Group.objects.get_or_create(name=nome)
            permissoes = []
            for modelo, acoes in modelos.items():
                ct = modelo._meta.app_label + "." + modelo._meta.model_name
                for acao in acoes:
                    permissoes.append(Permission.objects.get(content_type__app_label=modelo._meta.app_label, content_type__model=modelo._meta.model_name, codename=f"{acao}_{modelo._meta.model_name}"))
            grupo.permissions.set(permissoes)
            self.stdout.write(self.style.SUCCESS(f"{'Criado' if criado else 'Atualizado'} grupo '{nome}' com {len(permissoes)} permissões"))
