# Gemeinsame Historie der Retro-Szenarien: sechs Commits, zweimal derselbe Fehler (fehlendes
# Timeout an urlopen), jeder Feature-Commit mit Test. Wird von setup.sh per "." geladen.
init_repo
slickfab_config
mkdir -p svc tests .slickrails
: > svc/__init__.py
: > tests/__init__.py
printf '# Review-Lehren\n\n- (noch keine)\n' > .slickrails/review-learnings.md
cat > svc/weather.py <<'PY'
import urllib.request


def fetch(url):
    return urllib.request.urlopen(url).read()
PY
cat > tests/test_weather.py <<'PY'
import unittest
from svc import weather


class WeatherTest(unittest.TestCase):
    def test_fetch_liest(self):
        class R:
            def read(self):
                return b"ok"
        weather.urllib.request.urlopen = lambda url, timeout=None: R()
        self.assertEqual(weather.fetch("x"), b"ok")
PY
commit "Wetterdienst abfragen (#1)"
sed -i.bak 's/urlopen(url)/urlopen(url, timeout=10)/' svc/weather.py && rm svc/weather.py.bak
commit "fix: Wetterabfrage hing ohne Timeout (#2)"
cat > svc/rates.py <<'PY'
import urllib.request


def fetch_rates(url):
    return urllib.request.urlopen(url).read()
PY
cat > tests/test_rates.py <<'PY'
import unittest
from svc import rates


class RatesTest(unittest.TestCase):
    def test_fetch(self):
        class R:
            def read(self):
                return b"1.1"
        rates.urllib.request.urlopen = lambda url, timeout=None: R()
        self.assertEqual(rates.fetch_rates("x"), b"1.1")
PY
commit "Wechselkurse abfragen (#3)"
sed -i.bak 's/urlopen(url)/urlopen(url, timeout=10)/' svc/rates.py && rm svc/rates.py.bak
commit "fix: Kursabfrage blockierte den Worker, Timeout fehlte (#4)"
cat > svc/fmt.py <<'PY'
def euro(cents):
    return "%d,%02d €" % divmod(cents, 100)
PY
cat > tests/test_fmt.py <<'PY'
import unittest
from svc.fmt import euro


class EuroTest(unittest.TestCase):
    def test_euro(self):
        self.assertEqual(euro(1999), "19,99 €")
PY
commit "Euro formatieren (#5)"
cat > svc/fmt.py <<'PY'
def euro(cents):
    """Cent als Euro-Text."""
    return "%d,%02d €" % divmod(cents, 100)
PY
commit "docs: Docstring für euro (#6)"
