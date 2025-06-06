import tkinter as tk
from tkinter import ttk

class BaccaratPredictor:
    def __init__(self, root):
        self.root = root
        self.root.title("Baccarat Predictor - Enhanced Dominant Pairs System")
        self.root.configure(bg='#2C2F33')
        self.root.geometry("650x700")
        self.root.resizable(True, True)

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

        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 12, 'bold'), padding=10, background='#7289DA', foreground='white', borderwidth=0)
        style.map('TButton', background=[('active', '#99AAB5')], foreground=[('active', 'white')])
        style.configure('TLabel', background='#2C2F33', foreground='white', font=('Helvetica', 12))
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('History.TFrame', background='#23272A')
        style.configure('TText', background='#23272A', foreground='white', font=('Helvetica', 10), borderwidth=0)

        # Main container
        main_frame = ttk.Frame(root, padding=20, style='TFrame')
        main_frame.pack(expand=True, fill='both')

        # Title
        self.label_title = ttk.Label(main_frame, text="Enhanced Dominant Pairs Baccarat Predictor", style='Title.TLabel')
        self.label_title.pack(pady=10)

        # Info frame
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(pady=10, fill='x')

        self.label_unit_info = ttk.Label(info_frame, text=f"Bet Amount: {self.bet_amount} unit(s)")
        self.label_unit_info.pack(pady=5)

        self.label_profit = ttk.Label(info_frame, text=f"Bankroll: {self.result_tracker}")
        self.label_profit.pack(pady=5)

        self.label_profit_lock = ttk.Label(info_frame, text=f"Profit Lock: {self.profit_lock}")
        self.label_profit_lock.pack(pady=5)

        self.label_prediction = ttk.Label(info_frame, text=f"Bet: {self.next_prediction}", font=('Helvetica', 14, 'bold'))
        self.label_prediction.pack(pady=5)

        self.label_streak = ttk.Label(info_frame, text="Streak: None")
        self.label_streak.pack(pady=5)

        # Button frame
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.pack(pady=10)

        self.button_player = ttk.Button(self.button_frame, text="Player", command=lambda: self.record_result('P'), width=12)
        self.button_player.grid(row=0, column=0, padx=10)

        self.button_banker = ttk.Button(self.button_frame, text="Banker", command=lambda: self.record_result('B'), width=12)
        self.button_banker.grid(row=0, column=1, padx=10)

        self.button_undo = ttk.Button(self.button_frame, text="Undo", command=self.undo, width=12)
        self.button_undo.grid(row=0, column=2, padx=10)

        # Deal History Area
        self.label_deal_history = ttk.Label(main_frame, text="Deal History:", font=('Helvetica', 12, 'bold'))
        self.label_deal_history.pack(pady=5)

        history_frame = ttk.Frame(main_frame, style='History.TFrame')
        history_frame.pack(pady=5, fill='both', expand=True)

        self.text_history = tk.Text(history_frame, height=8, width=50, bg='#23272A', fg='white', font=('Helvetica', 10), wrap="none", relief='flat')
        self.text_history.pack(side="left", fill='both', expand=True, padx=(0, 5))

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.text_history.yview)
        scrollbar.pack(side="right", fill='y')
        self.text_history.config(yscrollcommand=scrollbar.set)

        # Session Control Buttons
        session_frame = ttk.Frame(main_frame)
        session_frame.pack(pady=10)

        btn_reset_bet = ttk.Button(session_frame, text="Reset Bet", command=self.reset_betting, width=12)
        btn_reset_bet.grid(row=0, column=0, padx=5, pady=5)

        btn_reset = ttk.Button(session_frame, text="Reset Session", command=self.reset_all, width=12)
        btn_reset.grid(row=0, column=1, padx=5, pady=5)

        btn_new_session = ttk.Button(session_frame, text="New Session", command=self.new_session, width=12)
        btn_new_session.grid(row=0, column=2, padx=5, pady=5)
        print("New Session button created and added to session_frame.")

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def custom_messagebox(self, title, message, type="info"):
        """Create a custom messagebox with specified size and style."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg='#2C2F33')
        dialog.geometry("350x150")  # Custom size
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        dialog_width = 350
        dialog_height = 150
        x = root_x + (root_width - dialog_width) // 2
        y = root_y + (root_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Message label
        msg_label = ttk.Label(dialog, text=message, wraplength=300, background='#2C2F33', foreground='white', font=('Helvetica', 12))
        msg_label.pack(pady=20)

        # Button frame
        btn_frame = ttk.Frame(dialog, style='TFrame')
        btn_frame.pack(pady=10)

        result = [None]

        def set_result(value):
            result[0] = value
            dialog.destroy()

        if type == "yesno":
            yes_btn = ttk.Button(btn_frame, text="Yes", command=lambda: set_result(True), width=10)
            yes_btn.grid(row=0, column=0, padx=5)
            no_btn = ttk.Button(btn_frame, text="No", command=lambda: set_result(False), width=10)
            no_btn.grid(row=0, column=1, padx=5)
        else:  # info
            ok_btn = ttk.Button(btn_frame, text="OK", command=lambda: set_result(True), width=10)
            ok_btn.grid(row=0, column=0)

        self.root.wait_window(dialog)
        return result[0]

    def on_closing(self):
        if self.custom_messagebox("Exit", "Are you sure you want to exit?", type="yesno"):
            self.root.quit()

    def new_session(self):
        self.reset_all()
        print("New session started.")

    def reset_betting(self):
        self.result_tracker = 0
        self.bet_amount = self.unit
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.state_history = []
        self.streak_type = None

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

        self.update_display()
        print("Betting has been reset to initial state.")

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

        self.update_display()
        print("All session data has been reset, profit lock reset.")

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
            self.update_display()
            return

        pair = (self.previous_result, result)
        self.pair_types.append(pair)

        last_three = [self.pair_types[-i][1] for i in range(1, min(4, len(self.pair_types)))]
        if len(last_three) >= 3 and all(r == result for r in last_three):
            self.streak_type = result
        else:
            self.streak_type = None

        pair_type = "Even" if pair[0] == pair[1] else "Odd"

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
                        self.custom_messagebox("New Profit Lock", f"New profit lock achieved: {self.profit_lock} units! Betting reset to 1 unit.")
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
        self.update_display()

    def undo(self):
        if not self.state_history:
            self.custom_messagebox("Undo", "No actions to undo.")
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

        self.update_display()
        print("Last action undone.")

    def update_display(self):
        self.label_unit_info.config(text=f"Bet Amount: {max(self.unit, abs(self.bet_amount))} unit(s)")
        self.label_profit.config(text=f"Bankroll: {self.result_tracker}")
        self.label_profit_lock.config(text=f"Profit Lock: {self.profit_lock}")
        self.label_prediction.config(text=f"Bet: {self.next_prediction}")
        self.label_streak.config(text=f"Streak: {self.streak_type if self.streak_type else 'None'}")

        self.text_history.delete(1.0, tk.END)
        for i, pair in enumerate(self.pair_types[-100:], 1):
            pair_type = "Even" if pair[0] == pair[1] else "Odd"
            line = f"{pair} ({pair_type})\n"
            self.text_history.insert(tk.END, line)

        self.text_history.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = BaccaratPredictor(root)
    root.mainloop()
