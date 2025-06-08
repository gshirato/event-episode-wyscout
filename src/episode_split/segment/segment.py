def clear_start(primary: str, secondary: str) -> bool:
    if primary in [
        "corner",
        "throw_in",
        "goal_kick",
        "free_kick",
        "penalty",
    ]:
        return True
    return False


def clear_end(primary: str, secondary: str) -> bool:
    if primary in ["game_interruption", "offside", "infraction"]:
        return True
    if "ball_out" in secondary:
        return True
    if "conceded_goal" in secondary:
        return True
    return False


def loose_ball(secondary: str) -> bool:
    if "loose_ball_duel" in secondary:
        return True
    return False


def segment_events(event: dict) -> tuple[list, list, list, list]:
    """
    イベントをセグメントに分割し、goalkeeper_exitの処理を追加

    Returns:
        start: 開始イベントのIDリスト
        end: 終了イベントのIDリスト
        loose: ルーズボールイベントのIDリスト
        gk_exit_splits: goalkeeper_exitによる分割ポイントのIDリスト
    """
    start = []
    end = []
    loose = []
    gk_exit_splits = []

    for i, ev in enumerate(event):
        id = ev["id"]
        team = ev["team"]["id"]
        primary = ev["type"]["primary"]
        secondary = ev["type"]["secondary"]

        if clear_start(primary, secondary):
            start.append(id)
        if clear_end(primary, secondary):
            end.append(id)
        if loose_ball(secondary):
            loose.append(id)

        # goalkeeper_exitの処理
        if primary == "goalkeeper_exit":
            # 次のイベントから確認（最大5イベント先まで）
            found_duel = False
            duel_index = -1

            # まず関連するduelを探す
            for j in range(1, min(6, len(event) - i)):
                next_ev = event[i + j]
                next_team = next_ev["team"]["id"]
                next_primary = next_ev["type"]["primary"]

                if next_team == team and next_primary == "duel":
                    next_secondary = next_ev["type"]["secondary"]
                    if any(
                        s in next_secondary
                        for s in ["recovery", "firstTouch", "aerial_duel"]
                    ):
                        found_duel = True
                        duel_index = i + j
                        break

            # duelが見つかった場合、その後の最初のボール保持イベントから分割
            if found_duel:
                for k in range(duel_index + 1, min(duel_index + 4, len(event))):
                    next_ev = event[k]
                    next_team = next_ev["team"]["id"]
                    next_primary = next_ev["type"]["primary"]

                    if next_team == team and next_primary in ["pass", "touch", "carry"]:
                        gk_exit_splits.append(next_ev["id"])
                        break
            # duelが見つからない場合、直接的なボール保持イベントを探す
            else:
                for j in range(1, min(4, len(event) - i)):
                    next_ev = event[i + j]
                    next_team = next_ev["team"]["id"]
                    next_primary = next_ev["type"]["primary"]

                    if next_team == team and next_primary in ["pass", "touch", "carry"]:
                        gk_exit_splits.append(next_ev["id"])
                        break

    return start, end, loose, gk_exit_splits
