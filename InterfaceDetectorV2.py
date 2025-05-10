import tkinter as tk # cria interface grafica mais simples e pratica
from PIL import Image, ImageTk # modifica redimensiona entre outras ferramentas na imagem
from tkinter import ttk #Fornece widgets mais modernos e estilizados, como labels, botoes e tabelas
from tkinter import PhotoImage #exibe as imagens na interface grafica
import cv2 #captura a imagem/video e faz o pre processameto e passa essas imagens para o OCR
#import pytesseract #biblioteca necessaria para funcionamento correto do tesseract, 
#sua funcionalidade e capturar os acaracteres contidos em imagens ou video,
#usando OCR (Optical Character Recognition), ou Reconhecimento Óptico de Caracteres
import time #captura o tempo 
import tkinter.font as tkfont #ferramenta de manipulacao de fonts
import pandas as pd  #manipula dados / salva em .xlsx
from reportlab.lib.pagesizes import letter #ajusta os parametros do pdf
from reportlab.pdfgen import canvas #salvar em pdf
from tkinter import filedialog #janela de salvamento
from tkinter import messagebox
import torch
import mysql.connector

#pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class InterfaceDetector:
        
    def __init__(self,root,funcao_usuario):
        #VARIAVEIS 
        self.root =root
        self.funcao_usuario = funcao_usuario   
        self.cap = None
        self.cameras_disponiveis = []
        self.registros_placas = {}
        self.imgtk= None    
        self.is_video_playing = False
        self.is_detecting_plates = False
        self.conectar_banco()
            
        #chamando as funçoes da interface
        self.configurar_janela()
        self.criar_frame_label()
        self.criar_botoes_controle(self.frame_controle)
        self.criar_botoes_func_usuario()
        if self.funcao_usuario == "Administrador":
            self.criar_botoes_func_Adm()   
        self.listar_cameras()
        self.style_btn()

        self.modelo_yolo = torch.hub.load('ultralytics/yolov5', 'custom', path='placa.pt')
        self.modelo_yolo_carro  = torch.hub.load('ultralytics/yolov5', 'custom', path='carro.pt')
        self.modelo_crnn_antiga = torch.load("crnn_placaAntiga.pth")
        self.modelo_crnn_mercosul = torch.load("crnn_mercosul.pth")
    

    def conectar_banco(self):
        try:
            # Conexão com o banco de dados
            self.db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="&tec77@info!", # mk1209 / &tec77@info!
                database="detectar" 
            )
            self.cursor = self.db.cursor()
        except mysql.connector.Error as err:
            print(f"Erro de conexão: {err}")    
    
    def is_placa_mercosul(self, texto):
        # Critério baseado na estrutura da placa
        return len(texto) == 7 and texto[0].isalpha() and any(char.isalpha() for char in texto[3:])

    def reconhecer_caracteres_crnn(self, roi, modelo_crnn):
        # Converter a região da placa para escala de cinza e normalizar
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        roi_gray = cv2.resize(roi_gray, (128, 32))  # Ajuste o tamanho conforme necessário
        roi_tensor = torch.tensor(roi_gray, dtype=torch.float32).unsqueeze(0).unsqueeze(0) / 255.0

        # Passar a imagem pelo modelo CRNN
        with torch.no_grad():
            pred = modelo_crnn(roi_tensor)
        
        # Converter a saída do modelo em texto
        caracteres_detectados = self.converter_saida_crnn(pred)

        return caracteres_detectados

    def configurar_janela(self):
        self.root.title("Reconhecimento de Placas")
        self.root.attributes("-fullscreen", True) 
        self.carregar_imagem_fundo()
        root.bind("<Escape>", lambda event: root.attributes("-fullscreen", not root.attributes("-fullscreen")) if root.attributes("-fullscreen") else root.geometry("1920x1080"))
        root.geometry("1280x720")
       
    def carregar_imagem_fundo(self):  
        imagem_fundo = Image.open("imgs/bkMainLogo.png")
        tela_largura = self.root.winfo_screenwidth()
        tela_altura = self.root.winfo_screenheight()
        imagem_fundo = imagem_fundo.resize((tela_largura, tela_altura), Image.Resampling.LANCZOS)
        imagem_fundo_tk = ImageTk.PhotoImage(imagem_fundo)
        self.imagem_fundo_tk = imagem_fundo_tk
        self.label_fundo = tk.Label(self.root, image=self.imagem_fundo_tk)
        self.label_fundo.place(relx=0, rely=0, relwidth=1, relheight=1)
       
    def criar_frame_label(self):
        #Frame Video
        self.frame_video = ttk.LabelFrame(self.root, text="Vídeo")      
        self.frame_video.place(relx=0.005, rely=0.005, relwidth=0.4, relheight=0.6)     
       #Frame Registro
        self.frame_registro = ttk.LabelFrame(self.root, text="Registro")
        self.frame_registro.place(relx=0.41 / self.root.winfo_width(), rely=0.005, relwidth=0.585, relheight=0.7)    
        #Frame Controle
        self.frame_controle = ttk.LabelFrame(self.root, text="Controle")
        self.frame_controle.place(relx=0.005, rely=(0.6 + 0.02), relwidth=0.4, relheight=0.3)  
        #Frame de painel adm/cadastro 
        self.sub_frame_usuario = ttk.LabelFrame(self.root,text="Cadastro de Placas [Funcionários/Alunos]",style="Custom.TLabelframe")
        self.sub_frame_usuario.place(relx=0.41, rely=(0.7 + 0.01), relwidth=0.4, relheight=0.1)      
        self.sub_frame_admin = ttk.LabelFrame(self.root,text="Cadastro de Contas [Usuário/Administrador]",style="Custom.TLabelframe")
        if self.funcao_usuario == "Administrador":
            self.sub_frame_admin.place(relx=0.41, rely=(0.81 + 0.01), relwidth=0.4, relheight=0.1)       
        #Elementos do Frame Video
        self.imageV = PhotoImage(file="imgs/novideo250px.png")
        self.label_video = tk.Label(self.frame_video,image=self.imageV, bg="#d9d9d9")
        self.label_video.place(relx=0.0, rely=0.0, relwidth=1, relheight=1) 
         #Elementos do Frame Registro
        self.treeview = self.criar_tabela_registro(self.frame_registro)        
         #Elementos do Frame Controle
        self.image_controle = Image.open("imgs/bkControl.png")
        self.label_controle = tk.Label(self.frame_controle)
        self.label_controle.place(relx=0.0, rely=0.0, relwidth=1, relheight=1)
        #Elementos(subframe) do Frame Adm/Cadastro

    def criar_botoes_func_usuario(self):
        btn_cadastrar_cad_placa = ttk.Button(self.sub_frame_usuario, text="Cadastrar", command=self.janela_cadastro_placa, style="Custom.TButton")
        btn_cadastrar_cad_placa.place(relx=0.05, rely=0.25, relwidth=0.16, relheight=0.6)
        btn_editar_cad_placa = ttk.Button(self.sub_frame_usuario, text="Editar", command=self.janela_editar_placa, style="Custom.TButton")
        btn_editar_cad_placa.place(relx=0.26, rely=0.25, relwidth=0.16, relheight=0.6)
        btn_excluir_cad_placa = ttk.Button(self.sub_frame_usuario, text="Excluir", command=self.janela_excluir_placa, style="Custom.TButton")
        btn_excluir_cad_placa.place(relx=0.47, rely=0.25, relwidth=0.16, relheight=0.6)             
        btn_listar_cad_placas = ttk.Button(self.sub_frame_usuario,text="Listar Cadastros",command=self.listar_placas, style="Custom.TButton")
        btn_listar_cad_placas.place(relx=0.68, rely=0.25, relwidth=0.24, relheight=0.6)
       
    def criar_botoes_func_Adm(self):
        btn_cadastrar_usuario = ttk.Button(self.sub_frame_admin, text="Cadastrar", command=self.janela_cadastro_usuario, style="Custom.TButton")
        btn_cadastrar_usuario.place(relx=0.05, rely=0.25, relwidth=0.16, relheight=0.6)
        btn_editar_usuario = ttk.Button(self.sub_frame_admin, text="Editar", command=self.janela_editar_usuario, style="Custom.TButton")
        btn_editar_usuario.place(relx=0.26, rely=0.25, relwidth=0.16, relheight=0.6)
        btn_excluir_usuario = ttk.Button(self.sub_frame_admin, text="Excluir", command=self.janela_excluir_usuario, style="Custom.TButton")
        btn_excluir_usuario.place(relx=0.47, rely=0.25, relwidth=0.16, relheight=0.6)          
        btn_listar_usuarios = ttk.Button(self.sub_frame_admin,text="Listar Cadastros",command=self.listar_usuarios,style="Custom.TButton")
        btn_listar_usuarios.place(relx=0.68, rely=0.25, relwidth=0.24, relheight=0.6)

    def janela_cadastro_usuario(self):
        def cadastrar_usuario(dados):
            usuario, senha, funcao = dados
            query = "INSERT INTO usuarios (usuario, senha, funcao) VALUES (%s, %s, %s)"
            self.cursor.execute(query, (usuario, senha, funcao))
            self.db.commit()                         
        self.popup_generico("Cadastrar Usuário", ["Nome", "Senha", "Função"], cadastrar_usuario)

    def janela_editar_usuario(self):
        def editar_usuario(dados):
            nome_atual, novo_nome, nova_senha, nova_funcao = dados
            if not nome_atual.strip():
                messagebox.showerror("Erro", "O campo 'Nome Atual' é obrigatório.")
                return 
            query_busca = "SELECT usuario, senha, funcao FROM usuarios WHERE usuario = %s"
            self.cursor.execute(query_busca, (nome_atual,))
            resultado = self.cursor.fetchone()
            if not resultado:
                messagebox.showerror("Erro", f"Usuário '{nome_atual}' não encontrado.")
                return
            nome_existente, senha_existente, funcao_existente = resultado
            nome_final = novo_nome if novo_nome.strip() else nome_existente
            senha_final = nova_senha if nova_senha.strip() else senha_existente
            funcao_final = nova_funcao if nova_funcao.strip() else funcao_existente
            query_update = """
                UPDATE usuarios 
                SET usuario = %s, senha = %s, funcao = %s 
                WHERE usuario = %s
            """
            self.cursor.execute(query_update, (nome_final, senha_final, funcao_final, nome_atual))
            self.db.commit()
            print("Usuário atualizado com sucesso.")
        self.popup_generico("Editar Usuário", ["Nome Atual", "Novo Nome", "Nova Senha","Nova Função"], editar_usuario)

    def janela_excluir_usuario(self):
        def excluir_usuario(dados):
            nome = dados

            if not nome.strip():
                messagebox.showerror("Erro", "O campo 'Nome' é obrigatório.")
                return
            try:
                self.conectar_banco()   
                query_verifica = "SELECT * FROM usuarios WHERE usuario = %s"
                self.cursor.execute(query_verifica, (nome,))
                resultado = self.cursor.fetchone()
                if not resultado:
                    messagebox.showerror("Erro", f"Usuário '{nome}' não encontrado.")
                    return
                confirmar = messagebox.askyesno("Confirmação", f"Tem certeza que deseja excluir o usuário '{nome}'?")
                if not confirmar:
                    return
                query_delete = "DELETE FROM usuarios WHERE usuario = %s"
                self.cursor.execute(query_delete, (nome,))
                self.db.commit()
                messagebox.showinfo("Sucesso", f"Usuário '{nome}' excluído com sucesso.")

            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao excluir: {str(e)}")

            self.popup_generico("Excluir Usuário", ["Nome"], excluir_usuario)

    def janela_cadastro_placa(self):
        def cadastrar_placa(dados):
            nome, funcao, placas = dados
            query_usuario  = "INSERT INTO registro_usua (nome , funcao) VALUES (%s, %s)"
            self.cursor.execute(query_usuario, (nome, funcao))
            self.db.commit()
            id_usuario = self.cursor.lastrowid

            query_placa = "INSERT INTO placas (id_usuario, placa) VALUES (%s, %s)"
            for placa in placas:
                if placa.strip():
                    self.cursor.execute(query_placa, (id_usuario, placa))
            self.db.commit()    
        self.popup_generico("Cadastrar Placa", ["Nome","Função", "Placa"], cadastrar_placa)

    def janela_editar_placa(self):

        self.popup_generico("Editar Placa", ["Placa Atual", "Nova Placa"], lambda dados: print("Editar Placa:", dados))

    def janela_excluir_placa(self):
        self.popup_generico("Excluir Placa", ["Placa"], lambda dados: print("Excluir Placa:", dados))

    def listar_usuarios(self):
    # Exemplo de dados (simulando banco de dados)
        usuarios = [{"Nome": "João", "Função": "Adiministrador", "Senha": "1234"},{"Nome": "Maria", "Função": "Desenvolvedor", "Senha": "abcd"},{"Nome": "Carlos", "Função": "Usuário", "Senha": "xyz789"},]
        self.janela_listagem("Usuários Cadastrados", ["Nome", "Função","Senha"], usuarios)

    def listar_placas(self):
        # Exemplo de dados (simulando banco de dados)
        placas = [{"Nome": "João", "Função": "Aluno", "Placas": "ABC-1234"},{"Nome": "Maria", "Função": "Professor", "Placas": "XYZ-5678"},{"Nome": "João", "Função": "Aluno", "Placas": "DEF-9999"},]
        self.janela_listagem("Placas Cadastradas", ["Nome", "Função", "Placas"], placas)

    def janela_listagem(self, titulo, colunas, dados):
        janela = tk.Toplevel(self.root)
        janela.title(titulo)
        janela.configure(bg="#f5f5f5")
        frame = tk.Frame(janela, padx=10, pady=10, bg="#f5f5f5")
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text=titulo, font=("Segoe UI", 12, "bold"), bg="#f5f5f5").pack(pady=(0, 10))
        tree = ttk.Treeview(frame, columns=colunas, show="headings")
        for col in colunas:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", stretch=True)
        for item in dados:
            valores = [item[col] for col in colunas]
            tree.insert("", "end", values=valores)
        tree.pack(fill="both", expand=True)
        btn_fechar = tk.Button(frame, text="Fechar", command=janela.destroy, bg="#f0a5a5", font=("Segoe UI", 10, "bold"))
        btn_fechar.pack(pady=10)
        janela.update_idletasks()
        largura_popup = janela.winfo_width()
        altura_popup = janela.winfo_height()
        largura_tela = janela.winfo_screenwidth()
        altura_tela = janela.winfo_screenheight()
        x = (largura_tela // 2) - (largura_popup // 2)
        y = (altura_tela // 2) - (altura_popup // 2)
        janela.geometry(f"{largura_popup}x{altura_popup}+{x}+{y}")

    def popup_generico(self, titulo, campos, callback_salvar):
        janela = tk.Toplevel(self.root)
        janela.title(titulo)
        janela.configure(bg="#f5f5f5")
        frame = tk.Frame(janela, bg="#f5f5f5", padx=20, pady=10)
        frame.pack()
        tk.Label(frame, text=titulo, font=("Segoe UI", 12, "bold"), bg="#f5f5f5").grid(row=0, column=0, columnspan=2, pady=(0, 15))
        entradas = {}
        placa_entries = []
        for i, campo in enumerate(campos):
            row_index = i + 1
            if campo.lower() == "placa":
                tk.Label(frame, text=f"{campo}:", font=("Segoe UI", 11), bg="#f5f5f5").grid(row=row_index, column=0, sticky="ne", padx=10, pady=5)
                container = tk.Frame(frame, bg="#f5f5f5")
                container.grid(row=row_index, column=1, sticky="w")
                placa_entries.append([])
                def adicionar_placa():
                    entry = ttk.Entry(container, width=30)
                    entry.pack(pady=2,padx=10)
                    placa_entries[-1].append(entry)
                    if len(placa_entries[-1]) == 1:
                        entry.focus_set()
                adicionar_placa()
                ttk.Button(frame, text="+ Adicionar", command=adicionar_placa).grid(row=row_index + 1, column=1, sticky="w", pady=5,padx=10)
            else:
                tk.Label(frame, text=f"{campo}:", font=("Segoe UI", 11), bg="#f5f5f5").grid(row=row_index, column=0, padx=10, pady=5, sticky="e")
                entry = ttk.Entry(frame, width=30)
                entry.grid(row=row_index, column=1, padx=10, pady=5, sticky="w")
                entradas[campo] = entry
                if i == 0:
                    entry.focus_set() 
        total_linhas = len(campos) + 2  

        def salvar():
            dados = []
            placas = []

            for campo in campos:
                if campo.lower() == "placa":
                    placas = [e.get().strip() for e in placa_entries[-1] if e.get().strip()]
                    if not placas:
                        messagebox.showerror("Erro", "Informe pelo menos uma placa.")
                        return
                    dados.append(placas)
                else:
                    valor = entradas[campo].get().strip()
                    dados.append(valor)
            try:
                callback_salvar(dados)
                messagebox.showinfo("Sucesso", "Dados salvos com sucesso!")
                janela.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar: {str(e)}")

        btn_salvar = tk.Button(frame, text="Salvar", command=salvar, width=10, font=("Segoe UI", 11, "bold"),bg="#bcf7cc")
        btn_salvar.grid(row=total_linhas, column=0, columnspan=2, pady=15)

        janela.bind("<Return>", lambda event: salvar())
        janela.update_idletasks()
        largura_popup = janela.winfo_width()
        altura_popup = janela.winfo_height()
        largura_tela = janela.winfo_screenwidth()
        altura_tela = janela.winfo_screenheight()
        x = (largura_tela // 2) - (largura_popup // 2)
        y = (altura_tela // 2) - (altura_popup // 2)
        janela.geometry(f"{largura_popup}x{altura_popup}+{x}+{y}")
       
    def criar_tabela_registro(self,frame_registro):
        #Criação das tabelas de registro
        self.treeview = ttk.Treeview(frame_registro, columns=("PLACA", "ENTRADA", "SAÍDA"),show="headings")
        self.treeview.heading("PLACA", text="Número da Placa")
        self.treeview.heading("ENTRADA", text="Entrada")
        self.treeview.heading("SAÍDA", text="Saída")
        self.treeview.column("PLACA", width=150, anchor="center")
        self.treeview.column("ENTRADA", width=100, anchor="center")
        self.treeview.column("SAÍDA", width=100, anchor="center")
        self.treeview.place(relx=0.0, rely=0.0, relwidth=1, relheight=1)
        return self.treeview

    def criar_botoes_controle(self,frame_controle):
        #seleçao de camera
        self.icon_select = PhotoImage(file="imgs/icon-select.png")
        self.icon_select_image = self.icon_select
        self.icon_select = tk.Button(frame_controle,image=self.icon_select,bd=0,bg="#fafafa" )#fbfbfb
        self.icon_select.bind("<Button-1>", lambda event: "break")
        self.icon_select.place(relx=0.010, rely=0.1, relwidth=0.07, relheight=0.15)     
        self.label_selectCam = tk.Label(frame_controle, text="Selec. Câmera: ",bg="#fafafa")#fafafa
        self.label_selectCam.place (relx=0.083, rely=0.1, relwidth=0.20, relheight=0.14)      
        self.camera_escolhida =tk.StringVar()
        self.opçoes_cam = ttk.Combobox(frame_controle, textvariable=self.camera_escolhida, state="readonly",justify='center')
        self.opçoes_cam.place(relx=0.285, rely=0.1, relwidth=0.45, relheight=0.14)
        #Iniciar Vídeo    
        self.icon_iniciarVideo = PhotoImage(file="imgs/icon-video.png")
        self.icon_iniciarVideo_image = self.icon_iniciarVideo
        self.icon_iniciarVideo = tk.Button(frame_controle,image=self.icon_iniciarVideo,bd=0,bg="#fbfbfb" )#fbfbfb
        self.icon_iniciarVideo.bind("<Button-1>", lambda event: "break")
        self.icon_iniciarVideo.place(relx=0.010, rely=0.30, relwidth=0.07, relheight=0.15)    
        self.label_iniciarVideo = tk.Label(frame_controle, text="Iniciar Vídeo: ",bg="#fafafa")#fafafa
        self.label_iniciarVideo.place (relx=0.083, rely=0.30, relwidth=0.20, relheight=0.14)   
        btn_iniciarVideo = ttk.Button(frame_controle, text="Iniciar", command=self.iniciar_video, style="Custom.TButton")
        btn_iniciarVideo.place(relx=0.285, rely=0.30, relwidth=0.16,relheight=0.14 ) 
        btn_pararVideo = ttk.Button(frame_controle, text="Parar", command=self.parar_video, style="Custom.TButton")
        btn_pararVideo.place(relx=0.48, rely=0.30, relwidth=0.16, relheight=0.14) 
        #Fazer a Detecção
        self.icon_detectar = PhotoImage(file="imgs/icon-detectar.png")
        self.icon_detectar_image = self.icon_detectar
        self.icon_detectar = tk.Button(frame_controle,image=self.icon_detectar,bd=0,bg="#fbfbfb" )#fbfbfb
        self.icon_detectar.bind("<Button-1>", lambda event: "break")
        self.icon_detectar.place(relx=0.010, rely=0.50, relwidth=0.07, relheight=0.15)      
        self.label_detectar = tk.Label(frame_controle, text="Detectar Placa: ",bg="#fbfbfb")#fafafa
        self.label_detectar.place (relx=0.083, rely=0.50, relwidth=0.20, relheight=0.14)     
        btn_detectar = ttk.Button(frame_controle, text="Iniciar ",command=self.iniciar_detectar_placa, style="Custom.TButton")
        btn_detectar.place(relx=0.285, rely=0.50, relwidth=0.16, relheight=0.14)
        btn_detectar = ttk.Button(frame_controle, text="Parar ",command=self.parar_detectar_placa, style="Custom.TButton")
        btn_detectar.place(relx=0.48, rely=0.50, relwidth=0.16, relheight=0.14)       
        self.icon_on = PhotoImage (file="imgs/icon-ativo.png")
        self.icon_off = PhotoImage(file="imgs/icon-desativado.png")
        self.status = tk.Label(frame_controle,text="Status:", bg="#fafafa")
        self.status.place(relx=0.645, rely=0.50, relwidth=0.10, relheight=0.14) 
        self.icon_status = tk.Button(frame_controle,image=self.icon_off,bd=0, bg="#fafafa")
        self.icon_status.bind("<Button-1>", lambda event: "break")
        self.icon_status.place(relx=0.745, rely=0.50, relwidth=0.05, relheight=0.15)       
        #Salvar Registro
        self.icon_salvar = PhotoImage(file="imgs/icon-salvar.png")
        self.icon_salvar_image = self.icon_salvar
        self.icon_salvar = tk.Button(frame_controle,image=self.icon_salvar,bd=0,bg="#fbfbfb")
        self.icon_salvar.place(relx=0.010, rely=0.68, relwidth=0.07, relheight=0.15)
        self.icon_salvar.bind("<Button-1>", lambda event: "break")  
        self.label_salvar = tk.Label(frame_controle, text="Salvar Dados: ",bg="#fafafa")#fafafa
        self.label_salvar.place (relx=0.083, rely=0.68, relwidth=0.20, relheight=0.14) 
        btn_salvar_pdf = ttk.Button(frame_controle, text=".pdf ",command=self.exportar_para_pdf, style="Custom.TButton")
        btn_salvar_pdf.place(relx=0.285, rely=0.68, relwidth=0.16, relheight=0.14)
        btn_salvar_xlsx = ttk.Button(frame_controle, text=".xlsx ",command=self.exportar_para_excel, style="Custom.TButton")
        btn_salvar_xlsx.place(relx=0.48, rely=0.68, relwidth=0.16, relheight=0.14) 
        #Botão de fechar programa
        btn_fechar = ttk.Button(self.root, text="Fechar", command=self.root.quit,style="Custom.TButton")
        btn_fechar.place(relx=0.35, rely=(0.85 + 0.01), relwidth=0.05, relheight=0.05)                

    def update_image(self):
        width = self.label_controle.winfo_width()
        height = self.label_controle.winfo_height()
        resized_image = self.image_controle.resize((width, height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized_image)
        self.label_controle.config(image=photo)
        self.label_controle.image = photo

    def listar_cameras(self):
        self.cameras_disponiveis = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                camera_name = f"Câmera {i}"
                self.cameras_disponiveis.append(camera_name)
                cap.release()
            if self.cameras_disponiveis:
             self.opçoes_cam["values"] = self.cameras_disponiveis
             self.opçoes_cam.current(0)
    def iniciar_video(self):
            if not self.cameras_disponiveis:
                print("Erro: Nenhuma câmera disponível.")
                return           
            camera_index = self.opçoes_cam.current()  # Pega o índice da câmera selecionada
            if camera_index == -1:
                print("Erro: Nenhuma câmera foi selecionada.")
                return
            if self.cap and self.cap.isOpened():
                self.cap.release()

            self.opçoes_cam.set("Em Uso...")

            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                print("Erro: Não foi possível acessar a câmera.")
                return
            self.is_video_playing = True
            self.atualizar_video()
    
    def parar_video(self):
        self.is_video_playing = False
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()  # Libera a câmera
            cv2.destroyAllWindows()  # Fecha todas as janelas do OpenCV
        self.is_detecting_plates = False
        self.imageV = PhotoImage(file="imgs/novideo250px.png")  
        self.label_video.config(image=self.imageV)  
        self.label_video.image = self.imageV

    def iniciar_detectar_placa(self):
        self.is_detecting_plates = True  # Ativa a detecção
        print("Detecção de placas iniciada.")
        self.icon_status.config(image=self.icon_on)
        self.icon_status.image = self.icon_on

    def parar_detectar_placa(self):
        self.is_detecting_plates = False  # Desativa a detecção
        print("Detecção de placas parada.")
        self.icon_status.config(image=self.icon_off)
        self.icon_status.image = self.icon_off

    def atualizar_video(self):
            if self.cap is None or not self.cap.isOpened():
                return          
            ret, frame = self.cap.read()
            if not ret:
                print("Erro na leitura do frame da câmera")
                return             
            frame_resized = cv2.resize(frame, (640, 640))
            
            if self.is_detecting_plates:
                self.detectar_placa(frame_resized)

            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)

            largura_label = self.label_video.winfo_width()
            altura_label = self.label_video.winfo_height()
            nova_largura = int(largura_label * 0.996)
            nova_altura = int(altura_label * 0.996)
            nova_largura = max(nova_largura, 10)
            nova_altura = max(nova_altura, 10)
            img = Image.fromarray(frame_rgb)
            img = img.resize((nova_largura, nova_altura),Image.Resampling.LANCZOS)
            self.imgtk = ImageTk.PhotoImage(image=img)
            self.label_video.imgtk = self.imgtk
            self.label_video.config(image=self.imgtk)
            if self.is_video_playing:
                self.root.after(10, self.atualizar_video)

    def detectar_placa(self, frame=None):
        if frame is None:
            ret, frame = self.cap.read()
            if not ret:
                return

        results_carro = self.modelo_yolo_carro(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), size=640)
        detections_carro = results_carro.xyxy[0]

        results_placa = self.modelo_yolo(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), size=640)
        detections_placa = results_placa.xyxy[0]

        print(f"Total de detecções de veículos: {len(detections_carro)}")
        print(f"Total de detecções de placas: {len(detections_placa)}")

        # Ajuste do estilo da detecção de veículo (borda azul e preenchimento translúcido)
        for *box, conf, cls in detections_carro:
            x1, y1, x2, y2 = map(int, box)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 0, 0), -1)  # Azul preenchido
            alpha = 0.3
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)  # Borda azul do veículo

        # Detecção da placa (borda vermelha + preenchimento verde translúcido)
        for *box, conf, cls in detections_placa:
            x1, y1, x2, y2 = map(int, box)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), -1)  # Preenchimento verde translúcido
            alpha = 0.3
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Borda vermelha da placa

            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                print("ROI vazia, pulando.")
                continue

            # Converter ROI para escala de cinza e normalizar
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            roi_gray = cv2.resize(roi_gray, (128, 32))  # Ajustar o tamanho conforme necessário
            roi_tensor = torch.tensor(roi_gray, dtype=torch.float32).unsqueeze(0).unsqueeze(0) / 255.0

            # Escolher modelo baseado no padrão da placa
            modelo_crnn = self.modelo_crnn_mercosul if self.is_placa_mercosul(roi) else self.modelo_crnn_antiga

            with torch.no_grad():
                pred = modelo_crnn(roi_tensor)

            # Converter a saída do modelo CRNN para texto
            texto_detectado = self.converter_saida_crnn(pred)

            if texto_detectado.strip():
                agora = time.strftime('%H:%M:%S')
                if texto_detectado not in self.registros_placas:
                    self.registros_placas[texto_detectado] = time.time()
                    self.registrar_entrada(texto_detectado, agora)
                elif time.time() - self.registros_placas[texto_detectado] >= 30:
                    self.registros_placas[texto_detectado] = time.time()
                    self.registrar_saida(texto_detectado, agora)
                print(f"Placa detectada: {texto_detectado}")



    def registrar_entrada(self,placa, horario_entrada):
        query = "INSERT INTO entrada_saida (placa, entrada, saida) VALUES (%s, %s, %s)"
        values = (placa, horario_entrada, None)
        self.cursor.execute(query, values)
        self.db.commit()
        print(f"Entrada registrada Placa: {placa}.")

        update_query = "UPDATE veiculos SET ultima_entrada = %s WHERE placa = %s"
        update_values = (horario_entrada, placa)
        self.cursor.execute(update_query, update_values)
        self.db.commit()
        print(f"Ultima entrada registrada da placa: {placa}")

    def registrar_saida(self,placa, horario_saida):
        query = "UPDATE veiculos SET saida = %s WHERE placa = %s AND saida IS NULL"
        values = (horario_saida, placa)
        self.cursor.execute(query, values)
        self.db.commit()
        print(f"Saida registrada Placa: {placa}.")

        update_query = "UPDATE veiculos SET ultima_saida = %s WHERE placa = %s"
        update_values = (horario_saida, placa)
        self.cursor.execute(update_query, update_values)
        self.db.commit()
        print(f"Última saída registrada da placa {placa}.")

    def exportar_para_excel(self):
        registros = []
        for item in self.treeview.get_children():
            placa, entrada, saida = self.treeview.item(item, 'values')
            registros.append([placa, entrada, saida])

        df = pd.DataFrame(registros, columns=["Placa", "Entrada", "Saída"])
        caminho_arquivo = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if caminho_arquivo:
            df.to_excel(caminho_arquivo, index=False)
            print("Registros exportados para Excel com sucesso!")
        else:
         print("Operação de exportação cancelada.")

# Função para exportar os dados para PDF
    def exportar_para_pdf(self):
        registros = []
        for item in self.treeview.get_children():
            placa, entrada, saida = self.treeview.item(item, 'values')
            registros.append([placa, entrada, saida])
        caminho_arquivo = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    
        if caminho_arquivo:
            c = canvas.Canvas(caminho_arquivo, pagesize=letter)
            largura, altura = letter

            c.setFont("Helvetica", 10)
            c.drawString(50, altura - 40, "Placa  | Entrada  | Saída")

            y_position = altura - 60
            for registro in registros:
                c.drawString(50, y_position, f"{registro[0]}  | {registro[1]}  | {registro[2]}")
                y_position -= 20
                if y_position < 40:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    c.drawString(50, altura - 40, "Placa  | Entrada  | Saída")
                    y_position = altura - 60      
            c.save()
            print("Registros exportados para PDF com sucesso!")
        else:
            print("Operação de exportação cancelada.")
        
    def style_btn(self):
        style = ttk.Style()
        style.theme_use("alt")
        style.configure("Custom.TButton",           
                  relief="raised",      
                  background="#262424", 
                  foreground="white", 
                  width=0, 
                  borderwidth=3,
                  )
        style.map("Custom.TButton", background=[("active", "#0e0d0d")])#272727
        self.root.bind("<Configure>", self.atualizar_estilo)

    def atualizar_estilo(self, event):
        font_size = int(self.root.winfo_height() / 80) 
        font_botoes = tkfont.Font(family="Georgia", size=font_size)
        font_labels = tkfont.Font(family="Georgia", size=font_size,weight="bold")
        style = ttk.Style()
        style.configure("Custom.TButton", font=font_botoes)
        style.configure("Custom.TLabelframe.Label", font=font_labels, anchor="center")
        # Força a atualização dos botões
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.configure(style="Custom.TButton")
            self.label_selectCam.config(font=font_labels)
            self.label_iniciarVideo.config(font=font_labels)
            self.label_detectar.config(font=font_labels)    
            self.opçoes_cam.config(font=font_labels)
            self.label_salvar.config(font=font_labels)
            self.status.config(font=font_labels)       
        self.update_image()

import sys     
if __name__ == "__main__":
     funcao_usuario = sys.argv[1] if len(sys.argv) > 1 else "Usuário"  # valor padrão
     root= tk.Tk()
     app= InterfaceDetector(root, funcao_usuario)

     root.mainloop()