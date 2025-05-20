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
    if primary in ["game_interruption", "offside"]:
        return True
    if "ball_out" in secondary:
        return True
    return False


def segment_events(event: dict) -> tuple[list[tuple], list[tuple]]:
    start = []
    end = []

    for ev in event:
        id = ev["id"]
        team = ev["team"]["id"]
        primary = ev["type"]["primary"]
        secondary = ev["type"]["secondary"]
        videoTimestamp = ev["videoTimestamp"]
        period = ev["matchPeriod"]

        if clear_start(primary, secondary):
            start.append(id)
        if clear_end(primary, secondary):
            end.append(id)

    return start, end
