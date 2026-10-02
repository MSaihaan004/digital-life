from domain.food import Food

def test_food_construction():
    food = Food(x=15.5, y=20.2)
    assert food.x == 15.5
    assert food.y == 20.2

