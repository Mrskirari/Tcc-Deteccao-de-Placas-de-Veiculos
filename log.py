import tkinter as tk
from tkinter import ttk
import mysql.connector
from tkinter import messagebox
import os
import subprocess  #melhora o controle dos processos

def conectar_banco():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="&tec77@info!", #&tec77@info!, mk1209
            database="detectar",
        )
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao conectar ao banco de dados: {err}")
        return None

def fazer_login():
    usuario = entry_usuario.get()
    senha = entry_senha.get()
    funcao = combo_funcao.get()

    conn = conectar_banco()
    if conn:
        cursor = conn.cursor()
        query = "SELECT * FROM usuarios WHERE usuario=%s AND senha=%s AND funcao=%s"
        cursor.execute(query, (usuario, senha, funcao))
        resultado = cursor.fetchone()
        if resultado:
            messagebox.showinfo("Sucesso", f"Bem-vindo, {usuario}!")
            print(f"Usuário logado: {usuario}, Função: {funcao}")
            root.quit()
            try:
                subprocess.Popen(["python", "InterfaceDetectorV2.py",funcao])  # Usa subprocess para iniciar o novo script
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao iniciar o aplicativo: {e}")
        else:
            messagebox.showerror("Erro", "Usuário, senha ou função incorretos!")
        cursor.close()
        conn.close()

root = tk.Tk()
root.title("🔐 Login - Sistema de Detecção")
root.geometry("400x300")
root.configure(bg="#f0f0f5")
root.resizable(False, False)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 400
window_height = 300
position_top = (screen_height // 2) - (window_height // 2)
position_right = (screen_width // 2) - (window_width // 2)

root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

# Estilo moderno com ttk
style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", font=("Segoe UI", 10), background="#f0f0f5")
style.configure("TEntry", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10, "bold"), background="#4a90e2", foreground="white")
style.map("TButton", background=[("active", "#357ABD")])

estilo_label = {
    "font": ("Segoe UI", 12, "bold"),
    "bg": "#f0f0f5",
    "fg": "#333333"
}

frame_login = tk.Frame(root, bg="#f0f0f5")
frame_login.place(relx=0.5, rely=0.5, anchor="center")

label_usuario = tk.Label(frame_login, text="Nome de Usuário:",**estilo_label)
label_usuario.grid(row=0, column=0, padx=10, pady=15, sticky="w")

entry_usuario = tk.Entry(frame_login, font=("Segoe UI", 12), width=20)
entry_usuario.grid(row=0, column=1, padx=2, pady=15, sticky="w")

label_senha = tk.Label(frame_login, text="Senha de Acesso:",**estilo_label)
label_senha.grid(row=1, column=0, padx=10, pady=15, sticky="w")

entry_senha = tk.Entry(frame_login, show="*", font=("Segoe UI", 12,"bold"), width=20)
entry_senha.grid(row=1, column=1, padx=2, pady=15, sticky="w")

label_funcao = tk.Label(frame_login, text="Nível de Acesso:",**estilo_label)
label_funcao.grid(row=2, column=0, padx=10, pady=20, sticky="w")

funcoes = ["Administrador","Usuário"]
combo_funcao = ttk.Combobox(frame_login, values=funcoes, state="readonly", width=21, font=("Segoe UI", 11),justify="center")
combo_funcao.set("-Selecione-")
combo_funcao.grid(row=2, column=1, padx=2, pady=20, sticky="w")


button_login = tk.Button(frame_login, text="Entrar", command=fazer_login,font=("Segoe UI", 12, "bold"), width=10, height=1,relief="solid",bd=2,highlightthickness=0, activebackground="#357ABD",activeforeground="white",borderwidth=2)
button_login.grid(row=3, columnspan=2, pady=20)





root.mainloop()
