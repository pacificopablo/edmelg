import streamlit as st
import pandas as pd

class BaccaratPredictor:
    def __init__(self):
        # Initialize session state variables
        if 'pair_types' not in st.session_state:
            st.session_state.pair_types = []
            st.session_state.next_prediction = "N/A"
            st.session_state.unit = 1
            st.session_state.bet_amount = 0
            st.session_state.result_tracker = 0
            st.session_state.profit_lock = 0
            st.session_state.previous_result = None
            st.session_state.state_history = []
            st.session_state.current_dominance = "N/A"
            st.session_state.consecutive_wins = 0
            st.session_state.consecutive_losses = 0
            st.session_state.streak_type = None
            st.session_state.message = ""  # For dynamic feedback

    def reset_betting(self):
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

        st.session_state.message = "Betting has been reset to initial state."

    def reset_all(self):
        st.session_state.pair_types = []
        st.session_state.result_tracker = 0
        st.session_state.profit_lock = 0
        st.session_state.bet_amount = st.session_state.unit
        st.session_state.next_prediction = "N/A"
        st.session_state.previous_result = None
        st.session_state.state_history = []
        st.session_state.current_dominance = "N/A"
        st.session_state.consecutive_wins = 0
        st.session_state.consecutive_losses = 0
        st.session_state.streak_type = None
        st.session_state.message = "All session data has been reset, profit lock reset."

    def record_result(self, result):
        # Save current state for undo
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
            'streak_type': st.session_state.streak_type
        }
        st.session_state.state_history.append(state)

        if st.session_state.previous_result is None:
            st.session_state.previous_result = result
            st.session_state.next_prediction = "N/A"
            return

        pair = (st.session_state.previous_result, result)
        st.session_state.pair_types.append(pair)

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
                        self.reset_betting()
                        st.session_state.message = f"New profit lock achieved: {st.session_state.profit_lock} units! Betting reset to 1 unit."
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

    def undo(self):
        if not st.session_state.state_history:
            st.session_state.message = "No actions to undo."
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
        st.session_state.message = "Last action undone."

    def render(self):
        # Set page configuration
        st.set_page_config(page_title="Baccarat Predictor", layout="centered")

        # Custom CSS for professional look with mobile optimization
        st.markdown("""
            <style>
            .main {
                background-color: #1E2124;
                color: white;
                font-family: 'Helvetica Neue', Arial, sans-serif;
            }
            .stButton>button {
                background: linear-gradient(45deg, #5865F2, #7289DA);
                color: white;
                font-weight: 600;
                font-size: 16px;
                padding: 12px 20px;
                border: none;
                border-radius: 10px;
                width: 140px;
                margin: 5px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                background: linear-gradient(45deg, #99AAB5, #B0B7C3);
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
            }
            @media (max-width: 768px) {
                .stButton>button {
                    font-size: 14px;
                    width: 120px;
                    padding: 10px 15px;
                }
            }
            .title {
                font-size: 32px;
                font-weight: 700;
                text-align: center;
                margin-bottom: 30px;
                color: #FFFFFF;
                letter-spacing: 1px;
            }
            .info-card {
                background-color: #23272A;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                margin-bottom: 25px;
                border: 1px solid #3A3F44;
            }
            .info-text {
                font-size: 16px;
                margin: 12px 0;
                color: #DCDDDE;
            }
            .section-label {
                font-size: 18px;
                font-weight: 600;
                color: #B9BBBE;
                margin-top: 20px;
            }
            .prediction-text {
                font-size: 22px;
                font-weight: 600;
                padding: 12px;
                border-radius: 8px;
                text-align: center;
                margin: 15px 0;
            }
            .prediction-player {
                background-color: #2E7D32;
                color: white;
            }
            .prediction-banker {
                background-color: #D32F2F;
                color: white;
            }
            .prediction-hold {
                background-color: #546E7A;
                color: white;
            }
            .history-card {
                background-color: #23272A;
                padding: 20px;
                border-radius: 12px;
                max-height: 350px;
                overflow-y: auto;
                margin-top: 25px;
                border: 1px solid #3A3F44;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            }
            .history-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
                color: #DCDDDE;
            }
            .history-table th {
                background-color: #2C2F33;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                border-bottom: 2px solid #3A3F44;
                position: sticky;
                top: 0;
                z-index: 1;
            }
            .history-table td {
                padding: 12px;
                border-bottom: 1px solid #3A3F44;
            }
            .history-table tr:nth-child(even) {
                background-color: #2A2D31;
            }
            .history-table tr:hover {
                background-color: #35393F;
            }
            .even-row {
                background-color: rgba(46, 125, 50, 0.2);
            }
            .odd-row {
                background-color: rgba(211, 47, 47, 0.2);
            }
            @media (max-width: 768px) {
                .history-table th, .history-table td {
                    font-size: 12px;
                    padding: 8px;
                }
                .history-card {
                    max-height: 200px;
                }
            }
            .message-box {
                font-size: 14px;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
            }
            .success {
                background-color: #2E7D32;
                color: white;
            }
            .warning {
                background-color: #FFB300;
                color: black;
            }
            </style>
        """, unsafe_allow_html=True)

        # Title
        st.markdown('<div class="title">Enhanced Dominant Pairs Baccarat Predictor</div>', unsafe_allow_html=True)

        # Message placeholder for dynamic feedback
        message_placeholder = st.empty()
        if st.session_state.message:
            message_class = "success" if "profit lock" in st.session_state.message.lower() or "reset" in st.session_state.message.lower() or "undone" in st.session_state.message.lower() else "warning"
            message_placeholder.markdown(f'<div class="message-box {message_class}">{st.session_state.message}</div>', unsafe_allow_html=True)

        # Info section
        with st.container():
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="info-text"><b>Bet Amount:</b> {max(st.session_state.unit, abs(st.session_state.bet_amount))} unit(s)</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-text"><b>Bankroll:</b> {st.session_state.result_tracker}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-text"><b>Profit Lock:</b> {st.session_state.profit_lock}</div>', unsafe_allow_html=True)
            prediction_class = "prediction-player" if st.session_state.next_prediction == "Player" else \
                              "prediction-banker" if st.session_state.next_prediction == "Banker" else \
                              "prediction-hold"
            st.markdown(f'<div class="prediction-text {prediction_class}"><b>Bet:</b> {st.session_state.next_prediction}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-text"><b>Streak:</b> {st.session_state.streak_type if st.session_state.streak_type else "None"}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Single form for all buttons
        with st.form(key="main_form"):
            # Result buttons
            st.markdown('<div class="section-label">Record Result:</div>', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                player_clicked = st.form_submit_button("Player")
            with col2:
                banker_clicked = st.form_submit_button("Banker")
            with col3:
                undo_clicked = st.form_submit_button("Undo")

            # Session control buttons
            st.markdown('<div class="section-label">Session Controls:</div>', unsafe_allow_html=True)
            col4, col5, col6 = st.columns([1, 1, 1])
            with col4:
                reset_bet_clicked = st.form_submit_button("Reset Bet")
            with col5:
                reset_session_clicked = st.form_submit_button("Reset Session")
            with col6:
                new_session_clicked = st.form_submit_button("New Session")

            # Handle form submission
            if any([player_clicked, banker_clicked, undo_clicked, reset_bet_clicked, reset_session_clicked, new_session_clicked]):
                st.session_state.message = ""  # Clear previous message
                if player_clicked:
                    self.record_result('P')
                elif banker_clicked:
                    self.record_result('B')
                elif undo_clicked:
                    self.undo()
                elif reset_bet_clicked:
                    self.reset_betting()
                elif reset_session_clicked:
                    self.reset_all()
                elif new_session_clicked:
                    self.reset_all()
                    st.session_state.message = "New session started."
                st.rerun()

        # Deal History as a styled table
        st.markdown('<div class="section-label">Deal History:</div>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="history-card">', unsafe_allow_html=True)
            if st.session_state.pair_types:
                history_data = [
                    {"Index": i + 1, "Pair": f"{pair[0]}{pair[1]}", "Type": "Even" if pair[0] == pair[1] else "Odd"}
                    for i, pair in enumerate(st.session_state.pair_types[-100:])
                ]
                history_html = '<div style="overflow-x: auto;"><table class="history-table"><tr><th>Index</th><th>Pair</th><th>Type</th></tr>'
                for row in history_data:
                    row_class = "even-row" if row["Type"] == "Even" else "odd-row"
                    history_html += f'<tr class="{row_class}"><td>{row["Index"]}</td><td>{row["Pair"]}</td><td>{row["Type"]}</td></tr>'
                history_html += '</table></div>'
                st.markdown(history_html, unsafe_allow_html=True)
            else:
                st.markdown('<div class="info-text">No history yet.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    app = BaccaratPredictor()
    app.render()
