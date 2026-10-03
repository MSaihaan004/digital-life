from enum import Enum

from domain.sensors import SensorData


class Action(Enum):
    MOVE = "move"
    EAT = "eat"
    REPRODUCE = "reproduce"
    IDLE = "idle"


class RuleBrain:

    def decide(self, sensors: SensorData):

        # If food is visible and energy is low,
        # move toward the food.
        if (
            sensors.nearest_food_distance != float("inf")
            and sensors.energy_ratio < 0.5
        ):
            return Action.MOVE

        # If energy is high and no food is visible,
        # reproduction can be considered.
        if (
            sensors.energy_ratio >= 0.8
            and sensors.nearest_food_distance == float("inf")
        ):
            return Action.REPRODUCE

        # Default behavior: explore.
        return Action.MOVE

    def movement_direction(self, sensors: SensorData):

        if sensors.nearest_food_distance != float("inf"):
            return (
                sensors.nearest_food_dx,
                sensors.nearest_food_dy
            )

        # No food detected → explore to the right.
        return (1.0, 0.0)
