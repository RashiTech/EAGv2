class Memory:
    def __init__(self):
        self.preference = ""

    def set_preferences(self, preference: str):
        self.preference = preference

    def get_preference(self) -> str:
        return self.preference