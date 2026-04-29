def reward_function(params):
    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    all_wheels_on_track = params['all_wheels_on_track']

    if not all_wheels_on_track:
        return 1e-3

    marker = track_width / 2
    reward = 1.0 - (distance_from_center / marker) ** 2
    return float(max(reward, 1e-3))
