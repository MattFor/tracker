#!/usr/bin/env bash
set -euo pipefail

BIN_DIR="${HOME}/.local/bin"
MAN_DIR="${HOME}/.local/share/man/man1"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SHORT_BIN="${BIN_DIR}/t"
TRACKER_BIN="${BIN_DIR}/tracker"
MAN_PAGE="${MAN_DIR}/tracker.1"

print_help() {
    cat <<EOF
Tracker installer

Usage:
    ./install.sh [options]

Options:
    --daemon, daemon, -d, d
        Install Tracker and enable daemon autostart.

    --uninstall, uninstall, -u, u
        Remove the launchers, the man page and the autostart entry.

    --help, help, -h, h
        Show this help message.
EOF
}

INSTALL_DAEMON=false
UNINSTALL=false

for arg in "$@"; do
    case "${arg}" in
        --daemon|-d|daemon|d)
            INSTALL_DAEMON=true
            ;;
        --uninstall|-u|uninstall|u)
            UNINSTALL=true
            ;;
        --help|-h|help|h)
            print_help
            exit 0
            ;;
        *)
            echo "[ERROR] unknown option: ${arg}"
            echo
            print_help
            exit 1
            ;;
    esac
done

AUTOSTART_DIR="${HOME}/.config/autostart"
AUTOSTART_FILE="${AUTOSTART_DIR}/tracker-daemon.desktop"

if "${UNINSTALL}"; then
    "${TRACKER_BIN}" daemon stop >/dev/null 2>&1 || true

    rm -f "${TRACKER_BIN}" "${SHORT_BIN}"
    rm -f "${MAN_PAGE}.gz" "${MAN_DIR}/t.1.gz"
    rm -f "${AUTOSTART_FILE}"

    echo "Tracker has been uninstalled."
    echo "Settings and database in ${PROJECT_DIR} were left alone."
    exit 0
fi

mkdir -p "${BIN_DIR}"

PYTHON_BIN="${PROJECT_DIR}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
    PYTHON_BIN="$(command -v python3 || true)"
fi

if [[ -z "${PYTHON_BIN}" ]]; then
    echo "[ERROR] python3 was not found."
    exit 1
fi

if ! "${PYTHON_BIN}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "[ERROR] Python 3.11 or newer is required (found $("${PYTHON_BIN}" -V))."
    exit 1
fi

cat > "${TRACKER_BIN}" <<EOF
#!/usr/bin/env bash

set -e

cd "${PROJECT_DIR}"
exec "${PYTHON_BIN}" -m tracker "\$@"
EOF

chmod +x "${TRACKER_BIN}"
ln -sfn "${TRACKER_BIN}" "${SHORT_BIN}"

if [[ ! -f "${PROJECT_DIR}/man/tracker.1" ]]; then
    echo "[ERROR] ${PROJECT_DIR}/man/tracker.1 was not found."
    exit 1
fi

mkdir -p "${MAN_DIR}"

cp "${PROJECT_DIR}/man/tracker.1" "${MAN_PAGE}"
gzip -f "${MAN_PAGE}"

ln -sfn "tracker.1.gz" "${MAN_DIR}/t.1.gz"

if "${INSTALL_DAEMON}"; then
    mkdir -p "${AUTOSTART_DIR}"

    cat > "${AUTOSTART_FILE}" <<EOF
[Desktop Entry]
Type=Application
Name=Tracker Daemon
Comment=Track your projects in the background
Exec=${TRACKER_BIN} daemon
Terminal=false
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
EOF

    echo
    echo "Daemon autostart has been installed to [${AUTOSTART_FILE}]"
fi

case ":${PATH}:" in
    *:"${BIN_DIR}":*)
        ;;
    *)
        echo
        echo "[WARNING] ${BIN_DIR} not found in PATH."
        echo
        echo "Add this to your shell configuration:"
        # shellcheck disable=SC2016
        echo 'export PATH="$HOME/.local/bin:$PATH"'
        echo
        ;;
esac

echo
echo "Tracker has been installed successfully. To use type t / tracker."
echo "-  t [${SHORT_BIN}]"
echo "-  tracker [${TRACKER_BIN}]"
echo "-  man t [${MAN_DIR}/t.1.gz]"
echo "-  man tracker [${MAN_PAGE}.gz]"

if "${INSTALL_DAEMON}"; then
    echo "-  daemon autostarts from here: [${AUTOSTART_FILE}]"

    "${TRACKER_BIN}" daemon start
fi

echo
echo "If ~/.local/bin is in PATH, you can use them immediately."
