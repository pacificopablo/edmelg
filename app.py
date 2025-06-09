import streamlit as st
import random
import pandas as pd
import uuid
import numpy as np
import math
from collections import deque

def initialize_session_state():
    """Initialize session state variables with proper types and defaults."""
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
    if 'state_history' not in st.session_state or not isinstance(st.session_state.state_history, deque):
        st.session_state.state_history = deque(maxlen=100)
    else:
        valid_history = []
        for state in st.session_state.state_history:
            if isinstance(state, dict) and 'pair_types' in state:
                valid_pairs = [p for p in state['pair_types'] if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
                state['pair_types'] = valid_pairs
                valid_history.append(state)
        if len(valid_history) < len(st.session_state.state_history):
            add_alert("warning", f"Cleaned {len(st.session_state.state_history) - len(valid_history)} invalid state_history entries.")
        st.session_state.state_history = deque(valid_history, maxlen=100)
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
            elif key in ['wins', 'losses', 'ties', 'odd_pairs', 'even_pairs', 'alternating_pairs']:
                st.session_state.stats[key] = int(st.session_state.stats[key])
    if 'pattern_confidence' not in st.session_state:
        st.session_state.pattern_confidence = {"Odd": 0.0, "Even": 0.0, "Alternating": 0.0, "Streak": 0.0, "Choppy": 0.0, "Markov": 0.0, "Bayesian": 0.0}
    if 'alerts' not in st.session_state:
        st.session_state.alerts = deque(maxlen=50)
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'debug' not in st.session_state:
        st.session_state.debug = False
    add_debug_alert(f"Initialized session state: pair_types={type(st.session_state.pair_types).__name__}, "
                    f"results={type(st.session_state.results).__name__}, "
                    f"state_history={type(st.session_state.state_history).__name__}, "
                    f"stats={type(st.session_state.stats).__name__}")

def add_alert(alert_type, message):
    """Add an alert to the session state with the specified type and message."""
    st.session_state.alerts.append({"type": alert_type, "message": message, "id": str(uuid.uuid4())})

def add_debug_alert(message):
    """Add a debug alert if debug mode is enabled."""
    if st.session_state.debug:
        add_alert("info", f"DEBUG: {message}")

def validate_pair_types():
    """Validate and fix pair_types if invalid, preserving valid data."""
    if not isinstance(st.session_state.pair_types, deque):
        add_alert("error", f"pair_types invalid (type: {type(st.session_state.pair_types).__name__}); reinitialized.")
        st.session_state.pair_types = deque(maxlen=100)
        return False
    try:
        valid_pairs = [p for p in st.session_state.pair_types if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
        if len(valid_pairs) < len(st.session_state.pair_types):
            add_alert("warning", f"Removed {len(st.session_state.pair_types) - len(valid_pairs)} invalid pairs from pair_types.")
            st.session_state.pair_types = deque(valid_pairs, maxlen=100)
            return False
        return True
    except Exception as e:
        add_alert("error", f"Error validating pair_types: {str(e)}; reinitialized.")
        st.session_state.pair_types = deque(maxlen=100)
        return False

def set_base_amount():
    """Set the base amount from user input."""
    if st.session_state.processing:
        add_alert("warning", "Processing another action, please wait.")
        return
    try:
        amount = float(st.session_state.base_amount_input)
        if 1 <= amount <= 100:
            st.session_state.base_amount = round(amount, 2)
            st.session_state.bet_amount = round(st.session_state.base_amount, 2) if st.session_state.next_prediction in ["Player", "Banker"] else 0.0
            add_alert("success", "Base amount updated successfully.")
        else:
            add_alert("error", "Invalid base amount. Must be between $1 and $100.")
    except Exception as e:
        add_alert("error", f"Error setting base amount: {str(e)}")

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
        current, next_state = results[i], results[i + 1]
        if current in transitions and next_state in transitions[current]:
            transitions[current][next_state] += 1
    
    posterior_probs = {'P': {}, 'B': {}, 'T': {}}
    for state in transitions:
        total_counts = sum(transitions[state].values())
        total_alpha = sum(prior_params[state].values()) * alpha
        for next_state in transitions[state]:
            count = transitions[state][next_state]
            prior = prior_params[state][next_state] * alpha
            posterior_probs[state][next_state] = (count + prior) / (total_counts + total_alpha)
    
    return posterior_probs

def analyze_patterns():
    """Analyze patterns, Markov, and Bayesian probabilities to determine dominant strategy and bet amount."""
    if not validate_pair_types():
        add_debug_alert("pair_types validated and cleaned in analyze_patterns.")
    results = list(st.session_state.results)
    valid_pairs = [p for p in st.session_state.pair_types if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
    if len(valid_pairs) < 2:
        st.session_state.bet_amount = 0.0
        return {"Odd": 0.0, "Even": 0.0, "Alternating": 0.0, "Streak": 0.0, "Choppy": 0.0, "Markov": 0.0, "Bayesian": 0.0}, "N/A", "N/A", None

    recent_pairs = valid_pairs[-10:] if len(valid_pairs) >= 10 else valid_pairs
    alternation_rate = sum(1 for i in range(len(recent_pairs)-1) if recent_pairs[i][1] != recent_pairs[i+1][1]) / (len(recent_pairs)-1) if len(recent_pairs) > 1 else 0
    window_sizes = [3, 5, 8] if alternation_rate > 0.7 else [5, 10, 8]

    pattern_scores = {"Odd": 0.0, "Even": 0.0, "Alternating": 0.0, "Streak": 0.0, "Choppy": 0.0, "Markov": 0.0, "Bayesian": 0.0}
    total_weight = 0.0

    for window in window_sizes:
        if len(valid_pairs) >= window:
            recent_pairs_window = valid_pairs[-window:]
            recent_results = results[-window-1:] if len(results) >= window+1 else results

            odd_count = sum(1 for a, b in recent_pairs_window if a != b)
            even_count = sum(1 for a, b in recent_pairs_window if a == b)
            total_pairs = odd_count + even_count
            odd_score = (odd_count / total_pairs) * (window / 20) if total_pairs > 0 else 0.0
            even_score = (even_count / total_pairs) * (window / 20) if total_pairs > 0 else 0.0
            pattern_scores["Odd"] += odd_score
            pattern_scores["Even"] += even_score
            total_weight += window / 20

            alternating_count = sum(1 for i in range(len(recent_pairs_window)-1) if recent_pairs_window[i][1] != recent_pairs_window[i+1][1])
            alternating_score = (alternating_count / (window-1)) * (window / 20) if window > 1 else 0.0
            pattern_scores["Alternating"] += alternating_score

            streak_length = 1
            current_streak = recent_results[-1] if recent_results else None
            for i in range(2, len(recent_results)+1):
                if recent_results[-i] == current_streak and recent_results[-i] != 'T':
                    streak_length += 1
                else:
                    break
            streak_score = (streak_length / 5) * (window / 20) if streak_length >= 2 else 0.0
            pattern_scores["Streak"] += streak_score

            choppy_count = sum(1 for i in range(len(recent_results)-1) if recent_results[i] != recent_results[i+1] and recent_results[i] != 'T' and recent_results[i+1] != 'T')
            choppy_score = (choppy_count / (window-1)) * (window / 20) if window > 1 else 0.0
            pattern_scores["Choppy"] += choppy_score

    if total_weight > 0:
        for pattern in ['Odd', 'Even', 'Alternating', 'Streak', 'Choppy']:
            pattern_scores[pattern] /= total_weight

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
        if len(last_four) >= 3 and all(r == last_four[0] for r in last_four):
            streak_type = last_four[0]
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

    st.session_state.bet_amount = round(min(3 * st.session_state.base_amount, bet_multiplier * st.session_state.base_amount), 2) if final_prediction in ["Player", "Banker"] else 0.0

    return pattern_scores, dominance, final_prediction, streak_type

def reset_betting():
    """Reset betting parameters and update prediction."""
    if st.session_state.processing:
        add_alert("warning", "Processing another action, please wait.")
        return
    if not validate_pair_types():
        add_debug_alert("pair_types validated and cleaned in reset_betting.")
    if st.session_state.result_tracker <= -10 * st.session_state.base_amount:
        add_alert("warning", "Stop-loss reached. Resetting to resume betting.")
    if st.session_state.result_tracker >= 0:
        st.session_state.result_tracker = 0.0
    st.session_state.consecutive_wins = 0
    st.session_state.consecutive_losses = 0
    st.session_state.streak_type = None
    pattern_scores, dominance, prediction, streak_type = analyze_patterns()
    st.session_state.pattern_confidence = pattern_scores
    st.session_state.current_dominance = dominance
    st.session_state.next_prediction = prediction
    st.session_state.streak_type = streak_type
    add_alert("success", "Betting reset.")

def reset_all():
    """Reset all session data."""
    if st.session_state.processing:
        add_alert("warning", "Processing another action, please wait.")
        return
    st.session_state.pair_types = deque(maxlen=100)
    st.session_state.results = deque(maxlen=200)
    st.session_state.result_tracker = 0.0
    st.session_state.profit_lock = 0.0
    st.session_state.bet_amount = 0.0
    st.session_state.base_amount = 10.0
    st.session_state.next_prediction = "N/A"
    st.session_state.previous_result = None
    st.session_state.state_history = deque(maxlen=100)
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
    st.session_state.alerts = deque(maxlen=50)
    add_alert("success", "All session data reset successfully.")

def record_result(result):
    """Record a game result and update state."""
    if st.session_state.processing:
        add_alert("warning", "Processing another action, please wait.")
        return
    if result not in ['P elf.session_state.processing = True

    try:
        if not validate_pair_types():
            add_debug_alert(f"pair_types validated and cleaned in record_result. Initial state: {list(st.session_state.pair_types)}")

        add_debug_alert(f"pair_types before = {list(st.session_state.pair_types)}, type: {type(st.session_state.pair_types).__name__}")

        current_prediction = st.session_state.next_prediction
        st.session_state.results.append(result)

        valid_pairs = [p for p in st.session_state.pair_types if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
        state = {
            'pair_types': valid_pairs,
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
        add_debug_alert(f"state_history length = {len(st.session_state.state_history)}")

        if result == 'T':
            st.session_state.stats['ties'] = int(st.session_state.stats.get('ties', 0)) + 1
            st.session_state.previous_result = result
            st.session_state.bet_amount = 0.0
            add_alert("info", "Tie recorded!")
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
            st.session_state.bet_amount = 0.0
            add_alert("info", "Waiting for more results to start betting.")
            pattern_scores, dominance, prediction, streak_type = analyze_patterns()
            st.session_state.pattern_confidence = pattern_scores
            st.session_state.current_dominance = dominance
            st.session_state.next_prediction = prediction
            st.session_state.streak_type = streak_type
            st.session_state.processing = False
            return

        if st.session_state.previous_result != 'T':
            pair = (st.session_state.previous_result, result)
            try:
                st.session_state.pair_types.append(pair)
                pair_type = "Even" if pair[0] == pair[1] else "Odd"
                st.session_state.stats['odd_pairs' if pair_type == 'Odd' else 'even_pairs'] = int(
                    st.session_state.stats.get('odd_pairs' if pair_type == 'Odd' else 'even_pairs', 0)) + 1
                if len(st.session_state.pair_types) >= 2:
                    last_two_pairs = [p for p in st.session_state.pair_types[-2:] if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
                    if len(last_two_pairs) == 2 and last_two_pairs[0][1] != last_two_pairs[1][1]:
                        st.session_state.stats['alternating_pairs'] = int(st.session_state.stats.get('alternating_pairs', 0)) + 1
            except Exception as e:
                add_alert("error", f"Error appending pair {pair}: {str(e)}")
                validate_pair_types()

        try:
            add_debug_alert(f"About to access pair_types[-4:], current state: {list(st.session_state.pair_types)}")
            last_four_pairs = [p for p in st.session_state.pair_types[-4:] if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
            last_four = [p[1] for p in last_four_pairs if p[1] != 'T']
            add_debug_alert(f"pair_types after = {list(st.session_state.pair_types)}, last_four = {last_four}")
        except Exception as e:
            add_alert("error", f"Error processing last four pairs: {str(e)}")
            last_four = []

        if len(last_four) >= 3 and all(r == last_four[0] for r in last_four):
            st.session_state.streak_type = result
            st.session_state.stats['streaks'].append(len(last_four))
        else:
            st.session_state.streak_type = None

        effective_bet = st.session_state.bet_amount if current_prediction in ["Player", "Banker"] else 0.0
        outcome = ""
        if effective_bet > 0:
            if current_prediction == "Player" and result == 'P':
                st.session_state.result_tracker += round(effective_bet, 2)
                st.session_state.stats['wins'] = int(st.session_state.stats.get('wins', 0)) + 1
                st.session_state.consecutive_wins += 1
                st.session_state.consecutive_losses = 0
                st.session_state.bet_amount = round(st.session_state.base_amount, 2)
                outcome = f"Won ${effective_bet:.2f}"
                add_alert("success", f"Bet won! +${effective_bet:.2f}")
            elif current_prediction == "Banker" and result == 'B':
                st.session_state.result_tracker += round(effective_bet * 0.95, 2)
                st.session_state.stats['wins'] = int(st.session_state.stats.get('wins', 0)) + 1
                st.session_state.consecutive_wins += 1
                st.session_state.consecutive_losses = 0
                st.session_state.bet_amount = round(st.session_state.base_amount, 2)
                outcome = f"Won ${effective_bet * 0.95:.2f}"
                add_alert("success", f"Bet won! +${effective_bet * 0.95:.2f}")
            elif current_prediction in ["Player", "Banker"]:
                st.session_state.result_tracker -= round(effective_bet, 2)
                st.session_state.stats['losses'] = int(st.session_state.stats.get('losses', 0)) + 1
                st.session_state.consecutive_losses += 1
                st.session_state.consecutive_wins = 0
                st.session_state.bet_amount = round(min(3 * st.session_state.base_amount, math.ceil((st.session_state.bet_amount + 0.5 * st.session_state.base_amount) / st.session_state.base_amount) * st.session_state.base_amount), 2)
                outcome = f"Lost ${effective_bet:.2f}"
                add_alert("error", f"Bet lost! -${effective_bet:.2f}")

        st.session_state.stats['bet_history'].append({
            'prediction': current_prediction,
            'result': result,
            'bet_amount': effective_bet,
            'outcome': outcome
        })

        if st.session_state.result_tracker >= 3 * st.session_state.base_amount:
            st.session_state.profit_lock += st.session_state.result_tracker
            st.session_state.result_tracker = 0.0
            st.session_state.bet_amount = round(st.session_state.base_amount, 2)
            add_alert("info", f"Profit locked at ${st.session_state.profit_lock:.2f}! Bankroll reset.")
            pattern_scores, dominance, prediction, streak_type = analyze_patterns()
            st.session_state.pattern_confidence = pattern_scores
            st.session_state.current_dominance = dominance
            st.session_state.next_prediction = prediction
            st.session_state.streak_type = streak_type
            st.session_state.processing = False
            return
        elif st.session_state.result_tracker <= -10 * st.session_state.base_amount:
            add_alert("warning", "Loss limit reached. Resetting to resume betting.")
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
        add_alert("error", f"Critical error in record_result: {str(e)}")
    finally:
        st.session_state.processing = False

def undo():
    """Undo the last action."""
    if st.session_state.processing:
        add_alert("warning", "Processing another action, please wait.")
        return
    st.session_state.processing = True

    try:
        if not st.session_state.state_history:
            add_alert("error", "No actions to undo.")
            st.session_state.processing = False
            return

        add_debug_alert(f"Undoing state, history length = {len(st.session_state.state_history)}")

        last_state = st.session_state.state_history.pop()
        valid_pairs = [p for p in last_state.get('pair_types', []) if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
        if len(valid_pairs) < len(last_state.get('pair_types', [])):
            add_alert("warning", f"Invalid pairs found in state history; cleaned. Restored pairs: {valid_pairs}")

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

        add_debug_alert(f"Restored pair_types: {list(st.session_state.pair_types)}")

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
        add_alert("success", "Last action undone.")

    finally:
        st.session_state.processing = False

def simulate_games():
    """Simulate 100 games."""
    if st.session_state.processing:
        add_alert("warning", "Processing another action, please wait.")
        return
    try:
        outcomes = ['P', 'B', 'T']
        weights = [0.446, 0.458, 0.096]
        for _ in range(100):
            result = random.choices(outcomes, weights)[0]
            record_result(result)
        add_alert("success", "Simulated 100 games. Check stats and bet history for results.")
    except Exception as e:
        add_alert("error", f"Error simulating 100 games: {str(e)}")

def simulate_choppy_games():
    """Simulate 90 games with choppy shoe characteristics."""
    if st.session_state.processing:
        add_alert("warning", "Processing another action, please wait.")
        return
    try:
        outcomes = ['P', 'B', 'T']
        weights = [0.48, 0.48, 0.04]
        for _ in range(90):
            if random.random() < 0.8 and st.session_state.previous_result:
                result = 'P' if st.session_state.previous_result == 'B' else 'B'
            else:
                result = random.choices(outcomes, weights)[0]
            record_result(result)
        add_alert("success", "Simulated 90 choppy games.")
    except Exception as e:
        add_alert("error", f"Error simulating 90 choppy games: {str(e)}")

def clear_alerts():
    """Clear all alerts."""
    if st.session_state.processing:
        add_alert("warning", "Processing another action, please wait.")
        return
    st.session_state.alerts = deque(maxlen=50)

def main():
    """Main Streamlit application."""
    initialize_session_state()
    add_alert("success", "Application initialized successfully.")

    css_styles = """
    <style>
        body, .stApp {
            background-color: #1f2528;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #e5e7eb;
        }
        .card {
            background-color: #2c2f33;
            border-radius: 0.75rem;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        }
        .stButton>button {
            background-color: #6366f1;
            color: white;
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
            font-weight: 600;
            transition: background-color 0.2s;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #4f46e5;
        }
        .stNumberInput input {
            background-color: #23272a;
            color: white;
            border: 1px solid #4b5563;
            border-radius: 0.25rem;
            padding: 0.5rem;
        }
        .stDataFrame {
            background-color: #23272a;
            color: white;
            border-collapse: collapse;
        }
        .stDataFrame th {
            background-color: #374151;
            color: white;
            font-weight: bold;
            padding: 0.75rem;
        }
        .stDataFrame td {
            padding: 0.75rem;
            border-bottom: 1px solid #4b5563;
        }
        .stDataFrame tr:nth-child(even) {
            background-color: #2d3748;
        }
        h1 {
            font-size: 2.25rem;
            font-weight: bold;
            color: #f3f4f6;
            margin-bottom: 1rem;
        }
        h2 {
            font-size: 1.5rem;
            font-weight: bold;
            color: #d1d5db;
            margin-bottom: 0.75rem;
        }
        .alert {
            padding: 0.75rem;
            border-radius: 0.25rem;
            margin-bottom: 0.75rem;
        }
        .alert-success {
            background-color: #10b981;
            color: white;
        }
        .alert-error {
            background-color: #ef4444;
            color: white;
        }
        .alert-info {
            background-color: #3b82f6;
            color: white;
        }
        .alert-warning {
            background-color: #f59e0b;
            color: white;
        }
        .result-history {
            display: flex;
            flex-wrap: nowrap;
            overflow-x: auto;
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
            background-color: #3b82f6;
        }
        .result-b {
            background-color: #ef4444;
        }
        .result-t {
            background-color: #10b981;
        }
        .next-bet {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            font-weight: bold;
            text-align: center;
            min-width: 4rem;
        }
        .next-bet-player {
            background-color: #3b82f6;
            color: white;
        }
        .next-bet-banker {
            background-color: #ef4444;
            color: white;
        }
        .next-bet-hold {
            background-color: #6b7280;
            color: white;
        }
    </style>
    """
    st.markdown(css_styles, unsafe_allow_html=True)

    alert_container = st.container()
    with alert_container:
        for alert in list(st.session_state.alerts)[-5:]:
            alert_class = f"alert alert-{alert['type'].lower()}"
            st.markdown(f'<div class="{alert_class}">{alert["message"]}</div>', unsafe_allow_html=True)
        if st.session_state.alerts:
            st.button("Clear Alerts", on_click=clear_alerts, disabled=st.session_state.processing)

    st.markdown("<h1>Baccarat Predictor</h1>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("<h2>Controls</h2>", unsafe_allow_html=True)
        with st.expander("Bet Settings", expanded=True):
            st.number_input("Base Amount ($1-$100)", min_value=1.0, max_value=100.0, value=st.session_state.base_amount, step=1.0, key="base_amount_input")
            st.button("Set Amount", on_click=set_base_amount, disabled=st.session_state.processing)
        with st.expander("Record Result", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.button("Player (P)", on_click=lambda: record_result('P'), disabled=st.session_state.processing)
            with col2:
                st.button("Banker (B)", on_click=lambda: record_result('B'), disabled=st.session_state.processing)
            with col3:
                st.button("Tie (T)", on_click=lambda: record_result('T'), disabled=st.session_state.processing)
            st.button("Undo Last Result", on_click=undo, disabled=st.session_state.processing)
        with st.expander("Session Actions", expanded=False):
            st.button("Reset Bet", on_click=reset_betting, disabled=st.session_state.processing)
            st.button("Reset Session", on_click=reset_all, disabled=st.session_state.processing)
            st.button("New Session", on_click=lambda: [reset_all(), add_alert("success", "New session started.")], disabled=st.session_state.processing)
            st.button("Simulate 100 Games", on_click=simulate_games, disabled=st.session_state.processing)
            st.button("Simulate 90 Choppy Games", on_click=simulate_choppy_games, disabled=st.session_state.processing)
        with st.expander("Debug", expanded=False):
            st.checkbox("Enable Debug Alerts", value=st.session_state.debug, key="debug_toggle", on_change=lambda: setattr(st.session_state, 'debug', st.session_state.debug_toggle))

    with st.container():
        st.markdown("<h2>Statistics</h2>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div class="card">
                    <p class="text-sm font-semibold text-gray-400">Bankroll</p>
                    <p class="text-xl font-bold text-white">${st.session_state.result_tracker:.2f}</p>
                </div>
                <div class="card">
                    <p class="text-sm font-semibold text-gray-400">Profit Locked</p>
                    <p class="text-xl font-bold text-white">${st.session_state.profit_lock:.2f}</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="card">
                    <p class="text-sm font-semibold text-gray-400">Next Bet</p>
                    <div class="next-bet next-bet-{'player' if st.session_state.next_prediction == 'Player' else 'banker' if st.session_state.next_prediction == 'Banker' else 'hold'}">
                        {st.session_state.next_prediction} ${st.session_state.bet_amount:.2f}
                    </div>
                </div>
                <div class="card">
                    <p class="text-sm font-semibold text-gray-400">Dominant Pattern</p>
                    <p class="text-xl font-bold text-white">{st.session_state.current_dominance}</p>
                </div>
            """, unsafe_allow_html=True)

    with st.container():
        st.markdown("<h2>Result History</h2>", unsafe_allow_html=True)
        if st.session_state.results:
            result_html = '<div class="result-history">'
            for result in list(st.session_state.results)[-20:]:
                result_class = {'P': 'result-p', 'B': 'result-b', 'T': 'result-t'}[result]
                result_label = {'P': 'Player', 'B': 'Banker', 'T': 'Tie'}[result]
                result_html += f'<div class="result-item {result_class}" title="{result_label}">{result}</div>'
            result_html += '</div>'
            st.markdown(result_html, unsafe_allow_html=True)
        else:
            st.markdown("<p>No results recorded yet.</p>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<h2>Pattern Confidence</h2>", unsafe_allow_html=True)
        confidence_data = pd.DataFrame({
            'Pattern': list(st.session_state.pattern_confidence.keys()),
            'Confidence': [f"{v:.2%}" for v in st.session_state.pattern_confidence.values()]
        })
        st.dataframe(confidence_data, use_container_width=True, hide_index=True)

        # Generate a bar chart for pattern confidence
        chart_data = {
            "type": "bar",
            "data": {
                "labels": list(st.session_state.pattern_confidence.keys()),
                "datasets": [{
                    "label": "Pattern Confidence",
                    "data": [v * 100 for v in st.session_state.pattern_confidence.values()],
                    "backgroundColor": [
                        "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#f97316"
                    ],
                    "borderColor": [
                        "#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed", "#db2777", "#ea580c"
                    ],
                    "borderWidth": 1
                }]
            },
            "options": {
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "title": {"display": True, "text": "Confidence (%)"}
                    },
                    "x": {
                        "title": {"display": True, "text": "Pattern"}
                    }
                },
                "plugins": {
                    "legend": {"display": False}
                }
            }
        }
        st.markdown("### Confidence Distribution")
        st.chart(chart_data)

    with st.container():
        st.markdown("<h2>Bet History</h2>", unsafe_allow_html=True)
        if st.session_state.stats['bet_history']:
            bet_history = pd.DataFrame(st.session_state.stats['bet_history'])
            bet_history = bet_history[['prediction', 'result', 'bet_amount', 'outcome']].tail(10)
            st.dataframe(bet_history, use_container_width=True)
        else:
            st.markdown("<p>No bets placed yet.</p>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<h2>Summary Statistics</h2>", unsafe_allow_html=True)
        stats_data = {
            'Metric': ['Wins', 'Losses', 'Ties', 'Odd Pairs', 'Even Pairs', 'Alternating Pairs'],
            'Value': [
                st.session_state.stats['wins'],
                st.session_state.stats['losses'],
                st.session_state.stats['ties'],
                st.session_state.stats['odd_pairs'],
                st.session_state.stats['even_pairs'],
                st.session_state.stats['alternating_pairs']
            ]
        }
        st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
