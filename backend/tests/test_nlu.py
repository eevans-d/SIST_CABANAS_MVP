def test_nlu_intents_detection():  # type: ignore
    from app.services import nlu
    cases = [
        ("¿Hay disponibilidad para el 15?", "disponibilidad"),
        ("Cuál es el precio por noche?", "precio"),
        ("Quiero reservar del 10 al 12", "reservar"),
        ("Tienen wifi y qué servicios incluyen?", "servicios"),
    ]
    for text, intent in cases:
        result = nlu.analyze(text)
        assert intent in result["intents"], result

def test_nlu_dates_and_weekend():  # type: ignore
    from app.services import nlu
    r1 = nlu.analyze("Necesito saber precio para 15/01/2026")
    assert any(d.startswith("2026-01-15") for d in r1.get("dates", [])), r1
    r2 = nlu.analyze("Quiero el fin de semana próximo")
    assert len(r2.get("dates", [])) == 2, r2

def test_nlu_unknown_intent():  # type: ignore
    from app.services import nlu
    r = nlu.analyze("Hola")
    assert r["intents"] == ["desconocido"], r

def test_nlu_extract_guests_and_range():  # type: ignore
    from app.services import nlu
    r = nlu.analyze("Hay libre 25/12 al 28/12 para 4 personas?")
    # Debe detectar 2 fechas y 4 huéspedes
    assert len(r.get("dates", [])) >= 2, r
    assert r.get("guests") == 4, r