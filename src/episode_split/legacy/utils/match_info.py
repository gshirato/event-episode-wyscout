def find_team_id_by_side(data, side):
    """
    Find the team ID based on the given side.

    Args:
        data (dict): A dictionary containing team information.
        side (str): The side of the team (e.g., "home" or "away").

    Returns:
        str or None: The team ID if found, or None if not found.
    """
    for key, value in data.items():
        if value["side"] == side:
            return key
    return None

