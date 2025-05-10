# app_tkinter.py

import tkinter as tk

def criar_janela():
    # Criando a janela principal
    janela = tk.Tk()
    janela.title("Meu TCC - Tkinter")

    # Criando um rótulo de texto
    rotulo = tk.Label(janela, text="Olá, seja bem-vindo ao meu TCC!")
    rotulo.pack()

    # Criando um botão para fechar a janela
    botao = tk.Button(janela, text="Fechar", command=janela.quit)
    botao.pack()

    # Iniciar a aplicação Tkinter
    janela.mainloop()

if __name__ == "__main__":
    criar_janela()
