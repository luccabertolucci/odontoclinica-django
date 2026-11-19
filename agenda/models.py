from datetime import timedelta

from django.core.exceptions import ValidationError
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
        verbose_name="Dentista",
        on_delete=models.PROTECT,
        related_name="consultas",
    )
    data_hora = models.DateTimeField("Data e hora")
    duracao_min = models.PositiveIntegerField("duração (min)", default=30)
    status = models.CharField(
        "Status",
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

    def clean(self):
        super().clean()
        if (
            self.status == self.Status.CANCELADA
            or not self.dentista_id
            or not self.data_hora
            or self.duracao_min is None
        ):
            return

        inicio = self.data_hora
        fim = inicio + timedelta(minutes=self.duracao_min)
        candidatas = Consulta.objects.filter(
            dentista_id=self.dentista_id,
            status__in=[
                self.Status.AGENDADA,
                self.Status.CONFIRMADA,
                self.Status.REALIZADA,
            ],
            data_hora__lt=fim,
        ).exclude(pk=self.pk)

        for consulta in candidatas.only("data_hora", "duracao_min").iterator():
            consulta_fim = consulta.data_hora + timedelta(
                minutes=consulta.duracao_min
            )
            if inicio < consulta_fim:
                raise ValidationError(
                    {
                        "data_hora": (
                            "Este dentista já possui uma consulta nesse intervalo."
                        )
                    }
                )

    def __str__(self):
        return f"{self.data_hora:%d/%m/%Y %H:%M} - {self.paciente}"
