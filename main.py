import sys
import os
import zipfile
import shutil
from PIL import Image
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QListWidget,
    QLabel, QProgressBar, QHBoxLayout, QCheckBox, QLineEdit, QMessageBox, QComboBox
)
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon


class ImageConverterWorker(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str, bool)
    start_loading_signal = pyqtSignal()
    stop_loading_signal = pyqtSignal()

    def __init__(self, png_paths, filename, output_folder, use_separate_folder, output_format):
        super().__init__()
        self.png_paths = png_paths
        self.filename = filename
        self.output_folder = output_folder
        self.use_separate_folder = use_separate_folder
        self.output_format = output_format.lower()
        self.is_running = True

    def run(self):
        self.start_loading_signal.emit()

        try:
            # Déterminer le chemin de sortie
            folder_name = f"{self.output_format.upper()}_Converted" if self.use_separate_folder else ""

            if self.use_separate_folder:
                output_directory = os.path.join(self.output_folder, folder_name)
                os.makedirs(output_directory, exist_ok=True)
                output_path = os.path.join(output_directory, f"{self.filename}.{self.output_format}")
            else:
                output_path = os.path.join(self.output_folder, f"{self.filename}.{self.output_format}")

            self.status_signal.emit(f"Création du {self.output_format.upper()} : {self.filename}")

            if self.output_format == 'cbz':
                self.create_cbz(output_path)
            elif self.output_format == 'epub':
                self.create_epub(output_path)

            if self.is_running:
                self.progress_signal.emit(100)
                self.result_signal.emit(f"{self.filename}.{self.output_format}", True)
                self.status_signal.emit("Conversion terminée !")

        except Exception as e:
            self.result_signal.emit(f"Erreur générale: {str(e)}", False)
            self.status_signal.emit("Erreur lors de la conversion !")

        self.stop_loading_signal.emit()

    def create_cbz(self, output_path):
        """Créer un fichier CBZ"""
        temp_dir = "temp_images"
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Traiter les images
            total_images = len(self.png_paths)
            for i, png_path in enumerate(self.png_paths):
                if not self.is_running:
                    return

                try:
                    with Image.open(png_path) as img:
                        # Convertir en RGB si nécessaire
                        if img.mode in ('RGBA', 'LA', 'P'):
                            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                            img = rgb_img

                        # Sauvegarder avec un nom ordonné
                        output_filename = f"page_{i + 1:03d}.jpg"
                        temp_path = os.path.join(temp_dir, output_filename)
                        img.save(temp_path, "JPEG", quality=95)

                except Exception as e:
                    self.result_signal.emit(f"Erreur avec {os.path.basename(png_path)}: {str(e)}", False)
                    continue

                progress = int(((i + 1) / total_images) * 80)
                self.progress_signal.emit(progress)

            # Créer le fichier CBZ
            if self.is_running:
                self.status_signal.emit("Création du fichier CBZ...")
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as cbz:
                    for img_file in sorted(os.listdir(temp_dir)):
                        if not self.is_running:
                            break
                        cbz.write(os.path.join(temp_dir, img_file), img_file)

        finally:
            self.cleanup_temp_dir(temp_dir)

    def create_epub(self, output_path):
        """Créer un fichier EPUB"""
        temp_dir = "temp_epub"
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Structure EPUB
            os.makedirs(os.path.join(temp_dir, "META-INF"), exist_ok=True)
            os.makedirs(os.path.join(temp_dir, "OEBPS", "images"), exist_ok=True)

            # Fichier mimetype
            with open(os.path.join(temp_dir, "mimetype"), "w") as f:
                f.write("application/epub+zip")

            # META-INF/container.xml
            container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
            with open(os.path.join(temp_dir, "META-INF", "container.xml"), "w") as f:
                f.write(container_xml)

            # Traiter les images
            total_images = len(self.png_paths)
            image_files = []

            for i, png_path in enumerate(self.png_paths):
                if not self.is_running:
                    return

                try:
                    with Image.open(png_path) as img:
                        # Convertir en RGB si nécessaire
                        if img.mode in ('RGBA', 'LA', 'P'):
                            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                            img = rgb_img

                        # Sauvegarder l'image
                        img_filename = f"page_{i + 1:03d}.jpg"
                        img_path = os.path.join(temp_dir, "OEBPS", "images", img_filename)
                        img.save(img_path, "JPEG", quality=95)
                        image_files.append(img_filename)

                except Exception as e:
                    self.result_signal.emit(f"Erreur avec {os.path.basename(png_path)}: {str(e)}", False)
                    continue

                progress = int(((i + 1) / total_images) * 60)
                self.progress_signal.emit(progress)

            if not self.is_running:
                return

            # Créer content.opf
            self.create_epub_content_opf(temp_dir, image_files)

            # Créer toc.ncx
            self.create_epub_toc_ncx(temp_dir)

            # Créer les pages XHTML
            self.create_epub_pages(temp_dir, image_files)

            # Créer le fichier EPUB
            self.status_signal.emit("Création du fichier EPUB...")
            self.progress_signal.emit(90)

            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_STORED) as epub:
                # Ajouter mimetype en premier (non compressé)
                epub.write(os.path.join(temp_dir, "mimetype"), "mimetype")

                # Ajouter le reste avec compression
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file == "mimetype":
                            continue
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, temp_dir)
                        epub.write(file_path, arc_path, zipfile.ZIP_DEFLATED)

        finally:
            self.cleanup_temp_dir(temp_dir)

    def create_epub_content_opf(self, temp_dir, image_files):
        """Créer le fichier content.opf pour EPUB"""
        manifest_items = []
        spine_items = []

        for i, img_file in enumerate(image_files):
            page_id = f"page_{i + 1:03d}"
            manifest_items.append(
                f'    <item id="{page_id}" href="pages/{page_id}.xhtml" media-type="application/xhtml+xml"/>')
            manifest_items.append(f'    <item id="img_{i + 1:03d}" href="images/{img_file}" media-type="image/jpeg"/>')
            spine_items.append(f'    <itemref idref="{page_id}"/>')

        content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>{self.filename}</dc:title>
        <dc:creator>Image Converter</dc:creator>
        <dc:identifier id="BookId">urn:uuid:{self.filename}</dc:identifier>
        <dc:language>fr</dc:language>
        <meta name="cover" content="img_001"/>
    </metadata>
    <manifest>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
{chr(10).join(manifest_items)}
    </manifest>
    <spine toc="ncx">
{chr(10).join(spine_items)}
    </spine>
</package>'''

        with open(os.path.join(temp_dir, "OEBPS", "content.opf"), "w", encoding="utf-8") as f:
            f.write(content_opf)

    def create_epub_toc_ncx(self, temp_dir):
        """Créer le fichier toc.ncx pour EPUB"""
        toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="urn:uuid:{self.filename}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle>
        <text>{self.filename}</text>
    </docTitle>
    <navMap>
        <navPoint id="navpoint-1" playOrder="1">
            <navLabel>
                <text>Début</text>
            </navLabel>
            <content src="pages/page_001.xhtml"/>
        </navPoint>
    </navMap>
</ncx>'''

        with open(os.path.join(temp_dir, "OEBPS", "toc.ncx"), "w", encoding="utf-8") as f:
            f.write(toc_ncx)

    def create_epub_pages(self, temp_dir, image_files):
        """Créer les pages XHTML pour EPUB"""
        os.makedirs(os.path.join(temp_dir, "OEBPS", "pages"), exist_ok=True)

        for i, img_file in enumerate(image_files):
            if not self.is_running:
                return

            page_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Page {i + 1}</title>
    <style type="text/css">
        body {{ margin: 0; padding: 0; text-align: center; }}
        img {{ max-width: 100%; max-height: 100%; }}
    </style>
</head>
<body>
    <img src="../images/{img_file}" alt="Page {i + 1}"/>
</body>
</html>'''

            page_filename = f"page_{i + 1:03d}.xhtml"
            with open(os.path.join(temp_dir, "OEBPS", "pages", page_filename), "w", encoding="utf-8") as f:
                f.write(page_content)

    def stop(self):
        self.is_running = False

    def cleanup_temp_dir(self, temp_dir):
        """Nettoie le dossier temporaire"""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except:
            pass


class ImageConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.png_paths = []
        self.use_separate_folder = True
        self.worker = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Convertisseur d'Images → CBZ/EPUB")
        self.setGeometry(100, 100, 650, 650)

        layout = QVBoxLayout()

        # Boutons de sélection et gestion des fichiers
        file_buttons_layout = QHBoxLayout()
        self.select_button = QPushButton("Sélectionner des images PNG")
        self.select_button.clicked.connect(self.select_pngs)
        file_buttons_layout.addWidget(self.select_button)

        self.add_button = QPushButton("➕")
        self.add_button.clicked.connect(self.add_pngs)
        file_buttons_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("➖")
        self.remove_button.clicked.connect(self.remove_selected)
        file_buttons_layout.addWidget(self.remove_button)

        layout.addLayout(file_buttons_layout)

        # Liste des fichiers sélectionnés avec boutons de réorganisation
        list_layout = QHBoxLayout()

        self.file_list = QListWidget()
        list_layout.addWidget(self.file_list)

        # Boutons pour réorganiser
        order_buttons_layout = QVBoxLayout()
        self.move_up_button = QPushButton("▲")
        self.move_up_button.clicked.connect(self.move_up)
        order_buttons_layout.addWidget(self.move_up_button)

        self.move_down_button = QPushButton("▼")
        self.move_down_button.clicked.connect(self.move_down)
        order_buttons_layout.addWidget(self.move_down_button)

        order_buttons_layout.addStretch()
        list_layout.addLayout(order_buttons_layout)

        layout.addLayout(list_layout)

        # Nom du fichier de sortie et format
        name_format_layout = QHBoxLayout()

        name_format_layout.addWidget(QLabel("Nom du fichier:"))
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("Entrez le nom du fichier")
        name_format_layout.addWidget(self.filename_input)

        name_format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CBZ", "EPUB"])
        self.format_combo.setCurrentText("CBZ")
        name_format_layout.addWidget(self.format_combo)

        layout.addLayout(name_format_layout)

        # Sélection du dossier de sortie
        output_layout = QHBoxLayout()
        self.output_button = QPushButton("Choisir dossier de sortie")
        self.output_button.clicked.connect(self.select_output_folder)
        output_layout.addWidget(self.output_button)

        self.output_label = QLabel("Aucun dossier sélectionné")
        output_layout.addWidget(self.output_label)
        layout.addLayout(output_layout)

        # Option de destination
        self.folder_checkbox = QCheckBox("Enregistrer dans un sous-dossier (CBZ_Converted/EPUB_Converted)")
        self.folder_checkbox.setChecked(True)
        self.folder_checkbox.stateChanged.connect(self.toggle_folder_option)
        layout.addWidget(self.folder_checkbox)

        # Boutons pour démarrer et arrêter la conversion
        button_layout = QHBoxLayout()
        self.convert_button = QPushButton("Démarrer la conversion")
        self.convert_button.clicked.connect(self.start_conversion)
        button_layout.addWidget(self.convert_button)

        self.stop_button = QPushButton("🛑 Stop")
        self.stop_button.clicked.connect(self.stop_conversion)
        self.stop_button.setVisible(False)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)

        # Texte fichier en cours de conversion + Animation
        self.status_layout = QHBoxLayout()
        self.status_label = QLabel("Aucune conversion en cours")
        self.status_layout.addWidget(self.status_label)

        # Animation de chargement (optionnelle)
        try:
            self.loading_gif = QMovie("loading.gif")
            self.loading_gif.setScaledSize(QSize(30, 30))
            self.loading_label = QLabel()
            self.loading_label.setMovie(self.loading_gif)
            self.loading_label.setVisible(False)
            self.status_layout.addWidget(self.loading_label)
        except:
            self.loading_label = None

        layout.addLayout(self.status_layout)

        # Barre de progression avec pourcentage
        self.progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setTextVisible(False)
        self.progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("0%")
        self.progress_layout.addWidget(self.progress_label)

        layout.addLayout(self.progress_layout)

        # Liste des résultats
        self.result_list = QListWidget()
        layout.addWidget(self.result_list)

        self.setLayout(layout)

        # Variables pour le dossier de sortie
        self.output_folder = ""

    def select_pngs(self):
        png_paths, _ = QFileDialog.getOpenFileNames(
            self, "Sélectionner des images", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
        )
        if png_paths:
            self.png_paths = list(png_paths)
            self.update_file_list()

    def add_pngs(self):
        png_paths, _ = QFileDialog.getOpenFileNames(
            self, "Ajouter des images", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
        )
        if png_paths:
            self.png_paths.extend(png_paths)
            self.update_file_list()

    def remove_selected(self):
        selected_items = self.file_list.selectedItems()
        if selected_items:
            for item in selected_items:
                filename = item.text()
                for png in self.png_paths:
                    if os.path.basename(png) == filename:
                        self.png_paths.remove(png)
                        break
                self.file_list.takeItem(self.file_list.row(item))

    def move_up(self):
        current_row = self.file_list.currentRow()
        if current_row > 0:
            # Échanger dans la liste des chemins
            self.png_paths[current_row], self.png_paths[current_row - 1] = \
                self.png_paths[current_row - 1], self.png_paths[current_row]
            # Mettre à jour l'affichage
            self.update_file_list()
            self.file_list.setCurrentRow(current_row - 1)

    def move_down(self):
        current_row = self.file_list.currentRow()
        if current_row < len(self.png_paths) - 1 and current_row >= 0:
            # Échanger dans la liste des chemins
            self.png_paths[current_row], self.png_paths[current_row + 1] = \
                self.png_paths[current_row + 1], self.png_paths[current_row]
            # Mettre à jour l'affichage
            self.update_file_list()
            self.file_list.setCurrentRow(current_row + 1)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir le dossier de sortie")
        if folder:
            self.output_folder = folder
            self.output_label.setText(f"Sortie: {folder}")

    def toggle_folder_option(self, state):
        self.use_separate_folder = state == Qt.CheckState.Checked.value

    def start_conversion(self):
        if not self.png_paths:
            QMessageBox.warning(self, "Attention", "Aucune image sélectionnée !")
            return

        filename = self.filename_input.text().strip()
        if not filename:
            QMessageBox.warning(self, "Attention", "Veuillez entrer un nom pour le fichier !")
            return

        if not self.output_folder:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un dossier de sortie !")
            return

        # Nettoyer le nom du fichier
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()
        output_format = self.format_combo.currentText()

        self.worker = ImageConverterWorker(
            self.png_paths, filename, self.output_folder,
            self.use_separate_folder, output_format
        )
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.status_signal.connect(self.status_label.setText)
        self.worker.result_signal.connect(self.update_results)
        self.worker.start_loading_signal.connect(self.start_loading_animation)
        self.worker.stop_loading_signal.connect(self.stop_loading_animation)

        self.worker.start()
        self.stop_button.setVisible(True)
        self.convert_button.setEnabled(False)

    def stop_conversion(self):
        if self.worker:
            self.worker.stop()
            self.stop_button.setVisible(False)
            self.convert_button.setEnabled(True)

    def update_file_list(self):
        self.file_list.clear()
        for i, png in enumerate(self.png_paths):
            self.file_list.addItem(f"{i + 1:02d}. {os.path.basename(png)}")

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.progress_label.setText(f"{value}%")

    def update_results(self, filename, success):
        if success:
            self.result_list.addItem(f"✅ {filename}")
        else:
            self.result_list.addItem(f"❌ {filename}")

    def start_loading_animation(self):
        if self.loading_label:
            self.loading_label.setVisible(True)
            self.loading_gif.start()

    def stop_loading_animation(self):
        if self.loading_label:
            self.loading_label.setVisible(False)
            self.loading_gif.stop()
        self.stop_button.setVisible(False)
        self.convert_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageConverterApp()
    window.show()
    sys.exit(app.exec())