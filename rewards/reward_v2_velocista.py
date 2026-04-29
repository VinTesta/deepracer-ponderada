def reward_function(params):
    if not params['all_wheels_on_track']:
        return 1e-3

    speed = params['speed']
    abs_steering = abs(params['steering_angle'])
    progress = params['progress']

    speed_reward = speed / 4.0
    smoothness = max(0.0, 1.0 - (abs_steering / 30.0))
    progress_bonus = progress / 100.0

    reward = 0.5 * speed_reward + 0.3 * smoothness + 0.2 * progress_bonus
    return float(max(reward, 1e-3))
