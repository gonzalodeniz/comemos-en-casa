# Comprueba las consultas y operaciones de planificación de comidas.
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import select, text

from app.models import MealAssignment


from meal_planning_test_support import meal_database, api_get, api_post, authenticate, seed_labels, post_with_session


def test_meal_planning_reads_require_an_active_session(meal_database):
    assert api_get("/api/v1/food-labels").status_code == 401
    assert (
        api_get(
            "/api/v1/meal-planning",
            params={"start_date": "2026-11-02", "end_date": "2026-11-08"},
        ).status_code
        == 401
    )

def test_meal_planning_reads_reject_inactive_users(meal_database):
    cookies = authenticate(meal_database, active=False)

    assert api_get("/api/v1/food-labels", cookies=cookies).status_code == 401
    assert (
        api_get(
            "/api/v1/meal-planning",
            params={"start_date": "2026-11-02", "end_date": "2026-11-08"},
            cookies=cookies,
        ).status_code
        == 401
    )

def test_meal_planning_range_is_inclusive_and_reports_canary_date(
    meal_database, monkeypatch
):
    cookies = authenticate(meal_database)
    pescado, arroz = seed_labels(meal_database)
    with meal_database() as db:
        db.add_all(
            [
                MealAssignment(
                    date=date(2026, 11, 1), slot="dinner", label_id=pescado.id
                ),
                MealAssignment(
                    date=date(2026, 11, 2), slot="lunch", label_id=arroz.id
                ),
                MealAssignment(
                    date=date(2026, 11, 8), slot="dinner", label_id=pescado.id
                ),
                MealAssignment(
                    date=date(2026, 11, 9), slot="lunch", label_id=arroz.id
                ),
            ]
        )
        db.commit()

    monkeypatch.setattr(
        "app.meal_planning_api.canary_today", lambda: date(2026, 11, 2)
    )
    response = api_get(
        "/api/v1/meal-planning",
        params={"start_date": "2026-11-02", "end_date": "2026-11-08"},
        cookies=cookies,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["start_date"] == "2026-11-02"
    assert payload["end_date"] == "2026-11-08"
    assert payload["today"] == "2026-11-02"
    assert payload["timezone"] == "Atlantic/Canary"
    assert [entry["date"] for entry in payload["assignments"]] == [
        "2026-11-02",
        "2026-11-08",
    ]
    assert [entry["slot"] for entry in payload["assignments"]] == [
        "lunch",
        "dinner",
    ]
    assert [entry["label"]["code"] for entry in payload["assignments"]] == [
        "arroz",
        "pescado",
    ]
    with meal_database() as db:
        assert db.query(MealAssignment).count() == 4

def test_meal_planning_rejects_a_reversed_range_without_writes(meal_database):
    cookies = authenticate(meal_database)

    response = api_get(
        "/api/v1/meal-planning",
        params={"start_date": "2026-11-09", "end_date": "2026-11-02"},
        cookies=cookies,
    )

    assert response.status_code == 422
    with meal_database() as db:
        assert db.query(MealAssignment).count() == 0

def test_assigning_meal_schedules_canary_reminder_for_all_active_users(meal_database, monkeypatch):
    """Verifica configuración de recordatorio y destinatarios activos."""
    from app.models import User
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    class Reloj(datetime):
        """Fija el instante de programación para la prueba."""
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 1, 17, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("app.meal_planning_api.datetime", Reloj)
    payload = {"action": "assign", "start_date": "2026-11-02", "slot": "lunch", "label_id": str(pescado.id), "reminder": {"days_before": 0, "send_time": "18:00", "message": "Sacar el pollo"}}
    response = post_with_session("/api/v1/meal-planning/operations", payload, cookies)
    assert response.status_code == 200
    with meal_database() as db:
        assignment = db.scalar(select(MealAssignment))
        assert (assignment.reminder_days, assignment.reminder_time, assignment.reminder_message) == (0, "18:00", "Sacar el pollo")
        assert db.query(User).filter(User.is_active.is_(True)).count() == 1

def test_preview_is_authenticated_csrf_protected_and_has_no_side_effects(
    meal_database,
):
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    payload = {
        "action": "assign",
        "start_date": "2026-11-02",
        "slot": "lunch",
        "label_id": str(pescado.id),
        "repeat": {"interval_weeks": 1, "end_date": "2026-11-16"},
    }

    assert api_post("/api/v1/meal-planning/preview", payload=payload).status_code == 401
    assert (
        api_post(
            "/api/v1/meal-planning/preview",
            payload=payload,
            cookies=cookies,
            csrf_token=cookies["csrf_token"],
            origin=False,
        ).status_code
        == 403
    )
    response = post_with_session("/api/v1/meal-planning/preview", payload, cookies)

    assert response.status_code == 200
    preview = response.json()
    assert [entry["date"] for entry in preview["dates"]] == [
        "2026-11-02",
        "2026-11-09",
        "2026-11-16",
    ]
    assert preview["changed_count"] == 3
    assert preview["requires_confirmation"] is False
    assert preview["preview_token"]
    with meal_database() as db:
        assert db.query(MealAssignment).count() == 0

def test_assignment_repeat_replaces_only_after_confirming_current_preview(
    meal_database,
):
    cookies = authenticate(meal_database)
    pescado, arroz = seed_labels(meal_database)
    with meal_database() as db:
        db.add(
            MealAssignment(date=date(2026, 11, 9), slot="lunch", label_id=arroz.id)
        )
        db.commit()
    payload = {
        "action": "assign",
        "start_date": "2026-11-02",
        "slot": "lunch",
        "label_id": str(pescado.id),
        "repeat": {"interval_weeks": 1, "end_date": "2026-11-16"},
    }

    preview = post_with_session(
        "/api/v1/meal-planning/preview", payload, cookies
    ).json()
    assert preview["requires_confirmation"] is True
    assert [entry["change"] for entry in preview["dates"]] == [
        "assign",
        "replace",
        "assign",
    ]

    unconfirmed = post_with_session(
        "/api/v1/meal-planning/operations", payload, cookies
    )
    assert unconfirmed.status_code == 409
    with meal_database() as db:
        assert db.get(MealAssignment, db.scalar(select(MealAssignment.id))) is not None
        assert db.scalar(
            select(MealAssignment.label_id).where(
                MealAssignment.date == date(2026, 11, 9)
            )
        ) == arroz.id

    operation = {
        **payload,
        "confirmed": True,
        "preview_token": preview["preview_token"],
    }
    response = post_with_session("/api/v1/meal-planning/operations", operation, cookies)
    assert response.status_code == 200
    assert response.json()["changed_count"] == 3
    with meal_database() as db:
        assert db.query(MealAssignment).count() == 3
        assert set(db.scalars(select(MealAssignment.label_id)).all()) == {pescado.id}

def test_stale_preview_returns_fresh_confirmation_without_overwriting(
    meal_database,
):
    cookies = authenticate(meal_database)
    pescado, arroz = seed_labels(meal_database)
    payload = {
        "action": "assign",
        "start_date": "2026-11-02",
        "slot": "dinner",
        "label_id": str(pescado.id),
        "repeat": None,
    }
    original_preview = post_with_session(
        "/api/v1/meal-planning/preview", payload, cookies
    ).json()
    with meal_database() as db:
        db.add(
            MealAssignment(date=date(2026, 11, 2), slot="dinner", label_id=arroz.id)
        )
        db.commit()

    stale_request = {
        **payload,
        "confirmed": True,
        "preview_token": original_preview["preview_token"],
    }
    response = post_with_session(
        "/api/v1/meal-planning/operations", stale_request, cookies
    )
    assert response.status_code == 409
    refreshed = response.json()["detail"]["preview"]
    assert refreshed["requires_confirmation"] is True
    assert refreshed["preview_token"] != original_preview["preview_token"]
    with meal_database() as db:
        assert db.scalar(select(MealAssignment.label_id)) == arroz.id

    fresh_request = {**payload, "confirmed": True, "preview_token": refreshed["preview_token"]}
    applied = post_with_session(
        "/api/v1/meal-planning/operations", fresh_request, cookies
    )
    assert applied.status_code == 200
    with meal_database() as db:
        assert db.scalar(select(MealAssignment.label_id)) == pescado.id

# Comprueba que el borrado repetido incluye platos diferentes y exige confirmación.
def test_delete_repeatedly_removes_different_labels_and_requires_confirmation(
    meal_database,
):
    cookies = authenticate(meal_database)
    pescado, arroz = seed_labels(meal_database)
    with meal_database() as db:
        db.add_all(
            [
                MealAssignment(date=date(2026, 11, 2), slot="dinner", label_id=pescado.id),
                MealAssignment(date=date(2026, 11, 9), slot="dinner", label_id=arroz.id),
            ]
        )
        db.commit()
    payload = {
        "action": "delete",
        "start_date": "2026-11-02",
        "slot": "dinner",
        "label_id": str(pescado.id),
        "repeat": {"interval_weeks": 1, "end_date": "2026-11-09"},
    }
    preview = post_with_session("/api/v1/meal-planning/preview", payload, cookies).json()
    assert [entry["change"] for entry in preview["dates"]] == ["delete", "delete"]
    assert preview["requires_confirmation"] is True

    unconfirmed = post_with_session("/api/v1/meal-planning/operations", payload, cookies)
    assert unconfirmed.status_code == 409
    operation = {**payload, "confirmed": True, "preview_token": preview["preview_token"]}
    response = post_with_session("/api/v1/meal-planning/operations", operation, cookies)
    assert response.status_code == 200
    assert response.json()["changed_dates"] == ["2026-11-02", "2026-11-09"]
    with meal_database() as db:
        remaining = db.scalars(select(MealAssignment)).all()
        assert len(remaining) == 0

# Comprueba los límites temporales y que se conserva la otra franja.
def test_repeated_delete_preserves_other_dates_and_slot(meal_database):
    cookies = authenticate(meal_database)
    pescado, arroz = seed_labels(meal_database)
    with meal_database() as db:
        for dia, franja in [(26, "lunch"), (2, "lunch"), (9, "lunch"), (16, "lunch"), (23, "lunch"), (16, "dinner")]:
            mes = 10 if dia == 26 else 11
            db.add(MealAssignment(date=date(2026, mes, dia), slot=franja, label_id=arroz.id))
        db.commit()
    payload = {"action": "delete", "start_date": "2026-11-02", "slot": "lunch", "label_id": str(pescado.id), "repeat": {"interval_weeks": 2, "end_date": "2026-11-16"}}
    preview = post_with_session("/api/v1/meal-planning/preview", payload, cookies).json()
    response = post_with_session("/api/v1/meal-planning/operations", {**payload, "confirmed": True, "preview_token": preview["preview_token"]}, cookies)
    assert response.json()["changed_dates"] == ["2026-11-02", "2026-11-16"]
    with meal_database() as db:
        restantes = {(fila.date.isoformat(), fila.slot) for fila in db.scalars(select(MealAssignment))}
    assert restantes == {("2026-10-26", "lunch"), ("2026-11-09", "lunch"), ("2026-11-23", "lunch"), ("2026-11-16", "dinner")}

def test_invalid_operations_reject_bad_dates_interval_slot_and_label(meal_database):
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    base = {
        "action": "assign",
        "start_date": "2026-11-02",
        "slot": "lunch",
        "label_id": str(pescado.id),
        "repeat": None,
    }
    invalid = [
        {**base, "slot": "breakfast"},
        {**base, "label_id": str(uuid4())},
        {**base, "repeat": {"interval_weeks": True, "end_date": "2026-11-16"}},
        {**base, "repeat": {"interval_weeks": 1, "end_date": "2026-11-01"}},
        {**base, "start_date": "not-a-date"},
    ]
    for payload in invalid:
        response = post_with_session(
            "/api/v1/meal-planning/preview", payload, cookies
        )
        assert response.status_code == 422
    with meal_database() as db:
        assert db.query(MealAssignment).count() == 0

def test_failed_repeated_operation_rolls_back_the_entire_batch(meal_database):
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    with meal_database() as db:
        db.execute(
            text(
                """CREATE TRIGGER reject_second_meal_date
                   BEFORE INSERT ON meal_assignments
                   WHEN NEW.date = '2026-11-09'
                   BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END"""
            )
        )
        db.commit()
    payload = {
        "action": "assign",
        "start_date": "2026-11-02",
        "slot": "lunch",
        "label_id": str(pescado.id),
        "repeat": {"interval_weeks": 1, "end_date": "2026-11-09"},
    }

    response = post_with_session("/api/v1/meal-planning/operations", payload, cookies)
    assert response.status_code == 503
    with meal_database() as db:
        assert db.query(MealAssignment).count() == 0

# Verifica que una fecha de envío vencida no deja un aviso pendiente.
def test_recordatorio_vencido_no_se_programa(meal_database, monkeypatch):
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    class Reloj(datetime):
        """Fija el instante de guardado para comprobar el vencimiento."""
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 2, 19, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("app.meal_planning_api.datetime", Reloj)
    respuesta = post_with_session("/api/v1/meal-planning/operations", {"action":"assign", "start_date":"2026-11-02", "slot":"lunch", "label_id":str(pescado.id), "reminder":{"days_before":0,"send_time":"18:00","message":"Sacar pollo"}}, cookies)
    assert respuesta.status_code == 200
    with meal_database() as db:
        assert db.scalar(select(MealAssignment)).reminder_days is None

# Verifica destinatarios activos, contenido y ausencia de reenvío tras un envío correcto.
def test_envio_recordatorio_a_todos_los_usuarios_activos(meal_database, monkeypatch):
    import app.meal_planning_api as api
    from app.models import User
    authenticate(meal_database)
    authenticate(meal_database)
    authenticate(meal_database, active=False)
    pescado, _ = seed_labels(meal_database)
    with meal_database() as db:
        db.add(MealAssignment(date=date(2026, 11, 2), slot="lunch", label_id=pescado.id, reminder_days=0, reminder_time="18:00", reminder_message="Sacar pollo"))
        correos = set(db.scalars(select(User.email).where(User.is_active.is_(True))).all())
        db.commit()
    envios = []
    monkeypatch.setattr(api, "SessionFactory", meal_database)
    monkeypatch.setattr(api, "send_meal_reminder_email", lambda *args: envios.append(args))
    assert api.deliver_due_meal_reminders(datetime(2026, 11, 2, 17, 59, tzinfo=timezone.utc)) == 0
    assert api.deliver_due_meal_reminders(datetime(2026, 11, 2, 18, 0, tzinfo=timezone.utc)) == 1
    assert {e[0] for e in envios} == correos
    assert all(e[1:] == ("Sacar pollo", pescado.name, date(2026, 11, 2)) for e in envios)
    assert api.deliver_due_meal_reminders(datetime(2026, 11, 2, 18, 1, tzinfo=timezone.utc)) == 0
    assert len(envios) == 2

# Comprueba el envío inmediato sin alterar el recordatorio programado.
def test_probar_recordatorio_envia_copia_sin_modificar_programacion(meal_database, monkeypatch):
    import app.meal_planning_api as api
    from app.models import User
    cookies = authenticate(meal_database)
    authenticate(meal_database)
    authenticate(meal_database, active=False)
    pescado, _ = seed_labels(meal_database)
    with meal_database() as db:
        comida = MealAssignment(date=date(2027, 1, 5), slot="lunch", label_id=pescado.id, reminder_days=1, reminder_time="18:00", reminder_message="Sacar pollo")
        db.add(comida)
        db.commit()
        identificador = comida.id
        destinatarios = set(db.scalars(select(User.email).where(User.is_active.is_(True))).all())
    correos = []
    monkeypatch.setattr(api, "send_meal_reminder_email", lambda *args: correos.append(args))
    ruta = f"/api/v1/meal-planning/{identificador}/reminder/test"
    assert api_post(ruta, payload={}).status_code == 401
    assert api_post(ruta, payload={}, cookies=cookies).status_code == 403
    assert post_with_session(ruta, {}, cookies).status_code == 200
    assert {correo[0] for correo in correos} == destinatarios
    assert all(correo[1:] == ("Sacar pollo", pescado.name, date(2027, 1, 5)) for correo in correos)
    with meal_database() as db:
        comida = db.get(MealAssignment, identificador)
        assert comida.reminder_sent_at is None
        assert comida.reminder_days == 1

# Comprueba las respuestas del envío de prueba cuando falta la comida o su aviso.
def test_probar_recordatorio_rechaza_comidas_sin_aviso(meal_database, monkeypatch):
    import app.meal_planning_api as api
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    with meal_database() as db:
        comida = MealAssignment(date=date(2027, 1, 5), slot="lunch", label_id=pescado.id)
        db.add(comida)
        db.commit()
        identificador = comida.id
    envios = []
    monkeypatch.setattr(api, "send_meal_reminder_email", lambda *args: envios.append(args))
    assert post_with_session(f"/api/v1/meal-planning/{uuid4()}/reminder/test", {}, cookies).status_code == 404
    assert post_with_session(f"/api/v1/meal-planning/{identificador}/reminder/test", {}, cookies).status_code == 409
    assert envios == []

# Comprueba que un fallo de correo no impide continuar ni provoca reenvíos.
def test_error_de_recordatorio_se_registra_y_no_se_reintenta(meal_database, monkeypatch, caplog):
    import app.meal_planning_api as api
    authenticate(meal_database)
    authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    with meal_database() as db:
        db.add(MealAssignment(date=date(2026, 11, 2), slot="lunch", label_id=pescado.id, reminder_days=0, reminder_time="18:00", reminder_message="Sacar pollo"))
        db.commit()
    intentos = []
    def enviar(correo, *args):
        """Falla el primer destinatario y registra cada intento."""
        intentos.append(correo)
        if len(intentos) == 1:
            raise OSError("SMTP no disponible")
    monkeypatch.setattr(api, "SessionFactory", meal_database)
    monkeypatch.setattr(api, "send_meal_reminder_email", enviar)
    api.deliver_due_meal_reminders(datetime(2026, 11, 2, 18, 0, tzinfo=timezone.utc))
    api.deliver_due_meal_reminders(datetime(2026, 11, 2, 18, 1, tzinfo=timezone.utc))
    assert len(intentos) == 2
    assert "meal_reminder_delivery_failed" in caplog.text

# Comprueba cada envío semanal y sus destinatarios en la hora de Canarias.
def test_envia_recordatorios_de_cada_comida_repetida(meal_database, monkeypatch):
    import app.meal_planning_api as api
    from app.models import User
    cookies = authenticate(meal_database)
    authenticate(meal_database)
    authenticate(meal_database, active=False)
    pescado, _ = seed_labels(meal_database)
    class Reloj(datetime):
        """Fija el momento anterior a la primera comida de la serie."""
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(api, "datetime", Reloj)
    monkeypatch.setattr(api, "SessionFactory", meal_database)
    envios = []
    monkeypatch.setattr(api, "send_meal_reminder_email", lambda *args: envios.append(args))
    respuesta = post_with_session("/api/v1/meal-planning/operations", {"action":"assign", "start_date":"2026-11-08", "slot":"lunch", "label_id":str(pescado.id), "repeat":{"interval_weeks":1,"end_date":"2026-11-15"}, "reminder":{"days_before":1,"send_time":"18:00","message":"Sacar el pollo"}}, cookies)
    assert respuesta.status_code == 200
    with meal_database() as db:
        correos = set(db.scalars(select(User.email).where(User.is_active.is_(True))).all())
    assert api.deliver_due_meal_reminders(datetime(2026, 11, 7, 17, 59, tzinfo=timezone.utc)) == 0
    assert api.deliver_due_meal_reminders(datetime(2026, 11, 7, 18, 0, tzinfo=timezone.utc)) == 1
    assert {(e[0], e[1], e[2], e[3]) for e in envios} == {(c, "Sacar el pollo", "Pescado", date(2026, 11, 8)) for c in correos}
    assert api.deliver_due_meal_reminders(datetime(2026, 11, 14, 18, 0, tzinfo=timezone.utc)) == 1
    assert {(e[0], e[3]) for e in envios} == {(c, fecha) for c in correos for fecha in (date(2026, 11, 8), date(2026, 11, 15))}
    assert len(envios) == 4

# Comprueba que un aviso vencido no impide los envíos futuros de una serie.
def test_omite_primer_aviso_vencido_y_envia_el_siguiente(meal_database, monkeypatch):
    import app.meal_planning_api as api
    from app.models import User
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    class Reloj(datetime):
        """Sitúa el guardado después del primer aviso y antes del siguiente."""
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 7, 19, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(api, "datetime", Reloj)
    monkeypatch.setattr(api, "SessionFactory", meal_database)
    envios = []
    monkeypatch.setattr(api, "send_meal_reminder_email", lambda *args: envios.append(args))
    respuesta = post_with_session("/api/v1/meal-planning/operations", {"action":"assign", "start_date":"2026-11-08", "slot":"lunch", "label_id":str(pescado.id), "repeat":{"interval_weeks":1,"end_date":"2026-11-15"}, "reminder":{"days_before":1,"send_time":"18:00","message":"Sacar el pollo"}}, cookies)
    assert respuesta.status_code == 200
    with meal_database() as db:
        correos = set(db.scalars(select(User.email).where(User.is_active.is_(True))).all())
    assert api.deliver_due_meal_reminders(datetime(2026, 11, 7, 19, 1, tzinfo=timezone.utc)) == 0
    assert api.deliver_due_meal_reminders(datetime(2026, 11, 14, 18, 0, tzinfo=timezone.utc)) == 1
    assert {(e[0], e[1], e[2], e[3]) for e in envios} == {(c, "Sacar el pollo", "Pescado", date(2026, 11, 15)) for c in correos}

# Comprueba que la consulta entrega la configuración del aviso al editor.
def test_consulta_planificacion_incluye_recordatorio_guardado(meal_database):
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    with meal_database() as db:
        db.add(MealAssignment(date=date(2026, 11, 2), slot="lunch", label_id=pescado.id, reminder_days=2, reminder_time="18:30", reminder_message="Sacar pescado"))
        db.commit()
    respuesta = api_get("/api/v1/meal-planning", params={"start_date": "2026-11-02", "end_date": "2026-11-02"}, cookies=cookies)
    assert respuesta.status_code == 200
    assert respuesta.json()["assignments"][0]["reminder"] == {"days_before": 2, "send_time": "18:30", "message": "Sacar pescado"}

# Comprueba que la edición cambia el aviso y no envía el contenido anterior.
def test_actualiza_aviso_pendiente_con_nueva_comida_mensaje_y_horario(meal_database, monkeypatch):
    import app.meal_planning_api as api
    cookies = authenticate(meal_database)
    pescado, arroz = seed_labels(meal_database)
    with meal_database() as db:
        db.add(MealAssignment(date=date(2099, 11, 8), slot="lunch", label_id=pescado.id, reminder_days=1, reminder_time="12:00", reminder_message="Anterior"))
        db.commit()
    monkeypatch.setattr(api, "SessionFactory", meal_database)
    envios = []
    monkeypatch.setattr(api, "send_meal_reminder_email", lambda *args: envios.append(args))
    operacion = {"action":"assign", "start_date":"2099-11-08", "slot":"lunch", "label_id":str(arroz.id), "reminder":{"days_before":1,"send_time":"18:00","message":"Nuevo"}}
    previa = post_with_session("/api/v1/meal-planning/preview", operacion, cookies).json()
    assert post_with_session("/api/v1/meal-planning/operations", {**operacion, "confirmed": True, "preview_token": previa["preview_token"]}, cookies).status_code == 200
    assert api.deliver_due_meal_reminders(datetime(2099, 11, 7, 12, 0, tzinfo=timezone.utc)) == 0
    assert api.deliver_due_meal_reminders(datetime(2099, 11, 7, 18, 0, tzinfo=timezone.utc)) == 1
    assert len(envios) == 1
    assert envios[0][1:] == ("Nuevo", "Arroz", date(2099, 11, 8))

# Comprueba que desactivar un aviso impide su envío posterior.
def test_no_envia_aviso_al_desactivar_recordatorio(meal_database, monkeypatch):
    import app.meal_planning_api as api
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    with meal_database() as db:
        db.add(MealAssignment(date=date(2099, 11, 8), slot="lunch", label_id=pescado.id, reminder_days=1, reminder_time="18:00", reminder_message="Sacar"))
        db.commit()
    monkeypatch.setattr(api, "SessionFactory", meal_database)
    envios = []
    monkeypatch.setattr(api, "send_meal_reminder_email", lambda *args: envios.append(args))
    operacion = {"action":"assign", "start_date":"2099-11-08", "slot":"lunch", "label_id":str(pescado.id)}
    assert post_with_session("/api/v1/meal-planning/operations", operacion, cookies).status_code == 200
    assert api.deliver_due_meal_reminders(datetime(2099, 11, 7, 18, 0, tzinfo=timezone.utc)) == 0
    assert not envios

# Comprueba que borrar una comida cancela su recordatorio pendiente.
def test_no_envia_aviso_al_borrar_comida(meal_database, monkeypatch):
    import app.meal_planning_api as api
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    with meal_database() as db:
        db.add(MealAssignment(date=date(2099, 11, 8), slot="lunch", label_id=pescado.id, reminder_days=1, reminder_time="18:00", reminder_message="Sacar"))
        db.commit()
    monkeypatch.setattr(api, "SessionFactory", meal_database)
    envios = []
    monkeypatch.setattr(api, "send_meal_reminder_email", lambda *args: envios.append(args))
    operacion = {"action":"delete", "start_date":"2099-11-08", "slot":"lunch", "label_id":str(pescado.id)}
    previa = post_with_session("/api/v1/meal-planning/preview", operacion, cookies).json()
    assert post_with_session("/api/v1/meal-planning/operations", {**operacion, "confirmed": True, "preview_token": previa["preview_token"]}, cookies).status_code == 200
    assert api.deliver_due_meal_reminders(datetime(2099, 11, 7, 18, 0, tzinfo=timezone.utc)) == 0
    assert not envios

# Comprueba que editar un recordatorio ya enviado no lo vuelve a enviar.
def test_no_reenvia_aviso_ya_enviado_al_editarlo(meal_database, monkeypatch):
    import app.meal_planning_api as api
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    with meal_database() as db:
        db.add(MealAssignment(date=date(2099, 11, 8), slot="lunch", label_id=pescado.id, reminder_days=1, reminder_time="12:00", reminder_message="Original"))
        db.commit()
    monkeypatch.setattr(api, "SessionFactory", meal_database)
    envios = []
    monkeypatch.setattr(api, "send_meal_reminder_email", lambda *args: envios.append(args))
    assert api.deliver_due_meal_reminders(datetime(2099, 11, 7, 12, 0, tzinfo=timezone.utc)) == 1
    operacion = {"action":"assign", "start_date":"2099-11-08", "slot":"lunch", "label_id":str(pescado.id), "reminder":{"days_before":1,"send_time":"18:00","message":"Modificado"}}
    assert post_with_session("/api/v1/meal-planning/operations", operacion, cookies).status_code == 200
    assert api.deliver_due_meal_reminders(datetime(2099, 11, 7, 18, 0, tzinfo=timezone.utc)) == 0
    assert len(envios) == 1
