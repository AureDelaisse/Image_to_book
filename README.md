# Convertisseur d'Images → CBZ/EPUB

Une application graphique PyQt6 pour convertir vos images en formats **CBZ** (Comic Book Archive) ou **EPUB** (Electronic Publication), parfaite pour créer des bandes dessinées numériques ou des livres d'images.

## ✨ Fonctionnalités

- **Support multi-formats** : PNG, JPG, JPEG, BMP, GIF, TIFF
- **Formats de sortie** : CBZ et EPUB
- **Interface intuitive** : Glisser-déposer et organisation des images
- **Réorganisation facile** : Boutons pour déplacer les images vers le haut/bas
- **Gestion flexible** : Ajout/suppression d'images individuelles
- **Options de destination** : Sauvegarde dans le dossier choisi ou sous-dossiers automatiques
- **Suivi en temps réel** : Barre de progression et statut de conversion
- **Arrêt d'urgence** : Possibilité d'interrompre la conversion

## 🖼️ Aperçu

L'application permet de :
1. Sélectionner des images dans l'ordre souhaité
2. Réorganiser les pages avec les boutons ▲/▼
3. Choisir le format de sortie (CBZ ou EPUB)
4. Définir un nom personnalisé pour le fichier final
5. Convertir avec suivi visuel du progrès

## 📋 Prérequis

```bash
Python 3.7+
```

### Dépendances Python
```bash
pip install PyQt6 Pillow
```

## 🚀 Installation

1. **Cloner le repository**
```bash
git clone https://github.com/votre-username/image-converter.git
cd image-converter
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Lancer l'application**
```bash
python image_converter.py
```

## 📦 Fichier requirements.txt

```txt
PyQt6>=6.0.0
Pillow>=8.0.0
```

## 🎯 Utilisation

### Étapes de base

1. **Sélectionner les images** : Cliquez sur "Sélectionner des images PNG" 
2. **Organiser l'ordre** : Utilisez les boutons ▲/▼ pour réorganiser
3. **Nommer le fichier** : Entrez un nom dans le champ "Nom du fichier"
4. **Choisir le format** : CBZ (recommandé pour BD) ou EPUB (pour livres)
5. **Dossier de sortie** : Sélectionnez où sauvegarder le fichier
6. **Convertir** : Cliquez sur "Démarrer la conversion"

### Options avancées

- **➕ Ajouter** : Ajouter des images supplémentaires à la sélection
- **➖ Supprimer** : Enlever les images sélectionnées de la liste
- **Sous-dossier** : Cochez pour créer automatiquement `CBZ_Converted/` ou `EPUB_Converted/`
- **🛑 Stop** : Interrompre la conversion en cours

## 📁 Structure des fichiers générés

### Format CBZ
```
manga.cbz
├── page_001.jpg
├── page_002.jpg
└── page_xxx.jpg
```

### Format EPUB
```
livre.epub
├── mimetype
├── META-INF/
│   └── container.xml
└── OEBPS/
    ├── content.opf
    ├── toc.ncx
    ├── images/
    │   ├── page_001.jpg
    │   └── ...
    └── pages/
        ├── page_001.xhtml
        └── ...
```

## 🔧 Détails techniques

### Traitement des images
- **Conversion automatique** : Les images RGBA/LA/P sont converties en RGB
- **Qualité optimisée** : Sauvegarde JPEG avec qualité 95%
- **Nommage ordonné** : Format `page_001.jpg`, `page_002.jpg`, etc.

### Architecture
- **Threading** : Conversion en arrière-plan pour interface réactive
- **Nettoyage automatique** : Suppression des fichiers temporaires
- **Gestion d'erreur** : Traitement robuste des erreurs par image

## 🐛 Dépannage

### Problèmes courants

**"Module PyQt6 introuvable"**
```bash
pip install PyQt6
```

**"Impossible d'ouvrir l'image"**
- Vérifiez que le fichier n'est pas corrompu
- Assurez-vous que le format est supporté

**"Erreur de permission"**
- Vérifiez les droits d'écriture dans le dossier de destination
- Fermez les fichiers ouverts dans d'autres applications

## 🎨 Formats supportés

### Entrée
- PNG (recommandé)
- JPG/JPEG
- BMP
- GIF
- TIFF

### Sortie
- **CBZ** : Archive ZIP contenant des images JPEG (parfait pour les lecteurs de BD)
- **EPUB** : Format livre électronique standard (compatible avec la plupart des liseuses)

## 📱 Compatibilité

### Lecteurs CBZ
- ComiCat (Android)
- ComicRack (Windows)
- Chunky Comic Reader (iOS)
- Tous les lecteurs supportant les archives ZIP

### Lecteurs EPUB
- Calibre
- Adobe Digital Editions
- Apple Books
- Kindle (avec conversion)
- La plupart des liseuses électroniques

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs via les Issues
- Proposer des améliorations
- Soumettre des Pull Requests

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👨‍💻 Auteur

Développé avec ❤️ pour faciliter la création de livres numériques à partir d'images.

---

**💡 Conseil** : Pour de meilleurs résultats, utilisez des images de même taille et orientation. Le format CBZ est recommandé pour les bandes dessinées, EPUB pour les livres avec texte.
