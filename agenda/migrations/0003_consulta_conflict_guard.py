from django.db import migrations


def install_conflict_triggers(apps, schema_editor):
    if schema_editor.connection.vendor != "sqlite":
        return

    consulta = apps.get_model("agenda", "Consulta")
    table = schema_editor.quote_name(consulta._meta.db_table)
    insert_trigger = schema_editor.quote_name("agenda_consulta_conflict_insert")
    update_trigger = schema_editor.quote_name("agenda_consulta_conflict_update")
    conflict_condition = """
        NEW.status <> 'CANCELADA'
        AND EXISTS (
            SELECT 1
            FROM {table} AS existing
            WHERE existing.dentista_id = NEW.dentista_id
              AND existing.status <> 'CANCELADA'
              AND existing.id <> NEW.id
              AND julianday(NEW.data_hora)
                    < julianday(
                        existing.data_hora,
                        '+' || existing.duracao_min || ' minutes'
                    )
              AND julianday(existing.data_hora)
                    < julianday(
                        NEW.data_hora,
                        '+' || NEW.duracao_min || ' minutes'
                    )
        )
    """.format(table=table)

    schema_editor.execute(
        """
        CREATE TRIGGER {trigger}
        BEFORE INSERT ON {table}
        WHEN {condition}
        BEGIN
            SELECT RAISE(ABORT, 'conflito_agendamento');
        END
        """.format(trigger=insert_trigger, table=table, condition=conflict_condition)
    )
    schema_editor.execute(
        """
        CREATE TRIGGER {trigger}
        BEFORE UPDATE OF dentista_id, data_hora, duracao_min, status ON {table}
        WHEN {condition}
        BEGIN
            SELECT RAISE(ABORT, 'conflito_agendamento');
        END
        """.format(trigger=update_trigger, table=table, condition=conflict_condition)
    )


def remove_conflict_triggers(apps, schema_editor):
    if schema_editor.connection.vendor != "sqlite":
        return

    schema_editor.execute(
        "DROP TRIGGER IF EXISTS "
        + schema_editor.quote_name("agenda_consulta_conflict_insert")
    )
    schema_editor.execute(
        "DROP TRIGGER IF EXISTS "
        + schema_editor.quote_name("agenda_consulta_conflict_update")
    )


class Migration(migrations.Migration):
    dependencies = [
        ("agenda", "0002_alter_consulta_data_hora_alter_consulta_dentista_and_more"),
    ]

    operations = [
        migrations.RunPython(
            install_conflict_triggers,
            reverse_code=remove_conflict_triggers,
        ),
    ]
