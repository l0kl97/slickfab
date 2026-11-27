#!/usr/bin/env python3
"""context-guard: warnt einen Studio-Agent selbst, wenn sein Kontext voll wird.

PostToolBatch-Hook. Liest den Füllstand aus der Statuszeilen-Datei des
Herdr-Terminals ($HOME/.config/studio-board/sessions/<HC_TERMINAL_ID>.json) und
gibt ab 65 % bzw. 80 % je einmal einen Hinweis als zusätzlichen Kontext aus.
Er warnt nur in Rollen-Terminals (Herdr-Label studio.role); sonst bleibt er still.

Er blockiert nie: Jeder Fehler endet still mit Exit 0 und ohne Ausgabe.
Nur Standardbibliothek, läuft mit Python 3.9.
"""
import json
import os
import re
import subprocess
import sys
import time

# Herdr-Terminal-Adressen (t9z) und Session-IDs (UUID); alles andere wird nie zu einem Dateipfad.
TERMINAL_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")
SESSION_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")

# Die Statuszeile schreibt nach jeder Antwort des Modells. Älter heißt: Die Session
# hängt oder die Datei ist von früher. Ein einzelner langer Werkzeugaufruf bleibt darunter.
STALE_SECONDS = 30 * 60
MAX_STATUS_BYTES = 256 * 1024

WARN_WRAP_UP = 65
WARN_HANDOFF = 80

TEXT = {
    WARN_WRAP_UP: (
        "slickfab context-guard: Dein Kontext ist zu {p} % voll (Schwelle 65 %). "
        "Schließ die laufende Teilaufgabe ab und fang nichts Neues an. "
        "Ab 80 % schreibst du die Übergabe."),
    WARN_HANDOFF: (
        "slickfab context-guard: Dein Kontext ist zu {p} % voll (Schwelle 80 %). "
        "Hör jetzt auf zu bauen und schreib die Übergabe mit dem Schritt `handoff` "
        "(/slickfab:handoff <Ticket>). Danach endest du mit dem Marker `NEEDS_CONTEXT` "
        "als letzter Zeile: `SLICKFAB-STATUS: NEEDS_CONTEXT`. Eine frische Session macht weiter."),
}


def used_percentage(terminal, session, now):
    """Füllstand in Prozent aus der Statuszeilen-Datei, oder None, wenn sie fehlt,
    kaputt ist, zu einer anderen Session gehört oder zu alt ist."""
    path = os.path.join(os.path.expanduser("~"), ".config", "studio-board", "sessions",
                        terminal + ".json")
    try:
        with open(path, "rb") as f:
            age = now - os.fstat(f.fileno()).st_mtime
            status = json.loads(f.read(MAX_STATUS_BYTES).decode("utf-8"))
    except (OSError, ValueError):
        return None
    if age > STALE_SECONDS or not isinstance(status, dict) or status.get("session_id") != session:
        return None
    window = status.get("context_window")
    p = window.get("used_percentage") if isinstance(window, dict) else None
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not 0 <= p <= 100:
        return None  # NaN fällt hier auch heraus
    return p


def role_of(terminal):
    """Rollen-Terminal = Herdr-Label studio.role ist ein nicht leerer Text.
    Gefragt wird die Herdr-CLI über ihren lokalen Socket, kein Netz.
    True/False ist eine Antwort von hc; None heißt: hc gab keine (Fehler, Müll)."""
    r = subprocess.run(["hc", "get", "--json", terminal], capture_output=True, text=True,
                       timeout=2, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        return None
    info = json.loads(r.stdout)
    labels = info.get("labels") if isinstance(info, dict) else None
    if not isinstance(labels, dict):
        return None
    role = labels.get("studio.role")
    return isinstance(role, str) and role.strip() != ""


def state_folder(env):
    base = env.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(base, "slickfab", "context-guard")


def noted(env, session, what):
    return os.path.exists(os.path.join(state_folder(env), "%s.%s" % (session, what)))


def note_first(env, session, what):
    """Legt je Sitzung eine leere Merkdatei an. Atomar über O_EXCL: Nur der erste
    Aufruf legt sie an und bekommt True. Wer nicht schreiben kann, wirft (und schweigt damit)."""
    folder = state_folder(env)
    os.makedirs(folder, mode=0o700, exist_ok=True)
    try:
        fd = os.open(os.path.join(folder, "%s.%s" % (session, what)),
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    os.close(fd)
    return True


def warning(event, env):
    if not isinstance(event, dict) or "agent_id" in event:
        return None
    terminal = env.get("HC_TERMINAL_ID", "")
    session = event.get("session_id")
    if not TERMINAL_ID.fullmatch(terminal) or not isinstance(session, str) \
            or not SESSION_ID.fullmatch(session):
        return None
    p = used_percentage(terminal, session, time.time())
    if p is None:
        return None
    threshold = WARN_HANDOFF if p >= WARN_HANDOFF else WARN_WRAP_UP if p >= WARN_WRAP_UP else None
    if threshold is None:
        return None
    # Billige Prüfungen vor hc: schon gewarnt (nach 80 % gilt auch 65 % als erledigt)
    # oder hc hat in dieser Session schon „keine Rolle“ gesagt.
    if noted(env, session, WARN_HANDOFF) or noted(env, session, threshold) \
            or noted(env, session, "norole"):
        return None
    role = role_of(terminal)
    if role is False:
        note_first(env, session, "norole")
    if not role or not note_first(env, session, threshold):
        return None
    return TEXT[threshold].format(p=round(p))


def main():
    # Nie blockieren, nie stören: Jeder Fehler endet still (Exit 0, keine Ausgabe).
    try:
        text = warning(json.load(sys.stdin), os.environ)
    except Exception:
        return 0
    if text:
        json.dump({"hookSpecificOutput": {"hookEventName": "PostToolBatch",
                                          "additionalContext": text}},
                  sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
