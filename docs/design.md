# スマホ操作・衝突防止キャタピラ式ラジコン

動作環境: RaspberryPi Zero WH

## 機能

- スマホ操作
	- WebサイトをWi-Fiネットワーク上に公開
	- 一人称視点 (ラジコン搭載カメラから映像配信)
	- ジョイスティック操作 (スティックに合わせてPWM制御)
- 衝突防止
	- 超音波センサ (HC-SR04) による障害物検知
	- 自動停止
	- 圧電ブザーで警告音を鳴らす

## 使用技術

### [µStreamer](https://github.com/pikvm/ustreamer) (表記ゆれ: ustreamer)

1. MJPEGでの映像配信
	- MJPEGについて
		- Pythonでの映像配信は遅延が大きく、ラジコン操作に不向き
		- MJPEGでの映像配信は処理が軽く、低遅延
		- ハードウェアエンコード (V4L2等) を活用して映像処理の負荷を最小化できる
		- 基本的にHTTPサーバーからデータを送信する
	- mjpg-streamer vs μStreamer → μStreamer
		- LinuxでのMJPEG配信はmjpg-streamerやμStreamerなどのソフトが有名
		- μStreamerはmjpg-streamerより軽量かつ高速で、映像も高品質
		- mjpg-streamerは開発停止しており、運用に不安が残る

2. Webサイト公開
	- μStreamerのHTTPサーバーは静的ファイル配信が可能 (`--static` オプション ) 
		- この機能でHTMLを配信し、Webサイトを公開できる
		- もしPythonやApacheで公開する場合、一つ多くHTTPサーバーが必要になる
		- 映像配信とWebサイト公開を同じサーバーで行い、CPU使用率を最適化する
        - PythonでFlaskなどを使う必要がなくなり、依存関係が最小になる

### WebSocket

クライアントとサーバー間でリアルタイムに双方向通信を行うための通信プロトコル
ジョイスティックのデータを連続的に送信でき、低遅延な操作を実現できる
- クライアント側
	- ジョイスティック操作中、50ms間隔でスティックの傾きを取得する
	- 取得した値を左右のモーター出力 (PWM値) に変換し、JSONで送信する
	- 操作終了 (指を離した) 時、停止命令を送信し、データ送信を停止する
- サーバー側
	- `websockets`ライブラリでサーバープロセスを稼働させ、データを受信する
	- 受信したPWM値をpigpiodへ渡し、モーターを制御する
	- 障害物検知中は、前進命令を無視して後退命令のみ受け付ける
	- 操作中に150ms以上データが来ない場合、通信異常としてモーターを停止する

### pigpio

- pigpioはGPIO操作をPythonプロセスからpigpiodに委譲し、命令のみ行う
- pigpiodはバックグラウンド常駐プロセスで、GPIOをハードウェアレベルで直接制御する
- RPi.GPIOのGPIO操作はPythonプロセスで行われるため、遅延リスクがある
- GPIO操作をpigpiodに切り出すことで、Python側でWebSocketなどのブロッキング処理が発生してもGPIO信号の安定性に影響しない

1. PWM制御 (モーターとブザーの制御) 
	- RPi.GPIOはPythonのループ処理でPWMを制御するため、CPU使用率が高く信号の安定性も低い
	- pigpiodはメモリに直接PWMパターンを書き込むため、CPUの使用は命令時のみ

2. 超音波センサ制御
	- Pythonでの計測や検知は、CPU負荷による精度低下や遅延がある
	- pigpiodはGPIOピンの変化をハードウェアレベルで記録するため、高精度・低遅延

pigpiodを自動起動に設定するコマンド
```bash
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```
