import os
import sys
import subprocess
import threading
from pathlib import Path
import customtkinter as ctk

ROOT = Path(__file__).resolve().parent

# Set up CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AIC4Launcher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AIC-4 Aerial Tracking - Control Panel")
        self.geometry("800x600")
        self.resizable(False, False)

        # Background processes
        self.dashboard_process = None
        self.simulation_process = None

        self._build_ui()

    def _build_ui(self):
        # ─── Left Panel: Controls ─────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        self.logo_label = ctk.CTkLabel(self.sidebar, text="AIC-4 Control", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=(20, 30))

        # AirSim Control
        self.btn_airsim = ctk.CTkButton(self.sidebar, text="Launch AirSim (Blocks)", command=self.start_airsim)
        self.btn_airsim.pack(pady=10, padx=20, fill="x")

        # Dashboard Control
        self.btn_dash = ctk.CTkButton(self.sidebar, text="Start Dashboard", command=self.toggle_dashboard)
        self.btn_dash.pack(pady=10, padx=20, fill="x")
        
        self.lbl_dash_status = ctk.CTkLabel(self.sidebar, text="Dashboard: STOPPED", text_color="gray")
        self.lbl_dash_status.pack(pady=(0, 20))

        # Simulation Control
        self.lbl_sim = ctk.CTkLabel(self.sidebar, text="Simulation Engine", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_sim.pack(pady=(20, 10))

        self.btn_sim_real = ctk.CTkButton(self.sidebar, text="Run Single Drone", fg_color="#2B7A0B", hover_color="#1E5608", command=lambda: self.start_simulation(mock=False, swarm=False))
        self.btn_sim_real.pack(pady=5, padx=20, fill="x")

        self.btn_sim_mock = ctk.CTkButton(self.sidebar, text="Run Single (Mock)", fg_color="#A95C00", hover_color="#824600", command=lambda: self.start_simulation(mock=True, swarm=False))
        self.btn_sim_mock.pack(pady=5, padx=20, fill="x")

        self.btn_sim_swarm = ctk.CTkButton(self.sidebar, text="Run Swarm (3 Drones)", fg_color="#8b3dff", hover_color="#6e2cc7", command=lambda: self.start_simulation(mock=False, swarm=True))
        self.btn_sim_swarm.pack(pady=5, padx=20, fill="x")

        self.btn_stop_sim = ctk.CTkButton(self.sidebar, text="Stop Simulation", fg_color="#D21312", hover_color="#990E0D", command=self.stop_simulation, state="disabled")
        self.btn_stop_sim.pack(pady=5, padx=20, fill="x")

        self.lbl_sim_status = ctk.CTkLabel(self.sidebar, text="Simulation: STOPPED", text_color="gray")
        self.lbl_sim_status.pack(pady=(5, 20))

        # Exit
        self.btn_exit = ctk.CTkButton(self.sidebar, text="Exit", fg_color="transparent", border_width=1, command=self.destroy)
        self.btn_exit.pack(side="bottom", pady=20, padx=20, fill="x")

        # ─── Right Panel: Console Log ─────────────────────────────────────────
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.pack(side="right", fill="both", expand=True)

        self.lbl_log = ctk.CTkLabel(self.main_frame, text="System Log", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_log.pack(pady=(20, 10), padx=20, anchor="w")

        self.log_box = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(family="Consolas", size=12), wrap="none")
        self.log_box.pack(pady=(0, 20), padx=20, fill="both", expand=True)
        self.log_message("System initialized. Ready.")

    def log_message(self, message: str):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def _read_process_output(self, process, prefix=""):
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.log_message(f"[{prefix}] {line.strip()}")
        except Exception as e:
            self.log_message(f"[{prefix}] Error reading output: {e}")

    def start_airsim(self):
        airsim_exe = ROOT / "airsim_envs" / "Blocks" / "WindowsNoEditor" / "Blocks.exe"
        if not airsim_exe.exists():
            self.log_message(f"[ERROR] AirSim binary not found at {airsim_exe}")
            self.log_message("Please run `python setup/download_airsim_env.py` first.")
            return

        self.log_message(f"[LAUNCH] Starting AirSim: {airsim_exe}")
        try:
            subprocess.Popen([str(airsim_exe), "-windowed", "-ResX=1280", "-ResY=720"])
        except Exception as e:
            self.log_message(f"[ERROR] Failed to launch AirSim: {e}")

    def _get_python_exe(self):
        # If running as a PyInstaller bundle, sys.executable is the launcher .exe.
        # We need the real Python to run the scripts.
        if getattr(sys, 'frozen', False):
            # Try to find python in PATH or assume it's installed
            return "python"
        return sys.executable

    def toggle_dashboard(self):
        if self.dashboard_process is None:
            # Start dashboard
            self.log_message("[LAUNCH] Starting Dashboard on http://127.0.0.1:5000 ...")
            env = os.environ.copy()
            # Unbuffered output
            env["PYTHONUNBUFFERED"] = "1"
            
            # Use waitress if available, else flask run
            self.dashboard_process = subprocess.Popen(
                [self._get_python_exe(), "dashboard/app.py"],
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            threading.Thread(target=self._read_process_output, args=(self.dashboard_process, "DASH"), daemon=True).start()
            
            self.btn_dash.configure(text="Stop Dashboard", fg_color="#D21312", hover_color="#990E0D")
            self.lbl_dash_status.configure(text="Dashboard: RUNNING", text_color="#2B7A0B")
            
            # Try to open browser
            import webbrowser
            webbrowser.open("http://127.0.0.1:5000/demo")
        else:
            # Stop dashboard
            self.log_message("[STOP] Stopping Dashboard...")
            self.dashboard_process.terminate()
            self.dashboard_process = None
            self.btn_dash.configure(text="Start Dashboard", fg_color="#1f538d", hover_color="#14375e")
            self.lbl_dash_status.configure(text="Dashboard: STOPPED", text_color="gray")

    def start_simulation(self, mock=False, swarm=False):
        if self.simulation_process is not None:
            return

        mode_str = "MOCK" if mock else "REAL"
        type_str = "SWARM" if swarm else "SINGLE"
        self.log_message(f"[LAUNCH] Starting Simulation ({type_str} {mode_str} mode)...")
        
        script = "scripts/run_swarm.py" if swarm else "scripts/run_simulation.py"
        cmd = [self._get_python_exe(), script, "--record"]
        if mock:
            cmd.append("--mock")
            
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        self.simulation_process = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        threading.Thread(target=self._read_process_output, args=(self.simulation_process, "SIM"), daemon=True).start()
        
        # Monitor process end
        threading.Thread(target=self._monitor_simulation, daemon=True).start()
        
        self.btn_sim_real.configure(state="disabled")
        self.btn_sim_mock.configure(state="disabled")
        self.btn_sim_swarm.configure(state="disabled")
        self.btn_stop_sim.configure(state="normal")
        self.lbl_sim_status.configure(text=f"Simulation: RUNNING ({type_str})", text_color="#2B7A0B")
        
        if swarm:
            import webbrowser
            webbrowser.open("http://127.0.0.1:5000/swarm")

    def _monitor_simulation(self):
        self.simulation_process.wait()
        self.simulation_process = None
        # Safe GUI update
        self.after(0, self._simulation_stopped_ui)

    def _simulation_stopped_ui(self):
        self.log_message("[STOP] Simulation process exited.")
        self.btn_sim_real.configure(state="normal")
        self.btn_sim_mock.configure(state="normal")
        self.btn_sim_swarm.configure(state="normal")
        self.btn_stop_sim.configure(state="disabled")
        self.lbl_sim_status.configure(text="Simulation: STOPPED", text_color="gray")

    def stop_simulation(self):
        if self.simulation_process:
            self.log_message("[STOP] Requesting simulation termination...")
            stop_file = ROOT / "experiments" / "results" / ".sim_stop"
            stop_file.parent.mkdir(parents=True, exist_ok=True)
            stop_file.touch()
            # Also gracefully try to terminate process
            try:
                self.simulation_process.terminate()
            except Exception:
                pass

    def destroy(self):
        if self.dashboard_process:
            self.dashboard_process.terminate()
        if self.simulation_process:
            self.simulation_process.terminate()
        super().destroy()

def main():
    app = AIC4Launcher()
    app.mainloop()

if __name__ == "__main__":
    main()
