# セットアップ手順

この手順は Raspberry Pi Zero WH と Raspberry Pi OS を前提とする。コマンドは Raspberry Pi 上で実行する。

## 1. リポジトリを配置する

```bash
git clone <REPOSITORY_URL>
cd workshop
```

既に配置済みの場合は、リポジトリのルートへ移動する。

## 2. OS 側の依存関係を用意する

Python 3、venv、pigpio / pigpiod と ustreamer をインストールする。ustreamer の導入方法は利用している Raspberry Pi OS に合わせ、インストール後に次のコマンドで確認する。

```bash
python3 --version
pigpiod -v
ustreamer --version
```

`python3 -m venv` が使えない場合は、OS のパッケージマネージャーで `python3-venv` を追加する。

## 3. Python 環境を作る

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

以後、Python 側を起動するターミナルでは先に `source .venv/bin/activate` を実行する。

## 4. 配線と設定値を確認する

[配線と設定値](hardware.md) を確認し、実装済みの左右モーターは `src/config.py` の設定に合わせて配線する。未実装のセンサーやブザーは、実装時に実機の配線に合わせて BCM GPIO 番号を決める。GPIO 番号は物理 PIN 番号ではなく BCM 番号として扱う。

配線を変更するときは Raspberry Pi とリレー回路、モーター用電源を切る。モーター用電源を Raspberry Pi の 5 V ピンから直接取らない。

## 5. カメラを確認する

USB カメラを接続し、デバイスを確認する。

```bash
ls -l /dev/video*
```

想定するカメラが `/dev/video0` 以外の場合は、ustreamer の `--device` を実際のパスへ変更する。

## 6. 起動確認をする

[運用手順](operations.md) に従い、pigpiod、Python WebSocket サーバー、ustreamer の順で起動する。スマートフォンから Web UI を開き、映像表示と操作通信を確認する。
