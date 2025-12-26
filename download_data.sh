#!/bin/bash

DATA_DIR="data"

if [ ! -d "$DATA_DIR" ]; then
    mkdir -p "$DATA_DIR"
fi

echo "📥 Скачиваем исходные данные..."

echo "🗂️ RAW text"
gdown "https://drive.google.com/file/d/18z25ebWwHVF4SqXmpyXgYclYedlkMu18/view?usp=sharing" -O "$DATA_DIR/monte-cristo.txt" --fuzzy

echo "📄 nodes.json"
gdown "https://drive.google.com/file/d/1wEV0DwVmEE87YP6pByyQ1cKbB5a42vBG/view?usp=sharing" -O "$DATA_DIR/nodes.json" --fuzzy

echo "📄 edges.json"
gdown "https://drive.google.com/file/d/1Ne1WMZ-OVGD3SkNQ1sN9uT-gN4x5Z1sX/view?usp=sharing" -O "$DATA_DIR/edges.json" --fuzzy

echo "📄 names_map.json"
gdown "https://drive.google.com/file/d/1UEqlZDoC6Yc6gMULb8WIrUa1MvT2PQ4-/view?usp=sharing" -O "$DATA_DIR/names_map.json" --fuzzy


echo "✅ Данные готовы"