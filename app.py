import streamlit as st
import logging
import plotly.graph_objects as go
import math
import json
import os

# Set up logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Unified state management class
class BaccaratState:
    def __init__(self):
        self.history = []
        self.pair_types = []
        self.previous_result = None
        self.state_history = []
        self.bet_amount = 1.0
        self.unit = 1.0
        self.result_tracker = 1000.0  # Initial bankroll
        self.max_profit = 0.0
        self.current_dominance = "N/A"
        self.next_prediction = "N/A"
        self.t3_level = 1
        self.t3_results = []

    def save(self, filename="baccarat_session.json"):
        try:
            with open(filename, "w" if os.path.exists(filename) else "x") as f:
                json.dump({
                    "history": self.history,
                    "pair_types": self.pair_types,
                    "previous_result": self.previous_result,
                    "state_history": self.state_history,
                    "bet_amount": self.bet_amount,
                    "unit": self.unit,
                    "result_tracker": self.result_tracker,
                    "max_profit": self.max_profit,
                    "current_dominance": self.current_dominance,
                    "next_prediction": self.next_prediction,
                    "t3_level": self.t3_level,
                    "t3_results": self.t3_results
                }, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving session: {e}")
            return False

    def load(self, filename="baccarat_session.json"):
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    data = json.load(f)
                    self.history = data.get("history", [])
                    self.pair_types = data.get("pair_types", [])
                    self.previous_result = data.get("previous_result", None)
                    self.state_history = data.get("state_history", [])
                    self.bet_amount = data.get("bet_amount", 1.0)
                    self.unit = data.get("unit", 1.0)
                    self.result_tracker = data.get("result_tracker", 1000.0)
                    self.max_profit = data.get("max_profit", 0.0)
                    self.current_dominance = data.get("current_dominance", "N/A")
                    self.next_prediction = data.get("next_prediction", "N/A")
                    self.t3_level = data.get("t3_level", 1)
                    self.t3_results = data.get("t3_results", [])
                return True
            return False
        except Exception as e:
            logging.error(f"Error loading session: {e}")
            return False

# Normalize input
def normalize(s):
    s = s.strip().lower()
    if s in ('banker', 'b'):
        return 'Banker'
    if s in ('player', 'p'):
        return 'Player'
    if s in ('tie', 't'):
        return 'Tie'
    return None

# Pattern detection functions
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

def is_alternating(s, min_length=4):
    if len(s) < min_length:
        return False
    for i in range(len(s) - 1):
        if s[i] == s[i + 1]:
            return False
    return True

def is_zigzag(s):
    if len(s) < 3:
        return False
    for i in range(len(s) - 2):
        if s[i] == s[i + 2] and s[i] != s[i + 1]:
            return True
    return False

def recent_trend(s, window=10):
    recent = s[-window:] if len(s) >= window else s
    if not recent:
        return None, 0
    freq = frequency_count(recent)
    total = len(recent)
    if total == 0:
        return None, 0
    banker_ratio = freq['Banker'] / total
    player_ratio = freq['Player'] / total
    if banker_ratio > player_ratio + 0.2:
        return 'Banker', min(banker_ratio * 50, 80)
    elif player_ratio > banker_ratio + 0.2:
        return 'Player', min(player_ratio * 50, 80)
    return None, 0

def frequency_count(s):
    count = {'Banker': 0, 'Player': 0, 'Tie': 0}
    for r in s:
        if r in count:
            count[r] += 1
    return count

# Roadmap functions
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

# Dominant Pairs betting logic (enhanced with roadmap integration)
def dominant_pairs_bet_selection(state):
    if not state.history or len(state.history) < 2:
        return 'Pass', 0, "Not enough results to form a pair.", "Cautious", []

    result = state.history[-1]
    reason_parts = []
    pattern_insights = []
    emotional_tone = "Neutral"
    confidence = 0

    # Map result
    mapped_result = 'P' if result == 'Player' else 'B' if result == 'Banker' else None
    if mapped_result is None:
        return 'Pass', 0, "Last result was a Tie. Waiting for Player or Banker.", "Cautious", []

    # Save state for undo
    state_copy = {
        'pair_types': state.pair_types.copy(),
        'previous_result': state.previous_result,
        'result_tracker': state.result_tracker,
        'bet_amount': state.bet_amount,
        'current_dominance': state.current_dominance,
        'next_prediction': state.next_prediction
    }
    state.state_history.append(state_copy)

    # Update pair_types
    if state.previous_result is not None:
        pair = (state.previous_result, mapped_result)
        state.pair_types.append(pair)
        pair_type = "Even" if pair[0] == pair[1] else "Odd"
        pattern_insights.append(f"Pair: {pair} ({pair_type})")
        reason_parts.append(f"Recorded pair: {pair} ({pair_type})")
    else:
        reason_parts.append("First result recorded. Waiting for second result.")
        state.previous_result = mapped_result
        return 'Pass', 0, " ".join(reason_parts), "Cautious", pattern_insights

    state.previous_result = mapped_result

    # Determine dominance and prediction after 5 pairs
    if len(state.pair_types) >= 5:
        odd_count = sum(1 for a, b in state.pair_types if a != b)
        even_count = sum(1 for a, b in state.pair_types if a == b)
        pattern_insights.append(f"Odd pairs: {odd_count}, Even pairs: {even_count}")

        # Integrate Big Road and Big Eye Boy
        big_road_grid, num_cols = build_big_road(state.history)
        big_eye_grid, big_eye_cols = build_big_eye_boy(big_road_grid, num_cols)
        roadmap_bonus = 0
        if big_eye_cols > 1:
            last_signal = next((big_eye_grid[row][big_eye_cols-1] for row in range(6) if big_eye_grid[row][big_eye_cols-1] in ['R', 'B']), None)
            if last_signal == 'R':
                roadmap_bonus = 10
                pattern_insights.append("Big Eye Boy: Repeat pattern detected")
            elif last_signal == 'B':
                roadmap_bonus = -10
                pattern_insights.append("Big Eye Boy: Break pattern detected")

        if odd_count > even_count:
            state.current_dominance = "Odd"
            state.next_prediction = 'Player' if mapped_result == 'B' else 'Banker'
            confidence = min(50 + (odd_count - even_count) * 5 + roadmap_bonus, 85)
            reason_parts.append(f"Odd dominance ({odd_count} vs {even_count}). Predicting {state.next_prediction}.")
            pattern_insights.append(f"Dominance: Odd (predict {state.next_prediction})")
            emotional_tone = "Confident"
        else:
            state.current_dominance = "Even"
            state.next_prediction = 'Player' if mapped_result == 'P' else 'Banker'
            confidence = min(50 + (even_count - odd_count) * 5 + roadmap_bonus, 85)
            reason_parts.append(f"Even dominance ({even_count} vs {odd_count}). Predicting {state.next_prediction}.")
            pattern_insights.append(f"Dominance: Even (predict {state.next_prediction})")
            emotional_tone = "Confident"
    else:
        state.next_prediction = 'Pass'
        confidence = 0
        reason_parts.append(f"Only {len(state.pair_types)} pairs recorded. Need 5 pairs to predict.")
        emotional_tone = "Cautious"

    return state.next_prediction, confidence, " ".join(reason_parts), emotional_tone, pattern_insights

# Advanced bet selection (includes Dominant Pairs and other strategies)
def advanced_bet_selection(state, mode='Conservative'):
    if mode == 'Dominant Pairs':
        return dominant_pairs_bet_selection(state)

    max_recent_count = 40
    recent = state.history[-max_recent_count:] if len(state.history) >= max_recent_count else state.history
    if not recent:
        return 'Pass', 0, "No results yet.", "Cautious", []

    scores = {'Banker': 0, 'Player': 0, 'Tie': 0}
    reason_parts = []
    pattern_insights = []
    emotional_tone = "Neutral"
    confidence = 0
    pattern_count = 0
    shoe_position = len(state.history)

    def decay_weight(index, total_length, half_life=20):
        return 0.5 ** ((total_length - index - 1) / half_life)

    # Streak detection
    streak_value, streak_length = detect_streak(recent)
    if streak_length >= 3 and streak_value != "Tie":
        streak_score = min(25 + (streak_length - 3) * 8, 50)
        if streak_length >= 6:
            streak_score += 10
            pattern_insights.append(f"Dragon Tail: {streak_length} {streak_value}")
            emotional_tone = "Confident"
        scores[streak_value] += streak_score
        reason_parts.append(f"Streak of {streak_length} {streak_value} wins detected.")
        pattern_insights.append(f"Streak: {streak_length} {streak_value}")
        pattern_count += 1
        if streak_length >= 5 and mode == 'Aggressive':
            contrarian_bet = 'Player' if streak_value == 'Banker' else 'Banker'
            scores[contrarian_bet] += 20
            reason_parts.append(f"Long streak ({streak_length}); considering break.")
            pattern_insights.append("Possible streak break")
            emotional_tone = "Skeptical"

    # Alternating pattern
    if len(recent) >= 6 and is_alternating(recent[-6:], min_length=6):
        last = recent[-1]
        alternate_bet = 'Player' if last == 'Banker' else 'Banker'
        scores[alternate_bet] += 35
        reason_parts.append("Strong alternating pattern (Ping Pong) in last 6 hands.")
        pattern_insights.append("Ping Pong: Alternating P/B")
        pattern_count += 1
        emotional_tone = "Excited"

    # Zigzag pattern
    if is_zigzag(recent[-8:]):
        last = recent[-1]
        zigzag_bet = 'Player' if last == 'Banker' else 'Banker'
        zigzag_score = 30 if shoe_position < 30 else 20
        scores[zigzag_bet] += zigzag_score
        reason_parts.append("Zigzag pattern detected in last 8 hands.")
        pattern_insights.append("Zigzag: P-B-P/B-P-B")
        pattern_count += 1
        emotional_tone = "Curious"

    # Recent trend
    trend_bet, trend_score = recent_trend(recent, window=12)
    if trend_bet:
        trend_weight = trend_score * (1 if shoe_position < 20 else 0.8)
        scores[trend_bet] += min(trend_weight, 35)
        reason_parts.append(f"Recent trend favors {trend_bet} in last 12 hands.")
        pattern_insights.append(f"Trend: {trend_bet} dominance")
        emotional_tone = "Hopeful"

    # Big Road
    big_road_grid, num_cols = build_big_road(recent)
    if num_cols > 0:
        last_col = [big_road_grid[row][num_cols - 1] for row in range(6)]
        col_length = sum(1 for x in last_col if x in ['P', 'B'])
        if col_length >= 3:
            bet_side = 'Player' if last_col[0] == 'P' else 'Banker'
            col_score = 25 if col_length == 3 else 35 if col_length == 4 else 45
            scores[bet_side] += col_score
            reason_parts.append(f"Big Road column of {col_length} {bet_side}.")
            pattern_insights.append(f"Big Road: {col_length} {bet_side}")
            pattern_count += 1

    # Big Eye Boy
    big_eye_grid, big_eye_cols = build_big_eye_boy(big_road_grid, num_cols)
    if big_eye_cols > 1:
        last_two_cols = [[big_eye_grid[row][c] for row in range(6)] for c in range(big_eye_cols - 2, big_eye_cols)]
        last_signals = [next((x for x in col if x in ['R', 'B']), None) for col in last_two_cols]
        if all(s == 'R' for s in last_signals if s):
            last_side = 'Player' if big_road_grid[0][num_cols - 1] == 'P' else 'Banker'
            scores[last_side] += 20
            reason_parts.append("Big Eye Boy shows consistent repeat pattern.")
            pattern_insights.append("Big Eye Boy: Consistent repeat")
            pattern_count += 1
        elif all(s == 'B' for s in last_signals if s):
            opposite_side = 'Player' if big_road_grid[0][num_cols - 1] == 'B' else 'Banker'
            scores[opposite_side] += 15
            reason_parts.append("Big Eye Boy shows consistent break pattern.")
            pattern_insights.append("Big Eye Boy: Consistent break")
            pattern_count += 1

    # Cockroach Pig
    cockroach_grid, cockroach_cols = build_cockroach_pig(big_road_grid, num_cols)
    if cockroach_cols > 1:
        last_two_cols = [[cockroach_grid[row][c] for row in range(6)] for c in range(cockroach_cols - 2, cockroach_cols)]
        last_signals = [next((x for x in col if x in ['R', 'B']), None) for col in last_two_cols]
        if all(s == 'R' for s in last_signals if s):
            last_side = 'Player' if big_road_grid[0][num_cols - 1] == 'P' else 'Banker'
            scores[last_side] += 15
            reason_parts.append("Cockroach Pig shows consistent repeat pattern.")
            pattern_insights.append("Cockroach Pig: Consistent repeat")
            pattern_count += 1
        elif all(s == 'B' for s in last_signals if s):
            opposite_side = 'Player' if big_road_grid[0][num_cols - 1] == 'B' else 'Banker'
            scores[opposite_side] += 12
            reason_parts.append("Cockroach Pig shows consistent break pattern.")
            pattern_insights.append("Cockroach Pig: Consistent break")
            pattern_count += 1

    # Entropy adjustment
    freq = frequency_count(recent)
    total = len(recent)
    if total > 0:
        entropy = -sum((count / total) * math.log2(count / total) for count in freq.values() if count > 0)
        if entropy > 1.5:
            for key in scores:
                scores[key] *= 0.7
            reason_parts.append("High randomness detected; lowering confidence.")
            pattern_insights.append("Randomness: High entropy")
            emotional_tone = "Cautious"

    # Recent momentum
    recent_wins = recent[-6:] if len(recent) >= 6 else recent
    for i, result in enumerate(recent_wins):
        if result in ['Banker', 'Player']:
            weight = decay_weight(i, len(recent_wins))
            scores[result] += 15 * weight
    reason_parts.append("Weighted recent momentum applied.")

    # Long-term frequency
    if total > 0:
        banker_ratio = freq['Banker'] / total
        player_ratio = freq['Player'] / total
        tie_ratio = freq['Tie'] / total
        scores['Banker'] += (banker_ratio * 0.9) * 25
        scores['Player'] += (player_ratio * 1.0) * 25
        scores['Tie'] += (tie_ratio * 0.6) * 25 if tie_ratio > 0.25 else 0
        reason_parts.append(f"Long-term: Banker {freq['Banker']}, Player {freq['Player']}, Tie {freq['Tie']}.")
        pattern_insights.append(f"Frequency: B:{freq['Banker']}, P:{freq['Player']}, T:{freq['Tie']}")

    # Pattern coherence
    if pattern_count >= 3:
        max_score = max(scores['Banker'], scores['Player'])
        if max_score > 0:
            coherence_bonus = 15 if pattern_count == 3 else 20
            max_bet = 'Banker' if scores['Banker'] > scores['Player'] else 'Player'
            scores[max_bet] += coherence_bonus
            reason_parts.append(f"Multiple patterns align on {max_bet} (+{coherence_bonus} bonus).")
            pattern_insights.append(f"Coherence: {pattern_count} patterns align")
        else:
            confidence_penalty = 15
            for key in scores:
                scores[key] = max(0, scores[key] - confidence_penalty)
            reason_parts.append("Conflicting patterns detected; reducing confidence.")
            emotional_tone = "Skeptical"

    bet_choice = max(scores, key=scores.get)
    confidence = min(round(max(scores.values(), default=0) * 1.3), 95)

    confidence_threshold = 65 if mode == 'Conservative' else 45
    if confidence < confidence_threshold:
        bet_choice = 'Pass'
        emotional_tone = "Hesitant"
        reason_parts.append(f"Confidence too low ({confidence}% < {confidence_threshold}%). Passing.")
    elif mode == 'Conservative' and confidence < 75:
        emotional_tone = "Cautious"
        reason_parts.append("Moderate confidence; proceeding cautiously.")

    if bet_choice == 'Tie' and (confidence < 85 or freq['Tie'] / total < 0.2):
        scores['Tie'] = 0
        bet_choice = max(scores, key=scores.get)
        confidence = min(round(scores[bet_choice] * 1.3), 95)
        reason_parts.append("Tie bet too risky; switching to safer option.")
        emotional_tone = "Cautious"

    if shoe_position > 60:
        confidence = max(confidence - 10, 40)
        reason_parts.append("Late in shoe; increasing caution.")
        emotional_tone = "Cautious"

    reason = " ".join(reason_parts)
    return bet_choice, confidence, reason, emotional_tone, pattern_insights

# Money management
def money_management(state, strategy, bet_outcome=None):
    min_bet = max(1.0, state.unit)
    max_bet = state.result_tracker

    if state.result_tracker < min_bet:
        logging.warning(f"Bankroll ({state.result_tracker:.2f}) is less than minimum bet ({min_bet:.2f}).")
        return 0.0

    if strategy == "T3":
        if bet_outcome == 'win':
            if not state.t3_results:
                state.t3_level = max(1, state.t3_level - 1)
            state.t3_results.append('W')
        elif bet_outcome == 'loss':
            state.t3_results.append('L')

        if len(state.t3_results) == 3:
            wins = state.t3_results.count('W')
            losses = state.t3_results.count('L')
            if wins > losses:
                state.t3_level = max(1, state.t3_level - 1)
            elif losses > wins:
                state.t3_level += 1
            state.t3_results = []

        calculated_bet = state.unit * state.t3_level
    elif strategy == "Dominant Pairs":
        if bet_outcome == 'win':
            state.bet_amount = state.unit
        elif bet_outcome == 'loss':
            state.bet_amount += state.unit
        calculated_bet = state.bet_amount
    else:  # Flat Betting
        calculated_bet = state.unit

    bet_size = round(calculated_bet / state.unit) * state.unit
    bet_size = max(min_bet, min(bet_size, max_bet))
    return round(bet_size, 2)

# Calculate bankroll and bet sizes
def calculate_bankroll(state, strategy, ai_mode):
    bankroll = state.result_tracker
    current_bankroll = bankroll
    bankroll_progress = []
    bet_sizes = []
    temp_state = BaccaratState()
    temp_state.__dict__.update(state.__dict__)

    for i in range(len(temp_state.history)):
        current_rounds = temp_state.history[:i + 1]
        temp_state.history = current_rounds[:-1]
        bet, confidence, _, _, _ = advanced_bet_selection(temp_state, ai_mode) if i != 0 else ('Pass', 0, '', 'Neutral', [])
        actual_result = current_rounds[i]
        mapped_result = 'P' if actual_result == 'Player' else 'B' if actual_result == 'Banker' else None

        if bet in (None, 'Pass', 'Tie') or actual_result == 'Tie':
            bankroll_progress.append(current_bankroll)
            bet_sizes.append(0.0)
            if mapped_result:
                temp_state.previous_result = mapped_result
            temp_state.history = current_rounds
            continue

        bet_size = money_management(temp_state, strategy, mode=ai_mode)
        if bet_size == 0.0:
            bankroll_progress.append(current_bankroll)
            bet_sizes.append(0.0)
            if mapped_result:
                temp_state.previous_result = mapped_result
            temp_state.history = current_rounds
            continue

        bet_sizes.append(bet_size)
        if actual_result == bet:
            if bet == 'Banker':
                win_amount = bet_size * 0.95
                current_bankroll += win_amount
            else:
                current_bankroll += bet_size
            if strategy in ["T3", "Dominant Pairs"]:
                money_management(temp_state, strategy, bet_outcome='win')
        else:
            current_bankroll -= bet_size
            if strategy in ["T3", "Dominant Pairs"]:
                money_management(temp_state, strategy, bet_outcome='loss')
        bankroll_progress.append(current_bankroll)
        if mapped_result:
            temp_state.previous_result = mapped_result
        temp_state.history = current_rounds
        temp_state.result_tracker = current_bankroll
        if current_bankroll > temp_state.max_profit:
            temp_state.max_profit = current_bankroll
            if strategy == "Dominant Pairs":
                temp_state.unit = 1.0
                temp_state.bet_amount = temp_state.unit

    return bankroll_progress, bet_sizes

# Calculate win/loss tracker
def calculate_win_loss_tracker(state, strategy, ai_mode):
    tracker = []
    temp_state = BaccaratState()
    temp_state.__dict__.update(state.__dict__)

    for i in range(len(temp_state.history)):
        current_rounds = temp_state.history[:i + 1]
        temp_state.history = current_rounds[:-1]
        bet, _, _, _, _ = advanced_bet_selection(temp_state, ai_mode) if i != 0 else ('Pass', 0, '', 'Neutral', [])
        actual_result = current_rounds[i]
        mapped_result = 'P' if actual_result == 'Player' else 'B' if actual_result == 'Banker' else None

        if actual_result == 'Tie':
            tracker.append('T')
        elif bet in (None, 'Pass'):
            tracker.append('S')
        elif actual_result == bet:
            tracker.append('W')
            if strategy in ["T3", "Dominant Pairs"]:
                money_management(temp_state, strategy, bet_outcome='win')
        else:
            tracker.append('L')
            if strategy in ["T3", "Dominant Pairs"]:
                money_management(temp_state, strategy, bet_outcome='loss')
        if mapped_result:
            temp_state.previous_result = mapped_result
        temp_state.history = current_rounds

    return tracker

def main():
    try:
        st.set_page_config(page_title="Mang Baccarat Predictor", page_icon="🎲", layout="wide")
        st.title("Mang Baccarat Predictor")

        # Initialize state
        if 'state' not in st.session_state:
            st.session_state.state = BaccaratState()
        if 'ai_mode' not in st.session_state:
            st.session_state.ai_mode = "Conservative"
        if 'selected_patterns' not in st.session_state:
            st.session_state.selected_patterns = ["Bead Bin", "Win/Loss", "Deal History"]
        if 'screen_width' not in st.session_state:
            st.session_state.screen_width = 1024

        # JavaScript for screen width and auto-scroll
        st.markdown("""
            <script>
            function updateScreenWidth() {
                const width = window.innerWidth;
                document.getElementById('screen-width-input').value = width;
            }
            function autoScrollPatterns() {
                const containers = [
                    'bead-bin-scroll', 'big-road-scroll', 'big-eye-scroll',
                    'cockroach-scroll', 'win-loss-scroll', 'deal-history-scroll'
                ];
                containers.forEach(id => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.scrollLeft = element.scrollWidth;
                    }
                });
            }
            window.onload = function() {
                updateScreenWidth();
                autoScrollPatterns();
            };
            window.onresize = updateScreenWidth;
            </script>
            <input type="hidden" id="screen-width-input">
        """, unsafe_allow_html=True)

        screen_width_input = st.text_input("Screen Width", key="screen_width_input", value=str(st.session_state.screen_width), disabled=True)
        try:
            st.session_state.screen_width = int(screen_width_input) if screen_width_input.isdigit() else 1024
        except ValueError:
            st.session_state.screen_width = 1024

        # CSS for styling
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
        """, unsafe_allow_html=True)

        # Game Settings
        with st.expander("Game Settings", expanded=False):
            cols = st.columns(4)
            with cols[0]:
                initial_bankroll = st.number_input("Initial Bankroll", min_value=1.0, value=st.session_state.state.result_tracker, step=10.0, format="%.2f")
            with cols[1]:
                base_bet = st.number_input("Base Bet (Unit Size)", min_value=1.0, max_value=initial_bankroll, value=st.session_state.state.unit, step=1.0, format="%.2f")
            with cols[2]:
                strategy_options = ["Flat Betting", "T3", "Dominant Pairs"]
                money_management_strategy = st.selectbox("Money Management Strategy", strategy_options, index=strategy_options.index(st.session_state.state.money_management_strategy if hasattr(st.session_state.state, 'money_management_strategy') else "Flat Betting"))
                st.markdown("*Flat Betting: Fixed bet size. T3: Adjusts bet level based on last three outcomes. Dominant Pairs: Increases bet by one unit after loss, resets after win.*")
            with cols[3]:
                ai_mode = st.selectbox("AI Mode", ["Conservative", "Aggressive", "Dominant Pairs"], index=["Conservative", "Aggressive", "Dominant Pairs"].index(st.session_state.ai_mode))

            st.session_state.state.result_tracker = initial_bankroll
            st.session_state.state.unit = base_bet
            st.session_state.state.bet_amount = base_bet
            st.session_state.state.money_management_strategy = money_management_strategy
            st.session_state.ai_mode = ai_mode
            st.markdown(f"**Selected Strategy: {money_management_strategy}**")

        # Session Management
        with st.expander("Session Management", expanded=False):
            cols = st.columns(2)
            with cols[0]:
                if st.button("Save Session"):
                    if st.session_state.state.save():
                        st.success("Session saved to baccarat_session.json")
                    else:
                        st.error("Failed to save session.")
            with cols[1]:
                if st.button("Load Session"):
                    if st.session_state.state.load():
                        st.success("Session loaded from baccarat_session.json")
                        st.rerun()
                    else:
                        st.error("No session file found or error loading.")

        # Input Game Results
        with st.expander("Input Game Results", expanded=True):
            cols = st.columns(4)
            with cols[0]:
                if st.button("Player"):
                    st.session_state.state.history.append("Player")
                    st.rerun()
            with cols[1]:
                if st.button("Banker"):
                    st.session_state.state.history.append("Banker")
                    st.rerun()
            with cols[2]:
                if st.button("Tie"):
                    st.session_state.state.history.append("Tie")
                    st.rerun()
            with cols[3]:
                undo_clicked = st.button("Undo", disabled=len(st.session_state.state.history) == 0)
                if undo_clicked and len(st.session_state.state.history) == 0:
                    st.warning("No results to undo!")
                elif undo_clicked:
                    st.session_state.state.history.pop()
                    if st.session_state.state.state_history:
                        last_state = st.session_state.state.state_history.pop()
                        st.session_state.state.pair_types = last_state['pair_types']
                        st.session_state.state.previous_result = last_state['previous_result']
                        st.session_state.state.bet_amount = last_state['bet_amount']
                        st.session_state.state.current_dominance = last_state['current_dominance']
                        st.session_state.state.next_prediction = last_state['next_prediction']
                    if st.session_state.state.money_management_strategy == "T3" and st.session_state.state.t3_results:
                        st.session_state.state.t3_results.pop()
                    st.rerun()

        # Shoe Patterns
        with st.expander("Shoe Patterns", expanded=False):
            pattern_options = ["Bead Bin", "Big Road", "Big Eye", "Cockroach", "Win/Loss", "Deal History"]
            st.session_state.focused_pattern = st.radio("Focused Pattern", pattern_options, index=0, key="focused_pattern")
            selected_patterns = [st.session_state.focused_pattern]
            st.session_state.selected_patterns = selected_patterns
            max_display_cols = 10 if st.session_state.screen_width < 768 else 14

            if "Bead Bin" in selected_patterns:
                st.markdown("### Bead Bin")
                sequence = [r for r in st.session_state.state.history][-84:]
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
                if not st.session_state.state.history:
                    st.markdown("No results yet.")

            if "Big Road" in selected_patterns:
                st.markdown("### Big Road")
                big_road_grid, num_cols = build_big_road(st.session_state.state.history)
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
                    st.markdown("No Big Road data.")

            if "Big Eye" in selected_patterns:
                st.markdown("### Big Eye Boy")
                st.markdown("<p style='font-size: 12px; color: #666666;'>Red (🔴): Repeat Pattern, Blue (🔵): Break Pattern</p>", unsafe_allow_html=True)
                big_road_grid, num_cols = build_big_road(st.session_state.state.history)
                big_eye_grid, big_eye_cols = build_big_eye_boy(big_road_grid, num_cols)
                if big_eye_cols > 0:
                    display_cols = min(big_eye_cols, max_display_cols)
                    st.markdown('<div id="big-eye-scroll" class="pattern-scroll">', unsafe_allow_html=True)
                    for row in range(6):
                        row_display = []
                        for col in range(display_cols):
                            outcome = big_eye_grid[row][col]
                            if outcome == 'R':
                                row_display.append(f'<div class="pattern-circle" style="background-color: # sabemos que el color rojo es #e53e3e; border-radius: 50%; border: 1px solid #000000;"></div>')
                            elif outcome == 'B':
                                row_display.append(f'<div class="pattern-circle" style="background-color: #3182ce; border-radius: 50%; border: 1px solid #000000;"></div>')
                            else:
                                row_display.append(f'<div class="display-circle"></div>')
                        st.markdown(''.join(row_display), unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown("No recent Big Eye data.")

            if "Cockroach" in selected_patterns:
                st.markdown("### Cockroach Pig")
                st.markdown("<p style='font: 12px; color: #666666;'>Red (🔴): Repeat Pattern, Blue (🔵): Break Pattern</p>", unsafe_allow_html=True)
                big_road_grid, num_cols = build_big_road(st.session_state.state.history)
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

            if "Win/Loss" in selected_patterns:
                st.markdown("### Win/Loss")
                st.markdown("<p style='font-size: 12px; color: #666666;'>Green (🟢): Win, Red (🔴): Loss, Gray (⬜): Skip or Tie</p>", unsafe_allow_html=True)
                tracker = calculate_win_loss_tracker(st.session_state.state, st.session_state.state.money_management_strategy, st.session_state.ai_mode)[-max_display_cols:]
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
                if not st.session_state.state.history:
                    st.markdown("No results yet.")

            if "Deal History" in selected_patterns:
                st.markdown("### Deal History")
                history_text = ""
                for pair in st.session_state.state.pair_types[-100:]:
                    pair_type = "Even" if pair[0] == pair[1] else "Odd"
                    history_text += f"{pair} ({pair_type})\n"
                st.text_area("Deal History", history_text, height=200, disabled=True)
                if not st.session_state.state.pair_types:
                    st.markdown("No pair history yet.")

        # Prediction
        with st.expander("Prediction", expanded=True):
            st.markdown("### Prediction")
            bet, confidence, reason, emotional_tone, pattern_insights = advanced_bet_selection(st.session_state.state, st.session_state.ai_mode)
            current_bankroll = calculate_bankroll(st.session_state.state, st.session_state.state.money_management_strategy, st.session_state.ai_mode)[0][-1] if st.session_state.state.history else st.session_state.state.result_tracker
            recommended_bet_size = money_management(st.session_state.state, st.session_state.state.money_management_strategy)
            if current_bankroll < max(1.0, st.session_state.state.unit):
                st.warning("Insufficient bankroll to place a bet.")
                bet = 'Pass'
                confidence = 0
                reason = "Bankroll too low to continue betting."
                emotional_tone = "Cautious"
            if bet == 'Pass':
                st.markdown("**No Bet**: Insufficient confidence or bankroll.")
            else:
                st.markdown(f"**Bet**: {bet} | **Confidence**: {confidence}% | **Bet Size**: ${recommended_bet_size:.2f} | **Mood**: {emotional_tone}")
            st.markdown(f"**Reasoning**: {reason}")
            if pattern_insights:
                st.markdown("### Pattern Insights")
                st.markdown("Detected patterns influencing the prediction:")
                for insight in pattern_insights:
                    st.markdown(f"- {insight}")

        # Bankroll Progress
        with st.expander("Bankroll Progress", expanded=True):
            bankroll_progress, bet_sizes = calculate_bankroll(st.session_state.state, st.session_state.state.money_management_strategy, st.session_state.ai_mode)
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
                st.markdown(f"**Current Bankroll**: ${st.session_state.state.result_tracker:.2f}")
                st.markdown("No bankroll history yet.")

        # Reset
        with st.expander("Reset", expanded=False):
            if st.button("New Game"):
                final_bankroll = calculate_bankroll(st.session_state.state, st.session_state.state.money_management_strategy, st.session_state.ai_mode)[0][-1] if st.session_state.state.history else st.session_state.state.result_tracker
                st.session_state.state = BaccaratState()
                st.session_state.state.result_tracker = max(1.0, final_bankroll)
                st.session_state.state.unit = min(10.0, st.session_state.state.result_tracker)
                st.session_state.state.bet_amount = st.session_state.state.unit
                st.session_state.state.money_management_strategy = "Flat Betting"
                st.session_state.ai_mode = "Conservative"
                st.session_state.selected_patterns = ["Bead Bin", "Win/Loss", "Deal History"]
                st.rerun()

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        st.error(f"Unexpected error: {str(e)}. Contact support if this persists.")

if __name__ == "__main__":
    main()
