import subprocess
import sys

def instalar_dependencias():
    pacotes = [
        'mysql-connector-python',
        'pillow',
        'opencv-python',
        'pytesseract',
        'pandas',
        'openpyxl',
        'reportlab',
        'git+https://github.com/ultralytics/yolov5.git',
        'torch',
        'torchvision'
        'requests'
    ]
    
    for pacote in pacotes:
        try:
            print(f"Instalando {pacote}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])
            print(f"{pacote} instalado com sucesso!")
        except subprocess.CalledProcessError:
            print(f"Falha ao instalar {pacote}. Verifique se o pacote está disponível e tente novamente.")

if __name__ == "__main__":
    instalar_dependencias()