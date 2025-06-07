import streamlit as st
import logging

# Set up logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

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

def main():
    try:
        st.set_page_config(page_title="Mang Baccarat Tracker with Enhanced Dominant Pairs", page_icon="🎲", layout="wide")
        st.title("Mang Baccarat Tracker with Enhanced Dominant Pairs")

        # Initialize session state
        if 'history' not in st.session_state:
            st.session_state.history = []
        if 'pair_types' not in st.session_state:
            st.session_state.pair_types = []
        if 'previous_result' not in st.session_state:
            st.session_state.previous_result = None
        if 'result_tracker' not in st.session_state:
            st.session_state.result_tracker = 0
        if 'profit_lock' not in st.session_state:
            st.session_state.profit_lock = 0
        if 'bet_amount' not in st.session_state:
            st.session_state.bet_amount = 1
        if 'unit' not in st.session_state:
            st.session_state.unit = 1
        if 'next_prediction' not in st.session_state:
            st.session_state.next_prediction = "N/A"
        if 'current_dominance' not in st.session_state:
            st.session_state.current_dominance = "N/A"
        if 'consecutive_wins' not in st.session_state:
            st.session_state.consecutive_wins = 0
        if 'consecutive_losses' not in st.session_state:
            st.session_state.consecutive_losses = 0
        if 'streak_type' not in st.session_state:
            st.session_state.streak_type = None
        if 'state_history' not in st.session_state:
            st.session_state.state_history = []
        if 'selected_patterns' not in st.session_state:
            st.session_state.selected_patterns = ["Bead Bin"]
        if 'screen_width' not in st.session_state:
            st.session_state.screen_width = 1024

        # Custom CSS for styling
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
                background-color: #7289DA;
                color: white;
                border: none;
                border-radius: 5px;
            }
            .stButton > button:hover {
                background-color: #99AAB5;
            }
            .stSelectbox {
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
            .info-box {
                background-color: #2C2F33;
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 10px;
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
                .stSelectbox div {
                    font-size: 0.9rem;
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
                    'deal-history-scroll'
                ];
                containers.forEach(id => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.scrollLeft = element.scrollWidth;
                    }
                });
            }
            window.onload = autoScrollPatterns;
            window.onresize = autoScrollPatterns;
            </script>
        """, unsafe_allow_html=True)

        # Update screen width
        screen_width_input = st.text_input("Screen Width", key="screen_width_input", value=str(st.session_state.screen_width), disabled=True)
        try:
            st.session_state.screen_width = int(screen_width_input) if screen_width_input.isdigit() else 1024
        except ValueError:
            st.session_state.screen_width = 1024

        # Display prediction and betting info
        with st.expander("Prediction and Betting Info", expanded=True):
            bet_color = "#3182ce" if st.session_state.next_prediction == "Player" else "#e53e3e" if st.session_state.next_prediction == "Banker" else "#ffffff"
            bet_display = f"<span style='font-weight: bold; background-color: {bet_color}; color: white; padding: 2px 5px; border-radius: 3px;'>{st.session_state.next_prediction}</span>"
            st.markdown(f"""
                <div class='info-box'>
                    <p><b>Bet Amount:</b> {max(st.session_state.unit, abs(st.session_state.bet_amount))} unit(s)</p>
                    <p><b>Bankroll:</b> {st.session_state.result_tracker}</p>
                    <p><b>Profit Lock:</b> {st.session_state.profit_lock}</p>
                    <p><b>Bet:</b> {bet_display}</p>
                    <p><b>Current Dominance:</b> {st.session_state.current_dominance}</p>
                    <p><b>Streak:</b> {st.session_state.streak_type if st.session_state.streak_type else 'None'}</p>
                </div>
            """, unsafe_allow_html=True)

        # Input game results
        with st.expander("Input Game Results", expanded=True):
            cols = st.columns(5)
            with cols[0]:
                if st.button("Player"):
                    record_result("P")
                    st.rerun()
            with cols[1]:
                if st.button("Banker"):
                    record_result("B")
                    st.rerun()
            with cols[2]:
                if st.button("Tie"):
                    record_result("T")
                    st.rerun()
            with cols[3]:
                if st.button("Undo", disabled=len(st.session_state.state_history) == 0):
                    undo()
                    st.rerun()
            with cols[4]:
                if st.button("Reset Betting"):
                    reset_betting()
                    st.rerun()

        # Session control
        with st.expander("Session Control", expanded=False):
            if st.button("New Session"):
                reset_all()
                st.rerun()

        # Deal history
        with st.expander("Deal History", expanded=True):
            st.markdown("### Deal History")
            st.markdown('<div id="deal-history-scroll" class="pattern-scroll">', unsafe_allow_html=True)
            history_text = ""
            for i, pair in enumerate(st.session_state.pair_types[-100:], 1):
                pair_type = "Even" if pair[0] == pair[1] else "Odd"
                history_text += f"{pair} ({pair_type})\n"
            if history_text:
                st.text(history_text)
            else:
                st.markdown("No deal history yet.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Shoe patterns
        with st.expander("Shoe Patterns", expanded=True):
            pattern_options = ["Bead Bin", "Big Road", "Big Eye", "Cockroach"]
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
                    st.markdown("No Big Road data.")

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

    except Exception as e:
        logging.error(f"Unexpected error in main: {str(e)}")
        st.error(f"Unexpected error: {str(e)}. Contact support if this persists.")

def record_result(result):
    # Save current state for undo
    state = {
        'history': st.session_state.history.copy(),
        'pair_types': st.session_state.pair_types.copy(),
        'previous_result': st.session_state.previous_result,
        'result_tracker': st.session_state.result_tracker,
        'profit_lock': st.session_state.profit_lock,
        'bet_amount': st.session_state.bet_amount,
        'current_dominance': st.session_state.current_dominance,
        'next_prediction': st.session_state.next_prediction,
        'consecutive_wins': st.session_state.consecutive_wins,
        'consecutive_losses': st.session_state.consecutive_losses,
        'streak_type': st.session_state.streak_type
    }
    st.session_state.state_history.append(state)

    # Append result to history
    st.session_state.history.append('Player' if result == 'P' else 'Banker' if result == 'B' else 'Tie')

    if result == 'T':
        st.session_state.next_prediction = "N/A" if st.session_state.previous_result is None else st.session_state.next_prediction
        st.session_state.previous_result = st.session_state.previous_result
    else:
        if st.session_state.previous_result is not None:
            pair = (st.session_state.previous_result, result)
            st.session_state.pair_types.append(pair)

            # Check for streak
            last_three = [st.session_state.pair_types[-i][1] for i in range(1, min(4, len(st.session_state.pair_types)))]
            if len(last_three) >= 3 and all(r == result for r in last_three):
                st.session_state.streak_type = result
            else:
                st.session_state.streak_type = None

            # Prediction logic
            if len(st.session_state.pair_types) >= 5:
                recent_pairs = st.session_state.pair_types[-10:]
                odd_count = sum(1 for a, b in recent_pairs if a != b)
                even_count = sum(1 for a, b in recent_pairs if a == b)

                if st.session_state.streak_type:
                    st.session_state.next_prediction = "Player" if st.session_state.streak_type == 'P' else "Banker"
                    st.session_state.current_dominance = f"Streak ({st.session_state.streak_type})"
                elif abs(odd_count - even_count) < 2:
                    st.session_state.current_dominance = "N/A"
                    st.session_state.next_prediction = "Hold"
                elif odd_count > even_count:
                    st.session_state.current_dominance = "Odd"
                    st.session_state.next_prediction = "Player" if result == 'B' else "Banker"
                else:
                    st.session_state.current_dominance = "Even"
                    st.session_state.next_prediction = "Player" if result == 'P' else "Banker"

                # Update betting
                if st.session_state.bet_amount == 0:
                    st.session_state.bet_amount = st.session_state.unit

                if len(st.session_state.pair_types) >= 6 and st.session_state.state_history[-1]['next_prediction'] != "Hold":
                    previous_prediction = st.session_state.state_history[-1]['next_prediction']
                    effective_bet = max(st.session_state.unit, abs(st.session_state.bet_amount))
                    if (previous_prediction == "Player" and result == 'P') or \
                       (previous_prediction == "Banker" and result == 'B'):
                        st.session_state.result_tracker += effective_bet
                        st.session_state.consecutive_wins += 1
                        st.session_state.consecutive_losses = 0
                        if st.session_state.result_tracker > st.session_state.profit_lock:
                            st.session_state.profit_lock = st.session_state.result_tracker
                            reset_betting()
                            st.info(f"New profit lock achieved: {st.session_state.profit_lock} units! Betting reset to 1 unit.")
                            return
                        if st.session_state.consecutive_wins >= 2:
                            st.session_state.bet_amount = max(1, st.session_state.bet_amount - 1)
                    else:
                        st.session_state.result_tracker -= effective_bet
                        st.session_state.consecutive_losses += 1
                        st.session_state.consecutive_wins = 0
                        if st.session_state.consecutive_losses >= 3:
                            st.session_state.bet_amount = min(5, st.session_state.bet_amount * 2)
                        else:
                            st.session_state.bet_amount += 1

        st.session_state.previous_result = result

def undo():
    if not st.session_state.state_history:
        st.warning("No actions to undo.")
        return
    last_state = st.session_state.state_history.pop()
    st.session_state.history = last_state['history']
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

def reset_betting():
    st.session_state.result_tracker = 0
    st.session_state.bet_amount = st.session_state.unit
    st.session_state.consecutive_wins = 0
    st.session_state.consecutive_losses = 0
    st.session_state.state_history = []

    if len(st.session_state.pair_types) >= 5:
        recent_pairs = st.session_state.pair_types[-10:]
        odd_count = sum(1 for a, b in recent_pairs if a != b)
        even_count = sum(1 for a, b in recent_pairs if a == b)
        result = st.session_state.previous_result
        if abs(odd_count - even_count) < 2:
            st.session_state.current_dominance = "N/A"
            st.session_state.next_prediction = "Hold"
        elif odd_count > even_count:
            st.session_state.current_dominance = "Odd"
            st.session_state.next_prediction = "Player" if result == 'B' else "Banker"
        else:
            st.session_state.current_dominance = "Even"
            st.session_state.next_prediction = "Player" if result == 'P' else "Banker"
        last_three = [st.session_state.pair_types[-i][1] for i in range(1, min(4, len(st.session_state.pair_types)))]
        if len(last_three) >= 3 and all(r == last_three[0] for r in last_three):
            st.session_state.streak_type = last_three[0]
            st.session_state.next_prediction = "Player" if st.session_state.streak_type == 'P' else "Banker"
            st.session_state.current_dominance = f"Streak ({st.session_state.streak_type})"
    else:
        st.session_state.next_prediction = "N/A"
        st.session_state.current_dominance = "N/A"
        st.session_state.streak_type = None

def reset_all():
    st.session_state.history = []
    st.session_state.pair_types = []
    st.session_state.previous_result = None
    st.session_state.result_tracker = 0
    st.session_state.profit_lock = 0
    st.session_state.bet_amount = st.session_state.unit
    st.session_state.next_prediction = "N/A"
    st.session_state.current_dominance = "N/A"
    st.session_state.consecutive_wins = 0
    st.session_state.consecutive_losses = 0
    st.session_state.streak_type = None
    st.session_state.state_history = []
    st.session_state.selected_patterns = ["Bead Bin"]

if __name__ == "__main__":
    main()
