# workshop

Raspberry Pi Zero WH を載せたキャタピラ式ラジコンを、同じ Wi-Fi に接続したスマートフォンから操作するためのプロジェクトです。カメラ映像と Web UI は ustreamer、操作命令は Python の WebSocket サーバー、モーター制御は pigpio / pigpiod を使います。

## 現在の実装範囲

- ustreamer で配信するスマートフォン向け Web UI
- ジョイスティック操作から左右モーターの PWM 値への変換
- WebSocket による操作命令の送信と受信
- pigpio 経由の左右モーター制御
- 通信が 150 ms 途絶えた場合と切断時のモーター停止
- HC-SR04 による距離計測
- 障害物検知中の前進抑止と自動停止
- 障害物検知中の圧電ブザー警告

障害物を検知した場合は並進の前進成分だけを除去するため、後退とその場旋回は引き続き操作できます。

## クイックスタート

最初に [セットアップ手順](docs/setup.md) を完了してください。Raspberry Pi 上で、リポジトリのルートから次の 3 プロセスを起動します。

```bash
sudo systemctl start pigpiod
source .venv/bin/activate
python3 src/main.py
```

別のターミナルで映像と Web UI を配信します。

```bash
ustreamer --device=/dev/video0 --host=0.0.0.0 --port=8080 --resolution=640x480 --desired-fps=16 --format=JPEG --encoder=HW --static=public
```

Raspberry Pi と同じ Wi-Fi に接続したスマートフォンで、`http://<RASPBERRY_PI_IP>:8080/` を開きます。`<RASPBERRY_PI_IP>` は Raspberry Pi の IP アドレスに置き換えてください。

起動確認、停止、ログ確認、手動復旧は [運用手順](docs/operations.md) を参照してください。

## ドキュメント

- [設計概要](docs/design.md): 採用技術と構成の背景
- [セットアップ手順](docs/setup.md): OS 側の準備、Python 環境、カメラ確認
- [映像と Web UI の配信](docs/streaming.md): ustreamer の設定値と採用理由
- [配線と設定値](docs/hardware.md): 部品、GPIO 割り当て、PWM、安全設定
- [運用手順](docs/operations.md): 起動、停止、ログ、スマートフォンからのアクセス
- [トラブルシューティング](docs/troubleshooting.md): 映像、操作、pigpio、センサーの切り分け

## 構成

```text
workshop/
├── public/          # ustreamer が配信する Web UI
├── src/             # WebSocket サーバーとモーター制御
├── docs/            # セットアップ、運用、設計資料
└── requirements.txt # Python 依存パッケージ
```

自動起動用の systemd unit は現在の `develop` ブランチには含まれていません。再起動後は [手動復旧手順](docs/operations.md#raspberry-pi-再起動後の手動復旧) に従ってください。
