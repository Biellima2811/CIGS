import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry  # pip install tkcalendar (Se não tiver, usa Entry normal)
from datetime import datetime

class ScheduleDialog(tk.Toplevel):
    def __init__(self, parent, callback_agendar):
        super().__init__(parent)
        self.callback = callback_agendar
        self.title("📅 Agendamento Tático de Manutenção")
        self.geometry("400x350")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")
        self.setup_ui()

    def setup_ui(self):
        # Configuração de colunas para expandir
        self.columnconfigure(0, weight=1)

        # Título
        tk.Label(self, text="Configurar Missão Programada",
                 font=("Arial", 12, "bold"), bg="#ecf0f1").grid(row=0, column=0, pady=(20, 15), sticky="ew")

        # Data
        tk.Label(self, text="Data de Execução:", bg="#ecf0f1", anchor="w").grid(row=1, column=0, sticky="w", padx=20)
        try:
            self.cal_date = DateEntry(self, width=12, background='darkblue',
                                      foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
            self.cal_date.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        except:
            self.cal_date = ttk.Entry(self)
            self.cal_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
            self.cal_date.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        # Hora
        tk.Label(self, text="Hora (HH:MM):", bg="#ecf0f1", anchor="w").grid(row=3, column=0, sticky="w", padx=20, pady=(10, 0))
        self.ent_hora = ttk.Entry(self)
        self.ent_hora.insert(0, "02:00")  # Padrão madrugada
        self.ent_hora.grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        # Nome da Tarefa
        tk.Label(self, text="Nome da Tarefa (Task Scheduler):", bg="#ecf0f1", anchor="w").grid(row=5, column=0, sticky="w", padx=20, pady=(10, 0))
        self.ent_task_name = ttk.Entry(self)
        self.ent_task_name.insert(0, "CIGS_Manutencao_Auto")
        self.ent_task_name.grid(row=6, column=0, padx=20, pady=5, sticky="ew")

        # Botão Ação
        btn = tk.Button(self, text="⏰ AGENDAR NO SERVIDOR", command=self.confirmar,
                        bg="#2980b9", fg="white", font=("Arial", 10, "bold"), pady=10)
        btn.grid(row=7, column=0, padx=20, pady=20, sticky="ew")

    def confirmar(self):
        # Pega a data (se for widget DateEntry ou Entry normal)
        try:
            data = self.cal_date.get_date().strftime("%d/%m/%Y")
        except:
            data = self.cal_date.get()

        hora = self.ent_hora.get()
        task = self.ent_task_name.get()

        if not data or not hora:
            return

        self.callback(data, hora, task)
        self.destroy()
