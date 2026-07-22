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

## 3. 配線と設定値を確認する

[配線と設定値](hardware.md) を確認し、左右モーター、前方左右2台の HC-SR04、圧電ブザーを `src/config.py` の設定に合わせて配線する。GPIO 番号は物理 PIN 番号ではなく BCM 番号として扱う。

配線を変更するときは Raspberry Pi とリレー回路、モーター用電源を切る。モーター用電源を Raspberry Pi の 5 V ピンから直接取らない。

HC-SR04 の Echo は 5 V のため、2台それぞれに分圧回路またはレベル変換を用意し、3.3 V にしてから GPIO へ接続する。

## 4. カメラを確認する

USB カメラを接続し、デバイスを確認する。

```bash
ls -l /dev/video*
```

想定するカメラが `/dev/video0` 以外の場合は、ustreamer の `--device` を実際のパスへ変更する。

## 5. セットアップと自動起動設定を行う

車体を浮かせるかモーター用電源を切った状態で実行する。

```bash
./scripts/setup
```

このスクリプトは次の処理を行う。

- `.venv` の作成と Python 依存パッケージのインストール
- Raspberry Pi 上での systemd unit のインストール
- `pigpiod.service` と `workshop.target` の自動起動設定
- pigpiod、Python操作サーバー、ustreamerの起動

スクリプト全体を `sudo` で実行しない。systemd の設定が必要な処理だけ、スクリプト内から `sudo` を呼び出す。

Raspberry Pi 以外では Python 環境だけを作り、systemd は変更しない。明示的に Python 環境だけを更新する場合は `./scripts/setup --no-services` を使う。

## 6. 起動確認をする

状態を確認する。

```bash
./scripts/status
```

pigpiod、Python操作サーバー、ustreamerが `active (running)` であることを確認する。続いてスマートフォンから Web UI を開き、映像表示と操作通信を確認する。詳しい確認方法は [運用手順](operations.md) を参照する。

## 7. 再起動後の自動起動を確認する

```bash
sudo reboot
```

再接続後に `./scripts/status` を実行し、すべてのサービスが自動的に起動していることを確認する。
