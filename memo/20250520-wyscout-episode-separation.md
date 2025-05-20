# サッカーイベントデータのセグメンテーション

### 概要

このコードは、サッカーの試合データ（イベントデータ）を**「攻撃の単位（エピソード）」ごとに分割（セグメント化）**することを目的としています。

- 「攻撃のはじまり」「攻撃の終わり」「ルーズボール」などのイベントを判定し、
- それに基づいて、一連のイベントを**エピソード（攻撃の区切り単位）**としてグループ化します。
- その結果、どのタイミングでボールの支配が切り替わったか、どのプレーが攻撃の始点か終点か、といった分析が可能になります。

### なぜやるのか？

サッカーでは「攻撃がどこから始まって、どこで終わるか」という単位でプレーを分析することが重要です。
このセグメンテーションは、攻撃ごとのパフォーマンス比較や、得点に結びついた流れの特定などに活用できます。

---

### 実装の概要

1. **攻撃の開始・終了イベントを定義**
   - 例：コーナーキック、スローイン、フリーキック等で攻撃開始
   - 例：ボールアウト、オフサイド等で攻撃終了

2. **ルーズボール状態の判定**
   - どちらのチームもボールを保持していない時間帯

3. **全イベントをなめて、「開始」「終了」「ルーズボール」のイベントIDを抽出**
   - イベントごとに攻撃のセグメントを振り分ける

---

### コード例

```python
# 1. 攻撃やプレーの開始イベント判定
def clear_start(primary: str, secondary: str) -> bool:
    return primary in [
        "corner", "throw_in", "goal_kick", "free_kick", "penalty"
    ]

# 2. 攻撃やプレーの終了イベント判定
def clear_end(primary: str, secondary: str) -> bool:
    if primary in ["game_interruption", "offside", "infraction"]:
        return True
    if "ball_out" in secondary:
        return True
    return False

# 3. ルーズボールイベント判定
def loose_ball(secondary: str) -> bool:
    return "loose_ball_duel" in secondary

# 4. イベントデータから、開始・終了・ルーズボールイベントのIDを抽出
def segment_events(events: list[dict]) -> tuple[list[int], list[int], list[int]]:
    start, end, loose = [], [], []
    for ev in events:
        id = ev["id"]
        primary = ev["type"]["primary"]
        secondary = ev["type"]["secondary"]
        if clear_start(primary, secondary):
            start.append(id)
        if clear_end(primary, secondary):
            end.append(id)
        if loose_ball(secondary):
            loose.append(id)
    return start, end, loose

```