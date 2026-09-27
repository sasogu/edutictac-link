#!/usr/bin/env bash
set -Eeuo pipefail

# Construeix un paquet .deb d'EduTicTac Link en un directori temporal,
# per no embrutar el repositori amb fitxers de dpkg-buildpackage.
#
# Requisits de construcció a Debian: debhelper, dh-python,
# pybuild-plugin-pyproject, python3-all, python3-setuptools.

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

src="$work/src"
mkdir -p "$src"

rsync -a \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.egg-info' \
  --exclude 'build' \
  --exclude 'dist' \
  --exclude '/debian' \
  "$repo_root"/ "$src"/

cp -a "$repo_root/packaging/debian" "$src/debian"
chmod +x "$src/debian/rules"

# El changelog ha de tindre la mateixa versió que pyproject.toml.
version="$(python3 -c "import tomllib,sys; print(tomllib.load(open('$src/pyproject.toml','rb'))['project']['version'])")"
changelog_version="$(dpkg-parsechangelog -l "$src/debian/changelog" -SVersion)"
if [[ "$version" != "$changelog_version" ]]; then
  printf "Avís: pyproject.toml (%s) i changelog (%s) tenen versions distintes.\n" \
    "$version" "$changelog_version" >&2
fi

( cd "$src" && dpkg-buildpackage -us -uc -b )

mkdir -p "$repo_root/dist"
mv "$work"/edutictac-link_*.deb "$repo_root/dist/"
printf "\nPaquet construït:\n"
ls -l "$repo_root/dist"
