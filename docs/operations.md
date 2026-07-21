# 運用手順

コマンドは Raspberry Pi 上のリポジトリルートで実行する。現在の `develop` ブランチにはプロジェクト固有の自動起動設定がないため、Raspberry Pi 再起動後は各プロセスを手動で起動する。

## 起動

### 1. pigpiod

```bash
sudo systemctl start pigpiod
systemctl is-active pigpiod
```

`active` と表示されることを確認する。

### 2. Python WebSocket サーバー

```bash
source .venv/bin/activate
python3 src/main.py 2>&1 | tee workshop-control.log
```

`Starting server on 0.0.0.0:8765` が表示されれば待受を開始している。このターミナルは開いたままにする。

### 3. ustreamer

別のターミナルで実行する。

```bash
ustreamer --device=/dev/video0 --host=0.0.0.0 --port=8080 --resolution=640x480 --desired-fps=16 --format=JPEG --encoder=HW --static=public 2>&1 | tee workshop-ustreamer.log
```

詳細な映像設定は [映像と Web UI の配信](streaming.md) を参照する。

## スマートフォンからアクセスする

Raspberry Pi の IP アドレスを確認する。

```bash
hostname -I
```

スマートフォンを同じ Wi-Fi に接続し、ブラウザで次を開く。

```text
http://<RASPBERRY_PI_IP>:8080/
```

映像が表示され、ジョイスティック操作時に Python 側へ WebSocket 接続ログが出れば、映像表示と操作通信は成功している。初回のモーター確認は車体を浮かせて行う。

HC-SR04 の正面 20 cm 以内に障害物を置くとモーターが停止してブザーが鳴り、前進操作が抑止されることも確認する。この状態でも後退とその場旋回は可能で、障害物を離すと通常操作へ戻る。

## 停止と再起動

Python WebSocket サーバーと ustreamer は、それぞれを起動したターミナルで `Ctrl+C` を押して停止する。Python 側は終了処理でモーターを停止する。

pigpiod を停止または再起動する場合は、先に Python WebSocket サーバーを停止する。

```bash
sudo systemctl stop pigpiod
sudo systemctl restart pigpiod
```

pigpiod 再起動後は Python WebSocket サーバーも起動し直す。

## ログ確認

手動起動時のログは `tee` で保存したファイルを確認する。

```bash
tail -f workshop-control.log
tail -f workshop-ustreamer.log
```

pigpiod の systemd ログは次で確認する。

```bash
journalctl -u pigpiod -n 100 --no-pager
journalctl -u pigpiod -f
```

## Raspberry Pi 再起動後の手動復旧

1. `sudo systemctl start pigpiod` を実行する。
2. `systemctl is-active pigpiod` が `active` になることを確認する。
3. venv を有効化し、`python3 src/main.py` を起動する。
4. 別のターミナルで ustreamer を起動する。
5. スマートフォンで `http://<RASPBERRY_PI_IP>:8080/` を開く。
6. 映像、WebSocket 接続、モーターの順で確認する。

自動起動を採用していない理由は、プロジェクト固有の systemd unit と実機上の配置先・実行ユーザーがまだ `develop` に確定していないためである。unit を導入する issue では、手動起動で実機確認したコマンドとパスを基準にする。
