def move_organism(organism, dx, dy, world):
    """
    Move an organism by the supplied direction.

    The movement vector is normalized so that diagonal
    movement isn't faster than horizontal/vertical movement.
    """

    magnitude = (dx ** 2 + dy ** 2) ** 0.5

    if magnitude == 0:
        return

    normalized_dx = dx / magnitude
    normalized_dy = dy / magnitude

    speed = organism.genome.speed

    organism.velocity_x = normalized_dx * speed
    organism.velocity_y = normalized_dy * speed

    organism.x += organism.velocity_x
    organism.y += organism.velocity_y

    # Keep organism inside the world.
    organism.x = max(0, min(organism.x, world.width))
    organism.y = max(0, min(organism.y, world.height))
