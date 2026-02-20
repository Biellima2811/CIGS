import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class WarGeneratorPanel(ttk.Frame):
    """
    Painel para criação em massa de arquivos .war (layout baseado em grid)
    """

    def __init__(self, parent, log_callback, progress_callback):
        super().__init__(parent)
        self.log = log_callback
        self.update_progress = progress_callback
        self.setup_ui()

    def setup_ui(self):
        # Configurar expansão das colunas
        self.columnconfigure(1, weight=1)  # Coluna da entrada expande
        self.columnconfigure(0, weight=0)  # Coluna do label não expande
        self.columnconfigure(2, weight=0)  # Coluna do botão não expande

        # Linha 0: label 'Arquivo de nomes'
        ttk.Label(self, text='Arquivo de nomes (.txt):').grid(
            row=0, column=0, sticky='w', padx=10, pady=(10, 0)
        )

        # Linha 1: Entrada + botão selecionar
        self.entry_txt = ttk.Entry(self)
        self.entry_txt.grid(row=1, column=0, columnspan=2, sticky='ew', padx=(10, 5), pady=2)
        ttk.Button(self, text='Selecionar', command=self.selecionar_txt).grid(
            row=1, column=2, padx=(0, 10), pady=2, sticky='w'
        )

        # Linha 2: Label "Arquivo base"
        ttk.Label(self, text='Arquivo base (.war):').grid(
            row=2, column=0, sticky='w', padx=10, pady=(10, 0)
        )

        # Linha 3: Entrada + botão Selecionar
        self.entry_war = ttk.Entry(self)
        self.entry_war.grid(row=3, column=0, columnspan=2, sticky='ew', padx=(10, 5), pady=2)
        ttk.Button(self, text='Selecionar', command=self.selecionar_war).grid(
            row=3, column=2, padx=(0, 10), pady=2, sticky='w'
        )

        # Linha 4: Label "Pasta de destino"
        ttk.Label(self, text='Pasta de destino:').grid(
            row=4, column=0, sticky='w', padx=10, pady=(10, 0)
        )

        # Linha 5: Entrada + botão Selecionar
        self.entry_dest = ttk.Entry(self)
        self.entry_dest.grid(row=5, column=0, columnspan=2, sticky='ew', padx=(10, 5), pady=2)
        ttk.Button(self, text='Selecionar', command=self.selecionar_pasta_destino).grid(
            row=5, column=2, padx=(0, 10), pady=2, sticky='w'
        )

        # Linha 6: Botão de execução (centralizado)
        self.btn_executar = ttk.Button(self, text='Gerar Cópias', command=self.iniciar_copia)
        self.btn_executar.grid(row=6, column=0, columnspan=3, pady=20)

        # Configurar peso da linha vazia para empurrar conteúdo para cima (opcional)
        self.rowconfigure(7, weight=1)

    def selecionar_txt(self):
        path = filedialog.askopenfilename(
            title='Selecione o arquivo de nomes (.txt)',
            filetypes=[('Arquivos de texto', '*.txt')]
        )
        if path:
            self.entry_txt.delete(0, tk.END)
            self.entry_txt.insert(0, path)

    def selecionar_war(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo base (.war)",
            filetypes=[("Arquivos WAR", "*.war")]
        )
        if path:
            self.entry_war.delete(0, tk.END)
            self.entry_war.insert(0, path)

    def selecionar_pasta_destino(self):
        path = filedialog.askdirectory(title="Selecione a pasta de destino")
        if path:
            self.entry_dest.delete(0, tk.END)
            self.entry_dest.insert(0, path)

    def iniciar_copia(self):
        txt_path = self.entry_txt.get().strip()
        war_path = self.entry_war.get().strip()
        dest_dir = self.entry_dest.get().strip()

        if not txt_path or not war_path or not dest_dir:
            messagebox.showerror('Erro', 'Favor, preencha todos os campos.')
            return

        if not os.path.exists(txt_path) or not os.path.exists(war_path):
            messagebox.showerror('Erro', 'Arquivo .txt ou .war não encontrado')
            return

        threading.Thread(target=self._worker_copia, args=(txt_path, war_path, dest_dir), daemon=True).start()

    def _worker_copia(self, txt_path, war_path, dest_dir):
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                nomes = [linha.strip() for linha in f if linha.strip()]

            if not nomes:
                self.log('⚠️ - Arquivo de nomes vazio.')
                return

            total = len(nomes)
            self.log(f' Iniciando cópia de {total} arquivos...')

            for i, nome in enumerate(nomes, start=1):
                destino = os.path.join(dest_dir, f'{nome}.war')
                shutil.copy2(war_path, destino)
                self.update_progress(i, total, f'Copiando...({i}/{total})')

            self.log(f'✅ -  {total} arquivos criados com sucesso em {dest_dir}')
            messagebox.showinfo('Concluído', f'{total} arquivos gerados!')
        except Exception as e:
            self.log(f'❌ - Erro: {str(e)}')
            messagebox.showerror('Erro', f'Ocorreu um erro: \n{e}')
        finally:
            self.update_progress(0, 100, "Pronto")  # Reset da barra