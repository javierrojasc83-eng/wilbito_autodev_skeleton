import unittest
from wilbito.executor.loop import ExecutorLoop


class TestLoopParser(unittest.TestCase):
    def setUp(self):
        # Creamos una instancia; no toca la DB para estas pruebas.
        self.loop = ExecutorLoop()

    def _ok(self, text, expected):
        got = self.loop._extract_first_json_obj(text)
        self.assertEqual(got, expected)

    # -----------------------------
    # Casos OK
    # -----------------------------
    def test_puro_json(self):
        self._ok('{"a":1,"b":"x"}', {"a": 1, "b": "x"})

    def test_json_con_logs_antes(self):
        text = """Some log...
more noise
{"ok": true, "items": [1,2,3]}
"""
        self._ok(text, {"ok": True, "items": [1, 2, 3]})

    def test_json_con_logs_despues(self):
        text = """{"msg": "hola", "n": 7}
--- end ---
otras cosas que no son json
"""
        self._ok(text, {"msg": "hola", "n": 7})

    def test_json_con_logs_antes_y_despues(self):
        text = """WARN: plugin sympy falló
{ "lint": {"ok": true}, "tests": {"passed": 2}}
==== FIN ====
"""
        self._ok(text, {"lint": {"ok": True}, "tests": {"passed": 2}})

    def test_multiples_jsons_toma_el_primero(self):
        text = """pre
{"uno": 1}
log intermedio
{"dos": 2}
post
"""
        self._ok(text, {"uno": 1})

    def test_bom_y_crlf(self):
        text = "\ufeff\r\nINFO\n{ \"x\": 10, \"y\": [\"a\", \"b\"] }\r\nDONE\r\n"
        self._ok(text, {"x": 10, "y": ["a", "b"]})

    def test_anidado_balanceado(self):
        # Verifica que el balanceo de llaves funcione con objetos anidados.
        text = """
INFO
{
  "outer": {
    "inner": {"a": 1, "b": {"c": 2}}
  }
}
LOG
"""
        self._ok(text, {"outer": {"inner": {"a": 1, "b": {"c": 2}}}})

    # -----------------------------
    # Casos que DEBEN fallar
    # -----------------------------
    def test_sin_json(self):
        text = "todo logs y nada de JSON { sin cerrar"
        with self.assertRaises(ValueError):
            self.loop._extract_first_json_obj(text)

    def test_json_malformado(self):
        text = "ruido\n{mal: json, sin: comillas}\nfin"
        with self.assertRaises(ValueError):
            self.loop._extract_first_json_obj(text)


if __name__ == "__main__":
    unittest.main()
