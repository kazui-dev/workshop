# 運用手順

コマンドは Raspberry Pi 上のリポジトリルートで実行する。初回のみ [セットアップ手順](setup.md) に従って `./scripts/setup` を実行する。セットアップ後は Raspberry Pi の起動時に、pigpiod、Python操作サーバー、ustreamerが自動的に立ち上がる。

## 一括操作

3つのプロセスをまとめて操作する。

```bash
./scripts/start
./scripts/stop
./scripts/restart
./scripts/status
```

- `start`: pigpiod、Python操作サーバー、ustreamerを起動する
- `stop`: Python操作サーバーとustreamerを停止してからpigpiodを停止する
- `restart`: 安全な順序で全プロセスを再起動する
- `status`: systemd上の現在の状態を表示する

Python操作サーバーの停止時には終了処理でモーターを停止する。pigpiodを単独で再起動せず、通常は `./scripts/restart` を使う。

## ログ確認

現在のRaspberry Pi起動以降に、Pythonのターミナルへ出力されるログ、ustreamerのログ、pigpiodのログをまとめて表示する。

```bash
./scripts/logs
```

このコマンドは `journalctl -f` でログを追跡する。終了するときは `Ctrl+C` を押す。

個別に直近100件を確認する場合は次を使う。

```bash
journalctl -b -u workshop-controller.service -n 100 --no-pager
journalctl -b -u workshop-streamer.service -n 100 --no-pager
journalctl -b -u pigpiod.service -n 100 --no-pager
```

### 操作信号の詳細ログ

通常はWebSocketの接続、切断、警告だけを記録する。受信した左右PWM値も記録する場合は、`systemd/workshop-controller.service.in` の `[Service]` に次を追加してから `./scripts/setup` を再実行する。

```ini
Environment=LOG_LEVEL=DEBUG
```

操作信号は操作中に 50 ms間隔で記録されるため、調査後は設定を戻して再度 `./scripts/setup` を実行する。

## スマートフォンからアクセスする

Raspberry Pi の IP アドレスを確認する。

```bash
hostname -I
```

スマートフォンを同じ Wi-Fi に接続し、ブラウザで次を開く。

```text
http://<RASPBERRY_PI_IP>:8080/
```

映像が表示され、ジョイスティック操作時に `./scripts/logs` へ WebSocket 接続ログが出れば、映像表示と操作通信は成功している。初回のモーター確認は車体を浮かせて行う。

前方左右の HC-SR04 を片方ずつ確認する。それぞれの正面 20 cm 以内に障害物を置くとモーターが停止し、前進操作が抑止されることを確認する。この状態でも後退とその場旋回は可能である。

次に両方の正面へ障害物を置き、片方だけを 25 cm 以上に離しても前進抑止が続くことを確認する。両方を 25 cm 以上に離すと通常操作へ戻ることを確認する。

## 再起動後の確認

セットアップ済みであれば手動起動は不要である。Raspberry Piへの再接続後に確認する。

```bash
./scripts/status
```

起動していないサービスがある場合は `./scripts/logs` で原因を確認し、修正後に `./scripts/restart` を実行する。

## systemdの構成

`workshop.target` がプロジェクト固有の2サービスをまとめる。

- `workshop-controller.service`: `src/main.py` を起動する
- `workshop-streamer.service`: カメラ映像と Web UI を配信する
- `pigpiod.service`: Raspberry Pi OS 側の GPIO デーモン

clone先の絶対パスと実行ユーザーは `./scripts/setup` が検出し、`.service.in` から実機用 unit を生成する。そのため、リポジトリを特定のホームディレクトリへ置く必要はない。
