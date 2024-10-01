import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QComboBox,
    QProgressBar,
    QLabel,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pytube import YouTube


class HiloDescarga(QThread):
    senal_progreso = pyqtSignal(int)
    senal_finalizado = pyqtSignal(str)
    senal_error = pyqtSignal(str)

    def __init__(self, url, ruta_guardado, calidad):
        super().__init__()
        self.url = url
        self.ruta_guardado = ruta_guardado
        self.calidad = calidad

    def verificar_progreso(self, transmision, fragmento, bytes_restantes):
        tamano = transmision.filesize
        progreso = int(((tamano - bytes_restantes) / tamano) * 100)
        self.senal_progreso.emit(progreso)

    def run(self):
        try:
            yt = YouTube(self.url, on_progress_callback=self.verificar_progreso)
            if self.calidad == "Audio MP3":
                transmision = yt.streams.filter(only_audio=True).first()
                if transmision is None:
                    raise Exception("No se encontró transmisión de audio")
                archivo_salida = transmision.download(output_path=self.ruta_guardado)
                base, ext = os.path.splitext(archivo_salida)
                nuevo_archivo = base + ".mp3"
                os.rename(archivo_salida, nuevo_archivo)
                self.senal_finalizado.emit(
                    f"Audio descargado: {os.path.basename(nuevo_archivo)}"
                )
            else:
                resolucion = self.calidad.split()[0]
                transmisiones = yt.streams.filter(
                    progressive=True, file_extension="mp4"
                )
                transmision = None
                if resolucion != "Mejor":
                    transmision = transmisiones.filter(resolution=resolucion).first()
                if transmision is None:
                    transmision = transmisiones.get_highest_resolution()
                if transmision is None:
                    raise Exception("No se encontró una transmisión válida")
                archivo_salida = transmision.download(output_path=self.ruta_guardado)
                self.senal_finalizado.emit(
                    f"Video descargado: {os.path.basename(archivo_salida)}"
                )
        except Exception as e:
            self.senal_error.emit(str(e))


class DescargadorYouTube(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Descargador de YouTube")
        self.setMinimumSize(500, 200)
        self.modo_oscuro = False
        self.hilo_descarga = None
        self.iniciar_interfaz()
        self.aplicar_tema()

    def iniciar_interfaz(self):
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        diseno = QVBoxLayout(widget_central)
        self.entrada_url = QLineEdit()
        self.entrada_url.setPlaceholderText("Ingrese la URL del video de YouTube")
        diseno.addWidget(self.entrada_url)
        diseno_calidad = QHBoxLayout()
        etiqueta_calidad = QLabel("Calidad:")
        self.combo_calidad = QComboBox()
        self.combo_calidad.addItems(
            ["Mejor calidad", "1080p", "720p", "480p", "360p", "Audio MP3"]
        )
        diseno_calidad.addWidget(etiqueta_calidad)
        diseno_calidad.addWidget(self.combo_calidad)
        diseno.addLayout(diseno_calidad)
        diseno_guardado = QHBoxLayout()
        self.ruta_guardado = QLineEdit()
        self.ruta_guardado.setPlaceholderText("Ubicación de guardado")
        self.ruta_guardado.setReadOnly(True)
        self.boton_examinar = QPushButton("Examinar")
        self.boton_examinar.clicked.connect(self.examinar_carpeta)
        diseno_guardado.addWidget(self.ruta_guardado)
        diseno_guardado.addWidget(self.boton_examinar)
        diseno.addLayout(diseno_guardado)
        self.barra_progreso = QProgressBar()
        diseno.addWidget(self.barra_progreso)
        diseno_botones = QHBoxLayout()
        self.boton_descarga = QPushButton("Descargar")
        self.boton_descarga.clicked.connect(self.iniciar_descarga)
        self.boton_tema = QPushButton("Cambiar Tema")
        self.boton_tema.clicked.connect(self.alternar_tema)
        diseno_botones.addWidget(self.boton_descarga)
        diseno_botones.addWidget(self.boton_tema)
        diseno.addLayout(diseno_botones)
        self.etiqueta_estado = QLabel("")
        diseno.addWidget(self.etiqueta_estado)

    def aplicar_tema(self):
        if self.modo_oscuro:
            self.setStyleSheet(
                """
                QMainWindow, QWidget { background-color: #333333; color: white; }
                QLineEdit, QComboBox { 
                    background-color: #444444; 
                    color: white; 
                    border: 1px solid #555555;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton { 
                    background-color: #555555; 
                    color: white; 
                    border: none;
                    padding: 8px;
                    border-radius: 3px;
                }
                QPushButton:hover { background-color: #666666; }
                QProgressBar {
                    border: 1px solid #555555;
                    background-color: #444444;
                    color: white;
                    border-radius: 3px;
                }
                QProgressBar::chunk { background-color: #3498db; }
            """
            )
        else:
            self.setStyleSheet(
                """
                QMainWindow, QWidget { background-color: #f0f0f0; color: black; }
                QLineEdit, QComboBox { 
                    background-color: white; 
                    border: 1px solid #cccccc;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton { 
                    background-color: #3498db; 
                    color: white; 
                    border: none;
                    padding: 8px;
                    border-radius: 3px;
                }
                QPushButton:hover { background-color: #2980b9; }
                QProgressBar {
                    border: 1px solid #cccccc;
                    background-color: white;
                    border-radius: 3px;
                }
                QProgressBar::chunk { background-color: #3498db; }
            """
            )

    def alternar_tema(self):
        self.modo_oscuro = not self.modo_oscuro
        self.aplicar_tema()

    def examinar_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de destino"
        )
        if carpeta:
            self.ruta_guardado.setText(carpeta)

    def iniciar_descarga(self):
        url = self.entrada_url.text().strip()
        ruta_guardado = self.ruta_guardado.text().strip()
        calidad = self.combo_calidad.currentText()
        if not url or not ruta_guardado:
            QMessageBox.warning(self, "Error", "Por favor, complete todos los campos")
            return
        self.boton_descarga.setEnabled(False)
        self.barra_progreso.setValue(0)
        self.etiqueta_estado.setText("Preparando descarga...")
        self.hilo_descarga = HiloDescarga(url, ruta_guardado, calidad)
        self.hilo_descarga.senal_progreso.connect(self.actualizar_progreso)
        self.hilo_descarga.senal_finalizado.connect(self.descarga_finalizada)
        self.hilo_descarga.senal_error.connect(self.error_descarga)
        self.hilo_descarga.start()

    def actualizar_progreso(self, progreso):
        self.barra_progreso.setValue(progreso)

    def descarga_finalizada(self, mensaje):
        self.etiqueta_estado.setText(mensaje)
        self.boton_descarga.setEnabled(True)
        self.barra_progreso.setValue(100)
        QMessageBox.information(self, "Éxito", "Descarga completada exitosamente!")

    def error_descarga(self, mensaje_error):
        self.etiqueta_estado.setText(f"Error: {mensaje_error}")
        self.boton_descarga.setEnabled(True)
        QMessageBox.critical(
            self, "Error", f"Error durante la descarga: {mensaje_error}"
        )


if __name__ == "__main__":
    aplicacion = QApplication(sys.argv)
    ventana = DescargadorYouTube()
    ventana.show()
    sys.exit(aplicacion.exec())
