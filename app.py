import streamlit as st
import random
import pandas as pd
import uuid
import json
from collections import deque
import numpy as np
import math

def initialize_session_state():
    """Initialize session state variables if not already set."""
    if 'pair_types' not in st.session_state or not isinstance(st.session_state.pair_types, deque):
        st.session_state.pair_types = deque(maxlen=100)
    if 'results' not in st.session_state or not isinstance(st.session_state.results, deque):
        st.session_state.results = deque(maxlen=200)
    if 'next_prediction' not in st.session_state:
        st.session_state.next_prediction = "N/A"
    if 'base_amount' not in st.session_state:
        st.session_state.base_amount = 10.0
    if 'bet_amount' not in st.session_state:
        st.session_state.bet_amount = 0.0
    if 'result_tracker' not in st.session_state:
        st.session_state.result_tracker = 0.0
    if 'profit_lock' not in st.session_state:
        st.session_state.profit_lock = 0.0
    if 'previous_result' not in st.session_state:
        st.session_state.previous_result = None
    if 'state_history' not in st.session_state:
        st.session_state.state_history = []
    if 'current_dominance' not in st.session_state:
        st.session_state.current_dominance = "N/A"
    if 'streak_type' not in st.session_state:
        st.session_state.streak_type = None
    if 'consecutive_wins' not in st.session_state:
        st.session_state.consecutive_wins = 0
    if 'consecutive_losses' not in st.session_state:
        st.session_state.consecutive_losses = 0
    if 'stats' not in st.session_state or not isinstance(st.session_state.stats, dict):
        st.session_state.stats = {
            'wins': 0,
            'losses': 0,
            'ties': 0,
            'streaks': [],
            'odd_pairs': 0,
            'even_pairs': 0,
            'alternating_pairs': 0,
            'bet_history': []
        }
    else:
        default_stats = {
            'wins': 0,
            'losses': 0,
            'ties': 0,
            'streaks': [],
            'odd_pairs': 0,
            'even_pairs': 0,
            'alternating_pairs': 0,
            'bet_history': []
        }
        for key, value in default_stats.items():
            if key not in st.session_state.stats or not isinstance(st.session_state.stats[key], type(value)):
                st.session_state.stats[key] = value
    if 'pattern_confidence' not in st.session_state:
        st.session_state.pattern_confidence = {"Odd": 0.0, "Even": 0.0, "Alternating": 0.0, "Streak": 0.0, "Choppy": 0.0, "Markov": 0.0, "Bayesian": 0.0}
    if 'alerts' not in st.session_state:
        st.session_state.alerts = []
    if 'processing' not in st.session_state:
        st.session_state.processing = False

def validate_pair_types():
    """Validate and fix pair_types if invalid."""
    if not isinstance(st.session_state.pair_types, deque):
        st.session_state.alerts.append({"type": "warning", "message": "pair_types is not a deque; reinitialized.", "id": str(uuid.uuid4())})
        st.session_state.pair_types = deque(maxlen=100)
        return False
    valid_pairs = [p for p in st.session_state.pair_types if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
    if len(valid_pairs) < len(st.session_state.pair_types):
        st.session_state.alerts.append({"type": "warning", "message": f"Found {len(st.session_state.pair_types) - len(valid_pairs)} invalid pairs in pair_types; cleaned.", "id": str(uuid.uuid4())})
        st.session_state.pair_types = deque(valid_pairs, maxlen=100)
        return False
    return True

def set_base_amount():
    """Set the base amount from user input."""
    try:
        amount = float(st.session_state.base_amount_input)
        if 1 <= amount <= 100:
            st.session_state.base_amount = amount
            st.session_state.bet_amount = st.session_state.base_amount if st.session_state.next_prediction in ["Player", "Banker"] else 0
            st.session_state.alerts.append({"type": "success", "message": "Base amount updated successfully.", "id": str(uuid.uuid4())})
        else:
            st.session_state.alerts.append({"type": "error", "message": "Invalid base amount. Must be between $1 and $100.", "id": str(uuid.uuid4())})
    except ValueError:
        st.session_state.alerts.append({"type": "error", "message": "Please enter a valid number.", "id": str(uuid.uuid4())})

def compute_markov_probabilities(results):
    """Compute Markov transition probabilities from results."""
    transitions = {'P': {'P': 0, 'B': 0, 'T': 0}, 'B': {'P': 0, 'B': 0, 'T': 0}, 'T': {'P': 0, 'B': 0, 'T': 0}}
    counts = {'P': 0, 'B': 0, 'T': 0}
    
    for i in range(len(results) - 1):
        current, next_state = results[i], results[i + 1]
        if current in transitions and next_state in transitions[current]:
            transitions[current][next_state] += 1
            counts[current] += 1
    
    probabilities = {'P': {'P': 0.0, 'B': 0.0, 'T': 0.0}, 'B': {'P': 0.0, 'B': 0.0, 'T': 0.0}, 'T': {'P': 0.0, 'B': 0.0, 'T': 0.0}}
    for state in transitions:
        total = counts[state]
        if total > 0:
            for next_state in transitions[state]:
                probabilities[state][next_state] = transitions[state][next_state] / total
        else:
            probabilities[state] = {'P': 0.446, 'B': 0.458, 'T': 0.096}
    
    return probabilities

def compute_bayesian_probabilities(results):
    """Compute Bayesian posterior transition probabilities using Dirichlet priors."""
    prior_params = {'P': {'P': 0.446, 'B': 0.458, 'T': 0.096}, 
                   'B': {'P': 0.446, 'B': 0.458, 'T': 0.096}, 
                   'T': {'P': 0.446, 'B': 0.458, 'T': 0.096}}
    alpha = 1.0
    transitions = {'P': {'P': 0, 'B': 0, 'T': 0}, 'B': {'P': 0, 'B': 0, 'T': 0}, 'T': {'P': 0, 'B': 0, 'T': 0}}
    
    for i in range(len(results) - 1):
        current, next_state = results[i], results[i + 1']
        if current in transitions and next_state in transitions[current]:
            transitions[current][next_state] += 1
    
    posterior_probs = {'P': {}, 'B': {}, 'T': {}}
    for state in transitions:
        total_counts = sum(transitions[state].values())
        total_alpha = sum(prior_params[state].values()) * alpha
        for next_state in transitions[state]:
            count = transitions[state][next_state]
            prior = prior_params[state][next_state]
            posterior_probs[state][next_state] = (count + prior) / (total_counts + total_alpha)
    
    return posterior_probs

def analyze_patterns():
    """Analyze patterns, Markov, and Bayesian probabilities to determine dominant strategy and bet amount."""
    validate_pair_types()
    results = list(st.session_state.results)
    valid_pairs = [p for p in st.session_state.pair_types if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T']] and p[1] in ['P', 'B', 'T']]
    if len(valid_pairs) < 2:
        st.session_state.bet_amount = 0
        return {"Odd": 0.0, "Even": 0.0, "Alternating": 0.0, "Streak": 0.0, "Choppy": 0.0, "Markov": 0, "Bayesian": 0.0}, "N/A", None

    recent_pairs = valid_pairs[-10:] if len(valid_pairs) >= 10 else valid_pairs
    alternation_rate = sum(1 for i in range(len(recent_pairs)-1)) if recent_pairs[i][1] != recent_pairs[i+1][1]) / (len(recent_pairs) - 1) if len(recent_pairs) > 1 else 0
    window_sizes = [3, 5, 8] if alternation_rate > 0.7 else [5, 10, 8]

    pattern_scores = {"Odd": 0.0, "Even": 0.0, "Alternating": 0.0, "Streak": 0.0, "Choppy": 0.0, "Markov": 0.0, "Bayesian": 0.0}
    total_weight = 0.0

    for window in window_sizes:
        if len(valid_pairs) >= window:
            recent_pairs = recent_pairs[-window:]
            recent_results = results[-window-1:] if len(results) >= window+1 else results

            odd_count = sum(1 for a, b in recent_pairs if a != b)
            even_count = sum(1 for a, b in recent_pairs if a == b)
            total_pairs = odd_count + even_count
            odd_score = (odd_count / total_pairs) * (window / 20) if total_pairs > 0 else 0
            even_score = (even_count / total_pairs) * (window / 20) if total_pairs > 0 else 0
            pattern_scores["Odd"] += odd_score
            pattern_scores["Even"] += even_score
            total_weight += window / 20

            alternating_count = sum(1 for i in range(len(recent_pairs)-1)) if recent_pairs[i][1] != recent_pairs[i+1][1])
            alternating_score = (alternating_count / (window-1)) * (window / 20) if window > 1 else 0
            streak_length = 1
            current_streak = recent_results[-1] if recent_results else None
            for i in range(2, len(recent_results)+1):
                if recent_results[-i] == current_streak and recent_results[-i] != 'T':
                    streak_length += 1
                else:
                    break
            streak_score = (streak_length / 5) * (window / 20) if streak_length >= 2 else 0
            pattern_scores["Streak"] += streak_score

            choppy_count = sum(1 for i in range(len(recent_results)-1)) if recent_results[i] != recent_results[i+1] and recent_results[i] != 'T' and recent_results[i+1] != 'T')
            choppy_score = (choppy_count / (window-1)) * (window / 20) if window > 1 else 0
            if total_weight > 0:
        for pattern in ['Odd', 'Even', 'Alternating', 'Streak', 'Choppy']:
            pattern_scores[pattern"] /= total_weight

    markov_probs = compute_markov_probabilities(results)
    last_result = st.session_state.previous_result
    if last_result in markov_probs:
        max_prob = max(markov_probs[last_result].values())
        markov_prediction = max(markov_probs[last_result], key=markov_probs[last_result].get)
        pattern_scores["Markov"] = max_prob
    else:
        markov_prediction = random.choice(['P', 'B'])
        pattern_scores["Markov"] = 0.458

    bayesian_probs = compute_bayesian_probabilities(results)
    if last_result in bayesian_probs:
        max_prob = max(bayesian_probs[last_result].values())
        bayesian_prediction = max(bayesian_probs[last_result], key=bayesian_probs[last_result].get)
        pattern_scores["Bayesian"] = max_prob
    else:
        bayesian_prediction = random.choice(['P', 'B'])
        pattern_scores["Bayesian"] = 0.458

    dominant_pattern = max(pattern_scores, key=pattern_scores.get)
    confidence = pattern_scores[dominant_pattern]
    streak_type = None
    bet_multiplier = 1.0

    if len(valid_pairs) >= 8:
        odd_count = sum(1 for a, b in recent_pairs if a != b)
        even_count = sum(1 for a, b in recent_pairs if a == b)
        dominance_diff = abs(odd_count - even_count)
        total_pairs = len(recent_pairs)
        confidence = dominance_diff / total_pairs if total_pairs > 0 else 0.0

        pair_sequence = ["Odd" if a != b else "Even" for a, b in recent_pairs]
        cycle_detected = False
        cycle_length = 0
        for length in range(2, min(5, len(pair_sequence) // 2 + 1)):
            if len(pair_sequence) >= 2 * length:
                recent = pair_sequence[-2 * length:-length]
                previous = pair_sequence[-length:]
                if recent == previous:
                    cycle_detected = True
                    cycle_length = length
                    confidence += 0.2
                    break

        last_three_pairs = pair_sequence[-3:] if len(pair_sequence) >= 3 else []
        pair_streak = len(last_three_pairs) >= 3 and all(p == last_three_pairs[0] for p in last_three_pairs)

        last_four = [p[1] for p in valid_pairs[-4:] if isinstance(p, (tuple, list)) and len(p) > 1 and p[1] in ['P', 'B', 'T'] and p[1] != 'T']
        if len(last_four) >= 3 and all(r == last_four[-1] for r in last_four):
            streak_type = last_four[-1]
            pattern_prediction = "Player" if streak_type == 'P' else "Banker"
            dominance = f"Streak ({streak_type})"
            streak_length = len([p for p in valid_pairs[-5:] if isinstance(p, (tuple, list)) and len(p) > 1 and p[1] == streak_type])
            bet_multiplier = min(3.0, 1 + 0.5 * (streak_length - 2))
        elif pair_streak:
            dominance = f"Pair Streak ({last_three_pairs[0]})"
            if last_three_pairs[0] == "Odd":
                pattern_prediction = "Player" if last_result == 'B' else "Banker"
            else:
                pattern_prediction = "Player" if last_result == 'P' else "Banker"
            bet_multiplier = math.ceil(1.5 if confidence < 0.7 else 2.0)
        elif cycle_detected:
            dominance = f"Cycle (length {cycle_length})"
            last_pair_type = pair_sequence[-1]
            if last_pair_type == "Odd":
                pattern_prediction = "Player" if last_result == 'B' else "Banker"
            else:
                pattern_prediction = "Player" if last_result == 'P' else "Banker"
            bet_multiplier = math.ceil(1.2 + 0.3 * cycle_length)
        elif dominance_diff >= 4 and confidence > 0.5:
            if odd_count > even_count:
                dominance = "Odd"
                pattern_prediction = "Player" if last_result == 'B' else "Banker"
            else:
                dominance = "Even"
                pattern_prediction = "Player" if last_result == 'P' else "Banker"
            bet_multiplier = math.ceil(1.0 + confidence)
        else:
            dominance = "N/A"
            pattern_prediction = "Hold"
            bet_multiplier = 0.0
    else:
        dominance = "N/A"
        pattern_prediction = "N/A"
        bet_multiplier = 1.0

    final_prediction = pattern_prediction
    if pattern_prediction == "Hold":
        if bayesian_prediction in ['P', 'B'] and pattern_scores["Bayesian"] > 0.5:
            final_prediction = "Player" if bayesian_prediction == 'P' else "Banker"
            dominance = "Bayesian"
            bet_multiplier = 1.0
        elif markov_prediction in ['P', 'B'] and pattern_scores["Markov"] > 0.5:
            final_prediction = "Player" if markov_prediction == 'P' else "Banker"
            dominance = "Markov"
            bet_multiplier = 1.0
    elif pattern_prediction in ["Player", "Banker"]:
        markov_pred_equiv = "Player" if markov_prediction == 'P' else "Banker" if markov_prediction == 'B' else "Hold"
        bayesian_pred_equiv = "Player" if bayesian_prediction == 'P' else "Banker" if bayesian_prediction == 'B' else "Hold"
        if bayesian_pred_equiv in ["Player", "Banker"] and pattern_scores["Bayesian"] > confidence + 0.2 and pattern_scores["Bayesian"] > pattern_scores["Markov"]:
            final_prediction = bayesian_pred_equiv
            dominance = "Bayesian"
            bet_multiplier = 1.0
        elif markov_pred_equiv in ["Player", "Banker"] and pattern_scores["Markov"] > confidence + 0.2:
            final_prediction = markov_pred_equiv
            dominance = "Markov"
            bet_multiplier = 1.0

    if len(results) < 5:
        final_prediction = "Hold"
        dominance = "N/A"
        bet_multiplier = 0.0

    st.session_state.bet_amount = min(3 * st.session_state.base_amount, bet_multiplier * st.session_state.base_amount) if final_prediction in ["Player", "Banker"] else 0

    return pattern_scores, dominance, final_prediction, streak_type

def reset_betting():
    """Reset betting parameters and update prediction."""
    validate_pair_types()
    if st.session_state.result_tracker <= -10 * st.session_state.base_amount:
        st.session_state.alerts.append({"type": "warning", "message": "Stop-loss reached. Resetting to resume betting.", "id": str(uuid.uuid4())})
    if st.session_state.result_tracker >= 0:
        st.session_state.result_tracker = 0.0
    st.session_state.consecutive_wins = 0
    st.session_state.consecutive_losses = 0
    st.session_state.streak_type = None
    st.session_state.bet_amount = st.session_state.base_amount

    valid_pairs = [p for p in st.session_state.pair_types if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
    if len(valid_pairs) >= 5:
        recent_pairs = valid_pairs[-10:] if len(valid_pairs) >= 10 else valid_pairs
        odd_count = sum(1 for a, b in recent_pairs if a != b)
        even_count = sum(1 for a, b in recent_pairs if a == b)
        result = st.session_state.previous_result
        if abs(odd_count - even_count) < 2:
            st.session_state.current_dominance = "N/A"
            st.session_state.next_prediction = "Hold"
            st.session_state.bet_amount = 0.0
        elif odd_count > even_count:
            st.session_state.current_dominance = "Odd"
            st.session_state.next_prediction = "Player" if result == 'B' else "Banker"
            st.session_state.bet_amount = st.session_state.base_amount if abs(odd_count - even_count) < 3 else 2 * st.session_state.base_amount
        else:
            st.session_state.current_dominance = "Even"
            st.session_state.next_prediction = "Player" if result == 'P' else "Banker"
            st.session_state.bet_amount = st.session_state.base_amount if abs(odd_count - even_count) < 3 else 2 * st.session_state.base_amount
        last_four = [p[1] for p in valid_pairs[-4:] if isinstance(p, (tuple, list)) and len(p) > 1 and p[1] in ['P', 'B', 'T'] and p[1] != 'T']
        if len(last_four) >= 4 and all(r == last_four[0] for r in last_four):
            st.session_state.streak_type = last_four[0]
            st.session_state.next_prediction = "Player" if st.session_state.streak_type == 'P' else "Banker"
            st.session_state.current_dominance = f"Streak ({st.session_state.streak_type})"
            st.session_state.bet_amount = 2 * st.session_state.base_amount
    else:
        st.session_state.next_prediction = "N/A"
        st.session_state.current_dominance = "N/A"
        st.session_state.streak_type = None
        st.session_state.bet_amount = st.session_state.base_amount

    st.session_state.alerts.append({"type": "success", "message": "Betting reset.", "id": str(uuid.uuid4())})

def reset_all():
    """Reset all session data."""
    st.session_state.pair_types = deque(maxlen=100)
    st.session_state.results = deque(maxlen=200)
    st.session_state.result_tracker = 0.0
    st.session_state.profit_lock = 0.0
    st.session_state.bet_amount = 0.0
    st.session_state.base_amount = 10.0
    st.session_state.next_prediction = "N/A"
    st.session_state.previous_result = None
    st.session_state.state_history = []
    st.session_state.current_dominance = "N/A"
    st.session_state.consecutive_wins = 0
    st.session_state.consecutive_losses = 0
    st.session_state.streak_type = None
    st.session_state.stats = {
        'wins': 0,
        'losses': 0,
        'ties': 0,
        'streaks': [],
        'odd_pairs': 0,
        'even_pairs': 0,
        'alternating_pairs': 0,
        'bet_history': []
    }
    st.session_state.pattern_confidence = {"Odd": 0.0, "Even": 0.0, "Alternating": 0.0, "Streak": 0.0, "Choppy": 0.0, "Markov": 0.0, "Bayesian": 0.0}
    st.session_state.processing = False
    st.session_state.alerts.append({"type": "success", "message": "All session data reset, profit lock reset.", "id": str(uuid.uuid4())})

def record_result(result):
    """Record a game result and update state."""
    if st.session_state.processing:
        st.session_state.alerts.append({"type": "warning", "message": "Processing another action, please wait.", "id": str(uuid.uuid4())})
        return
    st.session_state.processing = True

    try:
        validate_pair_types()
        st.session_state.alerts.append({"type": "info", "message": f"Debug: pair_types before = {list(st.session_state.pair_types)}", "id": str(uuid.uuid4())})

        if not isinstance(st.session_state.stats, dict):
            st.session_state.stats = {
                'wins': 0,
                'losses': 0,
                'ties': 0,
                'streaks': [],
                'odd_pairs': 0,
                'even_pairs': 0,
                'alternating_pairs': 0,
                'bet_history': []
            }
        else:
            default_stats = {
                'wins': 0,
                'losses': 0,
                'ties': 0,
                'streaks': [],
                'odd_pairs': 0,
                'even_pairs': 0,
                'alternating_pairs': 0,
                'bet_history': []
            }
            for key, value in default_stats.items():
                if key not in st.session_state.stats or not isinstance(st.session_state.stats[key], type(value)):
                    st.session_state.stats[key] = value

        current_prediction = st.session_state.next_prediction
        st.session_state.results.append(result)

        state = {
            'pair_types': list(st.session_state.pair_types),
            'results': list(st.session_state.results),
            'previous_result': st.session_state.previous_result,
            'result_tracker': st.session_state.result_tracker,
            'profit_lock': st.session_state.profit_lock,
            'bet_amount': st.session_state.bet_amount,
            'current_dominance': st.session_state.current_dominance,
            'next_prediction': st.session_state.next_prediction,
            'consecutive_wins': st.session_state.consecutive_wins,
            'consecutive_losses': st.session_state.consecutive_losses,
            'streak_type': st.session_state.streak_type,
            'stats': st.session_state.stats.copy(),
            'pattern_confidence': st.session_state.pattern_confidence.copy()
        }
        st.session_state.state_history.append(state)

        if result == 'T':
            st.session_state.stats['ties'] = int(st.session_state.stats.get('ties', 0)) + 1
            st.session_state.previous_result = result
            st.session_state.bet_amount = 0
            st.session_state.alerts.append({"type": "info", "message": "Tie recorded. No bet placed.", "id": str(uuid.uuid4())})
            pattern_scores, dominance, prediction, streak_type = analyze_patterns()
            st.session_state.pattern_confidence = pattern_scores
            st.session_state.current_dominance = dominance
            st.session_state.next_prediction = prediction
            st.session_state.streak_type = streak_type
            st.session_state.processing = False
            return

        if st.session_state.previous_result is None:
            st.session_state.previous_result = result
            st.session_state.next_prediction = "N/A"
            st.session_state.bet_amount = 0
            st.session_state.alerts.append({"type": "info", "message": "Waiting for more results to start betting.", "id": str(uuid.uuid4())})
            pattern_scores, dominance, prediction, streak_type = analyze_patterns()
            st.session_state.pattern_confidence = pattern_scores
            st.session_state.current_dominance = dominance
            st.session_state.next_prediction = prediction
            st.session_state.streak_type = streak_type
            st.session_state.processing = False
            return

        if st.session_state.previous_result != 'T':
            pair = (st.session_state.previous_result, result)
            st.session_state.pair_types.append(pair)
            pair_type = "Even" if pair[0] == pair[1] else "Odd"
            st.session_state.stats['odd_pairs' if pair_type == "Odd" else 'even_pairs'] = int(st.session_state.stats.get('odd_pairs' if pair_type == "Odd" else 'even_pairs', 0)) + 1
            if len(st.session_state.pair_types) >= 2:
                last_two_pairs = [p for p in st.session_state.pair_types[-2:] if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
                if len(last_two_pairs) == 2 and last_two_pairs[0][1] != last_two_pairs[1][1]:
                    st.session_state.stats['alternating_pairs'] = int(st.session_state.stats.get('alternating_pairs', 0)) + 1

        try:
            last_four_pairs = [p for p in st.session_state.pair_types[-4:] if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
            last_four = [p[1] for p in last_four_pairs if p[1] != 'T']
            st.session_state.alerts.append({"type": "info", "message": f"Debug: pair_types after = {list(st.session_state.pair_types)}, last_four = {last_four}", "id": str(uuid.uuid4())})
        except Exception as e:
            st.session_state.alerts.append({"type": "error", "message": f"Error processing last_four_pairs: {str(e)}", "id": str(uuid.uuid4())})
            last_four_pairs = []
            last_four = []

        if len(last_four) >= 3 and all(r == result for r in last_four):
            st.session_state.streak_type = result
            st.session_state.stats['streaks'] = st.session_state.stats.get('streaks', []) + [len(last_four)]
        else:
            st.session_state.streak_type = None

        effective_bet = st.session_state.bet_amount if current_prediction in ["Player", "Banker"] else 0
        if effective_bet > 0:
            outcome = ""
            if current_prediction == "Player" and result == 'P':
                st.session_state.result_tracker += effective_bet
                st.session_state.stats['wins'] = int(st.session_state.stats.get('wins', 0)) + 1
                st.session_state.consecutive_wins = int(st.session_state.consecutive_wins) + 1
                st.session_state.consecutive_losses = 0
                st.session_state.bet_amount = st.session_state.base_amount
                outcome = f"Won ${effective_bet:.2f}"
                st.session_state.alerts.append({"type": "success", "message": f"Bet won! +${effective_bet:.2f}", "id": str(uuid.uuid4())})
            elif current_prediction == "Banker" and result == 'B':
                st.session_state.result_tracker += effective_bet * 0.95
                st.session_state.stats['wins'] = int(st.session_state.stats.get('wins', 0)) + 1
                st.session_state.consecutive_wins = int(st.session_state.consecutive_wins) + 1
                st.session_state.consecutive_losses = 0
                st.session_state.bet_amount = st.session_state.base_amount
                outcome = f"Won ${effective_bet * 0.95:.2f}"
                st.session_state.alerts.append({"type": "success", "message": f"Bet won! +${effective_bet * 0.95:.2f}", "id": str(uuid.uuid4())})
            elif current_prediction in ["Player", "Banker"]:
                st.session_state.result_tracker -= effective_bet
                st.session_state.stats['losses'] = int(st.session_state.stats.get('losses', 0)) + 1
                st.session_state.consecutive_losses = int(st.session_state.consecutive_losses) + 1
                st.session_state.consecutive_wins = 0
                st.session_state.bet_amount = min(3 * st.session_state.base_amount, math.ceil((st.session_state.bet_amount + 0.5 * st.session_state.base_amount) / st.session_state.base_amount) * st.session_state.base_amount)
                outcome = f"Lost ${effective_bet:.2f}"
                st.session_state.alerts.append({"type": "error", "message": f"Bet lost! -${effective_bet:.2f}", "id": str(uuid.uuid4())})

            st.session_state.stats['bet_history'] = st.session_state.stats.get('bet_history', []) + [{
                'prediction': current_prediction,
                'result': result,
                'bet_amount': effective_bet,
                'outcome': outcome
            }]

        if st.session_state.result_tracker >= 3 * st.session_state.base_amount:
            st.session_state.profit_lock += st.session_state.result_tracker
            st.session_state.result_tracker = 0.0
            st.session_state.bet_amount = st.session_state.base_amount
            st.session_state.alerts.append({"type": "info", "message": f"Profit of ${st.session_state.profit_lock:.2f} locked! Bankroll reset.", "id": str(uuid.uuid4())})
            pattern_scores, dominance, prediction, streak_type = analyze_patterns()
            st.session_state.pattern_confidence = pattern_scores
            st.session_state.current_dominance = dominance
            st.session_state.next_prediction = prediction
            st.session_state.streak_type = streak_type
            st.session_state.processing = False
            return
        elif st.session_state.result_tracker <= -10 * st.session_state.base_amount:
            st.session_state.alerts.append({"type": "warning", "message": "Loss limit reached. Resetting to resume betting.", "id": str(uuid.uuid4())})
            st.session_state.next_prediction = "Hold"
            st.session_state.bet_amount = 0.0
            pattern_scores, dominance, prediction, streak_type = analyze_patterns()
            st.session_state.pattern_confidence = pattern_scores
            st.session_state.current_dominance = dominance
            st.session_state.next_prediction = prediction
            st.session_state.streak_type = streak_type
            st.session_state.processing = False
            return

        pattern_scores, dominance, prediction, streak_type = analyze_patterns()
        st.session_state.pattern_confidence = pattern_scores
        st.session_state.current_dominance = dominance
        st.session_state.next_prediction = prediction
        st.session_state.streak_type = streak_type
        st.session_state.previous_result = result

    except Exception as e:
        st.error(f"Critical error in record_result: {str(e)}")
        st.session_state.alerts.append({"type": "error", "message": f"Critical error: {str(e)}", "id": str(uuid.uuid4())})
    finally:
        st.session_state.processing = False

def undo():
    """Undo the last action."""
    if st.session_state.processing:
        st.session_state.alerts.append({"type": "warning", "message": "Processing another action, please wait.", "id": str(uuid.uuid4())})
        return
    st.session_state.processing = True

    try:
        if not st.session_state.state_history:
            st.session_state.alerts.append({"type": "error", "message": "No actions to undo.", "id": str(uuid.uuid4())})
            st.session_state.processing = False
            return

        last_state = st.session_state.state_history.pop()
        valid_pairs = [p for p in last_state.get('pair_types', []) if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
        if len(valid_pairs) < len(last_state.get('pair_types', [])):
            st.session_state.alerts.append({"type": "warning", "message": "Invalid pairs found in state history; cleaned.", "id": str(uuid.uuid4())})
        st.session_state.pair_types = deque(valid_pairs, maxlen=100)
        st.session_state.results = deque(last_state.get('results', []), maxlen=200)
        st.session_state.previous_result = last_state.get('previous_result', None)
        st.session_state.result_tracker = last_state.get('result_tracker', 0.0)
        st.session_state.profit_lock = last_state.get('profit_lock', 0.0)
        st.session_state.bet_amount = last_state.get('bet_amount', 0.0)
        st.session_state.current_dominance = last_state.get('current_dominance', "N/A")
        st.session_state.next_prediction = last_state.get('next_prediction', "N/A")
        st.session_state.consecutive_wins = last_state.get('consecutive_wins', 0)
        st.session_state.consecutive_losses = last_state.get('consecutive_losses', 0)
        st.session_state.streak_type = last_state.get('streak_type', None)
        
        if not isinstance(last_state.get('stats', {}), dict):
            st.session_state.stats = {
                'wins': 0,
                'losses': 0,
                'ties': 0,
                'streaks': [],
                'odd_pairs': 0,
                'even_pairs': 0,
                'alternating_pairs': 0,
                'bet_history': []
            }
        else:
            st.session_state.stats = last_state['stats'].copy()
            default_stats = {
                'wins': 0,
                'losses': 0,
                'ties': 0,
                'streaks': [],
                'odd_pairs': 0,
                'even_pairs': 0,
                'alternating_pairs': 0,
                'bet_history': []
            }
            for key, value in default_stats.items():
                if key not in st.session_state.stats or not isinstance(st.session_state.stats[key], type(value)):
                    st.session_state.stats[key] = value
                elif key in ['wins', 'losses', 'ties', 'odd_pairs', 'even_pairs', 'alternating_pairs']:
                    st.session_state.stats[key] = int(st.session_state.stats[key])

        st.session_state.pattern_confidence = last_state.get('pattern_confidence', {"Odd": 0.0, "Even": 0.0, "Alternating": 0.0, "Streak": 0.0, "Choppy": 0.0, "Markov": 0.0, "Bayesian": 0.0})
        st.session_state.alerts.append({"type": "success", "message": "Last action undone.", "id": str(uuid.uuid4())})
    finally:
        st.session_state.processing = False

def simulate_games():
    """Simulate 100 games."""
    outcomes = ['P', 'B', 'T']
    weights = [0.446, 0.458, 0.096]
    for _ in range(100):
        result = random.choices(outcomes, weights)[0]
        record_result(result)
    st.session_state.alerts.append({"type": "success", "message": "Simulated 100 games. Check stats and bet history for results.", "id": str(uuid.uuid4())})

def simulate_choppy_games():
    """Simulate 100 games with choppy shoe characteristics."""
    outcomes = ['P', 'B', 'T']
    weights = [0.48, 0.48, 0.04]
    for _ in range(100):
        if random.random() < 0.8 and st.session_state.previous_result:
            result = 'B' if st.session_state.previous_result == 'P' else 'P'
        else:
            result = random.choices(outcomes, weights)[0]
        record_result(result)
    st.session_state.alerts.append({"type": "success", "message": "Simulated 100 choppy games.", "id": str(uuid.uuid4())})

def clear_alerts():
    """Clear all alerts."""
    st.session_state.alerts = []

def main():
    """Main Streamlit application."""
    initialize_session_state()
    st.session_state.alerts.append({"type": "info", "message": "Main function loaded successfully.", "id": str(uuid.uuid4())})

    css_html = """
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <style>
            body, .stApp {
                background-color: #1F2528;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                color: #E5E7EB;
            }
            .card {
                background-color: #2C2F33;
                border-radius: 0.75rem;
                padding: 1.5rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                margin-bottom: 1rem;
            }
            .stButton>button {
                background-color: #6366F1;
                color: white;
                border-radius: 0.5rem;
                padding: 0.75rem 1.5rem;
                font-weight: 600;
                transition: background-color 0.2s;
                width: 100%;
            }
            .stButton>button:hover {
                background-color: #4F46E5;
            }
            .stNumberInput input {
                background-color: #23272A;
                color: white;
                border: 1px solid #4B5563;
                border-radius: 0.5rem;
                padding: 0.5rem;
            }
            .stDataFrame table {
                background-color: #23272A;
                color: white;
                border-collapse: collapse;
            }
            .stDataFrame th {
                background-color: #374151;
                color: white;
                font-weight: 600;
                padding: 0.75rem;
            }
            .stDataFrame td {
                padding: 0.75rem;
                border-bottom: 1px solid #4B5563;
            }
            .stDataFrame tr:nth-child(even) {
                background-color: #2D3748;
            }
            h1 {
                font-size: 2.25rem;
                font-weight: 700;
                color: #F3F4F6;
                margin-bottom: 1rem;
            }
            h2 {
                font-size: 1.5rem;
                font-weight: 600;
                color: #D1D5DB;
                margin-bottom: 0.75rem;
            }
            .alert {
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
            }
            .alert-success {
                background-color: #10B981;
                color: white;
            }
            .alert-error {
                background-color: #EF4444;
                color: white;
            }
            .alert-info {
                background-color: #3B82F6;
                color: white;
            }
            .alert-warning {
                background-color: #F59E0B;
                color: white;
            }
            .sidebar .stButton>button {
                margin-bottom: 0.5rem;
            }
            .result-history {
                display: flex;
                flex-wrap: nowrap;
                overflow-x: auto;
                scroll-behavior: smooth;
                gap: 0.25rem;
                padding: 0.5rem;
                max-width: 100%;
            }
            .result-item {
                min-width: 2rem;
                height: 2rem;
                line-height: 2rem;
                text-align: center;
                border-radius: 0.25rem;
                font-size: 0.875rem;
                font-weight: bold;
                color: white;
            }
            .result-p {
                background-color: #3B82F6;
            }
            .result-b {
                background-color: #EF4444;
            }
            .result-t {
                background-color: #10B981;
            }
            .next-bet-badge {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                border-radius: 0.25rem;
                font-size: 0.875rem;
                font-weight: bold;
                text-align: center;
                min-width: 4rem;
            }
        </style>
    """
    st.markdown(css_html, unsafe_allow_html=True)

    alert_container = st.container()
    with alert_container:
        for alert in st.session_state.alerts[-3:]:
            alert_class = f"alert alert-{alert['type'].lower()}"
            st.markdown(f'<div class="{alert_class}">{alert["message"]}</div>', unsafe_allow_html=True)
        if st.session_state.alerts:
            if st.button("Clear Alerts", disabled=st.session_state.processing):
                clear_alerts()

    st.markdown('<h1>Baccarat Predictor with Balanced Progression</h1>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<h2>Controls</h2>', unsafe_allow_html=True)
        with st.expander("Bet Settings", expanded=True):
            st.number_input("Base Amount ($1-$100)", min_value=1.0, max_value=100.0, value=st.session_state.base_amount, step=1.0, key="base_amount_input")
            st.button("Set Amount", on_click=set_base_amount, disabled=st.session_state.processing)

        with st.expander("Session Actions"):
            st.button("Reset Bet", on_click=reset_betting, disabled=st.session_state.processing)
            st.button("Reset Session", on_click=reset_all, disabled=st.session_state.processing)
            st.button("New Session", on_click=lambda: [reset_all(), st.session_state.alerts.append({"type": "success", "message": "New session started.", "id": str(uuid.uuid4())})], disabled=st.session_state.processing)
            st.button("Simulate 100 Games", on_click=simulate_games, disabled=st.session_state.processing)
            st.button("Simulate 100 Choppy Games", on_click=simulate_choppy_games, disabled=st.session_state.processing)

    with st.container():
        st.markdown('<h2>Betting Overview</h2>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div class="card">
                    <p class="text-sm font-semibold text-gray-400">Bankroll</p>
                    <p class="text-xl font-bold text-white">${st.session_state.result_tracker:.2f}</p>
                </div>
                <div class="card">
                    <p class="text-sm font-semibold text-gray-400">Profit Lock</p>
                    <p class="text-xl font-bold text-white">${st.session_state.profit_lock:.2f}</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            badge_class = (
                "next-bet-badge bg-blue-500" if st.session_state.next_prediction == "Player" else
                "next-bet-badge bg-red-500" if st.session_state.next_prediction == "Banker" else
                "next-bet-badge bg-yellow-500" if st.session_state.next_prediction == "Hold" else
                "next-bet-badge bg-gray-500"
            )
            st.markdown(f"""
                <div class="card">
                    <p class="text-sm font-semibold text-gray-400">Next Bet</p>
                    <span class="{badge_class} text-white">{st.session_state.next_prediction}</span>
                </div>
                <div class="card">
                    <p class="text-sm font-semibold text-gray-400">Bet Amount</p>
                    <p class="text-xl font-bold text-white">{'No Bet' if st.session_state.bet_amount == 0 else f'${st.session_state.bet_amount:.2f}'}</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown('<h2>Result History</h2>', unsafe_allow_html=True)
        if st.session_state.results:
            recent_results = list(st.session_state.results)[-20:]
            result_items = [
                f'<span class="result-item result-{r.lower()}">{r}</span>'
                for r in recent_results
            ]
            result_html = "".join(result_items)
            st.markdown(f"""
                <div class="card">
                    <p class="text-sm font-semibold text-gray-400">Last 20 Results (P: Player, B: Banker, T: Tie)</p>
                    <div class="result-history" id="resultHistory">
                        {result_html}
                    </div>
                </div>
                <script>
                    document.addEventListener('DOMContentLoaded', function() {{
                        const resultDiv = document.getElementById('resultHistory');
                        if (resultDiv) {{
                            resultDiv.scrollLeft = resultDiv.scrollWidth;
                        }}
                    }});
                </script>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<p class="text-gray-400">No results yet.</p>', unsafe_allow_html=True)

        st.markdown('<h2>Record Result</h2>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.button("Player", on_click=lambda: record_result('P'), disabled=st.session_state.processing)
        with col2:
            st.button("Banker", on_click=lambda: record_result('B'), disabled=st.session_state.processing)
        with col3:
            st.button("Tie", on_click=lambda: record_result('T'), disabled=st.session_state.processing)
        with col4:
            st.button("Undo", on_click=undo, disabled=st.session_state.processing)

        st.markdown('<h2>Deal History</h2>', unsafe_allow_html=True)
        validate_pair_types()
        valid_pairs = [p for p in st.session_state.pair_types if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
        if valid_pairs:
            history_data = [
                {"Pair": f"{pair[0]}{pair[1]}", "Type": "Even" if pair[0] == pair[1] else "Odd"}
                for pair in valid_pairs
            ]
            st.dataframe(pd.DataFrame(history_data), use_container_width=True, height=300)
        else:
            st.markdown('<p class="text-gray-400">No history yet.</p>', unsafe_allow_html=True)

        total_games = st.session_state.stats.get('wins', 0) + st.session_state.stats.get('losses', 0)
        win_rate = (st.session_state.stats.get('wins', 0) / total_games * 100) if total_games > 0 else 0
        avg_streak = sum(st.session_state.stats.get('streaks', [])) / len(st.session_state.stats.get('streaks', [])) if st.session_state.stats.get('streaks', []) else 0
        recent_pairs = valid_pairs[-10:] if len(valid_pairs) >= 10 else valid_pairs
        alternation_rate = sum(1 for i in range(len(recent_pairs)-1) if recent_pairs[i][1] != recent_pairs[i+1][1]) / (len(recent_pairs)-1) if len(recent_pairs) > 1 else 0
        st.markdown(f"""
            <div class="card">
                <p class="text-sm font-semibold text-gray-400">Statistics</p>
                <p class="text-base text-white">Win Rate: {win_rate:.1f}%</p>
                <p class="text-base text-white">Avg Streak: {avg_streak:.1f}</p>
                <p class="text-base text-white">Alternation Rate: {alternation_rate:.2f}</p>
                <p class="text-base text-white">Patterns: Odd: {st.session_state.stats.get('odd_pairs', 0)}, Even: {st.session_state.stats.get('even_pairs', 0)}, Alternating: {st.session_state.stats.get('alternating_pairs', 0)}</p>
                <p class="text-base text-white">Streak: {st.session_state.streak_type if st.session_state.streak_type else 'None'}</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<h2>Pattern Confidence</h2>', unsafe_allow_html=True)
        chart_config = {
            "type": "line",
            "data": {
                "labels": ["Odd", "Even", "Alternating", "Streak", "Choppy", "Markov", "Bayesian"],
                "datasets": [
                    {
                        "label": "Pattern Confidence",
                        "data": [
                            st.session_state.pattern_confidence.get("Odd", 0.0),
                            st.session_state.pattern_confidence.get("Even", 0.0),
                            st.session_state.pattern_confidence.get("Alternating", 0.0),
                            st.session_state.pattern_confidence.get("Streak", 0.0),
                            st.session_state.pattern_confidence.get("Choppy", 0.0),
                            st.session_state.pattern_confidence.get("Markov", 0.0),
                            st.session_state.pattern_confidence.get("Bayesian", 0.0)
                        ],
                        "borderColor": "#10B981",
                        "backgroundColor": "rgba(16, 185, 129, 0.2)",
                        "fill": True,
                        "tension": 0.4
                    }
                ]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": True, "labels": {"color": "#E5E7EB"}},
                    "title": {"display": True, "text": "Pattern Confidence Scores", "color": "#E5E7EB"}
                },
                "scales": {
                    "x": {"ticks": {"color": "#E5E7EB"}, "grid": {"color": "#4B5563"}},
                    "y": {
                        "beginAtZero": True,
                        "max": 1,
                        "ticks": {"color": "#E5E7EB"},
                        "grid": {"color": "#4B5563"}
                    }
                }
            }
        }
        
        chart_json = json.dumps(chart_config, ensure_ascii=True).replace('"', '"')
        st.markdown(f"""
            <div class="card">
                <canvas id="patternChart"></canvas>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    const ctx = document.getElementById('patternChart').getContext('2d');
                    new Chart(ctx, {chart_json});
                }});
            </script>
        """, unsafe_allow_html=True)

        st.markdown('<h2>Bet History</h2>', unsafe_allow_html=True)
        if st.session_state.stats.get('bet_history', []):
            bet_history = pd.DataFrame(st.session_state.stats.get('bet_history', []))
            st.dataframe(bet_history, use_container_width=True, height=200)
        else:
            st.markdown('<p class="text-gray-400">No bets placed yet.</p>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
