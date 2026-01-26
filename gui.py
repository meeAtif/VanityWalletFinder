import customtkinter as ctk
import multiprocessing
import os
import sys
from datetime import datetime
from wallet_generator import GeneratorManager

# Initialize customtkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class WalletFinderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Vanity Wallet Finder Pro")
        self.geometry("900x700")
        
        # Generator Manager
        self.manager = GeneratorManager()
        self.is_running = False
        self.start_time = 0
        self.total_checked = 0
        self.found_count = 0
        
        # Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # === CONTROL PANEL (Top) ===
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        
        # Network Selection
        self.network_label = ctk.CTkLabel(self.control_frame, text="Network:")
        self.network_label.grid(row=0, column=0, padx=10, pady=10)
        self.network_var = ctk.StringVar(value="ETH")
        self.network_menu = ctk.CTkOptionMenu(
            self.control_frame, 
            values=["ETH", "BTC_LEGACY", "BTC_SEGWIT"],
            variable=self.network_var
        )
        self.network_menu.grid(row=0, column=1, padx=10, pady=10)
        
        # Worker Count
        self.cpu_label = ctk.CTkLabel(self.control_frame, text="Threads:")
        self.cpu_label.grid(row=0, column=2, padx=10, pady=10)
        max_cpu = multiprocessing.cpu_count()
        self.cpu_slider = ctk.CTkSlider(self.control_frame, from_=1, to=max_cpu, number_of_steps=max_cpu-1)
        self.cpu_slider.set(max(1, max_cpu - 1))
        self.cpu_slider.grid(row=0, column=3, padx=10, pady=10, sticky="ew")
        self.cpu_val_label = ctk.CTkLabel(self.control_frame, text=f"{int(self.cpu_slider.get())}")
        self.cpu_val_label.grid(row=0, column=4, padx=5, pady=10)
        self.cpu_slider.configure(command=lambda v: self.cpu_val_label.configure(text=str(int(v))))
        
        # Start/Stop Button
        self.action_btn = ctk.CTkButton(
            self.control_frame, 
            text="START FINDING", 
            fg_color="green", 
            hover_color="darkgreen",
            command=self.toggle_generation
        )
        self.action_btn.grid(row=0, column=5, padx=20, pady=10)

        # Row 1: Advanced Settings
        self.words_label = ctk.CTkLabel(self.control_frame, text="Words:")
        self.words_label.grid(row=1, column=0, padx=10, pady=5)
        self.words_var = ctk.StringVar(value="12 Words")
        self.words_menu = ctk.CTkOptionMenu(
            self.control_frame, 
            values=["12 Words", "24 Words"],
            variable=self.words_var,
            width=100
        )
        self.words_menu.grid(row=1, column=1, padx=10, pady=5)
        
        self.scope_label = ctk.CTkLabel(self.control_frame, text="Scope:")
        self.scope_label.grid(row=1, column=2, padx=10, pady=5)
        self.scope_var = ctk.StringVar(value="First 5")
        self.scope_menu = ctk.CTkOptionMenu(
            self.control_frame, 
            values=["First 1", "First 5", "Specific"],
            variable=self.scope_var,
            command=self.on_scope_change,
            width=100
        )
        self.scope_menu.grid(row=1, column=3, padx=10, pady=5)
        
        self.index_entry = ctk.CTkEntry(self.control_frame, placeholder_text="Idx (e.g. 0)", width=80)
        # Initially hidden or disabled? Let's just grid it but disable if not needed, or hide.
        # Hiding is cleaner.
        self.index_entry.grid(row=1, column=4, padx=5, pady=5)
        self.index_entry.grid_remove() # Start hidden

        # === CRITERIA PANEL (Middle) ===
        self.criteria_frame = ctk.CTkFrame(self)
        self.criteria_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        # Pattern Inputs
        self.p_start_label = ctk.CTkLabel(self.criteria_frame, text="Starts with (comma sep):")
        self.p_start_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.p_start_entry = ctk.CTkEntry(self.criteria_frame, placeholder_text="0x000, 0xdead")
        self.p_start_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        self.p_end_label = ctk.CTkLabel(self.criteria_frame, text="Ends with (comma sep):")
        self.p_end_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.p_end_entry = ctk.CTkEntry(self.criteria_frame, placeholder_text="bad, cafe")
        self.p_end_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        self.p_cont_label = ctk.CTkLabel(self.criteria_frame, text="Contains (comma sep):")
        self.p_cont_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.p_cont_entry = ctk.CTkEntry(self.criteria_frame, placeholder_text="888")
        self.p_cont_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        self.criteria_frame.grid_columnconfigure(1, weight=1)

        # === RESULTS PANEL (Bottom) ===
        self.results_frame = ctk.CTkFrame(self)
        self.results_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.grid_rowconfigure(3, weight=1)
        
        # Stats
        self.stats_label = ctk.CTkLabel(
            self.results_frame, 
            text="Status: Ready | Speed: 0/s | Total Checked: 0 | Found: 0",
            font=("Consolas", 14, "bold")
        )
        self.stats_label.pack(pady=5)
        
        # Text Box
        self.result_box = ctk.CTkTextbox(self.results_frame, font=("Consolas", 12))
        self.result_box.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Loop
        self.after(100, self.update_loop)

        # Output handling
        self.output_dir = "found_wallets"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def on_scope_change(self, choice):
        if choice == "Specific":
            self.index_entry.grid()
        else:
            self.index_entry.grid_remove()

    def get_patterns(self):
        patterns = {}
        
        starts = self.p_start_entry.get().strip()
        if starts: patterns['starts_with'] = [x.strip() for x in starts.split(',') if x.strip()]
            
        ends = self.p_end_entry.get().strip()
        if ends: patterns['ends_with'] = [x.strip() for x in ends.split(',') if x.strip()]
            
        conts = self.p_cont_entry.get().strip()
        if conts: patterns['contains'] = [x.strip() for x in conts.split(',') if x.strip()]
            
        return patterns

    def toggle_generation(self):
        if not self.is_running:
            # Start
            patterns = self.get_patterns()
            if not patterns:
                self.log_msg("Error: Please specify at least one pattern criteria.")
                return
            
            # Get Params
            network = self.network_var.get()
            threads = int(self.cpu_slider.get())
            
            # Words
            w_str = self.words_var.get()
            word_count = 12 if "12" in w_str else 24
            
            # Scope
            scope = self.scope_var.get()
            indices = []
            if scope == "First 1":
                indices = [0]
            elif scope == "First 5":
                indices = [0, 1, 2, 3, 4]
            elif scope == "Specific":
                try:
                    idx = int(self.index_entry.get().strip())
                    if idx < 0: raise ValueError
                    indices = [idx]
                except:
                    self.log_msg("Error: Invalid Index. Please enter a positive number.")
                    return

            self.manager.start_generation(network, patterns, threads, word_count, indices)
            self.is_running = True
            self.start_time = datetime.now().timestamp()
            self.total_checked = 0
            self.found_count = 0
            
            self.action_btn.configure(text="STOP", fg_color="red", hover_color="darkred")
            self.log_msg(f"Started search for {network} ({word_count} words)...")
            self.log_msg(f"Scanning Indices: {indices}")
            self.log_msg(f"Patterns: {patterns}")
            
        else:
            # Stop
            self.manager.stop_generation()
            self.is_running = False
            self.action_btn.configure(text="START FINDING", fg_color="green", hover_color="darkgreen")
            self.log_msg("Stopped.")

    def update_loop(self):
        if self.is_running:
            # Update counters
            while not self.manager.counter_queue.empty():
                try:
                    self.total_checked += self.manager.counter_queue.get_nowait()
                except: pass
                
            # Check for results
            while not self.manager.result_queue.empty():
                try:
                    res = self.manager.result_queue.get_nowait()
                    self.found_count += 1
                    self.handle_found(res)
                except: pass
            
            # Update stats UI
            elapsed = datetime.now().timestamp() - self.start_time
            speed = int(self.total_checked / elapsed) if elapsed > 0 else 0
            
            status_txt = f"Status: RUNNING | Speed: {speed:,}/s | Total Checked: {self.total_checked:,} | Found: {self.found_count}"
            self.stats_label.configure(text=status_txt)
            
        self.after(500, self.update_loop)

    def handle_found(self, res):
        msg = (f"\n[FOUND] {res['address']}\n"
               f"Mnemonic: {res['mnemonic']}\n"
               f"Path Index: {res['path_index']} | Type: {res['type']}\n"
               f"{'-'*40}")
        self.log_msg(msg)
        
        # Save to file
        fname = f"wallets_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(os.path.join(self.output_dir, fname), "a") as f:
            f.write(msg + "\n")

    def log_msg(self, msg):
        self.result_box.insert("end", msg + "\n")
        self.result_box.see("end")

    def on_closing(self):
        if self.is_running:
            self.manager.stop_generation()
        self.destroy()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = WalletFinderApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
