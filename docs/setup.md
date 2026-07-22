# セットアップ手順

この手順は Raspberry Pi Zero WH と Raspberry Pi OS を前提とする。コマンドは Raspberry Pi 上で実行する。

## 1. 依存関係のインストール

- Git
- Python 3
- venv
- pigpio / pigpiod
- µStreamer

Git, Python, venv, pigpio / pigpiod は APT でインストールできる。

```bash
sudo apt update
sudo apt install -y \
  git \
  python3 \
  python3-venv \
  pigpio
```

µStreamerは [公式リポジトリ](https://github.com/pikvm/ustreamer) の手順に従ってインストールする。準備後、次のコマンドがすべて成功することを確認する。

```bash
git --version
python3 --version
python3 -m venv --help >/dev/null
pigpiod -v
systemctl cat pigpiod.service >/dev/null
ustreamer --version
```

失敗する項目がある場合は `./scripts/setup` へ進まず、[トラブルシューティング](troubleshooting.md#setupが失敗する)を参照する。

## 2. リポジトリを配置する

```bash
git clone <REPOSITORY_URL>
cd workshop
```

## 3. 配線と設定値を確認する

[配線と設定値](hardware.md) を確認し、左右モーター、前方左右2台の HC-SR04、圧電ブザーを `src/config.py` の設定に合わせて配線する。GPIO 番号は物理 PIN 番号ではなく BCM 番号として扱う。

配線を変更するときは Raspberry Pi とリレー回路、モーター用電源を切る。モーター用電源を Raspberry Pi の 5 V ピンから直接取らない。

HC-SR04 の Echo は 5 V のため、2台それぞれに分圧回路またはレベル変換を用意し、3.3 V にしてから GPIO へ接続する。

## 4. カメラを確認する

USBカメラを接続し、デバイスを確認する。

```bash
ls -l /dev/video0
```

このプロジェクトの systemd unitは `/dev/video0` を使用する。カメラが別の番号で認識される場合は、他のビデオデバイスを外してから再接続し、`/dev/video0` になることを確認する。

## 5. Python環境と自動起動をセットアップする

`setup` の最後にサービスが起動する。車体を浮かせるか、モーター用電源を切った状態で実行する。

```bash
./scripts/setup
```

このスクリプトは次の処理を行う。

- `.venv` の作成と Python 依存パッケージのインストール
- Raspberry Pi 上での systemd unit の生成とインストール
- `pigpiod.service` と `workshop.target` の自動起動設定
- pigpiod、Python 操作サーバー、 µStreamer の起動

Raspberry Pi 以外では Python 環境だけを作り、 systemd は変更しない。明示的に Python 環境だけを更新する場合は `./scripts/setup --no-services` を使う。

## 6. 起動を確認する

```bash
./scripts/status
```

pigpiod、Python操作サーバー、µStreamerが `active (running)` であることを確認する。続いて [運用手順](operations.md#スマートフォンからアクセスする) に従い、スマートフォンから映像表示と操作通信を確認する。

## 7. 再起動後の systemd 自動起動を確認する

```bash
sudo reboot
```

再接続後に `./scripts/status` を実行する。手動で `./scripts/start` を実行しなくても、すべてのサービスが起動していることを確認する。
