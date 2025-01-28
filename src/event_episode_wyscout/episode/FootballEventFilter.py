class FootballEventFilter:
    def __init__(self, data):
        self.data = data

    @property
    def event_secs(self):
        """Returns a list of event seconds."""
        return [event["eventSec"] for event in self.data]

    @property
    def unique_team_ids(self):
        return list(set([event["teamId"] for event in self.data]))

    @property
    def unique_player_ids(self):
        return list(set([event["playerId"] for event in self.data]))

    def filter_players_by_role(self, role, player_meta):
        role_meta = list(filter(lambda x: x["role"]["code2"] == role, player_meta))
        res = []
        for player in role_meta:
            res.extend(self.filter_by_attribute("playerId", player["wyId"]).data)
        return FootballEventFilter(res)

    def filter_by_attribute(self, attribute, value):
        """Filter data by attribute and value."""
        return FootballEventFilter(
            [event for event in self.data if event.get(attribute) == value]
        )

    def omit_by_attribute(self, attribute, value):
        """Omit data by attribute and value."""
        return FootballEventFilter(
            [event for event in self.data if event.get(attribute) != value]
        )

    def filter_by_match_id(self, match_id):
        """Filter data by match ID using self.filter_by_attribute()."""
        return self.filter_by_attribute("matchId", match_id)

    def filter_by_team_id(self, team_id):
        """Filter data by team ID using self.filter_by_attribute()."""
        return self.filter_by_attribute("teamId", team_id)

    def filter_by_event_sec(self, start_sec, end_sec):
        """Filter data by event second."""
        return FootballEventFilter(
            [event for event in self.data if start_sec <= event["eventSec"] <= end_sec]
        )

    def filter_by_match_period(self, match_period):
        """Filter data by match period using self.filter_by_attribute()."""
        return self.filter_by_attribute("matchPeriod", match_period)

    def filter_by_tags(self, tag_id):
        """Filter data by a specific tag ID."""
        return FootballEventFilter(
            [
                event
                for event in self.data
                if any(tag["id"] == tag_id for tag in event.get("tags", []))
            ]
        )

    def filter_by_position(self, x_range=(0, 100), y_range=(0, 100)):
        """Filter data by position range. Assumes positions list is not empty."""
        return FootballEventFilter(
            [
                event
                for event in self.data
                if x_range[0] <= event["positions"][0]["x"] <= x_range[1]
                and y_range[0] <= event["positions"][0]["y"] <= y_range[1]
            ]
        )

    def get_event_by_id(self, event_id):
        """Retrieve an event by its ID."""
        events = self.filter_by_attribute("eventId", event_id)
        return FootballEventFilter([events[0]]) if events else None

    def get_event_by_ids(self, event_ids):
        """Retrieve events by their IDs."""
        return FootballEventFilter(
            [event for event in self.data if event["id"] in event_ids]
        )

    def __len__(self):
        return len(self.data)

    def __repr__(self) -> str:
        return f"FootballEventFilter({self.data})"
