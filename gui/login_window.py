import tkinter as tk
from tkinter import messagebox
from core.db_manager import CIGSDatabase

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("C.I.G.S - Acesso Restrito")
        self.geometry("350x250")
        self.resizable(False, False)
        # Centraliza a janela
        self.eval('tk::PlaceWindow . center')
        
        self.db = CIGSDatabase()
        self.autenticado = False
        self.usuario_logado = None
        self.nivel_acesso = None

        self.construir_interface()

    def construir_interface(self):
        # Título
        tk.Label(self, text="C.I.G.S", font=("Helvetica", 24, "bold"), fg="darkgreen").pack(pady=(20, 5))
        tk.Label(self, text="Identifique-se, Operador", font=("Helvetica", 10)).pack(pady=(0, 20))

        # Campos
        frame_form = tk.Frame(self)
        frame_form.pack()

        tk.Label(frame_form, text="Usuário:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_user = tk.Entry(frame_form, width=25)
        self.entry_user.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_form, text="Senha:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_senha = tk.Entry(frame_form, width=25, show="*")
        self.entry_senha.grid(row=1, column=1, padx=5, pady=5)
        self.entry_senha.bind("<Return>", lambda event: self.fazer_login()) # Logar com o botão Enter

        # Botão
        tk.Button(self, text="AUTENTICAR", bg="darkgreen", fg="white", font=("Helvetica", 10, "bold"), 
                  command=self.fazer_login, width=20).pack(pady=20)

    def fazer_login(self):
        try:
            usuario = self.entry_user.get().strip()
            senha = self.entry_senha.get().strip()

            dados_usuario = self.db.verificar_usuario(usuario, senha)

            if dados_usuario:
                self.autenticado = True
                self.usuario_logado = dados_usuario['username']
                self.nivel_acesso = dados_usuario['role']
                self.destroy() # Fecha a tela de login e libera a abertura do sistema
            else:
                messagebox.showerror("Acesso Negado", "Usuário ou senha incorretos!", parent=self)
                self.entry_senha.delete(0, tk.END)
                
        except Exception as e:
            # Se der qualquer erro interno, agora ele joga na tela!
            messagebox.showerror("Alerta Vermelho", f"Erro no sistema: {e}", parent=self)