# トラブルシューティング

問題が起きたら、電源と配線、pigpiod、Python WebSocket サーバー、ustreamer、スマートフォンの順に切り分ける。モーターや GPIO の配線を触る前に電源を切る。

## 映像が出ない

1. `ls -l /dev/video*` でカメラデバイスを確認する。
2. `--device=/dev/video0` が実際のデバイスと一致するか確認する。
3. `tail -n 100 workshop-ustreamer.log` で起動エラーを確認する。
4. `curl -I http://127.0.0.1:8080/` を Raspberry Pi 上で実行し、HTTP 応答を確認する。
5. 別プロセスがポート `8080` やカメラを使用していないか確認する。
6. `--encoder=HW` で起動できない場合は、ハードウェア対応状況を確認するため一時的にこの指定を外して比較する。

## Web UI は出るが操作できない

1. Python 側に `Starting server on 0.0.0.0:8765` が出ているか確認する。
2. スマートフォンのブラウザ開発者ツールを利用できる場合は、WebSocket エラーを確認する。
3. Raspberry Pi 上で `ss -ltn | grep 8765` を実行し、待受を確認する。
4. スマートフォンと Raspberry Pi が同じネットワークにあり、端末間通信が禁止されていないか確認する。
5. 既に別のスマートフォンが操作接続していないか Python ログを確認する。同時に操作できる接続は 1 台だけである。
6. 操作値が 150 ms 以上途絶えると安全のためモーターが停止する。ブラウザがバックグラウンドになっていないか確認する。

## pigpio に接続できない

状態とログを確認する。

```bash
systemctl status pigpiod --no-pager
journalctl -u pigpiod -n 100 --no-pager
```

停止していれば起動する。

```bash
sudo systemctl start pigpiod
```

その後、Python WebSocket サーバーを起動し直す。`src/main.py` と pigpiod を異なるホストで動かす構成は現在想定していない。

## モーターが動かない、または向きが逆

1. リレー回路とモーター用電源、Raspberry Pi との GND 共通化を確認する。
2. [配線と設定値](hardware.md) の BCM GPIO 番号と `src/config.py` が一致するか確認する。
3. PWM ピンと方向ピンを取り違えていないか確認する。
4. 向きだけが逆なら `LEFT_REVERSE` / `RIGHT_REVERSE` を確認する。
5. 車体を浮かせ、低い PWM 値から片側ずつ確認する。

## センサー値がおかしい

HC-SR04 の距離計測で値がおかしい場合は、まず次を確認する。

1. Trig / Echo の BCM GPIO 番号と設定値が一致しているか。
2. Echo の 5 V 信号が分圧またはレベル変換で 3.3 V になっているか。
3. Raspberry Pi とセンサーの GND が共通か。
4. タイムアウトや範囲外の値が連続し、センサー異常として停止していないか。
5. センサー正面の近すぎる物体、柔らかい素材、斜めの面による反射不良がないか。
6. 複数回の測定結果と実測距離を比較し、単発ノイズか継続的なずれかを切り分ける。
