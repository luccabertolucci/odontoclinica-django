from django.db import models


class Especialidade(models.Model):
    nome = models.CharField("nome", max_length=120, unique=True)
    descricao = models.TextField("descrição", blank=True)
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "especialidade"
        verbose_name_plural = "especialidades"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Convenio(models.Model):
    nome = models.CharField("nome", max_length=120, unique=True)
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "convênio"
        verbose_name_plural = "convênios"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Paciente(models.Model):
    nome = models.CharField("nome", max_length=180)
    cpf = models.CharField("CPF", max_length=14, unique=True)
    data_nascimento = models.DateField("data de nascimento")
    telefone = models.CharField("telefone", max_length=20, blank=True)
    email = models.EmailField("e-mail", blank=True)
    convenio = models.ForeignKey(
        Convenio,
        verbose_name="convênio",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pacientes",
    )
    ativo = models.BooleanField("ativo", default=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "paciente"
        verbose_name_plural = "pacientes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Dentista(models.Model):
    nome = models.CharField("nome", max_length=180)
    cro = models.CharField("CRO", max_length=30, unique=True)
    especialidade = models.ForeignKey(
        Especialidade,
        verbose_name="especialidade",
        on_delete=models.PROTECT,
        related_name="dentistas",
    )
    telefone = models.CharField("telefone", max_length=20, blank=True)
    email = models.EmailField("e-mail", blank=True)
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "dentista"
        verbose_name_plural = "dentistas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome
