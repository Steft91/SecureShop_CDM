"""R11: stego_app solo lee e inserta análisis; los registros no se editan ni se borran."""

from conftest import APP_URL

from shared import testing


def test_r11_privilegios_stego(db):
    testing.assert_least_privilege(APP_URL, "analyses")
    rows = testing.sql(
        APP_URL,
        "SELECT has_table_privilege('analyses', 'INSERT') AS ins, "
        "has_table_privilege('analyses', 'UPDATE') AS upd, "
        "has_table_privilege('analyses', 'DELETE') AS del",
    )
    assert rows == [{"ins": True, "upd": False, "del": False}]
