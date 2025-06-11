# RawFlow

RawFlow est une application web de traçabilité des matières premières basée sur une blockchain simple, développée avec Django. Elle permet aux producteurs et transformateurs d'enregistrer et de suivre les transactions de produits, avec des rôles utilisateurs et une API REST.

## Fonctionnalités
- **Authentification** : Inscription et connexion avec rôles (Producteur, Transformateur).
- **Tableau de bord** : Affichage des blocs de la blockchain.
- **Ajout de transactions** : Enregistrement de transactions (ID produit, industrie, origine, détails).
- **Recherche** : Recherche de transactions par ID produit.
- **API REST** : Gestion des transactions via une interface API.

## Prérequis
- Python 3.12
- Django 5.2.3
- djangorestframework
- python-decouple

## Installation
1. Clonez le dépôt :
   ```bash
   git clone https://github.com/Chanel241/rawflow.git
   cd rawflow