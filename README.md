# ESG Nouvelair API

Une API robuste et complète pour la gestion des initiatives ESG (Environmental, Social, and Governance) de Nouvellaire.

## 📋 Table des matières

- [Description](#description)
- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Structure du projet](#structure-du-projet)
- [API Endpoints](#api-endpoints)
- [Documentation](#documentation)

## 📝 Description

L'API ESG Nouvelair est une solution backend complète développée avec **FastAPI** pour gérer tous les aspects de la stratégie environnementale, sociale et de gouvernance de Nouvelair. Elle permet de suivre et de gérer :

- Les émissions de CO2
- Les surcharges carburant
- La gestion des déchets
- Les données des employés
- Les formations professionnelles
- Les accidents du travail
- Le suivi des paiements
- Les obligations fiscales
- Les licences aviation
- Les utilisateurs et leurs rôles

## 🎯 Fonctionnalités

### Gestion Environnementale
- **CO2** : Suivi des émissions de carbone et calculs d'impact environnemental
- **Gestion des déchets** : Documentation et gestion des déchets produits
- **Surcharge carburant** : Gestion des surcharges et optimisation des carburants

### Gestion Sociale
- **Employés** : Gestion des données et profils des employés
- **Formations** : Suivi des programmes de formation et développement
- **Accidents du travail** : Enregistrement et suivi des incidents

### Gouvernance
- **Utilisateurs** : Authentification et gestion des rôles
- **Licences Aviation** : Suivi des certifications et licences
- **Obligations fiscales** : Conformité réglementaire et obligations
- **Suivi des paiements** : Gestion financière et traçabilité
- **Pilliers ESG** : Structuration et suivi des trois piliers ESG

## 🏗️ Architecture

Le projet suit une architecture en couches :

```
app/
├── controllers/        # Points d'entrée API (endpoints FastAPI)
├── services/          # Logique métier
├── models/            # Modèles de base de données (ORM)
├── schemas/           # Schémas de validation Pydantic
└── database.py        # Configuration de la base de données
```

### Modèle de conception
- **Controllers** : Gèrent les routes HTTP et la validation des entrées
- **Services** : Contiennent la logique métier et l'accès aux données
- **Models** : Définissent la structure des données en base de données
- **Schemas** : Valident et sérialisent les données avec Pydantic

## 🔧 Prérequis

- Python 3.8+
- pip (gestionnaire de paquets Python)
- Une base de données compatible (SQLAlchemy)

## 📦 Installation

### 1. Cloner le projet
```bash
git clone <votre-repo>
cd esg_nouvelaire
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv
```

### 3. Activer l'environnement virtuel

**Sur Windows :**
```bash
.\venv\Scripts\Activate.ps1
```

**Sur macOS/Linux :**
```bash
source venv/bin/activate
```

### 4. Installer les dépendances
```bash
pip install -r requirements.txt
```

## 🚀 Utilisation

### Lancer le serveur de développement
```bash
python main.py
```

Ou avec Uvicorn directement :
```bash
uvicorn main:app --reload
```

Le serveur démarre sur `http://localhost:8000`

### Accéder à la documentation interactive
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

## 📂 Structure du projet

```
esg_nouvelaire/
├── main.py                              # Point d'entrée de l'application
├── requirements.txt                     # Dépendances du projet
├── README.md                            # Ce fichier
└── app/
    ├── __init__.py
    ├── database.py                      # Configuration de la base de données
    │
    ├── controllers/                     # API Routes
    │   ├── aviation_license_controller.py
    │   ├── co2_controller.py
    │   ├── employee_controller.py
    │   ├── fuel_surcharge_controller.py
    │   ├── payment_tracking_controller.py
    │   ├── pillar_controller.py
    │   ├── tax_obligation_controller.py
    │   ├── training_controller.py
    │   ├── user_controller.py
    │   ├── waste_management_controller.py
    │   └── work_accident_controller.py
    │
    ├── services/                        # Logique métier
    │   ├── aviation_license_service.py
    │   ├── co2_service.py
    │   ├── employee_service.py
    │   ├── fuel_surcharge_service.py
    │   ├── payment_tracking_service.py
    │   ├── pillar_service.py
    │   ├── tax_obligation_service.py
    │   ├── training_service.py
    │   ├── user_service.py
    │   ├── waste_management_service.py
    │   └── work_accident_service.py
    │
    ├── models/                          # Modèles de données
    │   └── models.py
    │
    └── schemas/                         # Schémas de validation Pydantic
        ├── aviation_license_schemas.py
        ├── co2_schemas.py
        ├── employee_schemas.py
        ├── fuel_surcharge_schemas.py
        ├── payment_tracking_schemas.py
        ├── pillar_schemas.py
        ├── tax_obligation_schemas.py
        ├── training_schemas.py
        ├── user_schemas.py
        ├── waste_management_schemas.py
        └── work_accident_schemas.py
```

## 🔌 API Endpoints

### Modules disponibles

| Module | Description | Endpoints |
|--------|-------------|-----------|
| **CO2** | Gestion des émissions carbone | `/co2` |
| **Employees** | Gestion des employés | `/employees` |
| **Training** | Programmes de formation | `/training` |
| **Waste Management** | Gestion des déchets | `/waste` |
| **Work Accidents** | Suivi des accidents | `/accidents` |
| **Fuel Surcharge** | Gestion surcharges carburant | `/fuel-surcharge` |
| **Payment Tracking** | Suivi des paiements | `/payments` |
| **Tax Obligations** | Obligations fiscales | `/taxes` |
| **Aviation Licenses** | Licences aviation | `/licenses` |
| **Users** | Gestion des utilisateurs | `/users` |
| **Pillars** | Piliers ESG | `/pillars` |

Consultez la documentation Swagger (`/docs`) pour une liste complète des endpoints.

## 📚 Documentation

### Types de requêtes courantes

- **GET** : Récupérer des données
- **POST** : Créer une nouvelle ressource
- **PUT/PATCH** : Mettre à jour une ressource existante
- **DELETE** : Supprimer une ressource

### Exemple de requête
```bash
curl -X GET http://localhost:8000/employees \
  -H "Content-Type: application/json"
```

## 🔐 Sécurité

- Validation des entrées avec Pydantic
- Sanitization des données en entrée
- Gestion des erreurs cohérente
- Documentation des endpoints sécurisés

## 🤝 Contribution

Les contributions sont bienvenues ! Veuillez :

1. Créer une branche pour votre fonctionnalité (`git checkout -b feature/votre-feature`)
2. Commiter vos modifications (`git commit -am 'Ajout de votre feature'`)
3. Pousser vers la branche (`git push origin feature/votre-feature`)
4. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence [À spécifier selon votre configuration].

## 📞 Support

Pour toute question ou problème, veuillez ouvrir une issue sur le repository ou contacter l'équipe de développement.

---

**Dernière mise à jour** : Avril 2026
