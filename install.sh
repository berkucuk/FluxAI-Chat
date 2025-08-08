#!/usr/bin/env bash
set -euo pipefail

# Kurulum dizinleri ve dosya adları
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Flux AI Chat"
INSTALL_DIR="/usr/share/flux-ai-chat"
VENV_DIR="$INSTALL_DIR/python-env"
DESKTOP_FILE_SOURCE="$SCRIPT_DIR/Flux-AI.desktop"
DESKTOP_FILE_TARGET="$HOME/.local/share/applications/Flux-AI.desktop"

echo "[1/6] Bağımlılıklar kontrol ediliyor..."
if command -v pacman >/dev/null 2>&1; then
  sudo pacman -S --needed --noconfirm python python-virtualenv libpng
elif command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y python3 python3-venv python3-pip libpng-dev
else
  echo "Desteklenmeyen paket yöneticisi. Lütfen python3 ve python3-venv kurulu olduğundan emin olun." >&2
fi

echo "[2/6] Uygulama dosyaları kopyalanıyor..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r "$SCRIPT_DIR/icons" "$INSTALL_DIR"  # icon.png burada
sudo cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR"
sudo cp "$SCRIPT_DIR/flux_ai.py" "$INSTALL_DIR"

echo "[3/6] Sanal ortam oluşturuluyor..."
if [ ! -d "$VENV_DIR" ]; then
  sudo python3 -m venv "$VENV_DIR"
fi
sudo "$VENV_DIR/bin/pip" install --upgrade pip
sudo "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

echo "[4/6] Desktop kısayolu hazırlanıyor..."
mkdir -p "$(dirname "$DESKTOP_FILE_TARGET")"

# Desktop dosyasını doğru yollarla kopyala/düzenle
TMP_DESKTOP="/tmp/Flux-AI.desktop"
cp "$DESKTOP_FILE_SOURCE" "$TMP_DESKTOP"
sed -i "s|^Exec=.*$|Exec=$VENV_DIR/bin/python3 $INSTALL_DIR/flux_ai.py|" "$TMP_DESKTOP"
sed -i "s|^Icon=.*$|Icon=$INSTALL_DIR/icons/icon.png|" "$TMP_DESKTOP"
sed -i "s|^Name=.*$|Name=$APP_NAME|" "$TMP_DESKTOP"

install -m 644 "$TMP_DESKTOP" "$DESKTOP_FILE_TARGET"

echo "[5/6] Desktop veritabanı güncelleniyor..."
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" || true
fi

echo "[6/6] Kurulum tamamlandı. Başlatılıyor..."
echo "Uygulama: $APP_NAME"
echo "Komut: $VENV_DIR/bin/python3 $INSTALL_DIR/flux_ai.py"
echo "Kısayol: $DESKTOP_FILE_TARGET"
echo "İpucu: Menüden '$APP_NAME' olarak aratabilirsiniz."
