import os
import time
import threading
import pygame
import tkinter as tk
from tkinter import ttk, messagebox

# ==========================================
# 🎨 TEMA J.A.R.V.I.S. (Dark & Cyan)
# ==========================================
COLORS = {
    "bg": "#121212",        # Fundo Principal
    "panel": "#1E1E1E",     # Painéis Laterais
    "accent": "#00ADB5",    # Ciano (Destaque)
    "accent_hover": "#00FFF5",
    "text": "#EEEEEE",      # Texto Claro
    "text_dim": "#AAAAAA",  # Texto Secundário
    "danger": "#CF6679",    # Vermelho (Remover/Erro)
    "success": "#00C853",   # Verde (Play)
    "timeline": "#2C2C2C",  # Fundo da Timeline
    "card": "#393E46"       # Blocos da Timeline
}

DIRETORIO_BANCO = os.path.join("jarvis_system", "area_broca", "voice_bank_fish")

class JarvisStudioPro:
    def __init__(self, root):
        self.root = root
        self.root.title("J.A.R.V.I.S. DIRECTORS CUT")
        self.root.geometry("1100x750")
        self.root.configure(bg=COLORS["bg"])
        
        pygame.mixer.init()
        self.playlist = [] 
        self.palavras_cache = [] # Para a busca funcionar rápido

        # --- ESTILOS TTK (Scrollbars e afins) ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar", gripcount=0, background=COLORS["panel"], troughcolor=COLORS["bg"], borderwidth=0, arrowcolor=COLORS["accent"])
        style.configure("Horizontal.TScrollbar", gripcount=0, background=COLORS["panel"], troughcolor=COLORS["bg"], borderwidth=0, arrowcolor=COLORS["accent"])

        self.setup_ui()
        self.carregar_dados()

    def setup_ui(self):
        # === COLUNA ESQUERDA (BIBLIOTECA) ===
        self.frame_library = tk.Frame(self.root, bg=COLORS["panel"], width=250)
        self.frame_library.pack(side="left", fill="y")
        self.frame_library.pack_propagate(False)

        # Cabeçalho
        tk.Label(self.frame_library, text="VOCABULÁRIO", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI", 12, "bold")).pack(pady=(20, 10))
        
        # Barra de Pesquisa
        self.entry_search = tk.Entry(self.frame_library, bg="#333", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 10))
        self.entry_search.pack(fill="x", padx=15, pady=5)
        self.entry_search.bind("<KeyRelease>", self.filtrar_lista)
        
        # Lista
        self.listbox = tk.Listbox(self.frame_library, bg=COLORS["panel"], fg="white", selectbackground=COLORS["accent"], selectforeground="black",
                                  relief="flat", highlightthickness=0, font=("Segoe UI", 11), borderwidth=0)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.ao_selecionar_palavra)

        # === ÁREA PRINCIPAL ===
        self.frame_main = tk.Frame(self.root, bg=COLORS["bg"])
        self.frame_main.pack(side="right", fill="both", expand=True)

        # --- TOPO: PREVIEW E SELEÇÃO ---
        self.frame_preview = tk.Frame(self.frame_main, bg=COLORS["bg"], height=250)
        self.frame_preview.pack(fill="x", pady=20, padx=20)
        
        # Onde aparecem os botões de emoção (Dinâmico)
        self.lbl_selected_word = tk.Label(self.frame_preview, text="SELECIONE UMA PALAVRA", bg=COLORS["bg"], fg=COLORS["text_dim"], font=("Segoe UI", 24, "bold"))
        self.lbl_selected_word.pack(pady=10)
        
        self.frame_emotions = tk.Frame(self.frame_preview, bg=COLORS["bg"])
        self.frame_emotions.pack(fill="both", expand=True)

        # --- CENTRO: CONTROLES GERAIS ---
        self.frame_controls = tk.Frame(self.frame_main, bg=COLORS["bg"])
        self.frame_controls.pack(fill="x", padx=20)

        self.btn_play = tk.Button(self.frame_controls, text="▶  REPRODUZIR CENA", bg=COLORS["success"], fg="white", 
                                  font=("Segoe UI", 12, "bold"), relief="flat", padx=20, pady=8, cursor="hand2", command=self.tocar_cena)
        self.btn_play.pack(side="right")
        
        self.btn_clear = tk.Button(self.frame_controls, text="🗑  LIMPAR TUDO", bg=COLORS["danger"], fg="white", 
                                   font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8, cursor="hand2", command=self.limpar_timeline)
        self.btn_clear.pack(side="left")

        # --- BAIXO: TIMELINE (EDITOR) ---
        tk.Label(self.frame_main, text="LINHA DO TEMPO", bg=COLORS["bg"], fg=COLORS["text_dim"], font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.container_timeline = tk.Frame(self.frame_main, bg=COLORS["timeline"], height=220)
        self.container_timeline.pack(fill="x", expand=True, padx=20, pady=(0, 20))
        self.container_timeline.pack_propagate(False)

        # Canvas para scroll horizontal
        self.canvas = tk.Canvas(self.container_timeline, bg=COLORS["timeline"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container_timeline, orient="horizontal", command=self.canvas.xview)
        self.frame_track = tk.Frame(self.canvas, bg=COLORS["timeline"])

        self.canvas.create_window((0, 0), window=self.frame_track, anchor="nw")
        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="top", fill="both", expand=True)
        self.scrollbar.pack(side="bottom", fill="x")
        
        self.frame_track.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def carregar_dados(self):
        if not os.path.exists(DIRETORIO_BANCO):
            messagebox.showerror("Erro", "Banco de voz não encontrado!")
            return
        
        # Carrega e ordena
        self.palavras_cache = sorted([p for p in os.listdir(DIRETORIO_BANCO) if os.path.isdir(os.path.join(DIRETORIO_BANCO, p))])
        self.atualizar_lista(self.palavras_cache)

    def atualizar_lista(self, lista):
        self.listbox.delete(0, "end")
        for item in lista:
            self.listbox.insert("end", f" {item.upper()}")

    def filtrar_lista(self, event):
        termo = self.entry_search.get().lower()
        filtradas = [p for p in self.palavras_cache if termo in p.lower()]
        self.atualizar_lista(filtradas)

    def ao_selecionar_palavra(self, event):
        sel = self.listbox.curselection()
        if not sel: return
        palavra = self.listbox.get(sel[0]).strip().lower()
        self.renderizar_botoes_emo(palavra)

    def renderizar_botoes_emo(self, palavra):
        # Limpa área
        for w in self.frame_emotions.winfo_children(): w.destroy()
        
        self.lbl_selected_word.config(text=palavra.upper(), fg=COLORS["text"])
        
        pasta = os.path.join(DIRETORIO_BANCO, palavra)
        arquivos = sorted([f.replace(".mp3", "") for f in os.listdir(pasta) if f.endswith(".mp3")])

        if not arquivos:
            tk.Label(self.frame_emotions, text="Nenhum áudio encontrado.", bg=COLORS["bg"], fg=COLORS["danger"]).pack()
            return

        # Layout Fluido (Grid inteligente)
        row, col = 0, 0
        max_cols = 4
        
        grid_frame = tk.Frame(self.frame_emotions, bg=COLORS["bg"])
        grid_frame.pack(pady=10)

        for emo in arquivos:
            # Container do Botão
            f = tk.Frame(grid_frame, bg=COLORS["panel"], padx=5, pady=5)
            f.grid(row=row, column=col, padx=5, pady=5)
            
            # Botão Tocar (Preview)
            btn_prev = tk.Button(f, text="🔊", bg="#333", fg="white", relief="flat", width=3,
                                 command=lambda p=palavra, e=emo: self.preview_audio(p, e))
            btn_prev.pack(side="left", padx=(0, 5))

            # Botão Adicionar
            btn_add = tk.Button(f, text=emo.upper(), bg=COLORS["accent"], fg="black", relief="flat", width=12, font=("Segoe UI", 9, "bold"),
                                command=lambda p=palavra, e=emo: self.add_to_timeline(p, e))
            btn_add.pack(side="left")

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def preview_audio(self, palavra, emocao):
        c = os.path.join(DIRETORIO_BANCO, palavra, f"{emocao}.mp3")
        pygame.mixer.Sound(c).play()

    def add_to_timeline(self, palavra, emocao):
        # Cria o "Card" Visual
        card = tk.Frame(self.frame_track, bg=COLORS["card"], width=140, height=160, bd=1, relief="solid")
        card.pack_propagate(False)
        card.pack(side="left", padx=5, pady=10)
        
        # Faixa Colorida Topo
        tk.Frame(card, bg=COLORS["accent"], height=5).pack(fill="x")
        
        # Conteúdo
        tk.Label(card, text=palavra.upper(), bg=COLORS["card"], fg="white", font=("Segoe UI", 11, "bold")).pack(pady=(10, 0))
        tk.Label(card, text=emocao, bg=COLORS["card"], fg=COLORS["accent"], font=("Segoe UI", 9)).pack()
        
        # Input de Delay
        f_delay = tk.Frame(card, bg=COLORS["card"])
        f_delay.pack(pady=10)
        tk.Label(f_delay, text="Delay (s):", bg=COLORS["card"], fg="#aaa", font=("Segoe UI", 8)).pack()
        ent_delay = tk.Entry(f_delay, width=5, justify="center", bg="#222", fg="white", relief="flat", insertbackground="white")
        ent_delay.insert(0, "0.0")
        ent_delay.pack(pady=2)

        # Botão Remover
        btn_rm = tk.Button(card, text="✖", bg=COLORS["card"], fg=COLORS["danger"], relief="flat", font=("Arial", 10),
                           command=lambda: self.remover_card(card))
        btn_rm.pack(side="bottom", fill="x", pady=2)
        
        # Salva referência lógica
        self.playlist.append({
            "p": palavra,
            "e": emocao,
            "widget": card,
            "input": ent_delay
        })
        
        # Auto-scroll para a direita
        self.frame_track.update_idletasks()
        self.canvas.xview_moveto(1.0)

    def remover_card(self, card_widget):
        card_widget.destroy()
        self.playlist = [item for item in self.playlist if item["widget"] != card_widget]

    def limpar_timeline(self):
        for item in self.playlist:
            item["widget"].destroy()
        self.playlist = []

    def tocar_cena(self):
        if not self.playlist:
            messagebox.showinfo("Vazio", "Adicione palavras na timeline primeiro.")
            return

        def _play():
            self.btn_play.config(state="disabled", text="Tocando...", bg="#444")
            
            for item in self.playlist:
                p, e = item["p"], item["e"]
                
                try:
                    delay = float(item["input"].get())
                except:
                    delay = 0.0
                
                # Highlight visual
                item["widget"].config(bg="#555")
                
                path = os.path.join(DIRETORIO_BANCO, p, f"{e}.mp3")
                if os.path.exists(path):
                    s = pygame.mixer.Sound(path)
                    s.play()
                    # Lógica de Delay (Negativo = Atropela)
                    duracao = s.get_length()
                    wait = max(0, duracao + delay)
                    time.sleep(wait)
                
                # Remove Highlight
                item["widget"].config(bg=COLORS["card"])
            
            self.btn_play.config(state="normal", text="▶  REPRODUZIR CENA", bg=COLORS["success"])

        threading.Thread(target=_play, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisStudioPro(root)
    root.mainloop()