#!/usr/bin/env bash
set -Eeuo pipefail

# Instal·la i activa el servei d'usuari d'EduTicTac Link (instal·lació amb pipx).

binary="${EDUTICTAC_LINK_BIN:-$HOME/.local/bin/edutictac-link}"
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source_unit="$repo_root/packaging/systemd/edutictac-link.service"
unit_dir="$HOME/.config/systemd/user"

if ! command -v systemctl >/dev/null 2>&1; then
  printf "systemctl no està disponible en este sistema.\n" >&2
  exit 1
fi

if [[ ! -x "$binary" ]]; then
  printf "No s'ha trobat el binari: %s\n" "$binary" >&2
  printf "Instal·la'l primer amb: pipx install .\n" >&2
  exit 1
fi

install -d -m 0755 "$unit_dir"
install -m 0644 "$source_unit" "$unit_dir/edutictac-link.service"

systemctl --user daemon-reload
systemctl --user enable --now edutictac-link.service
systemctl --user status --no-pager edutictac-link.service || true

printf "Servei d'usuari activat. Per a vore'l: systemctl --user status edutictac-link\n"
