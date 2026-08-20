#!/usr/bin/env bash
set -euo pipefail

BIN_DIR="${HOME}/.local/bin"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SHORT_BIN="${BIN_DIR}/t"
TRACKER_BIN="${BIN_DIR}/tracker"

print_help() {
    cat <<EOF
Tracker installer

Usage:
    ./install.sh [options]

Options:
    --daemon, daemon, -d, d
        Install Tracker and enable daemon autostart.

    --help, help, -h, h
        Show this help message.
EOF
}

INSTALL_DAEMON=false

for arg in "$@"; do
    case "${arg}" in
        --daemon|-d|daemon|d)
            # shellcheck disable=SC2034
            INSTALL_DAEMON=true
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

mkdir -p "${BIN_DIR}"

# Where is python
PYTHON_BIN="${PROJECT_DIR}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
    PYTHON_BIN="$(command -v python3 || true)"
fi

if [[ -z "${PYTHON_BIN}" ]]; then
    echo "[ERROR] python3 was not found."
    exit 1
fi

cat > "${TRACKER_BIN}" <<EOF
#!/usr/bin/env bash

set -e

cd "${PROJECT_DIR}"
exec "${PYTHON_BIN}" "${PROJECT_DIR}/main.py" "\$@"
EOF

# Do links + perms
chmod +x "${TRACKER_BIN}"
ln -sfn "${TRACKER_BIN}" "${SHORT_BIN}"

if "${INSTALL_DAEMON}"; then
    AUTOSTART_DIR="${HOME}/.config/autostart"
    AUTOSTART_FILE="${AUTOSTART_DIR}/tracker-daemon.desktop"

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

if "${INSTALL_DAEMON}"; then
    echo "-  daemon autostarts from here: [${AUTOSTART_FILE}]"
fi

echo
echo "If ~/.local/bin in PATH, you can use them immediately."
