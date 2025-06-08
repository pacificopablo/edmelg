import streamlit as st
import random
import math
import uuid

def initialize_session_state():
    """Initialize session state variables if not already set."""
    if 'pair_types' not in st.session_state:
        st.session_state.pair_types = []
        st.session_state.next_prediction = "N/A"
        st.session_state.base_amount = 10.0
        st.session_state.bet_amount = st.session_state.base_amount
        st.session_state.result_tracker = 0.0
        st.session_state.profit_lock = 0.0
        st.session_state.previous_result = None
        st.session_state.state_history = []
        st.session_state.current_dominance = "N/A"
        st.session_state.streak_type = None
        st.session_state.consecutive_wins = 0
        st.session_state.consecutive_losses = 0
        st.session_state.stats = {'wins': 0, 'losses': 0, 'ties': 0, 'streaks': [], 'odd_pairs': 0, 'even_pairs': 0}

def set_base_amount():
    """Set the base betting amount and reset bet_amount."""
    try:
        amount = float(st.session_state.base_amount_input)
        if 1 <= amount <= 100:
            st.session_state.base_amount = amount
            st.session_state.bet_amount = st.session_state.base_amount
            update_display()
        else:
            st.error("Base amount must be between $1 and $100.")
    except ValueError:
        st.error("Please enter a valid number.")

def new_session():
    """Start a new session by resetting all state."""
    reset_all()
    st.success("New session started.")

def reset_betting():
    """Reset betting parameters based on current state."""
    if st.session_state.result_tracker <= -10 * st.session_state.base_amount:
        st.warning("Stop-loss reached. Resetting to resume betting.")
    if st.session_state.result_tracker >= 0:
        st.session_state.result_tracker = 0.0
    st.session_state.bet_amount = st.session_state.base_amount
    st.session_state.consecutive_wins = 0
    st.session_state.consecutive_losses = 0
    st.session_state.streak_type = None

    if len(st.session_state.pair_types) >= 5:
        recent_pairs = [p for p in st.session_state.pair_types[-10:] if p[0] != 'T' and p[1] != 'T']
        if recent_pairs:
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
            last_four = [p[1] for p in st.session_state.pair_types[-4:] if p[1] != 'T']
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

    update_display()
    st.success("Betting reset.")

def reset_all():
    """Reset all session data."""
    st.session_state.pair_types = []
    st.session_state.result_tracker = 0.0
    st.session_state.profit_lock = 0.0
    st.session_state.bet_amount = st.session_state.base_amount
    st.session_state.base_amount = 10.0
    st.session_state.next_prediction = "N/A"
    st.session_state.previous_result = None
    st.session_state.state_history = []
    st.session_state.current_dominance = "N/A"
    st.session_state.consecutive_wins = 0
    st.session_state.consecutive_losses = 0
    st.session_state.streak_type = None
    st.session_state.stats = {'wins': 0, 'losses': 0, 'ties': 0, 'streaks': [], 'odd_pairs': 0, 'even_pairs': 0}
    update_display()
    st.success("All session data reset, profit lock reset.")

def analyze_pair_patterns(recent_pairs, result):
    """Analyze pair patterns to determine prediction and confidence."""
    if not recent_pairs:
        return "N/A", "Hold", 0.0

    odd_count = sum(1 for a, b in recent_pairs if a != b)
    even_count = sum(1 for a, b in recent_pairs if a == b)
    total_pairs = len(recent_pairs)
    dominance_diff = abs(odd_count - even_count)
    confidence = dominance_diff / total_pairs

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

    if pair_streak:
        dominance = f"Pair Streak ({last_three_pairs[0]})"
        if last_three_pairs[0] == "Odd":
            prediction = "Player" if result == 'B' else "Banker"
        else:
            prediction = "Player" if result == 'P' else "Banker"
        bet_multiplier = math.ceil(1.5 if confidence < 0.7 else 2.0)
    elif cycle_detected:
        dominance = f"Cycle (length {cycle_length})"
        last_pair_type = pair_sequence[-1]
        if last_pair_type == "Odd":
            prediction = "Player" if result == 'B' else "Banker"
        else:
            prediction = "Player" if result == 'P' else "Banker"
        bet_multiplier = math.ceil(1.2 + 0.3 * cycle_length)
    elif dominance_diff >= 4 and confidence > 0.5:
        if odd_count > even_count:
            dominance = "Odd"
            prediction = "Player" if result == 'B' else "Banker"
        else:
            dominance = "Even"
            prediction = "Player" if result == 'P' else "Banker"
        bet_multiplier = math.ceil(1.0 + confidence)
    else:
        dominance = "N/A"
        prediction = "Hold"
        bet_multiplier = 0.0

    return dominance, prediction, bet_multiplier

def record_result(result):
    """Record a game result and update betting logic."""
    state = {
        'pair_types': st.session_state.pair_types.copy(),
        'previous_result': st.session_state.previous_result,
        'result_tracker': st.session_state.result_tracker,
        'profit_lock': st.session_state.profit_lock,
        'bet_amount': st.session_state.bet_amount,
        'current_dominance': st.session_state.current_dominance,
        'next_prediction': st.session_state.next_prediction,
        'consecutive_wins': st.session_state.consecutive_wins,
        'consecutive_losses': st.session_state.consecutive_losses,
        'streak_type': st.session_state.streak_type,
        'stats': st.session_state.stats.copy()
    }
    st.session_state.state_history.append(state)

    if result == 'T':
        st.session_state.stats['ties'] += 1
        update_display()
        return

    if st.session_state.previous_result is None:
        st.session_state.previous_result = result
        st.session_state.next_prediction = "N/A"
        st.session_state.bet_amount = st.session_state.base_amount
        update_display()
        return

    if st.session_state.previous_result != 'T':
        pair = (st.session_state.previous_result, result)
        st.session_state.pair_types.append(pair)
        pair_type = "Even" if pair[0] == pair[1] else "Odd"
        st.session_state.stats['odd_pairs' if pair_type == "Odd" else 'even_pairs'] += 1

    last_four = [p[1] for p in st.session_state.pair_types[-4:] if p[1] != 'T']
    if len(last_four) >= 3 and all(r == result for r in last_four):
        st.session_state.streak_type = result
        st.session_state.stats['streaks'].append(len(last_four))
    else:
        st.session_state.streak_type = None

    previous_prediction = st.session_state.state_history[-1]['next_prediction'] if st.session_state.state_history else "N/A"
    effective_bet = st.session_state.bet_amount if previous_prediction in ["Player", "Banker"] else 0

    if effective_bet > 0:
        if (previous_prediction == "Player" and result == 'P'):
            st.session_state.result_tracker += effective_bet
            st.session_state.stats['wins'] += 1
            st.session_state.consecutive_wins += 1
            st.session_state.consecutive_losses = 0
            st.session_state.bet_amount = st.session_state.base_amount
        elif (previous_prediction == "Banker" and result == 'B'):
            st.session_state.result_tracker += effective_bet * 0.95
            st.session_state.stats['wins'] += 1
            st.session_state.consecutive_wins += 1
            st.session_state.consecutive_losses = 0
            st.session_state.bet_amount = st.session_state.base_amount
        elif previous_prediction in ["Player", "Banker"]:
            st.session_state.result_tracker -= effective_bet
            st.session_state.stats['losses'] += 1
            st.session_state.consecutive_losses += 1
            st.session_state.consecutive_wins = 0
            st.session_state.bet_amount = min(3 * st.session_state.base_amount, math.ceil((st.session_state.bet_amount + 0.5 * st.session_state.base_amount) / st.session_state.base_amount) * st.session_state.base_amount)

    if st.session_state.result_tracker >= 3 * st.session_state.base_amount:
        st.session_state.profit_lock += st.session_state.result_tracker
        st.session_state.result_tracker = 0.0
        st.session_state.bet_amount = st.session_state.base_amount
        st.success(f"Profit of ${st.session_state.profit_lock:.2f} locked! Bankroll reset.")
        update_display()
        return
    elif st.session_state.result_tracker <= -10 * st.session_state.base_amount:
        st.warning("Loss limit reached. Reset to resume betting.")
        st.session_state.next_prediction = "Hold"
        st.session_state.bet_amount = 0.0
        update_display()
        return

    if len(st.session_state.pair_types) >= 8:
        recent_pairs = [p for p in st.session_state.pair_types[-15:] if p[0] != 'T' and p[1] != 'T']
        dominance, prediction, bet_multiplier = analyze_pair_patterns(recent_pairs, result)

        if st.session_state.streak_type:
            st.session_state.next_prediction = "Player" if st.session_state.streak_type == 'P' else "Banker"
            st.session_state.current_dominance = f"Streak ({st.session_state.streak_type})"
            streak_length = len([p for p in st.session_state.pair_types[-5:] if p[1] == st.session_state.streak_type])
            st.session_state.bet_amount = min(3 * st.session_state.base_amount, math.ceil((1 + 0.5 * (streak_length - 2)) * st.session_state.base_amount / st.session_state.base_amount) * st.session_state.base_amount)
        else:
            st.session_state.current_dominance = dominance
            st.session_state.next_prediction = prediction
            st.session_state.bet_amount = min(3 * st.session_state.base_amount, bet_multiplier * st.session_state.base_amount)
    else:
        st.session_state.current_dominance = "N/A"
        st.session_state.next_prediction = "N/A"
        st.session_state.bet_amount = st.session_state.base_amount

    st.session_state.previous_result = result
    update_display()

def undo():
    """Undo the last action by restoring the previous state."""
    if not st.session_state.state_history:
        st.error("No actions to undo.")
        return

    last_state = st.session_state.state_history.pop()
    st.session_state.pair_types = last_state['pair_types']
    st.session_state.previous_result = last_state['previous_result']
    st.session_state.result_tracker = last_state['result_tracker']
    st.session_state.profit_lock = last_state['profit_lock']
    st.session_state.bet_amount = last_state['bet_amount']
    st.session_state.current_dominance = last_state['current_dominance']
    st.session_state.next_prediction = last_state['next_prediction']
    st.session_state.consecutive_wins = last_state['consecutive_wins']
    st.session_state.consecutive_losses = last_state['consecutive_losses']
    st.session_state.streak_type = last_state['streak_type']
    st.session_state.stats = last_state['stats']
    update_display()
    st.success("Last action undone.")

def update_display():
    """Update the display with current session state."""
    st.session_state.bet_amount_display = f"Bet Amount: {'No Bet' if st.session_state.bet_amount == 0 else f'${st.session_state.bet_amount:.2f}'}"
    st.session_state.bankroll_display = f"Bankroll: ${st.session_state.result_tracker:.2f}"
    st.session_state.profit_lock_display = f"Profit Lock: ${st.session_state.profit_lock:.2f}"
    st.session_state.prediction_display = f"Bet: {st.session_state.next_prediction}"
    st.session_state.streak_display = f"Streak: {st.session_state.streak_type if st.session_state.streak_type else 'None'}"

    total_games = st.session_state.stats['wins'] + st.session_state.stats['losses']
    win_rate = (st.session_state.stats['wins'] / total_games * 100) if total_games > 0 else 0
    avg_streak = sum(st.session_state.stats['streaks']) / len(st.session_state.stats['streaks']) if st.session_state.stats['streaks'] else 0
    st.session_state.stats_display = f"Win Rate: {win_rate:.1f}% | Avg Streak: {avg_streak:.1f} | Patterns: Odd: {st.session_state.stats['odd_pairs']}, Even: {st.session_state.stats['even_pairs']}"

    history_text = ""
    for i, pair in enumerate(st.session_state.pair_types[-100:], 1):
        pair_type = "Even" if pair[0] == pair[1] else "Odd"
        history_text += f"{pair} ({pair_type})\n"
    st.session_state.history_display = history_text

def simulate_games():
    """Simulate 100 games with random outcomes."""
    outcomes = ['P', 'B', 'T']
    weights = [0.446, 0.458, 0.096]
    for _ in range(100):
        result = random.choices(outcomes, weights)[0]
        record_result(result)
    st.success("Simulated 100 games. Check stats for results.")

def main():
    """Main function to render the Streamlit app."""
    st.set_page_config(page_title="Baccarat Predictor", layout="centered")
    st.markdown("""
        <style>
        .main {background-color: #2C2F33; color: white;}
        .stButton>button {
            background-color: #7289DA;
            color: white;
            font-weight: bold;
            padding: 10px;
            border-radius: 5px;
            border: none;
        }
        .stButton>button:hover {
            background-color: #99AAB5;
        }
        .stTextInput>div>input {
            background-color: #23272A;
            color: white;
            border: none;
        }
        .stTextArea textarea {
            background-color: #23272A;
            color: white;
            border: none;
        }
        .title {font-size: 24px; font-weight: bold; text-align: center;}
        .label {font-size: 16px;}
        </style>
    """, unsafe_allow_html=True)

    initialize_session_state()

    st.markdown('<div class="title">Balanced Progression Baccarat Predictor</div>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.text_input("Base Amount ($1-$100)", value="10", key="base_amount_input")
    with col2:
        st.button("Set Amount", on_click=set_base_amount)
    with col3:
        pass

    st.markdown('<div class="label">Bet Amount:</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="label">{st.session_state.get("bet_amount_display", "Bet Amount: $10.00")}</div>', unsafe_allow_html=True)
    st.markdown('<div class="label">Bankroll:</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="label">{st.session_state.get("bankroll_display", "Bankroll: $0.00")}</div>', unsafe_allow_html=True)
    st.markdown('<div class="label">Profit Lock:</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="label">{st.session_state.get("profit_lock_display", "Profit Lock: $0.00")}</div>', unsafe_allow_html=True)
    st.markdown('<div class="label">Bet:</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="label" style="font-weight: bold; font-size: 18px;">{st.session_state.get("prediction_display", "Bet: N/A")}</div>', unsafe_allow_html=True)
    st.markdown('<div class="label">Streak:</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="label">{st.session_state.get("streak_display", "Streak: None")}</div>', unsafe_allow_html=True)

    st.markdown('<div class="label">Statistics:</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="label">{st.session_state.get("stats_display", "Win Rate: 0% | Avg Streak: 0 | Patterns: Odd: 0, Even: 0")}</div>', unsafe_allow_html=True)

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.button("Player", on_click=lambda: record_result('P'))
    with col2:
        st.button("Banker", on_click=lambda: record_result('B'))
    with col3:
        st.button("Tie", on_click=lambda: record_result('T'))
    with col4:
        st.button("Undo", on_click=undo)

    st.markdown('<div class="label">Deal History:</div>', unsafe_allow_html=True)
    st.text_area("", value=st.session_state.get("history_display", ""), height=200, disabled=True)

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.button("Reset Bet", on_click=reset_betting)
    with col2:
        st.button("Reset Session", on_click=reset_all)
    with col3:
        st.button("New Session", on_click=new_session)
    with col4:
        st.button("Simulate", on_click=simulate_games)

if __name__ == "__main__":
    main()
