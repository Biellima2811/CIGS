import hashlib
import tkinter as tk
from tkinter import ttk

class KeyGenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CIGS KeyGen - Acesso Restrito")
        self.root.geometry("420x350")
        self.root.configure(bg="#2c3e50")
        self.root.resizable(False, False)

        # Configuração de colunas para expandir
        self.root.columnconfigure(0, weight=1)

        # Título
        tk.Label(root, text="GERADOR DE CONTRA-SENHA", font=("Impact", 20),
                 fg="#ecf0f1", bg="#2c3e50").grid(row=0, column=0, pady=(20, 10), sticky="ew")

        # Entrada
        tk.Label(root, text="Insira o Token do CIGS:", font=("Arial", 10),
                 fg="#bdc3c7", bg="#2c3e50").grid(row=1, column=0, pady=5, sticky="ew")

        self.ent_token = tk.Entry(root, font=("Arial", 18), justify="center",
                                  bg="#34495e", fg="white", insertbackground="white", relief="flat")
        self.ent_token.grid(row=2, column=0, padx=50, pady=5, ipady=5, sticky="ew")
        self.ent_token.focus()

        # Botão Gerar
        tk.Button(root, text="🔓 DESCRIPTOGRAFAR", command=self.gerar,
                  bg="#27ae60", fg="white", font=("Segoe UI", 12, "bold"),
                  relief="flat", pady=5).grid(row=3, column=0, padx=50, pady=15, sticky="ew")

        # Resultado
        self.lbl_res = tk.Label(root, text="----", font=("Consolas", 24, "bold"),
                                fg="#e74c3c", bg="#2c3e50")
        self.lbl_res.grid(row=4, column=0, pady=5, sticky="ew")

        # Botão Copiar Resultado
        self.btn_copy = tk.Button(root, text="📋 Copiar Senha", command=self.copiar, state="disabled",
                                  bg="#95a5a6", fg="white", font=("Arial", 10), relief="flat")
        self.btn_copy.grid(row=5, column=0, pady=10)

        # Atalho Enter
        root.bind('<Return>', lambda e: self.gerar())

    def gerar(self):
        token = self.ent_token.get().strip()
        if len(token) != 6:
            self.lbl_res.config(text="INVÁLIDO", fg="#e74c3c")
            self.btn_copy.config(state="disabled", bg="#95a5a6")
            return

        seed = "CIGS_2026_ELITE"
        raw = f"{seed}{token}"
        senha_mestra = hashlib.sha256(raw.encode()).hexdigest()[:6].upper()

        self.lbl_res.config(text=senha_mestra, fg="#2ecc71")
        self.btn_copy.config(state="normal", bg="#3498db")
        self.senha_atual = senha_mestra

    def copiar(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.senha_atual)
        self.btn_copy.config(text="Copiado!", bg="#27ae60")
        self.root.after(2000, lambda: self.btn_copy.config(text="📋 Copiar Senha", bg="#3498db"))

if __name__ == "__main__":
    root = tk.Tk()
    app = KeyGenApp(root)
    root.mainloop()