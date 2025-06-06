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

        st.success("Betting has been reset to initial state.")

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
        st.success("All session data has been reset, profit lock reset.")

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
                        st.success(f"New profit lock achieved: {st.session_state.profit_lock} units! Betting reset to 1 unit.")
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
            st.warning("No actions to undo.")
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
        st.success("Last action undone.")

    def render(self):
        # Set page configuration
        st.set_page_config(page_title="Baccarat Predictor", layout="centered")

        # Custom CSS for styling
        st.markdown("""
            <style>
            .main {
                background-color: #2C2F33;
                color: white;
                font-family: Helvetica, sans-serif;
            }
            .stButton>button {
                background-color: #7289DA;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
                width: 120px;
                margin: 5px;
            }
            .stButton>button:hover {
                background-color: #99AAB5;
            }
            .title {
                font-size: 24px;
                font-weight: bold;
                text-align: center;
                margin-bottom: 20px;
            }
            .info-box {
                background-color: #23272A;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .history-box {
                background-color: #23272A;
                padding: 10px;
                border-radius: 5px;
                max-height: 200px;
                overflow-y: auto;
                font-size: 14px;
            }
            </style>
        """, unsafe_allow_html=True)

        # Title
        st.markdown('<div class="title">Enhanced Dominant Pairs Baccarat Predictor</div>', unsafe_allow_html=True)

        # Info section
        with st.container():
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.write(f"**Bet Amount:** {max(st.session_state.unit, abs(st.session_state.bet_amount))} unit(s)")
            st.write(f"**Bankroll:** {st.session_state.result_tracker}")
            st.write(f"**Profit Lock:** {st.session_state.profit_lock}")
            st.write(f"**Bet:** {st.session_state.next_prediction}", key="prediction")
            st.write(f"**Streak:** {st.session_state.streak_type if st.session_state.streak_type else 'None'}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Result buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Player"):
                self.record_result('P')
                st.rerun()
        with col2:
            if st.button("Banker"):
                self.record_result('B')
                st.rerun()
        with col3:
            if st.button("Undo"):
                self.undo()
                st.rerun()

        # Deal History
        st.markdown("**Deal History:**")
        with st.container():
            st.markdown('<div class="history-box">', unsafe_allow_html=True)
            history_text = ""
            for i, pair in enumerate(st.session_state.pair_types[-100:], 1):
                pair_type = "Even" if pair[0] == pair[1] else "Odd"
                history_text += f"{pair} ({pair_type})\n"
            st.text(history_text)
            st.markdown('</div>', unsafe_allow_html=True)

        # Session control buttons
        col4, col5, col6 = st.columns([1, 1, 1])
        with col4:
            if st.button("Reset Bet"):
                self.reset_betting()
                st.rerun()
        with col5:
            if st.button("Reset Session"):
                self.reset_all()
                st.rerun()
        with col6:
            if st.button("New Session"):
                self.reset_all()
                st.success("New session started.")
                st.rerun()

if __name__ == "__main__":
    app = BaccaratPredictor()
    app.render()
