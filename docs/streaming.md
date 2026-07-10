# カメラ映像と Web UI の配信手順

Raspberry Pi 上では ustreamer を使い、カメラ映像とスマホ操作用の静的 Web UI を同じ HTTP サーバーから配信する。

起動コマンド:

```bash
ustreamer --device=/dev/video0 --host=0.0.0.0 --port=8080 --resolution=640x480 --desired-fps=16 --format=JPEG --encoder=HW --static=public
```

配信 URL:

- Web UI: `http://<Raspberry Pi の IP>:8080/`
- MJPEG ストリーム: `http://<Raspberry Pi の IP>:8080/stream`

操作命令用の Python WebSocket サーバーは別プロセスで起動し、ポート `8765` を使う。

systemd で自動起動する場合は、`--static=public` のような相対パスに依存しないようにする。
unit ファイルで `WorkingDirectory` を指定するか、 `--static` に絶対パスを指定する。

## 採用構成

- カメラ: BSWHD06M
- 解像度: `640x480`
- FPS: `16`
- フォーマット: `JPEG`
- エンコーダー指定: `HW`

## 採用理由と再検討ポイント

カメラは BSWHD06M を採用する。Pi Camera と比べて画面表示までの遅延が少なく、ラジコン操作時の映像確認に使いやすいため。

Pi Camera は設定次第で改善する可能性があるため、遅延や取り付けやすさに課題が出る場合は再検討する。

`640x480 @ 16fps` は、低遅延とカクつきの少なさを優先した設定とする。
スマホでの視認性が不足する場合は、`1280x720` や `30fps` も候補にする。

`--format=JPEG` は MJPEG 配信前提として採用する。

`--encoder=HW` は遅延を抑えるために指定する。
