import tkinter as tk 
from PIL import Image, ImageTk 
from tkinter import ttk 
from tkinter import PhotoImage
import cv2
import pytesseract 
import time 
import tkinter.font as tkfont
import pandas as pd 
from reportlab.lib.pagesizes import letter 
from reportlab.pdfgen import canvas 
from tkinter import filedialog 

#pip install python
# pip install pillow
# pip install opencv-python
# pip install pytesseract
#pip install pandas openpyxl reportlab

#pip install python pillow opencv-python pytesseract pandas openpyxl reportlab mysql-connector-python

#pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # No Windows

class InterfaceDetector:
        
    def __init__(self,root):
        #VARIAVEIS 
        self.root =root   
        self.cap = None
        self.cameras_disponiveis = []
        self.registros_placas = {}
        self.haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml')
        self.imgtk= None    
        self.is_video_playing = False
        self.is_detecting_plates = False

        #chamando as funçoes da interface
        self.configurar_janela()
        self.criar_frame_label()
        self.criar_botoes_controle(self.frame_controle)
        self.listar_cameras()
        self.style_btn()
    
        


    def configurar_janela(self):
        self.root.title("Reconhecimento de Placas")
        self.root.attributes("-fullscreen", True) 
        self.carregar_imagem_fundo()
        root.bind("<Escape>", lambda event: root.attributes("-fullscreen", not root.attributes("-fullscreen")) if root.attributes("-fullscreen") else root.geometry("1920x1080"))
        root.geometry("1280x720")
       
    def carregar_imagem_fundo(self):  
        imagem_fundo = Image.open("imgs/fundocinzalogo.png")
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
        self.frame_registro.place(relx=0.41 / self.root.winfo_width(), rely=0.005, relwidth=0.585, relheight=0.8) 
        
        #Frame Controle
        self.frame_controle = ttk.LabelFrame(self.root, text="Controle")
        self.frame_controle.place(relx=0.005, rely=(0.6 + 0.02), relwidth=0.4, relheight=0.3)  
       
        #Elementos do Frame Video
        self.imageV = PhotoImage(file="imgs/novideo250px.png")
        self.label_video = tk.Label(self.frame_video,image=self.imageV, bg="#d9d9d9")
        self.label_video.place(relx=0.0, rely=0.0, relwidth=1, relheight=1)
  

         #Elementos do Frame Registro
        self.treeview = self.criar_tabela_registro(self.frame_registro)
        
         #Elementos do Frame Controle
        self.image_controle = Image.open("imgs/abst.png")
        self.label_controle = tk.Label(self.frame_controle)
        self.label_controle.place(relx=0.0, rely=0.0, relwidth=1, relheight=1)
       
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
        self.icon_select.place(relx=0.010, rely=0.1, relwidth=0.07, relheight=0.16)
        
        self.label_selectCam = tk.Label(frame_controle, text="Selec. Câmera: ",bg="#fafafa")#fafafa
        self.label_selectCam.place (relx=0.083, rely=0.1, relwidth=0.20, relheight=0.16)  
        
        self.camera_escolhida =tk.StringVar()
        self.opçoes_cam = ttk.Combobox(frame_controle, textvariable=self.camera_escolhida, state="readonly",justify='center')
        self.opçoes_cam.place(relx=0.285, rely=0.1, relwidth=0.45, relheight=0.16)

        #Iniciar Vídeo    
        self.icon_iniciarVideo = PhotoImage(file="imgs/icon-video.png")
        self.icon_iniciarVideo_image = self.icon_iniciarVideo
        self.icon_iniciarVideo = tk.Button(frame_controle,image=self.icon_iniciarVideo,bd=0,bg="#fbfbfb" )#fbfbfb
        self.icon_iniciarVideo.bind("<Button-1>", lambda event: "break")
        self.icon_iniciarVideo.place(relx=0.010, rely=0.30, relwidth=0.07, relheight=0.16)
        
        self.label_iniciarVideo = tk.Label(frame_controle, text="Iniciar Vídeo: ",bg="#fafafa")#fafafa
        self.label_iniciarVideo.place (relx=0.083, rely=0.30, relwidth=0.20, relheight=0.16)
       
        btn_iniciarVideo = ttk.Button(frame_controle, text="Iniciar", command=self.iniciar_video, style="Custom.TButton")
        btn_iniciarVideo.place(relx=0.285, rely=0.30, relwidth=0.16,relheight=0.16 ) 
        btn_pararVideo = ttk.Button(frame_controle, text="Parar", command=self.parar_video, style="Custom.TButton")
        btn_pararVideo.place(relx=0.48, rely=0.30, relwidth=0.16, relheight=0.16) 

        #Fazer a Detecção
        self.icon_detectar = PhotoImage(file="imgs/icon-detectar.png")
        self.icon_detectar_image = self.icon_detectar
        self.icon_detectar = tk.Button(frame_controle,image=self.icon_detectar,bd=0,bg="#fbfbfb" )#fbfbfb
        self.icon_detectar.bind("<Button-1>", lambda event: "break")
        self.icon_detectar.place(relx=0.010, rely=0.50, relwidth=0.07, relheight=0.16)
        
        self.label_detectar = tk.Label(frame_controle, text="Detectar Placa: ",bg="#fbfbfb")#fafafa
        self.label_detectar.place (relx=0.083, rely=0.50, relwidth=0.20, relheight=0.16)
        
        btn_detectar = ttk.Button(frame_controle, text="Iniciar ",command=self.iniciar_detectar_placa, style="Custom.TButton")
        btn_detectar.place(relx=0.285, rely=0.50, relwidth=0.16, relheight=0.16)
        btn_detectar = ttk.Button(frame_controle, text="Parar ",command=self.parar_detectar_placa, style="Custom.TButton")
        btn_detectar.place(relx=0.48, rely=0.50, relwidth=0.16, relheight=0.16) 
        
        self.icon_on = PhotoImage (file="imgs/icon-ativo.png")
        self.icon_off = PhotoImage(file="imgs/icon-desativado.png")
        self.status = tk.Label(frame_controle,text="Status:", bg="#fafafa")
        self.status.place(relx=0.645, rely=0.50, relwidth=0.10, relheight=0.16) 
        self.icon_status = tk.Button(frame_controle,image=self.icon_off,bd=0, bg="#fafafa")
        self.icon_status.bind("<Button-1>", lambda event: "break")
        self.icon_status.place(relx=0.745, rely=0.50, relwidth=0.05, relheight=0.16) 
        
        #Salvar Registro
        self.icon_salvar = PhotoImage(file="imgs/icon-salvar.png")
        self.icon_salvar_image = self.icon_salvar
        self.icon_salvar = tk.Button(frame_controle,image=self.icon_salvar,bd=0,bg="#fbfbfb")
        self.icon_salvar.place(relx=0.010, rely=0.68, relwidth=0.07, relheight=0.16)
        self.icon_salvar.bind("<Button-1>", lambda event: "break")
      
        self.label_salvar = tk.Label(frame_controle, text="Salvar Dados: ",bg="#fafafa")#fafafa
        self.label_salvar.place (relx=0.083, rely=0.68, relwidth=0.20, relheight=0.16)
      
        btn_salvar_pdf = ttk.Button(frame_controle, text=".pdf ",command=self.exportar_para_pdf, style="Custom.TButton")
        btn_salvar_pdf.place(relx=0.285, rely=0.68, relwidth=0.16, relheight=0.16)
        btn_salvar_xlsx = ttk.Button(frame_controle, text=".xlsx ",command=self.exportar_para_excel, style="Custom.TButton")
        btn_salvar_xlsx.place(relx=0.48, rely=0.68, relwidth=0.16, relheight=0.16) 

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
        #else:
             #self.opçoes_cam.set("--Selecione--")

    def iniciar_video(self):
            if not self.cameras_disponiveis:
                print("Erro: Nenhuma câmera disponível.")
                return
            
            camera_index = self.opçoes_cam.current()  # Pega o índice da câmera selecionada
            if camera_index == -1:
                print("Erro: Nenhuma câmera foi selecionada.")
                return

            try:
                camera_index = int(camera_index)
            except ValueError:
                print("Erro: Selecione uma câmera válida.")
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
                
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if self.is_detecting_plates:
                 self.detectar_placa(frame)

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

    def detectar_placa(self,frame=None):
            if frame is None:
                frame = self.cap.read()[1]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            placas = self.haar_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))


            for (x, y, w, h) in placas:
                x, y, w, h = int(x * 0.9), int(y * 0.9), int(w * 0.8), int(h * 0.8)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                roi = frame[y:y + h, x:x + w]
                roi_resized = cv2.resize(roi, (roi.shape[1] // 2, roi.shape[0] // 2))
                
                roi_gray = cv2.cvtColor(roi_resized, cv2.COLOR_BGR2GRAY)
                _, roi_bin = cv2.threshold(roi_gray, 100, 255, cv2.THRESH_BINARY)

                texto = pytesseract.image_to_string(roi_bin, config= '--psm 8 --oem 3 --psm 6')
                if texto.strip():
                    agora = time.time()
                    if texto not in self.registros_placas:
                        self.registros_placas[texto] = agora
                        self.registrar_entrada(texto)
                    elif agora - self.registros_placas[texto] >= 30:
                        self.registros_placas[texto] = agora
                        self.registrar_saida(texto)
                    print(f"Placa detectada: {texto}")
    def registrar_entrada(self,placa):
        self.treeview.insert('', 'end', values=(placa, time.strftime('%H:%M:%S'), '')) 

    def registrar_saida(self,placa):
        for item in self.treeview.get_children():
            if self.treeview.item(item, 'values')[0] == placa and self.treeview.item(item, 'values')[2] == '':
                self.treeview.item(item, values=(placa, self.treeview.item(item, 'values')[1], time.strftime('%H:%M:%S')))
                break 

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
if __name__ == "__main__":
     root= tk.Tk()
     app= InterfaceDetector(root)

     root.mainloop()
