from django import forms

from clinica.models import Convenio, Dentista, Especialidade, Paciente

from .models import Consulta


class ConsultaForm(forms.ModelForm):
    data_hora = forms.DateTimeField(
        label="Data e horário",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"},
        ),
    )

    class Meta:
        model = Consulta
        fields = (
            "paciente",
            "dentista",
            "data_hora",
            "duracao_min",
            "valor",
            "observacoes",
        )
        widgets = {
            "observacoes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["paciente"].queryset = Paciente.objects.filter(ativo=True)
        self.fields["dentista"].queryset = Dentista.objects.filter(ativo=True)
        self.fields["paciente"].empty_label = "Selecione um paciente"
        self.fields["dentista"].empty_label = "Selecione um profissional"
        self.fields["duracao_min"].initial = 30
        self.fields["valor"].initial = 0
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["observacoes"].required = False


class PortalModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-checkbox"
                if isinstance(field.widget, forms.CheckboxInput)
                else "form-control"
            )


class PacienteForm(PortalModelForm):
    class Meta:
        model = Paciente
        fields = (
            "nome",
            "cpf",
            "data_nascimento",
            "telefone",
            "email",
            "convenio",
            "ativo",
        )
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["convenio"].queryset = Convenio.objects.filter(ativo=True)
        self.fields["convenio"].required = False
        self.fields["convenio"].empty_label = "Sem convênio"


class DentistaForm(PortalModelForm):
    class Meta:
        model = Dentista
        fields = ("nome", "cro", "especialidade", "telefone", "email", "ativo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["especialidade"].queryset = Especialidade.objects.filter(ativo=True)
        self.fields["especialidade"].empty_label = "Selecione uma especialidade"


class ConvenioForm(PortalModelForm):
    class Meta:
        model = Convenio
        fields = ("nome", "ativo")


class EspecialidadeForm(PortalModelForm):
    class Meta:
        model = Especialidade
        fields = ("nome", "descricao", "ativo")
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 4}),
        }
