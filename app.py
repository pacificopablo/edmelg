
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
    if 'state_history' not in st.session_state or not isinstance(st.session_state.state_history, list):
        st.session_state.state_history = []
    else:
        # Validate state_history entries
        valid_history = []
        for state in st.session_state.state_history:
            if isinstance(state, dict) and 'pair_types' in state:
                valid_pairs = [p for p in state['pair_types'] if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
                state['pair_types'] = valid_pairs
                valid_history.append(state)
        if len(valid_history) < len(st.session_state.state_history):
            st.session_state.alerts.append({"type": "warning", "message": f"Cleaned {len(st.session_state.state_history) - len(valid_history)} invalid state_history entries.", "id": str(uuid.uuid4())})
        st.session_state.state_history = valid_history
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
    # Log initial state types for debugging
    st.session_state.alerts.append({
        "type": "info",
        "message": f"Initialized session state: pair_types={type(st.session_state.pair_types).__name__}, "
                   f"results={type(st.session_state.results).__name__}, "
                   f"state_history={type(st.session_state.state_history).__name__}, "
                   f"stats={type(st.session_state.stats).__name__}",
        "id": str(uuid.uuid4())
    })

def validate_pair_types():
    """Validate and fix pair_types if invalid."""
    if st.session_state.pair_types is None or not isinstance(st.session_state.pair_types, deque):
        st.session_state.alerts.append({"type": "error", "message": f"pair_types invalid (type: {type(st.session_state.pair_types).__name__}); reinitialized.", "id": str(uuid.uuid4())})
        st.session_state.pair_types = deque(maxlen=100)
        return False
    try:
        valid_pairs = [p for p in st.session_state.pair_types if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
        if len(valid_pairs) < len(st.session_state.pair_types):
            st.session_state.alerts.append({"type": "warning", "message": f"Found {len(st.session_state.pair_types) - len(valid_pairs)} invalid pairs in pair_types; cleaned.", "id": str(uuid.uuid4())})
            st.session_state.pair_types = deque(valid_pairs, maxlen=100)
            return False
        return True
    except Exception as e:
        st.session_state.alerts.append({"type": "error", "message": f"Error validating pair_types: {str(e)}; reinitialized.", "id": str(uuid.uuid4())})
        st.session_state.pair_types = deque(maxlen=100)
        return False

def set_base_amount():
    """Set the base amount from user input."""
    if st.session_state.processing:
        st.session_state.alerts.append({"type": "warning", "message": "Processing another action, please wait.", "id": str(uuid.uuid4())})
        return
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
        st.session_state.alerts.append({"type": "info", "message": "pair_types validated and cleaned in analyze_patterns.", "id": str(uuid.uuid4())})
    results = list(st.session_state.results)
    valid_pairs = [p for p in st.session_state.pair_types if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
    if len(valid_pairs) < 2:
        st.session_state.bet_amount = 0
        return {"Odd": 0.0, "Even": 0.0, "Alternating": 0.0, "Streak": 0.0, "Choppy": 0.0, "Markov": 0.0, "Bayesian": 0.0}, "consecutive_wins = st.session_state.consecutive_wins
    st.session_state.consecutive_losses = 0
    st.session_state.bet_amount = 0.0
    pattern_scores, dominance, prediction, streak_type = analyze_patterns()
    st.session_state.pattern_confidence = pattern_scores
    st.session_state.current_dominance = dominance
    st.session_state.next_prediction = prediction
    st.session_state.streak_type = streak_type
    st.session_state.processing = False
    return

def reset_betting():
    """Reset betting parameters and update prediction."""
    if st.session_state.processing:
        st.session_state.alerts.append({"type": "warning", "message": "Processing another action, please wait.", "id": str(uuid.uuid4())})
        return
    if not validate_pair_types():
        st.session_state.alerts.append({"type": "info", "message": "pair_types validated and cleaned in reset_betting.", "id": str(uuid.uuid4())})
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
    if st.session_state.processing:
        st.session_state.alerts.append({"type": "warning", "message": "Processing another action, please wait.", "id": str(uuid.uuid4())})
        return
    st.session_state.pair_types = deque(maxlen=100)
    st.session_state.results = deque(maxlen=200)
    st.session_state.result_tracker = 0.0
    st.session_state.profit_lock = 0.0
    st.session_state.bet_amount = 0.0
    st.session_state.base_amount = 10.0
    st.session_state.next_prediction = None
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
    st.session_state.alerts.append({"type": "success", "message": "All session data reset successfully.", "id": str(uuid.uuid4())})

def record_result(result):
    """Record a game result and update state."""
    if st.session_state.processing:
        st.session_state.alerts.append({"type": "warning", "message": "Processing another action, please wait.", "id": str(uuid.uuid4())})
        return
    st.session_state.processing = True

    try:
        if not validate_pair_types():
            st.session_state.alerts.append({"type": "info", "message": f"pair_types validated and cleaned in record_result. Initial state: {list(st.session_state.pair_types)}", "id": str(uuid.uuid4())})

        st.session_state.alerts.append({"type": "info", "message": f"DEBUG: pair_types before = {list(st.session_state.pair_types)}, type: {type(st.session_state.pair_types).__name__}", "id": str(uuid.uuid4())})

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

        # Validate state before saving to state_history
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
        st.session_state.alerts.append({"type": "info", "message": f"DEBUG: state_history length = {len(st.session_state.state_history)}", "id": str(uuid.uuid4())})

        if result == 'T':
            st.session_state.stats['ties'] = int(st.session_state.stats.get('ties', 0)) + 1
            st.session_state.previous_result = result
            st.session_state.bet_amount = 0
            st.session_state.alerts.append({"type": "info", "message": "Tie recorded!", "id": str(uuid.uuid4())})
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
            try:
                st.session_state.pair_types.append(pair)
                pair_type = "Even" if pair[0] == pair[1] else "Odd"
                st.session_state.stats['odd_pairs' if pair_type == 'Odd' else 'even_pairs'] = int(
                    st.session_state.stats.get('odd_pairs' if pair_type == 'Odd' else 'even_pairs', 0)) + 1
                if len(st.session_state.pair_types) >= 2:
                    last_two_pairs = [p for p in st.session_state.pair_types[-2:] if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
                    if len(last_two_pairs) == 2 and last_two_pairs[0][1] != last_two_pairs[1][1]:
                        alternating_pairs = st.session_state.stats.setdefault('alternating_pairs', 0)
                        st.session_state.stats['alternating_pairs'] = alternating_pairs + 1
            except Exception as e:
                st.session_state.alerts.append({"type": "error", "message": f"Error appending pair {pair}: {str(e)}", "id": str(uuid.uuid4())})
                validate_pair_types()

        try:
            st.session_state.alerts.append({"type": "info", "message": f"DEBUG: About to access pair_types[-4:], current state: {list(st.session_state.pair_types)}", "id": str(uuid.uuid4())})
            last_four_pairs = [p for p in st.session_state.pair_types[-4:] if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
            last_four = [p[1] for p in last_four_pairs if p[1] != 'T']
            st.session_state.alerts.append({"type": "info", "message": f"DEBUG: pair_types after = {list(st.session_state.pair_types)}, last_four = {last_four}", "id": str(uuid.uuid4())})
        except Exception as e:
            st.session_state.alerts.append({"type": "error", "message": f"Error processing last four pairs: {str(e)}", "id": str(uuid.uuid4())})
            last_four_pairs = []
            last_four = []

        if len(last_four) >= 3 and all(r == result for r in last_four):
            st.session_state.streak_type = result
            st.session_state.stats['streaks'].append(len(last_four))
        else:
            st.session_state.streak_type = None

        effective_bet = st.session_state.bet_amount if current_prediction in ["Player", "Banker"] else 0
        if effective_bet > 0:
            outcome = ""
            if current_prediction == "Player" and result == 'P':
                st.session_state.result_tracker += effective_bet
                st.session_state.stats['wins'] = int(st.session_state.stats.get('wins', 0)) + 1
                st.session_state.consecutive_wins += 1
                st.session_state.consecutive_losses = 0
                st.session_state.bet_amount = st.session_state.base_amount
                outcome = f"Won ${effective_bet:.2f}"
                st.session_state.alerts.append({"type": "success", "message": f"Bet won! +${effective_bet:.2f}", "id": str(uuid.uuid4())})
            elif current_prediction == "Banker" and result == 'B':
                st.session_state.result_tracker += effective_bet * 0.95
                st.session_state.stats['wins'] = int(st.session_state.stats.get('wins', 0)) + 1
                st.session_state.consecutive_wins += 1
                st.session_state.consecutive_losses = 0
                st.session_state.bet_amount = st.session_state.base_amount
                outcome = f"Won ${effective_bet * 0.95:.2f}"
                st.session_state.alerts.append({"type": "success", "message": f"Bet won! +${effective_bet * 0.95:.2f}", "id": str(uuid.uuid4())})
            elif current_prediction in ["Player", "Banker"]:
                st.session_state.result_tracker -= effective_bet
                st.session_state.stats['losses'] = int(st.session_state.stats.get('losses', 0)) + 1
                st.session_state.consecutive_losses += 1
                st.session_state.consecutive_wins = 0
                st.session_state.bet_amount = min(3 * st.session_state.base_amount, math.ceil((st.session_state.bet_amount + 0.5 * st.session_state.base_amount) / st.session_state.base_amount) * st.session_state.base_amount)
                outcome = f"Lost ${effective_bet:.2f}"
                st.session_state.alerts.append({"type": "error", "message": f"Bet lost! -${effective_bet:.2f}", "id": str(uuid.uuid4())})

        st.session_state.stats['bet_history'].append({
            'prediction': current_prediction,
            'result': result,
            'bet_amount': effective_bet,
            'outcome': outcome
        })

        if st.session_state.result_tracker >= 3 * st.session_state.base_amount:
            st.session_state.profit_lock += st.session_state.result_tracker
            st.session_state.result_tracker = 0.0
            st.session_state.bet_amount = st.session_state.base_amount
            st.session_state.alerts.append({"type": "info", "message": f"Profit locked at ${st.session_state.profit_lock:.2f}! Bankroll reset.", "id": str(uuid.uuid4())})
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

        st.session_state.alerts.append({"type": "info", "message": f"Debug: Undoing state, history length = {len(st.session_state.state_history)}", "id": str(uuid.uuid4())})

        last_state = st.session_state.state_history.pop()
        valid_pairs = [p for p in last_state.get('pair_types', []) if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
        if len(valid_pairs) < len(last_state.get('pair_types', [])):
            st.session_state.alerts.append({"type": "warning", "message": f"Invalid pairs found in state history; cleaned. Restored pairs: {valid_pairs}", "id": str(uuid.uuid4())})

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

        st.session_state.alerts.append({"type": "info", "message": f"Debug: Restored pair_types: {list(st.session_state.pair_types)}", "id": str(uuid.uuid4())})

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
    if st.session_state.processing:
        st.session_state.alerts.append({"type": "warning", "message": "Processing another action, please wait.", "id": str(uuid4())})
        return
    try:
        outcomes = ['P', 'B', 'T']
        weights = [0.446, 0.458, 0.096]
        for _ in range(100):
            result = random.choices(outcomes, weights)[0]
            record_result(result)
        st.session_state.alerts.append({"type": "success", "message": "Simulated 100 games. Check stats and bet history for results.", "id": str(uuid.uuid4())})

    except Exception as e:
        st.error(f"Failed to simulate 100 games: {str(e)}")
        st.session_state.alerts.append({"type": "error", "message": f"Error simulating games: {str(e)}", "id": str(uuid.uuid4())})

def simulate_choppy_games():
    """Simulate 90 games with choppy shoe characteristics."""
    if st.session_state.processing:
        st.session_state.alerts.append({"type": "warning", "message": "Processing another action, please wait.", "id": str(uuid.uuid4())})
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
        st.session_state.alerts.append({"type": "success", "message": "Simulated 90 choppy games.", "id": str(uuid.uuid4())})

    except Exception as e:
        st.error(f"Failed to simulate 90 choppy games: {str(e)}")
        st.session_state.alerts.append({"type": "error", "message": f"Error simulating choppy games: {str(e)}", "id": str(uuid.uuid4())})

def clear_alerts():
    """Clear all alerts."""
    if st.session_state.processing:
        st.session_state.alerts.append({"type": "warning", "message": "Processing another action, please wait.", "id": str(uuid.uuid4())})
        return
    st.session_state.alerts = []

def main():
    """Main Streamlit application."""
    initialize_session_state()
    st.session_state.alerts.append({"type": "success", "message": "Application initialized successfully.", "id": str(uuid.uuid4())})

    css_styles = """
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
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
        .sidebar .stButton>button {
            margin-bottom: 0.5rem;
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
    </style>
    """
    st.markdown(css_styles, unsafe_allow_html=True)

    alert_container = st.container()
    with alert_container:
        for alert in st.session_state.alerts[-5:]:
            alert_class = f"alert alert-{alert['type'].lower()}"
            st.markdown(f'<div class="{alert_class}">{alert["message"]}</div>', unsafe_allow_html=True)
        if st.session_state.alerts:
            st.button("Clear Alerts", on_click=clear_alerts, disabled=st.session_state.processing)

    st.markdown("<h1>Baccarat Predictor</h1>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("<h2>Controls</h2>", unsafe_allow_html=True)
        with st.expander("Bet Settings", expanded=True):
            st.number_input("Base Amount ($1-$100)", min_value=1.0, max_value=100.0, value=st.session_state.base_amount, step=1.0, key="base_amount_input")
            st.button("Set Amount", on_click=lambda: set_base_amount(), disabled=st.session_state.processing)
        with st.expander("Session Actions", expanded=False):
            st.button("Reset Bet", on_click=lambda: reset_betting(), disabled=st.session_state.processing)
            st.button("Reset Session", on_click=lambda: reset_all(), disabled=st.session_state.processing)
            st.button("New Session", on_click=lambda: [reset_all(), st.session_state.alerts.append({"type": "success", "message": "New session started.", "id": str(uuid.uuid4())})], disabled=st.session_state.processing)
            st.button("Simulate 100 Games", on_click=lambda: simulate_games(), disabled=st.session_state.processing)
            st.button("Simulate 90 Choppy Games", on_click=lambda: simulate_choppy_games(), disabled=st.session_state.processing)

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
            badge_class = (
                "next-bet badge bg-blue-500" if st.session_state.next_prediction == "Player" else
                "next-bet badge bg-red-500" if st.session_state.next_prediction == "Banker" else
                "next-bet badge bg-yellow-500" if st.session_state.next_prediction == "Hold" else
                "next-bet badge bg-gray-500"
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

        st.markdown("<h2>Result History</h2>", unsafe_allow_html=True)
        if st.session_state.results:
            recent_results = list(st.session_state.results)[-20:]
            result_items = [
                f'<span class="result-item result-{r.lower()}">{r}</span>'
                for r in recent_results
            ]
            result_html = "".join(result_items)
            st.markdown(f"""
                <div class="card">
                    <p class="text-sm font-semibold text-gray-400">Recent Results (P: Player, B: Banker, T: Tie)</p>
                    <div class="result-history" id="resultHistory">
                        {result_html}
                    </div>
                </div>
                <script>
                    document.addEventListener('DOMContentLoaded', () => {{
                        const resultDiv = document.getElementById('resultHistory');
                        if (resultDiv) {
                            resultDiv.scrollLeft = resultDiv.scrollWidth;
                        }
                    });
                </script>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<p class="text-gray-400">No results yet.</p>', unsafe_allow_html=True)

        st.markdown("<h2>Record Result</h2>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.button("Player", on_click=lambda: record_result('P'), disabled=st.session_state.processing)
        with col2:
            st.button("Banker", on_click=lambda: record_result('B'), disabled=st.session_state.processing)
        with col3:
            st.button("Tie", on_click=lambda: record_result('T'), disabled=st.session_state.processing)
        with col4:
            st.button("Undo", on_click=lambda: undo(), disabled=st.session_state.processing)

        st.markdown("<h2>Deal History</h2>", unsafe_allow_html=True)
        if not validate_pair_types():
            st.session_state.alerts.append({"type": "info", "message": "Invalid pair_types detected in deal history.", "id": str(uuid.uuid4())})
        valid_pairs = [p for p in st.session_state.pair_types if isinstance(p, (tuple, list)) and len(p) == 2 and p[0] in ['P', 'B', 'T'] and p[1] in ['P', 'B', 'T']]
        if valid_pairs:
            history_data = [
                {"Pair": f"{pair[0]}{pair[1]}", "Type": "Odd" if pair[0] != pair[1] else "Even"}
                for pair in valid_pairs
            ]
            history_df = pd.DataFrame(history_data)
            st.dataframe(history_df, use_container_width=True, height=300)
        else:
            st.markdown('<p class="text-gray-400">No deal history available.</p>', unsafe_allow_html=True)

        total_games = st.session_state.stats.get('wins', 0) + st.session_state.stats.get('losses', 0)
        win_rate = (st.session_state.stats.get('wins', 0) / total_games * 100) if total_games > 0 else 0.0
        avg_streak = sum(st.session_state.stats.get('streaks', [])) / len(st.session_state.stats.get('streaks', [])) if len(st.session_state.stats.get('streaks', [])) > 0 else 0
        recent_pairs = valid_pairs[-10:] if len(valid_pairs) >= 10 else valid_pairs
        alternation_rate = sum(1 for i in range(len(recent_pairs)-1) if recent_pairs[i][1] != recent_pairs[i+1][1]) / (len(recent_pairs)-1) if len(recent_pairs) > 1 else 0
        st.markdown(f"""
            <div class="card">
                <p class="text-sm font-semibold text-gray-400">Statistics</p>
                <p class="text-base">Win Rate: {win_rate:.1f}%</p>
                <p class="text-base">Average Streak: {avg_streak:.1f}</p>
                <p class="text-base">Alternation Rate: {alternation_rate:.2f}</p>
                <p class="text-base">Patterns: Odd: {st.session_state.stats.get('odd_pairs', 0)}, Even: {st.session_state.stats.get('even_pairs', 0)}, Alternating: {st.session_state.stats.get('alternating_pairs', 0)}</p>
                <p class="text-base">Streak: {st.session_state.streak_type or 'None'}</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<h2>Pattern Confidence</h2>", unsafe_allow_html=True)
        chart_config = {
            "type": "pie",
            "data": {
                "labels": ["Odd", "Even", "Alternating", "Streak", "Choppy", "Markov", "Bayesian"],
                "datasets": [
                    {
                        "label": "Pattern Confidence",
                        "data": [
                            st.session_state.pattern_confidence.get('Odd', 0.0),
                            st.session_state.pattern_confidence.get('Even', 0.0),
                            st.session_state.pattern_confidence.get('Alternating', 0.0),
                            st.session_state.pattern_confidence.get('Streak', 0.0),
                            st.session_state.pattern_confidence.get('Choppy', 0.0),
                            st.session_state.pattern_confidence.get('Markov', 0.0),
                            st.session_state.pattern_confidence.get('Bayesian', 0.0)
                        ],
                        "backgroundColor": [
                            "#FF6384",
                            "#36A2EB",
                            "#FFCE56",
                            "#4BC0C0",
                            "#9966FF",
                            "#FF9F40",
                            "#FF6347"
                        ]
                    }
                ]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {
                        "position": "top",
                        "labels": {"color": "#e5e7eb"}
                    },
                    "title": {
                        "display": True,
                        "text": "Pattern Confidence",
                        "color": "#e5e7eb"
                    }
                }
            }
        }
        st.markdown(f"""
            <div class="card">
                <canvas id="chart"></canvas>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.js"></script>
            <script>
                document.addEventListener('DOMContentLoaded', () => {{
                    const ctx = document.getElementById('chart').getContext('2d');
                    new Chart(ctx, {json.dumps(chart_config, ensure_ascii=False)});
                }});
            </script>
        """, unsafe_allow_html=True)

        st.markdown("<h2>Bet History</h2>", unsafe_allow_html=True)
        if st.session_state.stats.get('bet_history', []):
            bet_history = pd.DataFrame(st.session_state.stats.get('bet_history', []))
            st.dataframe(bet_history, use_container_width=True, height=200)
        else:
            st.markdown('<p class="text-gray-400">No bets placed yet.</p>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
