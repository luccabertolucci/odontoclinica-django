from django.db import models

from clinica.models import Dentista, Paciente


class Consulta(models.Model):
    class Status(models.TextChoices):
        AGENDADA = "AGENDADA", "Agendada"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        REALIZADA = "REALIZADA", "Realizada"
        CANCELADA = "CANCELADA", "Cancelada"

    paciente = models.ForeignKey(
        Paciente,
        verbose_name="paciente",
        on_delete=models.PROTECT,
        related_name="consultas",
    )
    dentista = models.ForeignKey(
        Dentista,
        verbose_name="dentista",
        on_delete=models.PROTECT,
        related_name="consultas",
    )
    data_hora = models.DateTimeField("data e hora")
    duracao_min = models.PositiveIntegerField("duração (min)", default=30)
    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.AGENDADA,
    )
    valor = models.DecimalField("valor (R$)", max_digits=8, decimal_places=2, default=0)
    observacoes = models.TextField("observações", blank=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "consulta"
        verbose_name_plural = "consultas"
        ordering = ["-data_hora"]

    def __str__(self):
        return f"{self.data_hora:%d/%m/%Y %H:%M} - {self.paciente}"
