import streamlit as st
import logging
import plotly.graph_objects as go
import math
import random

# Set up basic logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Normalize input
def normalize(s):
    s = s.strip().lower()
    if s == 'banker' or s == 'b':
        return 'Banker'
    if s == 'player' or s == 'p':
        return 'Player'
    if s == 'tie' or s == 't':
        return 'Tie'
    return None

# Helper functions from D5Final
def detect_streak(s):
    if not s:
        return None, 0
    last = s[-1]
    count = 1
    for i in range(len(s) - 2, -1, -1):
        if s[i] == last:
            count += 1
        else:
            break
    return last, count

def build_big_road(s):
    max_rows = 6
    max_cols = 50
    grid = [['' for _ in range(max_cols)] for _ in range(max_rows)]
    col = 0
    row = 0
    last_outcome = None

    for result in s:
        mapped = 'P' if result == 'Player' else 'B' if result == 'Banker' else 'T'
        if mapped == 'T':
            if col < max_cols and row < max_rows and grid[row][col] == '':
                grid[row][col] = 'T'
            continue
        if col >= max_cols:
            break
        if last_outcome is None or (mapped == last_outcome and row < max_rows - 1):
            grid[row][col] = mapped
            row += 1
        else:
            col += 1
            row = 0
            if col < max_cols:
                grid[row][col] = mapped
                row += 1
        last_outcome = mapped if mapped != 'T' else last_outcome
    return grid, col + 1

def build_big_eye_boy(big_road_grid, num_cols):
    max_rows = 6
    max_cols = 50
    grid = [['' for _ in range(max_cols)] for _ in range(max_rows)]
    col = 0
    row = 0

    for c in range(3, num_cols):
        if col >= max_cols:
            break
        last_col = [big_road_grid[r][c - 1] for r in range(max_rows)]
        third_last = [big_road_grid[r][c - 3] for r in range(max_rows)]
        last_non_empty = next((i for i, x in enumerate(last_col) if x in ['P', 'B']), None)
        third_non_empty = next((i for i, x in enumerate(third_last) if x in ['P', 'B']), None)
        if last_non_empty is not None and third_non_empty is not None:
            if last_col[last_non_empty] == third_last[third_non_empty]:
                grid[row][col] = 'R'
            else:
                grid[row][col] = 'B'
            row += 1
            if row >= max_rows:
                col += 1
                row = 0
        else:
            col += 1
            row = 0
    return grid, col + 1 if row > 0 else col

def build_cockroach_pig(big_road_grid, num_cols):
    max_rows = 6
    max_cols = 50
    grid = [['' for _ in range(max_cols)] for _ in range(max_rows)]
    col = 0
    row = 0

    for c in range(4, num_cols):
        if col >= max_cols:
            break
        last_col = [big_road_grid[r][c - 1] for r in range(max_rows)]
        fourth_last = [big_road_grid[r][c - 4] for r in range(max_rows)]
        last_non_empty = next((i for i, x in enumerate(last_col) if x in ['P', 'B']), None)
        fourth_non_empty = next((i for i, x in enumerate(fourth_last) if x in ['P', 'B']), None)
        if last_non_empty is not None and fourth_non_empty is not None:
            if last_col[last_non_empty] == fourth_last[fourth_non_empty]:
                grid[row][col] = 'R'
            else:
                grid[row][col] = 'B'
            row += 1
            if row >= max_rows:
                col += 1
                row = 0
        else:
            col += 1
            row = 0
    return grid, col + 1 if row > 0 else col

# Adapted from D5Final's analyze_pair_patterns
def analyze_pair_patterns(recent_pairs, result, mode='Conservative'):
    if not recent_pairs:
        return 'N/A', 'Pass', 0.0, "No results yet. Waiting for shoe to develop.", ["No patterns"], "Cautious"

    # Count Odd and Even pairs
    odd_count = sum(1 for a, b in recent_pairs if a != b)
    even_count = sum(1 for a, b in recent_pairs if a == b)
    total_pairs = len(recent_pairs)
    dominance_diff = abs(odd_count - even_count)
    confidence = min(dominance_diff / total_pairs * 100, 95)  # Base confidence

    # Detect repeating pair patterns (e.g., P-B-P-B or P-P-B-B)
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
                confidence += 20  # Boost confidence for detected cycles
                break

    # Detect pair streaks (e.g., multiple consecutive Odd or Even pairs)
    last_three_pairs = pair_sequence[-3:] if len(pair_sequence) >= 3 else []
    pair_streak = len(last_three_pairs) >= 3 and all(p == last_three_pairs[0] for p in last_three_pairs)

    reason_parts = []
    pattern_insights = []
    emotional_tone = "Neutral"

    # Determine prediction and dominance
    if pair_streak:
        dominance = f"Pair Streak ({last_three_pairs[0]})"
        if last_three_pairs[0] == "Odd":
            prediction = "Player" if result == 'B' else "Banker"
        else:  # Even
            prediction = "Player" if result == 'P' else "Banker"
        bet_multiplier = math.ceil(1.5 if confidence < 70 else 2.0)
        confidence = min(confidence + 20, 95)
        reason_parts.append(f"Detected pair streak of {last_three_pairs[0]} in last 3 pairs.")
        pattern_insights.append(f"Pair Streak: {last_three_pairs[0]}")
        emotional_tone = "Confident"
    elif cycle_detected:
        dominance = f"Cycle (length {cycle_length})"
        last_pair_type = pair_sequence[-1]
        if last_pair_type == "Odd":
            prediction = "Player" if result == 'B' else "Banker"
        else:  # Even
            prediction = "Player" if result == 'P' else "Banker"
        bet_multiplier = math.ceil(1.2 + 0.3 * cycle_length)
        confidence = min(confidence + 15 * cycle_length, 95)
        reason_parts.append(f"Detected repeating cycle of length {cycle_length}.")
        pattern_insights.append(f"Cycle: Length {cycle_length}")
        emotional_tone = "Curious"
    elif dominance_diff >= 4 and confidence > 50:
        if odd_count > even_count:
            dominance = "Odd"
            prediction = "Player" if result == 'B' else "Banker"
            reason_parts.append("Odd pair dominance detected.")
            pattern_insights.append("Odd Pair Dominance")
        else:
            dominance = "Even"
            prediction = "Player" if result == 'P' else "Banker"
            reason_parts.append("Even pair dominance detected.")
            pattern_insights.append("Even Pair Dominance")
        bet_multiplier = math.ceil(1.0 + confidence / 100)
        confidence = min(confidence + 10, 95)
        emotional_tone = "Hopeful"
    else:
        dominance = "N/A"
        prediction = "Pass"
        bet_multiplier = 0.0
        confidence = 0.0
        reason_parts.append("No strong pattern detected; insufficient confidence.")
        pattern_insights.append("No clear pattern")
        emotional_tone = "Cautious"

    # Adjust confidence based on mode
    if mode == 'Conservative' and confidence < 65:
        prediction = "Pass"
        reason_parts.append("Conservative mode: Confidence too low, passing.")
        emotional_tone = "Hesitant"
        bet_multiplier = 0.0
        confidence = 0.0
    elif mode == 'Aggressive' and confidence < 45:
        prediction = "Pass"
        reason_parts.append("Aggressive mode: Confidence too low, passing.")
        emotional_tone = "Hesitant"
        bet_multiplier = 0.0
        confidence = 0.0

    reason = " ".join(reason_parts)
    return dominance, prediction, bet_multiplier, reason, pattern_insights, emotional_tone

# Adapted bet selection from D5Final
def advanced_bet_selection(history, mode='Conservative'):
    if not history or len(history) < 2:
        return 'Pass', 0.0, "No results yet. Waiting for shoe to develop.", "Cautious", ["No patterns"]

    # Convert history to pairs
    pair_types = []
    for i in range(1, len(history)):
        prev = 'P' if history[i-1] == 'Player' else 'B' if history[i-1] == 'Banker' else 'T'
        curr = 'P' if history[i] == 'Player' else 'B' if history[i] == 'Banker' else 'T'
        if prev != 'T' and curr != 'T':
            pair_types.append((prev, curr))

    # Get the last result for prediction
    result = 'P' if history[-1] == 'Player' else 'B' if history[-1] == 'Banker' else 'T'

    # Check for streak
    last_four = [p[1] for p in pair_types[-4:] if p[1] != 'T']
    streak_type = None
    if len(last_four) >= 3 and all(r == result for r in last_four):
        streak_type = result

    # Analyze patterns
    recent_pairs = [p for p in pair_types[-15:] if p[0] != 'T' and p[1] != 'T']
    if len(pair_types) >= 8 and recent_pairs:  # Require at least 8 pairs for robust analysis
        dominance, prediction, bet_multiplier, reason, pattern_insights, emotional_tone = analyze_pair_patterns(recent_pairs, result, mode)
        if streak_type:
            prediction = "Player" if streak_type == 'P' else "Banker"
            dominance = f"Streak ({streak_type})"
            streak_length = len([p for p in pair_types[-5:] if p[1] == streak_type])
            bet_multiplier = min(3, math.ceil((1 + 0.5 * (streak_length - 2))))
            reason += f" Prioritizing streak of {streak_length} {streak_type}."
            pattern_insights.append(f"Streak: {streak_length} {streak_type}")
            emotional_tone = "Confident"
            confidence = min(75 + 5 * streak_length, 95)
        else:
            confidence = min(analyze_pair_patterns(recent_pairs, result, mode)[2] * 100 / 3, 95)
    else:
        dominance = "N/A"
        prediction = "Pass"
        bet_multiplier = 1.0
        confidence = 0.0
        reason = "Insufficient results for pattern analysis."
        pattern_insights = ["Insufficient data"]
        emotional_tone = "Cautious"

    return prediction, confidence, reason, emotional_tone, pattern_insights

# Adapted money management from D5Final
def money_management(bankroll, base_bet, result=None, previous_prediction=None):
    min_bet = max(1.0, base_bet)
    max_bet = bankroll

    if bankroll < min_bet:
        st.warning(f"Bankroll (${bankroll:.2f}) is less than minimum bet (${min_bet:.2f}).")
        return 0.0, False, False

    # Initialize session state variables if not present
    if 'consecutive_wins' not in st.session_state:
        st.session_state.consecutive_wins = 0
    if 'consecutive_losses' not in st.session_state:
        st.session_state.consecutive_losses = 0
    if 'bet_amount' not in st.session_state:
        st.session_state.bet_amount = base_bet
    if 'result_tracker' not in st.session_state:
        st.session_state.result_tracker = 0.0
    if 'profit_lock' not in st.session_state:
        st.session_state.profit_lock = 0.0

    profit_locked = False
    stop_loss = False

    # Update based on result
    if result and previous_prediction in ["Player", "Banker"]:
        effective_bet = st.session_state.bet_amount
        if (previous_prediction == "Player" and result == 'Player'):
            st.session_state.result_tracker += effective_bet
            st.session_state.consecutive_wins += 1
            st.session_state.consecutive_losses = 0
            st.session_state.bet_amount = base_bet  # Reset bet after win
        elif (previous_prediction == "Banker" and result == 'Banker'):
            st.session_state.result_tracker += effective_bet * 0.95  # Account for banker commission
            st.session_state.consecutive_wins += 1
            st.session_state.consecutive_losses = 0
            st.session_state.bet_amount = base_bet
        elif previous_prediction in ["Player", "Banker"]:
            st.session_state.result_tracker -= effective_bet
            st.session_state.consecutive_losses += 1
            st.session_state.consecutive_wins = 0
            st.session_state.bet_amount = min(3 * base_bet, math.ceil((st.session_state.bet_amount + 0.5 * base_bet) / base_bet) * base_bet)

        # Profit lock and stop-loss
        if st.session_state.result_tracker >= 3 * base_bet:
            st.session_state.profit_lock += st.session_state.result_tracker
            st.session_state.result_tracker = 0.0
            st.session_state.bet_amount = base_bet
            st.session_state.consecutive_wins = 0
            st.session_state.consecutive_losses = 0
            profit_locked = True
            st.info(f"Profit of ${st.session_state.profit_lock:.2f} locked! Bankroll reset.")
        elif st.session_state.result_tracker <= -10 * base_bet:
            st.session_state.bet_amount = 0.0
            stop_loss = True
            st.warning("Loss limit reached. Pausing betting until reset.")

    bet_size = st.session_state.bet_amount
    bet_size = max(min_bet, min(bet_size, max_bet))
    return round(bet_size, 2), profit_locked, stop_loss

# Updated calculate_bankroll
def calculate_bankroll(history, base_bet):
    bankroll = st.session_state.initial_bankroll
    current_bankroll = bankroll
    bankroll_progress = []
    bet_sizes = []
    pair_types = []
    previous_result = None
    st.session_state.result_tracker = 0.0
    st.session_state.profit_lock = 0.0
    st.session_state.bet_amount = base_bet
    st.session_state.consecutive_wins = 0
    st.session_state.consecutive_losses = 0

    for i in range(len(history)):
        current_rounds = history[:i + 1]
        result = history[i]
        mapped_result = 'P' if result == 'Player' else 'B' if result == 'Banker' else 'T'

        # Record pairs
        if previous_result and previous_result != 'T' and mapped_result != 'T':
            pair_types.append((previous_result, mapped_result))

        # Get prediction
        bet, confidence, _, _, _ = advanced_bet_selection(current_rounds[:-1], st.session_state.ai_mode) if i != 0 else ('Pass', 0, '', 'Neutral', [])
        if bet in (None, 'Pass', 'Tie'):
            bankroll_progress.append(current_bankroll)
            bet_sizes.append(0.0)
            previous_result = mapped_result
            continue

        # Calculate bet size
        bet_size, profit_locked, stop_loss = money_management(current_bankroll, base_bet, result, bet)
        if bet_size == 0.0 or stop_loss:
            bankroll_progress.append(current_bankroll)
            bet_sizes.append(0.0)
            previous_result = mapped_result
            continue

        bet_sizes.append(bet_size)
        if result == bet:
            if bet == 'Banker':
                win_amount = bet_size * 0.95
                current_bankroll += win_amount
            else:
                current_bankroll += bet_size
        elif result == 'Tie':
            bankroll_progress.append(current_bankroll)
            previous_result = mapped_result
            continue
        else:
            current_bankroll -= bet_size

        bankroll_progress.append(current_bankroll)
        previous_result = mapped_result

    return bankroll_progress, bet_sizes

# Updated calculate_win_loss_tracker
def calculate_win_loss_tracker(history, base_bet, ai_mode):
    tracker = []
    pair_types = []
    previous_result = None
    st.session_state.result_tracker = 0.0
    st.session_state.profit_lock = 0.0
    st.session_state.bet_amount = base_bet
    st.session_state.consecutive_wins = 0
    st.session_state.consecutive_losses = 0

    for i in range(len(history)):
        current_rounds = history[:i + 1]
        result = history[i]
        mapped_result = 'P' if result == 'Player' else 'B' if result == 'Banker' else 'T'

        # Record pairs
        if previous_result and previous_result != 'T' and mapped_result != 'T':
            pair_types.append((previous_result, mapped_result))

        bet, _, _, _, _ = advanced_bet_selection(current_rounds[:-1], ai_mode) if i != 0 else ('Pass', 0, '', 'Neutral', [])
        if result == 'Tie':
            tracker.append('T')
        elif bet in (None, 'Pass'):
            tracker.append('S')
        elif result == bet:
            tracker.append('W')
            money_management(st.session_state.initial_bankroll, base_bet, result, bet)
        else:
            tracker.append('L')
            money_management(st.session_state.initial_bankroll, base_bet, result, bet)

        previous_result = mapped_result
    return tracker

def main():
    try:
        st.set_page_config(page_title="Mang Baccarat Predictor", page_icon="🎲", layout="wide")
        st.title("Mang Baccarat Predictor")

        # Initialize session state
        if 'history' not in st.session_state:
            st.session_state.history = []
        if 'initial_bankroll' not in st.session_state:
            st.session_state.initial_bankroll = 1000.0
        if 'base_bet' not in st.session_state:
            st.session_state.base_bet = 10.0
        if 'ai_mode' not in st.session_state:
            st.session_state.ai_mode = "Conservative"
        if 'selected_patterns' not in st.session_state:
            st.session_state.selected_patterns = ["Bead Bin", "Win/Loss"]
        if 'screen_width' not in st.session_state:
            st.session_state.screen_width = 1024
        if 'pair_types' not in st.session_state:
            st.session_state.pair_types = []
        if 'previous_result' not in st.session_state:
            st.session_state.previous_result = None
        if 'state_history' not in st.session_state:
            st.session_state.state_history = []
        if 'stats' not in st.session_state:
            st.session_state.stats = {'wins': 0, 'losses': 0, 'ties': 0, 'streaks': [], 'odd_pairs': 0, 'even_pairs': 0}

        st.markdown("""
            <script>
            function updateScreenWidth() {
                const width = window.innerWidth;
                document.getElementById('screen-width-input').value = width;
            }
            window.onload = updateScreenWidth;
            window.onresize = updateScreenWidth;
            </script>
            <input type="hidden" id="screen-width-input">
        """, unsafe_allow_html=True)

        screen_width_input = st.text_input("Screen Width", key="screen_width_input", value=str(st.session_state.screen_width), disabled=True)
        try:
            st.session_state.screen_width = int(screen_width_input) if screen_width_input.isdigit() else 1024
        except ValueError:
            st.session_state.screen_width = 1024

        st.markdown("""
            <style>
            .pattern-scroll {
                overflow-x: auto;
                white-space: nowrap;
                max-width: 100%;
                padding: 10px;
                border: 1px solid #e1e1e1;
                background-color: #f9f9f9;
            }
            .pattern-scroll::-webkit-scrollbar {
                height: 8px;
            }
            .pattern-scroll::-webkit-scrollbar-thumb {
                background-color: #888;
                border-radius: 4px;
            }
            .stButton > button {
                width: 100%;
                padding: 8px;
                margin: 5px 0;
            }
            .stNumberInput, .stSelectbox {
                width: 100% !important;
            }
            .stExpander {
                margin-bottom: 10px;
            }
            h1 {
                font-size: 2.5rem;
                text-align: center;
            }
            h3 {
                font-size: 1.5rem;
            }
            p, div, span {
                font-size: 1rem;
            }
            .pattern-circle {
                width: 22px;
                height: 22px;
                display: inline-block;
                margin: 2px;
            }
            .display-circle {
                width: 22px;
                height: 22px;
                display: inline-block;
                margin: 2px;
            }
            @media (min-width: 769px) {
                .stButton > button, .stNumberInput, .stSelectbox {
                    max-width: 200px;
                }
            }
            @media (max-width: 768px) {
                h1 {
                    font-size: 1.8rem;
                }
                h3 {
                    font-size: 1.2rem;
                }
                p, div, span {
                    font-size: 0.9rem;
                }
                .pattern-circle, .display-circle {
                    width: 16px !important;
                    height: 16px !important;
                }
                .stButton > button {
                    font-size: 0.9rem;
                    padding: 6px;
                }
                .stNumberInput input, .stSelectbox div {
                    font-size: 0.9rem;
                }
                .st-emotion-cache-1dj3wfg {
                    flex-wrap: wrap;
                }
            }
            </style>
            <script>
            function autoScrollPatterns() {
                const containers = [
                    'bead-bin-scroll',
                    'big-road-scroll',
                    'big-eye-scroll',
                    'cockroach-scroll',
                    'win-loss-scroll'
                ];
                containers.forEach(id => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.scrollLeft = element.scrollWidth;
                    }
                });
            }
            window.onload = autoScrollPatterns;
            </script>
        """, unsafe_allow_html=True)

        with st.expander("Game Settings", expanded=False):
            cols = st.columns(3)
            with cols[0]:
                initial_bankroll = st.number_input("Initial Bankroll", min_value=1.0, value=st.session_state.initial_bankroll, step=10.0, format="%.2f")
            with cols[1]:
                base_bet = st.number_input("Base Bet (Unit Size)", min_value=1.0, max_value=100.0, value=st.session_state.base_bet, step=1.0, format="%.2f")
            with cols[2]:
                ai_mode = st.selectbox("AI Mode", ["Conservative", "Aggressive"], index=["Conservative", "Aggressive"].index(st.session_state.ai_mode))

            st.session_state.initial_bankroll = initial_bankroll
            st.session_state.base_bet = base_bet
            st.session_state.ai_mode = ai_mode

            st.markdown("**Money Management**: Balanced Progression (increases bet after loss, resets after win, with profit lock at 3x base bet and stop-loss at -10x base bet)")

        with st.expander("Input Game Results", expanded=True):
            cols = st.columns(4)
            with cols[0]:
                if st.button("Player"):
                    result = "Player"
                    mapped_result = 'P'
                    if st.session_state.previous_result and st.session_state.previous_result != 'T' and mapped_result != 'T':
                        pair_type = "Even" if st.session_state.previous_result == mapped_result else "Odd"
                        st.session_state.pair_types.append((st.session_state.previous_result, mapped_result))
                        st.session_state.stats['odd_pairs' if pair_type == "Odd" else 'even_pairs'] += 1
                    st.session_state.history.append(result)
                    st.session_state.stats['ties' if result == 'Tie' else 'wins' if result in ['Player', 'Banker'] else 'ties'] += 1
                    st.session_state.previous_result = mapped_result
                    st.rerun()
            with cols[1]:
                if st.button("Banker"):
                    result = "Banker"
                    mapped_result = 'B'
                    if st.session_state.previous_result and st.session_state.previous_result != 'T' and mapped_result != 'T':
                        pair_type = "Even" if st.session_state.previous_result == mapped_result else "Odd"
                        st.session_state.pair_types.append((st.session_state.previous_result, mapped_result))
                        st.session_state.stats['odd_pairs' if pair_type == "Odd" else 'even_pairs'] += 1
                    st.session_state.history.append(result)
                    st.session_state.stats['ties' if result == 'Tie' else 'wins' if result in ['Player', 'Banker'] else 'ties'] += 1
                    st.session_state.previous_result = mapped_result
                    st.rerun()
            with cols[2]:
                if st.button("Tie"):
                    result = "Tie"
                    mapped_result = 'T'
                    st.session_state.history.append(result)
                    st.session_state.stats['ties'] += 1
                    st.session_state.previous_result = mapped_result
                    st.rerun()
            with cols[3]:
                undo_clicked = st.button("Undo", disabled=len(st.session_state.history) == 0)
                if undo_clicked and len(st.session_state.history) == 0:
                    st.warning("No results to undo!")
                elif undo_clicked:
                    if st.session_state.state_history:
                        last_state = st.session_state.state_history.pop()
                        st.session_state.pair_types = last_state['pair_types']
                        st.session_state.previous_result = last_state['previous_result']
                        st.session_state.result_tracker = last_state['result_tracker']
                        st.session_state.profit_lock = last_state['profit_lock']
                        st.session_state.bet_amount = last_state['bet_amount']
                        st.session_state.consecutive_wins = last_state['consecutive_wins']
                        st.session_state.consecutive_losses = last_state['consecutive_losses']
                        st.session_state.stats = last_state['stats']
                        st.session_state.history.pop()
                        st.info("Last action undone.")
                    else:
                        st.session_state.history.pop()
                        st.session_state.previous_result = None if not st.session_state.history else ('P' if st.session_state.history[-1] == 'Player' else 'B' if st.session_state.history[-1] == 'Banker' else 'T')
                        if st.session_state.pair_types:
                            st.session_state.pair_types.pop()
                        st.info("Last action undone.")
                    st.rerun()

        with st.expander("Shoe Patterns", expanded=False):
            pattern_options = ["Bead Bin", "Big Road", "Big Eye", "Cockroach", "Win/Loss"]
            selected_patterns = st.multiselect(
                "Select Patterns to Display",
                pattern_options,
                default=st.session_state.selected_patterns,
                key="pattern_select"
            )
            st.session_state.selected_patterns = selected_patterns

            max_display_cols = 10 if st.session_state.screen_width < 768 else 14

            if "Bead Bin" in st.session_state.selected_patterns:
                st.markdown("### Bead Bin")
                sequence = [r for r in st.session_state.history][-84:]
                sequence = ['P' if result == 'Player' else 'B' if result == 'Banker' else 'T' for result in sequence]
                grid = [['' for _ in range(max_display_cols)] for _ in range(6)]
                for i, result in enumerate(sequence):
                    if result in ['P', 'B', 'T']:
                        col = i // 6
                        row = i % 6
                        if col < max_display_cols:
                            color = '#3182ce' if result == 'P' else '#e53e3e' if result == 'B' else '#38a169'
                            grid[row][col] = f'<div class="pattern-circle" style="background-color: {color}; border-radius: 50%; border: 1px solid #ffffff;"></div>'
                st.markdown('<div id="bead-bin-scroll" class="pattern-scroll">', unsafe_allow_html=True)
                for row in grid:
                    st.markdown(' '.join(row), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                if not st.session_state.history:
                    st.markdown("No results yet. Enter results below.")

            if "Big Road" in st.session_state.selected_patterns:
                st.markdown("### Big Road")
                big_road_grid, num_cols = build_big_road(st.session_state.history)
                if num_cols > 0:
                    display_cols = min(num_cols, max_display_cols)
                    st.markdown('<div id="big-road-scroll" class="pattern-scroll">', unsafe_allow_html=True)
                    for row in range(6):
                        row_display = []
                        for col in range(display_cols):
                            outcome = big_road_grid[row][col]
                            if outcome == 'P':
                                row_display.append(f'<div class="pattern-circle" style="background-color: #3182ce; border-radius: 50%; border: 1px solid #ffffff;"></div>')
                            elif outcome == 'B':
                                row_display.append(f'<div class="pattern-circle" style="background-color: #e53e3e; border-radius: 50%; border: 1px solid #ffffff;"></div>')
                            elif outcome == 'T':
                                row_display.append(f'<div class="pattern-circle" style="border: 2px solid #38a169; border-radius: 50%;"></div>')
                            else:
                                row_display.append(f'<div class="display-circle"></div>')
                        st.markdown(''.join(row_display), unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown("No Big Road Malformed data.")

            if "Big Eye" in st.session_state.selected_patterns:
                st.markdown("### Big Eye Boy")
                st.markdown("<p style='font-size: 12px; color: #666666;'>Red (🔴): Repeat Pattern, Blue (🔵): Break Pattern</p>", unsafe_allow_html=True)
                big_road_grid, num_cols = build_big_road(st.session_state.history)
                big_eye_grid, big_eye_cols = build_big_eye_boy(big_road_grid, num_cols)
                if big_eye_cols > 0:
                    display_cols = min(big_eye_cols, max_display_cols)
                    st.markdown('<div id="big-eye-scroll" class="pattern-scroll">', unsafe_allow_html=True)
                    for row in range(6):
                        row_display = []
                        for col in range(display_cols):
                            outcome = big_eye_grid[row][col]
                            if outcome == 'R':
                                row_display.append(f'<div class="pattern-circle" style="background-color: #e53e3e; border-radius: 50%; border: 1px solid #000000;"></div>')
                            elif outcome == 'B':
                                row_display.append(f'<div class="pattern-circle" style="background-color: #3182ce; border-radius: 50%; border: 1px solid #000000;"></div>')
                            else:
                                row_display.append(f'<div class="display-circle"></div>')
                        st.markdown(''.join(row_display), unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown("No recent Big Eye data.")

            if "Cockroach" in st.session_state.selected_patterns:
                st.markdown("### Cockroach Pig")
                st.markdown("<p style='font-size: 12px; color: #666666;'>Red (🔴): Repeat Pattern, Blue (🔵): Break Pattern</p>", unsafe_allow_html=True)
                big_road_grid, num_cols = build_big_road(st.session_state.history)
                cockroach_grid, cockroach_cols = build_cockroach_pig(big_road_grid, num_cols)
                if cockroach_cols > 0:
                    display_cols = min(cockroach_cols, max_display_cols)
                    st.markdown('<div id="cockroach-scroll" class="pattern-scroll">', unsafe_allow_html=True)
                    for row in range(6):
                        row_display = []
                        for col in range(display_cols):
                            outcome = cockroach_grid[row][col]
                            if outcome == 'R':
                                row_display.append(f'<div class="pattern-circle" style="background-color: #e53e3e; border-radius: 50%; border: 1px solid #000000;"></div>')
                            elif outcome == 'B':
                                row_display.append(f'<div class="pattern-circle" style="background-color: #3182ce; border-radius: 50%; border: 1px solid #000000;"></div>')
                            else:
                                row_display.append(f'<div class="display-circle"></div>')
                        st.markdown(''.join(row_display), unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown("No recent Cockroach data.")

            if "Win/Loss" in st.session_state.selected_patterns:
                st.markdown("### Win/Loss")
                st.markdown("<p style='font-size: 12px; color: #666666;'>Green (🟢): Win, Red (🔴): Loss, Gray (⬜): Skip or Tie</p>", unsafe_allow_html=True)
                tracker = calculate_win_loss_tracker(st.session_state.history, st.session_state.base_bet, st.session_state.ai_mode)[-max_display_cols:]
                row_display = []
                for result in tracker:
                    if result in ['W', 'L', 'S', 'T']:
                        color = '#38a169' if result == 'W' else '#e53e3e' if result == 'L' else '#A0AEC0'
                        row_display.append(f'<div class="pattern-circle" style="background-color: {color}; border-radius: 50%; border: 1px solid #000000;"></div>')
                    else:
                        row_display.append(f'<div class="display-circle"></div>')
                st.markdown('<div id="win-loss-scroll" class="pattern-scroll">', unsafe_allow_html=True)
                st.markdown(''.join(row_display), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                if not st.session_state.history:
                    st.markdown("No results yet. Enter results below.")

        with st.expander("Prediction", expanded=True):
            st.markdown("### Prediction")
            current_bankroll = calculate_bankroll(st.session_state.history, st.session_state.base_bet)[0][-1] if st.session_state.history else st.session_state.initial_bankroll
            bet, confidence, reason, emotional_tone, pattern_insights = advanced_bet_selection(st.session_state.history, st.session_state.ai_mode)
            recommended_bet_size, _, stop_loss = money_management(current_bankroll, st.session_state.base_bet)
            if current_bankroll < max(1.0, st.session_state.base_bet):
                st.warning("Insufficient bankroll to place a bet. Please increase your bankroll or reset the game.")
                bet = 'Pass'
                confidence = 0
                reason = "Bankroll too low to continue betting."
                emotional_tone = "Cautious"
                pattern_insights = ["Insufficient bankroll"]
            elif stop_loss:
                bet = 'Pass'
                confidence = 0
                reason = "Loss limit reached. Pausing betting until reset."
                emotional_tone = "Cautious"
                pattern_insights.append("Stop-loss activated")
            if bet == 'Pass':
                st.markdown("**No Bet**: Insufficient confidence or bankroll to place a bet.")
            else:
                st.markdown(f"**Bet**: {bet} | **Confidence**: {confidence}% | **Bet Size**: ${recommended_bet_size:.2f} | **Mood**: {emotional_tone}")
                st.markdown(f"**Profit Lock**: ${st.session_state.profit_lock:.2f}")
            st.markdown(f"**Reasoning**: {reason}")
            if pattern_insights:
                st.markdown("### Pattern Insights")
                st.markdown("Detected patterns influencing the prediction:")
                for insight in pattern_insights:
                    st.markdown(f"- {insight}")

        with st.expander("Bankroll Progress", expanded=True):
            bankroll_progress, bet_sizes = calculate_bankroll(st.session_state.history, st.session_state.base_bet)
            if bankroll_progress:
                st.markdown("### Bankroll Progress")
                total_hands = len(bankroll_progress)
                for i in range(total_hands):
                    hand_number = total_hands - i
                    val = bankroll_progress[total_hands - i - 1]
                    bet_size = bet_sizes[total_hands - i - 1]
                    bet_display = f"Bet ${bet_size:.2f}" if bet_size > 0 else "No Bet"
                    st.markdown(f"Hand {hand_number}: ${val:.2f} | {bet_display}")
                st.markdown(f"**Current Bankroll**: ${bankroll_progress[-1]:.2f}")
                st.markdown(f"**Profit Lock**: ${st.session_state.profit_lock:.2f}")

                st.markdown("### Bankroll Progression Chart")
                labels = [f"Hand {i+1}" for i in range(len(bankroll_progress))]
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=labels,
                        y=bankroll_progress,
                        mode='lines+markers',
                        name='Bankroll',
                        line=dict(color='#38a169', width=2),
                        marker=dict(size=6)
                    )
                )
                fig.update_layout(
                    title=dict(text="Bankroll Over Time", x=0.5, xanchor='center'),
                    xaxis_title="Hand",
                    yaxis_title="Bankroll ($)",
                    xaxis=dict(tickangle=45),
                    yaxis=dict(autorange=True),
                    template="plotly_white",
                    height=400,
                    margin=dict(l=40, r=40, t=50, b=100)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown(f"**Current Bankroll**: ${st.session_state.initial_bankroll:.2f}")
                st.markdown(f"**Profit Lock**: ${st.session_state.profit_lock:.2f}")
                st.markdown("No bankroll history yet. Enter results below.")

        with st.expander("Reset", expanded=False):
            if st.button("New Game"):
                final_bankroll = calculate_bankroll(st.session_state.history, st.session_state.base_bet)[0][-1] if st.session_state.history else st.session_state.initial_bankroll
                st.session_state.history = []
                st.session_state.initial_bankroll = max(1.0, final_bankroll + st.session_state.profit_lock)
                st.session_state.base_bet = min(10.0, st.session_state.initial_bankroll)
                st.session_state.ai_mode = "Conservative"
                st.session_state.selected_patterns = ["Bead Bin", "Win/Loss"]
                st.session_state.pair_types = []
                st.session_state.previous_result = None
                st.session_state.state_history = []
                st.session_state.result_tracker = 0.0
                st.session_state.profit_lock = 0.0
                st.session_state.bet_amount = st.session_state.base_bet
                st.session_state.consecutive_wins = 0
                st.session_state.consecutive_losses = 0
                st.session_state.stats = {'wins': 0, 'losses': 0, 'ties': 0, 'streaks': [], 'odd_pairs': 0, 'even_pairs': 0}
                st.rerun()

    except (KeyError, ValueError, IndexError) as e:
        logging.error(f"Error in main: {str(e)}")
        st.error(f"Error occurred: {str(e)}. Please try refreshing the page or resetting the game.")
    except Exception as e:
        logging.error(f"Unexpected error in main: {str(e)}")
        st.error(f"Unexpected error: {str(e)}. Contact support if this persists.")

if __name__ == "__main__":
    main()
