import streamlit as st
import logging

# Set up minimal logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_button_action(action, result=None):
    """Handle button actions."""
    try:
        feedback_placeholder = st.session_state.feedback_placeholder
        feedback_placeholder.empty()
        st.session_state.button_feedback = ""

        with feedback_placeholder.container():
            if action == "record_result" and result in ['P', 'B', 'T']:
                with st.spinner(f"Processing {'Player' if result == 'P' else 'Banker' if result == 'B' else 'Tie'}..."):
                    record_result(result)
                st.session_state.button_feedback = f"Recorded {'Player' if result == 'P' else 'Banker' if result == 'B' else 'Tie'} result."

            elif action == "undo":
                if not st.session_state.state_history:
                    st.session_state.button_feedback = "No actions to undo."
                else:
                    last_state = st.session_state.state_history.pop()
                    for key, value in last_state.items():
                        st.session_state[key] = value
                    st.session_state.button_feedback = "Undid last action."

            elif action == "reset_betting":
                reset_betting()
                st.session_state.button_feedback = "Betting reset."

            elif action == "reset_all":
                reset_all()
                st.session_state.button_feedback = "Started new session."

            if st.session_state.button_feedback:
                st.markdown(f"<div class='feedback-box'>{st.session_state.button_feedback}</div>", unsafe_allow_html=True)
    except Exception as e:
        logging.error(f"Error in handle_button_action: {str(e)}")
        st.session_state.button_feedback = f"Error: {str(e)}"
        feedback_placeholder.markdown(f"<div class='feedback-box'>Error: {str(e)}</div>", unsafe_allow_html=True)

def record_result(result):
    """Record game result."""
    try:
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

        st.session_state.history.append('Player' if result == 'P' else 'Banker' if result == 'B' else 'Tie')

        if result == 'T':
            st.session_state.next_prediction = "N/A" if st.session_state.previous_result is None else st.session_state.next_prediction
            st.session_state.previous_result = st.session_state.previous_result
        else:
            if st.session_state.previous_result is not None:
                pair = (st.session_state.previous_result, result)
                st.session_state.pair_types.append(pair)
                update_prediction_and_betting(result)
            st.session_state.previous_result = result
    except Exception as e:
        logging.error(f"Error in record_result: {str(e)}")
        raise e

def update_prediction_and_betting(result):
    """Update prediction and betting."""
    try:
        last_three = [st.session_state.pair_types[-i][1] for i in range(1, min(4, len(st.session_state.pair_types)))]
        if len(last_three) >= 3 and all(r == result for r in last_three):
            st.session_state.streak_type = result
        else:
            st.session_state.streak_type = None

        if len(st.session_state.pair_types) >= 5:
            recent_pairs = st.session_state.pair_types[-10:]
            odd_count = sum(1 for a, b in recent_pairs if a != b)
            even_count = sum(1 for a, b in recent_pairs if a == b)
            if st.session_state.streak_type:
                st.session_state.next_prediction = "Player" if st.session_state.streak_type == 'P' else 'Banker'
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

            if st.session_state.bet_amount == 0:
                st.session_state.bet_amount = st.session_state.unit
            if len(st.session_state.pair_types) >= 6 and st.session_state.state_history and st.session_state.state_history[-1]['next_prediction'] != "Hold":
                previous_prediction = st.session_state.state_history[-1]['next_prediction']
                effective_bet = max(st.session_state.unit, abs(st.session_state.bet_amount))
                if (previous_prediction == "Player" and result == 'P') or (previous_prediction == "Banker" and result == 'B'):
                    st.session_state.result_tracker += effective_bet
                    st.session_state.consecutive_wins += 1
                    st.session_state.consecutive_losses = 0
                    if st.session_state.result_tracker > st.session_state.profit_lock:
                        st.session_state.profit_lock = st.session_state.result_tracker
                        st.session_state.button_feedback = f"New profit lock: {st.session_state.profit_lock} units! Betting reset."
                        reset_betting()
                    elif st.session_state.consecutive_wins >= 2:
                        st.session_state.bet_amount = max(1, st.session_state.bet_amount - 1)
                else:
                    st.session_state.result_tracker -= effective_bet
                    st.session_state.consecutive_losses += 1
                    st.session_state.consecutive_wins = 0
                    if st.session_state.consecutive_losses >= 3:
                        st.session_state.bet_amount = min(5, st.session_state.bet_amount * 2)
                    else:
                        st.session_state.bet_amount += 1
    except Exception as e:
        logging.error(f"Error in update_prediction_and_betting: {str(e)}")
        raise e

def update_prediction():
    """Update prediction for resets."""
    try:
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
    except Exception as e:
        logging.error(f"Error in update_prediction: {str(e)}")
        raise e

def reset_betting():
    """Reset betting parameters."""
    try:
        st.session_state.result_tracker = 0
        st.session_state.bet_amount = st.session_state.unit
        st.session_state.consecutive_wins = 0
        st.session_state.consecutive_losses = 0
        update_prediction()
    except Exception as e:
        logging.error(f"Error in reset_betting: {str(e)}")
        raise e

def reset_all():
    """Reset session state."""
    try:
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
        st.session_state.button_feedback = ""
    except Exception as e:
        logging.error(f"Error in reset_all: {str(e)}")
        raise e

def main():
    try:
        st.set_page_config(page_title="Mang Baccarat Tracker", page_icon="🎲", layout="wide")
        st.title("Mang Baccarat Tracker")

        # Initialize session state
        for key, value in {
            'history': [],
            'pair_types': [],
            'previous_result': None,
            'result_tracker': 0,
            'profit_lock': 0,
            'bet_amount': 1,
            'unit': 1,
            'next_prediction': "N/A",
            'current_dominance': "N/A",
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'streak_type': None,
            'state_history': [],
            'button_feedback': "",
        }.items():
            if key not in st.session_state:
                st.session_state[key] = value

        if 'feedback_placeholder' not in st.session_state:
            st.session_state.feedback_placeholder = st.empty()

        # CSS and JavaScript
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
                    padding: 10px;
                    margin: 5px 0;
                    background: linear-gradient(to right, #4CAF50, #81C784);
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 1rem;
                }
                .stButton > button:hover {
                    background: linear-gradient(to right, #81C784, #4CAF50);
                }
                .stButton > button:disabled {
                    background: #cccccc;
                    cursor: not-allowed;
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
                .history-circle {
                    width: 18px;
                    height: 18px;
                    display: inline-block;
                    margin: 2px;
                    border-radius: 50%;
                    border: 1px solid #fff;
                }
                .info-box {
                    background-color: #2C2F33;
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 10px;
                }
                .feedback-box {
                    color: #2E7D32;
                    font-size: 0.9rem;
                    margin: 5px 0;
                    padding: 8px;
                    border: 1px solid #4CAF50;
                    border-radius: 4px;
                    background-color: #E8F5E9;
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
                    .history-circle {
                        width: 14px !important;
                        height: 14px !important;
                    }
                    .stButton > button {
                        font-size: 0.9rem;
                        padding: 8px;
                    }
                }
            </style>
            <script>
                function autoScrollHistory() {
                    try {
                        const el = document.getElementById('shoe-history-scroll');
                        if (el) {
                            el.scrollLeft = el.scrollWidth;
                        }
                    } catch (e) {
                        console.error('Error scrolling element shoe-history-scroll: ' + e);
                    }
                }
                window.onload = autoScrollHistory;
                window.onresize = autoScrollHistory;
            </script>
        """, unsafe_allow_html=True)

        # Prediction and Betting Info
        with st.expander("Prediction and Betting Info", expanded=True):
            bet_color = "#2196F3" if st.session_state.next_prediction == "Player" else "#F44336" if st.session_state.next_prediction == "Banker" else "#B0BEC5"
            bet_display = f'<span style="font-weight: bold; background-color: {bet_color}; color: white; padding: 3px 6px; border-radius: 4px;">{st.session_state.next_prediction}</span>'
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

        # Input Game Results
        with st.expander("Input Game Results", expanded=True):
            cols = st.columns(5)
            with cols[0]:
                if st.button("Player", key="player_button"):
                    handle_button_action("record_result", result="P")
            with cols[1]:
                if st.button("Banker", key="banker_button"):
                    handle_button_action("record_result", result="B")
            with cols[2]:
                if st.button("Tie", key="tie_button"):
                    handle_button_action("record_result", result="T")
            with cols[3]:
                if st.button("Undo", key="undo_button", disabled=len(st.session_state.state_history) == 0):
                    handle_button_action("undo")
            with cols[4]:
                if st.button("Reset Betting", key="reset_betting_button"):
                    handle_button_action("reset_betting")

        # Session Control
        with st.expander("Session Control", expanded=False):
            if st.button("New Session", key="new_session_button"):
                handle_button_action("reset_all")

        # Deal History
        with st.expander("Deal History", expanded=True):
            st.markdown("### Deal History")
            try:
                st.markdown('<div id="deal-history-scroll" class="pattern-scroll">', unsafe_allow_html=True)
                history_text = ""
                for i, pair in enumerate(st.session_state.pair_types[-100:], 1):
                    pair_type = "Even" if pair[0] == pair[1] else "Odd"
                    history_text += f"({pair[0]}, {pair[1]}) ({pair_type})\n"
                if history_text:
                    st.markdown(f"```\n{history_text}\n```")
                else:
                    st.markdown("No deal history yet.")
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                logging.error(f"Error rendering Deal History: {str(e)}")
                st.error(f"Error rendering Deal History: {str(e)}")

        # Shoe History
        with st.expander("Shoe History", expanded=True):
            st.markdown("### Shoe History")
            try:
                st.markdown('<div id="shoe-history-scroll" class="pattern-scroll">', unsafe_allow_html=True)
                if st.session_state.history:
                    color_map = {
                        'P': {"style": "background-color: #2196F3; border-radius: 50%; border: 1px solid #fff;"},
                        'B': {"style": "background-color: #F44336; border-radius: 50%; border: 1px solid #fff;"},
                        'T': {"style": "border: 2px solid #4CAF50; border-radius: 50%;"}
                    }
                    sequence = ['P' if r == 'Player' else 'B' if r == 'Banker' else 'T' for r in st.session_state.history][-100:]  # Limit to last 100 for performance
                    history_display = []
                    for result in sequence:
                        style = color_map[result]["style"]
                        history_display.append(f'<div class="history-circle" style="{style}"></div>')
                    st.markdown(''.join(history_display), unsafe_allow_html=True)
                else:
                    st.markdown("No shoe history yet.")
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                logging.error(f"Error rendering Shoe History: {str(e)}")
                st.error(f"Error rendering Shoe History: {str(e)}")

    except Exception as e:
        logging.error(f"Unexpected error in main: {str(e)}")
        st.error(f"Unexpected error: {str(e)}. Contact support.")

if __name__ == "__main__":
    main()
