from mesa import Agent, Model
from mesa.time import RandomActivation
import random

class PatientAgent(Agent):
    def __init__(self, unique_id, model, age, gender, race, region, health_issues):
        super().__init__(unique_id, model)
        self.age = age
        self.gender = gender
        self.race = race
        self.region = region
        self.health_issues = health_issues
        self.consented = False

    def step(self):
        # Simple logic to decide if patient consents based on model parameters
        consent_probability = self.model.consent_rate
        self.consented = random.random() < consent_probability

class RecruitmentModel(Model):
    def __init__(self, num_agents, consent_rate):
        self.num_agents = num_agents
        self.consent_rate = consent_rate
        self.schedule = RandomActivation(self)

        # Create agents
        for i in range(self.num_agents):
            age = random.randint(18, 80)  # Example attribute assignment
            gender = random.choice(['Male', 'Female'])
            race = random.choice(['White', 'Black', 'Asian', 'Hispanic'])
            region = random.choice(['North', 'South', 'East', 'West'])
            health_issues = random.choice(['Diabetes', 'Hypertension', 'None'])
            agent = PatientAgent(i, self, age, gender, race, region, health_issues)
            self.schedule.add(agent)

    def step(self):
        self.schedule.step()

# Example usage
model = RecruitmentModel(num_agents=100, consent_rate=0.5)
for i in range(10):  # Run for 10 steps