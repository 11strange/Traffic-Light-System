
class TrafficLight:
    def __init__(self):
        self.state = "GREEN"  
    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state
