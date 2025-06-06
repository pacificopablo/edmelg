import streamlit as st
import pandas as pd

class BaccaratPredictor:
    def __init__(self):
        self.pair_types = []
        self.next_prediction = "N/A"
        self.unit = 1
        self.bet_amount = 0
        self.result_tracker = 0
        self.profit_lock = 0
        self.previous_result = None
        self.state_history = []
        self.current_dominance = "N/A"
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.streak_type = None

    def reset_betting(self):
        self.result_tracker = 0
        self.bet_amount = self.unit
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.state_history = []

        if len(self.pair_types) >= 5:
            recent_pairs = self.pair_types[-10:]
            odd_count = sum(1 for a, b in recent_pairs if a != b)
            even_count = sum(1 for a, b in recent_pairs if a == b)
            result = self.previous_result
            if abs(odd_count - even_count) < 2:
                self.current_dominance = "N/A"
                self.next_prediction = "Hold"
            elif odd_count > even_count:
                self.current_dominance = "Odd"
                self.next_prediction = "Player" if result == 'B' else "Banker"
            else:
                self.current_dominance = "Even"
                self.next_prediction = "Player" if result == 'P' else "Banker"
            last_three = [self.pair_types[-i][1] for i in range(1, min(4, len(self.pair_types)))]
            if len(last_three) >= 3 and all(r == last_three[0] for r in last_three):
                self.streak_type = last_three[0]
                self.next_prediction = "Player" if self.streak_type == 'P' else "Banker"
                self.current_dominance = f"Streak ({self.streak_type})"
        else:
            self.next_prediction = "N/A"
            self.current_dominance = "N/A"
            self.streak_type = None

    def reset_all(self):
        self.pair_types = []
        self.result_tracker = 0
        self.profit_lock = 0
        self.bet_amount = self.unit
        self.next_prediction = "N/A"
        self.previous_result = None
        self.state_history = []
        self.current_dominance = "N/A"
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.streak_type = None

    def record_result(self, result):
        state = {
            'pair_types': self.pair_types.copy(),
            'previous_result': self.previous_result,
            'result_tracker': self.result_tracker,
            'profit_lock': self.profit_lock,
            'bet_amount': self.bet_amount,
            'current_dominance': self.current_dominance,
            'next_prediction': self.next_prediction,
            'consecutive_wins': self.consecutive_wins,
            'consecutive_losses': self.consecutive_losses,
            'streak_type': self.streak_type
        }
        self.state_history.append(state)

        if self.previous_result is None:
            self.previous_result = result
            self.next_prediction = "N/A"
            return

        pair = (self.previous_result, result)
        self.pair_types.append(pair)

        last_three = [self.pair_types[-i][1] for i in range(1, min(4, len(self.pair_types)))]
        if len(last_three) >= 3 and all(r == result for r in last_three):
            self.streak_type = result
        else:
            self.streak_type = None

        if len(self.pair_types) >= 5:
            recent_pairs = self.pair_types[-10:]
            odd_count = sum(1 for a, b in recent_pairs if a != b)
            even_count = sum(1 for a, b in recent_pairs if a == b)

            if self.streak_type:
                self.next_prediction = "Player" if self.streak_type == 'P' else "Banker"
                self.current_dominance = f"Streak ({self.streak_type})"
            elif abs(odd_count - even_count) < 2:
                self.current_dominance = "N/A"
                self.next_prediction = "Hold"
            elif odd_count > even_count:
                self.current_dominance = "Odd"
                self.next_prediction = "Player" if result == 'B' else "Banker"
            else:
                self.current_dominance = "Even"
                self.next_prediction = "Player" if result == 'P' else "Banker"

            if self.bet_amount == 0:
                self.bet_amount = self.unit

            if len(self.pair_types) >= 6 and self.state_history[-1]['next_prediction'] != "Hold":
                previous_prediction = self.state_history[-1]['next_prediction']
                effective_bet = max(self.unit, abs(self.bet_amount))
                if (previous_prediction == "Player" and result == 'P') or \
                   (previous_prediction == "Banker" and result == 'B'):
                    self.result_tracker += effective_bet
                    self.consecutive_wins += 1
                    self.consecutive_losses = 0
                    if self.result_tracker > self.profit_lock:
                        self.profit_lock = self.result_tracker
                        self.reset_betting()
                        st.success(f"New profit lock achieved: {self.profit_lock} units! Betting reset to 1 unit.")
                        return
                    if self.consecutive_wins >= 2:
                        self.bet_amount = max(1, self.bet_amount - 1)
                else:
                    self.result_tracker -= effective_bet
                    self.consecutive_losses += 1
                    self.consecutive_wins = 0
                    if self.consecutive_losses >= 3:
                        self.bet_amount = min(5, self.bet_amount * 2)
                    else:
                        self.bet_amount += 1

        self.previous_result = result

    def undo(self):
        if not self.state_history:
            st.warning("No actions to undo.")
            return
        last_state = self.state_history.pop()
        self.pair_types = last_state['pair_types']
        self.previous_result = last_state['previous_result']
        self.result_tracker = last_state['result_tracker']
        self.profit_lock = last_state['profit_lock']
        self.bet_amount = last_state['bet_amount']
        self.current_dominance = last_state['current_dominance']
        self.next_prediction = last_state['next_prediction']
        self.consecutive_wins = last_state['consecutive_wins']
        self.consecutive_losses = last_state['consecutive_losses']
        self.streak_type = last_state['streak_type']

def main():
    st.set_page_config(
        page_title="Baccarat Predictor",
        page_icon="🎰",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS for professional look
    st.markdown("""
        <style>
        .main { background-color: #1E1E1E; color: white; }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 5px;
            margin: 5px;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .metric-card {
            background-color: #2C2F33;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            text-align: center;
        }
        .stExpander {
            background-color: #2C2F33;
            border-radius: 8px;
        }
        h1 { color: #FFFFFF; text-align: center; }
        h3 { color: #BBBBBB; }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'predictor' not in st.session_state:
        st.session_state.predictor = BaccaratPredictor()

    predictor = st.session_state.predictor

    st.title("Enhanced Dominant Pairs Baccarat Predictor")

    # Metrics display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-card'><h3>Bet Amount</h3><p>{max(predictor.unit, abs(predictor.bet_amount))} unit(s)</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><h3>Bankroll</h3><p>{predictor.result_tracker}</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><h3>Profit Lock</h3><p>{predictor.profit_lock}</p></div>", unsafe_allow_html=True)

    st.markdown(f"<div class='metric-card'><h3>Bet</h3><p style='font-size: 20px; font-weight: bold;'>{predictor.next_prediction}</p></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-card'><h3>Streak</h3><p>{predictor.streak_type if predictor.streak_type else 'None'}</p></div>", unsafe_allow_html=True)

    # Input buttons
    col_p, col_b, col_u = st.columns(3)
    with col_p:
        if st.button("Player"):
            predictor.record_result('P')
            st.rerun()
    with col_b:
        if st.button("Banker"):
            predictor.record_result('B')
            st.rerun()
    with col_u:
        if st.button("Undo"):
            predictor.undo()
            st.rerun()

    # Session control buttons
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        if st.button("Reset Bet"):
            predictor.reset_betting()
            st.rerun()
    with col_r2:
        if st.button("Reset Session"):
            predictor.reset_all()
            st.rerun()
    with col_r3:
        if st.button("New Session"):
            predictor.reset_all()
            st.rerun()

    # Deal history in expander
    with st.expander("Bet and Reasoning"):
        if predictor.pair_types:
            history_data = [
                {"Pair": f"{pair[0]} -> {pair[1]}", "Type": "Even" if pair[0] == pair[1] else "Odd"}
                for pair in predictor.pair_types[-100:]
            ]
            st.dataframe(pd.DataFrame(history_data), use_container_width=True, height=300)
        else:
            st.write("No deal history available.")

if __name__ == "__main__":
    main()
