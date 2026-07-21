# 配線と設定値

GPIO の割り当ては `src/config.py` を正とする。実装済みの左右モーターは現在の設定値を示し、未実装の HC-SR04 とブザーは PIN 番号をプレースホルダーで示す。配線後はこの表と `src/config.py` の BCM GPIO 番号を一致させる。

## 使用部品

- Raspberry Pi Zero WH
- USB カメラ BSWHD06M
- リレー回路
- DC モーター 2 個
- HC-SR04 超音波距離センサー（今後実装）
- 圧電ブザー（今後実装）
- Raspberry Pi 用電源とモーター用電源

## GPIO 割り当て

| 用途 | BCM GPIO 番号 | コード上の設定 |
| --- | --- | --- |
| 左モーター PWM | `24` | `LEFT_PWM_PIN` |
| 左モーター方向 | `25` | `LEFT_DIR_PIN` |
| 右モーター PWM | `18` | `RIGHT_PWM_PIN` |
| 右モーター方向 | `23` | `RIGHT_DIR_PIN` |
| HC-SR04 Trig | `<DISTANCE_TRIG_GPIO>` | 実装時に追加 |
| HC-SR04 Echo | `<DISTANCE_ECHO_GPIO>` | 実装時に追加 |
| 圧電ブザー | `<BUZZER_GPIO>` | 実装時に追加 |

`<...>` はそのまま配線に使用せず、実機で選んだ BCM GPIO 番号に置き換える。Raspberry Pi ヘッダー上の物理 PIN 番号と混同しないこと。

HC-SR04 の Echo は 5 V 信号のため、Raspberry Pi の GPIO へ直接接続しない。分圧回路または適切なレベル変換を使用して 3.3 V に下げる。

## モーターと通信の設定値

現在の値は `src/config.py` を正とする。

| 設定 | 現在値 | 説明 |
| --- | --- | --- |
| PWM 範囲 | `-255` ～ `255` | 負数は後退、正数は前進、`0` は停止 |
| PWM 周波数 | `1000 Hz` | pigpio に設定する周波数 |
| 操作タイムアウト | `150 ms` | 操作中に受信が途絶えたら停止 |
| WebSocket ポート | `8765` | スマートフォンからの操作通信 |
| HTTP ポート | `8080` | Web UI と MJPEG 映像 |

左右の回転方向が実機と逆の場合は、配線を確認したうえで `LEFT_REVERSE` または `RIGHT_REVERSE` を調整する。最初の動作確認では車体を浮かせ、低い出力から試す。

## 障害物判定距離

HC-SR04 の距離計測と障害物判定はまだ実装されていない。実装時は障害物判定距離を `src/config.py` に集約し、ここにも `<OBSTACLE_DISTANCE_CM>` のようなプレースホルダーではなく採用値を記録する。
