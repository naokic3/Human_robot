class EnergyDrive:
    SETPOINT = 1.0
    _EPS = 0.1

    def urgency(self, energy):
        return 1.0 / (energy + self._EPS) ** 2

    def score(self, energy_now, energy_next):
        return self.urgency(energy_now) * (energy_next - energy_now)
    
class CuriosityDrive:
    #drive not driven by direct needs, but by desire to explore

    def __init__(self):
        self.visited: dict[tuple[int,int],int] = {}

    def score(self,row,col):
        return 1.0 / (self.visited.get((row,col),0) + 1)
    def record(self,row,col):
        self.visited[(row,col)] = self.visited.get((row,col),0) + 1

class DriveCORE:
    def __init__(self,weight_curiosity=0.5):
        self.energy_drive = EnergyDrive()
        self.curiosity_drive = CuriosityDrive()
        self.weight_curiosity = weight_curiosity

    def score(self,energy_now:float,energy_next:float,row_next:int,col_next:int):
        energy_score = self.energy_drive.score(energy_now, energy_next)
        curiosity_score = self.curiosity_drive.score(row_next,col_next)

        return energy_score + self.weight_curiosity*curiosity_score
    
    def record_visit(self,row,col):
        self.curiosity_drive.record(row,col)