import numpy as np
from scipy.optimize import linear_sum_assignment

def build_cost_matrix(artists, events):
    """
    Build a cost matrix based on artist availability, organizer's preferences, and genre match.
    """
    num_artists = len(artists)
    num_events = len(events)
    
    # Initialize the cost matrix with large values (infinity).
    cost_matrix = np.full((num_artists, num_events), np.inf)
    
    for i, artist in enumerate(artists):
        for j, event in enumerate(events):
            # Check artist availability
            if event['date'] in artist['available_dates']:
                # Set base cost to a medium-high value (e.g., 2)
                cost = 2
                
                # Check if artist is in organizer's preferred list for this event
                # if artist['id'] in organizer_preferences.get(event['id'], []):
                    # cost = 0  # Low cost for preferred artist
                
                # Check for genre match between event category and artist genres
                if any(category in artist['genres'] for category in event['categories']):
                    cost = 1  # Medium-low cost for genre match
                
                # Assign the calculated cost
                cost_matrix[i, j] = cost
            else:
                # Not available, set cost to infinity
                cost_matrix[i, j] = np.inf
    
    return cost_matrix

# def optimize_booking_schedule(artists, events, organizer_preferences):
def optimize_booking_schedule(artists, events):
    """
    Uses the Hungarian algorithm (linear sum assignment) to optimize event-artist scheduling
    based on availability, organizer preferences, and genre match.
    
    Returns an optimized match of artists to events.
    """
    # Step 1: Build the cost matrix based on availability, preferences, and genre match
    cost_matrix = build_cost_matrix(artists, events)
    
    # Step 2: Solve using the Hungarian algorithm (minimizing the cost)
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    # Step 3: Return optimal assignments as a list of (artist, event) tuples
    return [(artists[i]['id'], events[j]['id']) for i, j in zip(row_ind, col_ind) if cost_matrix[i, j] != np.inf]

