from flask import Flask, render_template, request, redirect, url_for, session, jsonify,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "1a6676b463603eaa5118f0a289721f25d52b7fb7be2afebccfadaa455b618b7f"
db = SQLAlchemy(app)

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
DOSSIER_IMAGE=os.path.join(BASE_DIR,'static','img')
app.config['DOSSIER_IMAGE']=DOSSIER_IMAGE

IMAGE_EXTENSIONS_VALIDES = {"png", "jpg", "jpeg", "gif"}
def image_valide(nom_fichier):
    return (
        '.' in nom_fichier and nom_fichier.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS_VALIDES
    )

def extension_valide(nom_fichier):
    return '.' in nom_fichier and nom_fichier.rsplit('.',1) [1].lower() in EXTENSION_VALIDES
EXTENSION_VALIDES={'txt','pdf','png','jpg','jpeg','gif'}

# -------------------- MODELES --------------------

class Utilisateurs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(30), nullable=False)
    mdp = db.Column(db.String(200), nullable=False)

    def _repr_(self):
        return f"base {self.nom}"

class Administracteurs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(30), nullable=False)
    mdp = db.Column(db.String(200), nullable=False)

class Commentaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(30), nullable=False)
    tel = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    date_post = db.Column(db.DateTime, default=datetime.utcnow)

class Abonnements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    service = db.Column(db.String(30), nullable=False)
    statut = db.Column(db.Boolean, default=True)  # actif à la création
    date_debut = db.Column(db.DateTime, default=datetime.utcnow)
    date_fin = db.Column(db.DateTime, nullable=False)

    utilisateur = db.relationship('Utilisateurs', backref=db.backref("abonnements", lazy=True))

    @property
    def est_actif(self) -> bool:
        return datetime.utcnow() <= (self.date_fin or datetime.utcnow())

    @property
    def jours_restants(self) -> int:
        if not self.date_fin:
            return 0
        delta = self.date_fin - datetime.utcnow()
        return max(delta.days, 0)

class Paiement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    service = db.Column(db.String(30), nullable=False)
    moyen = db.Column(db.String(20),nullable=False)
    nom_compte=db.Column(db.String(50), nullable=False)
    numero=db.Column(db.String(20), nullable=False)
    montant=db.Column(db.Float, nullable=False)
    statut = db.Column(db.Boolean, default=False)
    date_paiement = db.Column(db.DateTime, default=datetime.utcnow)
    utilisateur=db.relationship("Utilisateurs", backref="paiememts",lazy=True)

class Statut(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100))
    description = db.Column(db.Text)
    image = db.Column(db.String(200))  # chemin du fichier image
    date_post = db.Column(db.DateTime, default=datetime.utcnow)

class Activites(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer)
    is_admin = db.Column(db.Boolean, default=False)
    nom = db.Column(db.String(100))
    operation = db.Column(db.String(200))
    date_heure = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------- INIT DB --------------------

def init_base():
    with app.app_context():
        db.create_all()
        if Utilisateurs.query.first() is None:
            print("Taches initiales ajoutees.")
        else:
            print("La base contient deja des donnes.")
def page_precedentes():
    page_precedente= request.referrer or url_for('accueil')#permet de recuperer la page precedente pour le bouton retour   
    return page_precedente

# -------------------- PAGES PUBLIQUES --------------------

@app.route("/")
def introduction():
    return render_template("users/streaming_rdc.html")

@app.route("/accueil")
def accueil():
    statut_aff = Statut.query.order_by(Statut.date_post.desc()).all()
    return render_template("users/index.html", session=session, statut_aff=statut_aff)

@app.route("/iptv")
def iptv():
    return render_template("users/iptv.html", session=session)

@app.route("/netflix")
def netflix():
    return render_template("users/netflix.html", session=session)

@app.route("/crunchyroll")
def crunchyroll():
    return render_template("users/crunchyroll.html", session=session)


@app.route("/Prime video")
def prime_video():
    return render_template("users/prime.html", session=session)

@app.route("/Netflix et Prime video")
def net_prime():
    return render_template("users/netflix_prime.html", session=session)

# -------------------- AUTH UTILISATEUR --------------------

@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        nom = request.form['nom']
        mdp = request.form['mdp']
        if not mdp or not nom:
            return render_template("users/inscription.html", erreur="Vous n'avez pas rempli tous les champs", show_register=True)

        utilisateur_existant = Utilisateurs.query.filter_by(nom=nom).first()
        if utilisateur_existant:
            return render_template("users/inscription.html", erreur="Cet utilisateur existe déjà, veuillez choisir un autre nom.", show_register=True)

        nouvel_utilisateur = Utilisateurs(nom=nom, mdp=mdp)
        db.session.add(nouvel_utilisateur)
        db.session.commit()
        activite = Activites(
                                utilisateur_id=nouvel_utilisateur.id,
                                is_admin=False,
                                nom=nouvel_utilisateur.nom,
                                operation="s'est inscrit comme utilisateur"
                                        )
        db.session.add(activite)
        db.session.commit()

        # 🔑 session utilisateur (séparée)
        session['user_id'] = nouvel_utilisateur.id
        session['nom'] = nouvel_utilisateur.nom  # conservé pour tes templates actuels
        return redirect(url_for('accueil'))
    return render_template("users/inscription.html")

@app.route("/connexion", methods=["POST", "GET"])
def connexion():
    if request.method == "POST":
        nom = request.form['nom']
        mdp = request.form['mdp']
        utilisateur = Utilisateurs.query.filter_by(nom=nom).first()
        if utilisateur and utilisateur.mdp == mdp:
            session['user_id'] = utilisateur.id
            session['nom'] = utilisateur.nom
            next_page = request.args.get("next")
            return redirect(next_page or url_for("accueil"))
        else:
            return render_template("users/inscription.html", erreur="Identifiants incorrects", show_register=False)
    return render_template("users/inscription.html", show_register=False)

@app.route("/deconnexion", methods=['POST','GET'])
def deconnexion():
    # ❌ on ne touche qu'aux clés user
    session.pop("user_id", None)
    session.pop("nom", None)
    return render_template("users/index.html")

# -------------------- AUTH ADMIN --------------------

CODE_ADMIN = "001701"

@app.route("/connexion_admin", methods=["POST", "GET"])
def connexion_admin():
    if request.method == "POST":
        nom = request.form['nom']
        mdp = request.form['mdp']
        if not mdp or not nom:
            return render_template("admin/inscription.html", erreur="Vous n'avez pas rempli tous les champs", show_register=True)
        admin = Administracteurs.query.filter_by(nom=nom).first()
        if admin and admin.mdp == mdp:
            session['admin_id'] = admin.id
            session['admin_nom'] = admin.nom  # séparé du 'nom' utilisateur
            next_page = request.args.get("next")
            return redirect(next_page or url_for("accueil_admin"))
        else:
            return render_template("admin/inscription.html", erreur="Identifiants incorrects vous n'etes pas administracteur", show_register=False)
    return render_template("admin/inscription.html", show_register=False)

@app.route("/inscription_admin", methods=["GET", "POST"])
def inscription_admin():
    if request.method == "POST":
        nom = request.form['nom']
        mdp = request.form['mdp']
        code_admin = request.form['code_admin']
        if not mdp or not nom or not code_admin:
            return render_template("admin/inscription.html", erreur="Vous n'avez pas rempli tous les champs", show_register=True)
        if code_admin != CODE_ADMIN:
            return render_template("admin/inscription.html", erreur="informations incorrects vous n'ete pas administracteur", show_register=True)

        administrateurs_existant = Administracteurs.query.filter_by(nom=nom).first()
        if administrateurs_existant:
            return render_template("admin/inscription.html", erreur="cet utilisateur est deja utilise", show_register=True)

        nouvel_admin = Administracteurs(nom=nom, mdp=mdp)
        db.session.add(nouvel_admin)
        db.session.commit()
        activite = Activites(
                                utilisateur_id=nouvel_admin.id,
                                is_admin=True,
                                nom=nouvel_admin.nom,
                                operation="s'est inscrit comme Administrateur"
                                        )
        db.session.add(activite)
        db.session.commit()
        session['admin_id'] = nouvel_admin.id
        session['admin_nom'] = nouvel_admin.nom
        return redirect(url_for('accueil_admin'))
    return render_template("admin/inscription.html")

@app.route("/deconnexion_admin", methods=['POST','GET'])
def deconnexion_admin():
    # ❌ on ne touche qu'aux clés admin
    session.pop("admin_id", None)
    session.pop("admin_nom", None)
    return render_template("users/index.html")

# -------------------- ABONNEMENTS (USER) --------------------

@app.route("/Formulaire_de_paiement_netflix", methods=['POST','GET'])
def formulaire_paiement_netflix():
    h1="Merci pour votre confiance !"
    p1="Votre paiement a bien été envoyé."
    p2="Nous vous répondrons dans les plus brefs délais."
    m="Retour"
    if 'user_id' not in session:
        return redirect(url_for('connexion',next=url_for('formulaire_paiement_netflix')))
    service={
        "netflix":["Netflix classique","Netflix fidélité","Netflix economie","Netflix VIP"],
        "prime_video":["prime_video classique","prime_video fidélité","prime_video economie","prime_video VIP"],
        "iptv":["iptv pour 3 mois","iptv pour 6 mois","iptv pour 12 mois"],
    }
    # ...existing code...
    if request.method == "POST":
        service_choisi = request.form['service']
        moyen = request.form['moyen']
        nom_compte = request.form['nom_compte']
        numero = request.form['numero']
        montant = request.form['montant']

        # Vérification : abonnement actif pour ce service ?
        # Vérification : abonnement déjà existant pour ce nom et ce service ?
        abonnement_existe = Abonnements.query.join(Utilisateurs).filter(
            Utilisateurs.nom == session["nom"],
            Abonnements.service == service_choisi
        ).first()
        if abonnement_existe:
            return render_template("users/confirmation.html", session=session, service=service, erreur="Vous avez déjà souscrit à ce service. Paiement refusé.", retour=page_precedentes())
        new_paiement = Paiement(
            utilisateur_id=session["user_id"],
            service=service_choisi,
            moyen=moyen,
            nom_compte=nom_compte,
            numero=numero,
            montant=montant,
            statut=True,
            date_paiement=datetime.now()
        )
        db.session.add(new_paiement)
        db.session.commit()
        activite = Activites(
                                utilisateur_id=session.get("user_id"),
                                is_admin=False,
                                nom=session["nom"],
                                operation="A payer un abonnement netflix"
                                        )
        db.session.add(activite)
        db.session.commit()
        return render_template("users/confirmation.html", h1=h1, p1=p1, p2=p2, retour=page_precedentes(), m=m)
    return render_template("users/formulaire_paiement_netflix.html", session=session, service=service, retour=page_precedentes())

@app.route("/formulaire_de_paiement_prime", methods=['POST','GET'])
def formulaire_de_paiement_prime():
    h1="Merci pour votre confiance !"
    p1="Votre paiement a bien été envoyé."
    p2="Nous vous répondrons dans les plus brefs délais."
    m="Retour"
    if 'user_id' not in session:
        return redirect(url_for('connexion',next=url_for('formulaire_de_paiement_prime')))
    service={
        "netflix":["Netflix classique","Netflix fidélité","Netflix economie","Netflix VIP"],
        "prime_video":["prime video classique","prime video fidélité","prime video economie","prime video VIP"],
        "iptv":["iptv pour 3 mois","iptv pour 6 mois","iptv pour 12 mois"],
    }
    # ...existing code...
    if request.method == "POST":
        service_choisi = request.form['service']
        moyen = request.form['moyen']
        nom_compte = request.form['nom_compte']
        numero = request.form['numero']
        montant = request.form['montant']

        # Vérification : abonnement actif pour ce service ?
        # Vérification : abonnement déjà existant pour ce nom et ce service ?
        abonnement_existe = Abonnements.query.join(Utilisateurs).filter(
            Utilisateurs.nom == session["nom"],
            Abonnements.service == service_choisi
        ).first()
        if abonnement_existe:
            return render_template("users/confirmation.html", session=session, service=service, erreur="Vous avez déjà souscrit à ce service. Paiement refusé.", retour=page_precedentes())
        new_paiement = Paiement(
            utilisateur_id=session["user_id"],
            service=service_choisi,
            moyen=moyen,
            nom_compte=nom_compte,
            numero=numero,
            montant=montant,
            statut=True,
            date_paiement=datetime.now()
        )
        db.session.add(new_paiement)
        db.session.commit()
        activite = Activites(
                                utilisateur_id=session.get("user_id"),
                                is_admin=False,
                                nom=session["nom"],
                                operation="A payer un abonnement prime_video"
                                        )
        db.session.add(activite)
        db.session.commit()
        return render_template("users/confirmation.html", h1=h1, p1=p1, p2=p2, retour=page_precedentes(), m=m)
    return render_template("users/formulaire_de_paiement_prime.html", session=session, service=service, retour=page_precedentes())

@app.route("/formulaire_de_paiement_net_prime", methods=['POST','GET'])
def formulaire_de_paiement_net_prime():
    h1="Merci pour votre confiance !"
    p1="Votre paiement a bien été envoyé."
    p2="Nous vous répondrons dans les plus brefs délais."
    m="Retour"
    if 'user_id' not in session:
        return redirect(url_for('connexion',next=url_for('formulaire_de_paiement_net_prime')))
    service={
        "netflix et prime video":["Netflix et prime video classique","Netflix et prime video fidélité","Netflix et prime video economie","Netflix et prime video VIP"],
        "prime_video":["prime_video classique","prime_video fidélité","prime_video economie","prime_video VIP"],
        "iptv":["iptv pour 3 mois","iptv pour 6 mois","iptv pour 12 mois"],
    }
    # ...existing code...
    if request.method == "POST":
        service_choisi = request.form['service']
        moyen = request.form['moyen']
        nom_compte = request.form['nom_compte']
        numero = request.form['numero']
        montant = request.form['montant']

        # Vérification : abonnement actif pour ce service ?
        # Vérification : abonnement déjà existant pour ce nom et ce service ?
        abonnement_existe = Abonnements.query.join(Utilisateurs).filter(
            Utilisateurs.nom == session["nom"],
            Abonnements.service == service_choisi
        ).first()
        if abonnement_existe:
            return render_template("users/confirmation.html", session=session, service=service, erreur="Vous avez déjà souscrit à ce service. Paiement refusé.", retour=page_precedentes())
        new_paiement = Paiement(
            utilisateur_id=session["user_id"],
            service=service_choisi,
            moyen=moyen,
            nom_compte=nom_compte,
            numero=numero,
            montant=montant,
            statut=True,
            date_paiement=datetime.now()
        )
        db.session.add(new_paiement)
        db.session.commit()
        activite = Activites(
                                utilisateur_id=session.get("user_id"),
                                is_admin=False,
                                nom=session["nom"],
                                operation="A payer un abonnement Netflix_prime"
                                        )
        db.session.add(activite)
        db.session.commit()
        return render_template("users/confirmation.html", h1=h1, p1=p1, p2=p2, retour=page_precedentes(), m=m)
    return render_template("users/formulaire_de_paiement_net_prime.html", session=session, service=service, retour=page_precedentes())

@app.route("/Formulaire_de_paiement_iptv", methods=['POST','GET'])
def formulaire_de_paiement_iptv():
    h1="Merci pour votre confiance !"
    p1="Votre paiement a bien été envoyé."
    p2="Nous vous répondrons dans les plus brefs délais."
    m="Retour"
    if 'user_id' not in session:
        return redirect(url_for('connexion',next=url_for('formulaire_de_paiement_iptv')))
    service={
        "netflix":["Netflix classique","Netflix fidélité","Netflix economie","Netflix VIP"],
        "prime_video":["prime_video classique","prime_video fidélité","prime_video economie","prime_video VIP"],
        "iptv":["abonnement iptv pour 3 mois","abonnement iptv pour 6 mois","abonnement iptv pour 12 mois"],
    }
    # ...existing code...
    if request.method == "POST":
        service_choisi = request.form['service']
        moyen = request.form['moyen']
        nom_compte = request.form['nom_compte']
        numero = request.form['numero']
        montant = request.form['montant']

        # Vérification : abonnement actif pour ce service ?
        # Vérification : abonnement déjà existant pour ce nom et ce service ?
        abonnement_existe = Abonnements.query.join(Utilisateurs).filter(
            Utilisateurs.nom == session["nom"],
            Abonnements.service == service_choisi
        ).first()
        if abonnement_existe:
            return render_template("users/confirmation.html", session=session, erreur="Vous avez déjà souscrit à ce service. Paiement refusé.", retour=page_precedentes())
        new_paiement = Paiement(
            utilisateur_id=session["user_id"],
            service=service_choisi,
            moyen=moyen,
            nom_compte=nom_compte,
            numero=numero,
            montant=montant,
            statut=True,
            date_paiement=datetime.now()
        )
        db.session.add(new_paiement)
        db.session.commit()
        activite = Activites(
                                utilisateur_id=session.get("user_id"),
                                is_admin=False,
                                nom=session["nom"],
                                operation="A payer un abonnement iptv"
                                        )
        db.session.add(activite)
        db.session.commit()
        return render_template("users/confirmation.html", h1=h1, p1=p1, p2=p2, retour=page_precedentes(), m=m)
    return render_template("users/formulaire_de_paiement_iptv.html", session=session, service=service, retour=page_precedentes())

@app.route("/formulaire_de_paiement_crun", methods=['POST','GET'])
def formulaire_de_paiement_crun():
    h1="Merci pour votre confiance !"
    p1="Votre paiement a bien été envoyé."
    p2="Nous vous répondrons dans les plus brefs délais."
    m="Retour"
    if 'user_id' not in session:
        return redirect(url_for('connexion',next=url_for('formulaire_de_paiement_crun')))
    service={
        "crunchyroll":["crunchyroll pour 3 mois","crunchyroll pour 6 mois","crunchyroll pour 12 mois"]
    }
    # ...existing code...
    if request.method == "POST":
        service_choisi = request.form['service']
        moyen = request.form['moyen']
        nom_compte = request.form['nom_compte']
        numero = request.form['numero']
        montant = request.form['montant']

        # Vérification : abonnement actif pour ce service ?
        # Vérification : abonnement déjà existant pour ce nom et ce service ?
        abonnement_existe = Abonnements.query.join(Utilisateurs).filter(
            Utilisateurs.nom == session["nom"],
            Abonnements.service == service_choisi
        ).first()
        if abonnement_existe:
            return render_template("users/confirmation.html", session=session, service=service, erreur="Vous avez déjà souscrit à ce service. Paiement refusé.", retour=page_precedentes())
        new_paiement = Paiement(
            utilisateur_id=session["user_id"],
            service=service_choisi,
            moyen=moyen,
            nom_compte=nom_compte,
            numero=numero,
            montant=montant,
            statut=True,
            date_paiement=datetime.now()
        )
        db.session.add(new_paiement)
        db.session.commit()
        activite = Activites(
                                utilisateur_id=new_paiement.id,
                                is_admin=False,
                                nom=session["nom"],
                                operation="A payer un abonnement crunchyroll"
                                        )
        db.session.add(activite)
        db.session.commit()
        return render_template("users/confirmation.html", h1=h1, p1=p1, p2=p2, retour=page_precedentes(), m=m)
    return render_template("users/formulaire_de_paiement_crunch.html", session=session, service=service, retour=page_precedentes())

# ...existing code...
@app.route("/admin/valider_paiement/<int:id>", methods=["POST","GET"])
def valider_paiement(id):
    paiement=Paiement.query.get_or_404(id)
    nouvel_abonnement=Abonnements(
        utilisateur_id=paiement.utilisateur_id,
        service=paiement.service,
        date_debut=datetime.utcnow(),
        date_fin=datetime.utcnow()+timedelta(days=30),
        statut=True
        )
    db.session.add(nouvel_abonnement)
    db.session.delete(paiement)
    db.session.commit()
    activite = Activites(
                            utilisateur_id=session.get("admin_id"),
                            is_admin=True,
                            nom=session.get("admin_nom"),
                            operation="A valider un paiement"
                                    )
    db.session.add(activite)
    db.session.commit()
    print("c'est bon tout marche bien")
    return redirect(url_for('liste_paiement'))

@app.route("/admin/liste_paiement/supprimer_paiement/<int:id>", methods=["POST", "GET"])
def supprimer_paiement(id):
    paiement=Paiement.query.get(id)
    if not paiement:
      flash("Paiement introuvable","danger")
      return redirect(url_for("liste_paiement"))
    db.session.delete(paiement)
    db.session.commit()
    activite = Activites(
                        utilisateur_id=session.get("admin_id"),
                        is_admin=True,
                        nom=session.get("admin_nom"),
                        operation="A suprimer un paiement"
                                )
    db.session.add(activite)
    db.session.commit()
    flash("paiement Suprimer")
    return redirect(url_for('liste_paiement'))

@app.route("/mon_abonnement")
def mon_abonnement():
    if 'user_id' not in session:
        return redirect(url_for('connexion', next=url_for('mon_abonnement')))
    abonnements = Abonnements.query.filter_by(utilisateur_id=session["user_id"]).order_by(Abonnements.date_fin.desc()).all()
    now=datetime.now()
    return render_template("users/mon_abonnement.html", abonnements=abonnements, session=session, now=now)

# -------------------- CONTACT --------------------

@app.route("/Contact", methods=['POST','GET'])
def contacts():
    h1="Merci pour votre commentaire !"
    p1="Votre message a bien été envoyé."
    p2="Nous vous répondrons dans les plus brefs délais."
    m="Ajouter encore un commentaire?"
    if request.method == "POST":
        nom = request.form.get('nom')
        tel = request.form['tel']
        message = request.form['message']
        nouveau_commentaire = Commentaire(nom=nom, tel=tel, message=message)
        db.session.add(nouveau_commentaire)
        db.session.commit()
        activite = Activites(
                            utilisateur_id=nouveau_commentaire.id,
                            is_admin=False,
                            nom=session["nom"],
                            operation="A ajouter un commetaire"
                                    )
        db.session.add(activite)
        db.session.commit()
        return render_template("users/confirmation.html",h1=h1,p1=p1,p2=p2,retour=page_precedentes(),m=m)
    return render_template("users/contact.html")

@app.route("/confirmation")
def confirmation():
    return render_template("users/confirmation.html", session=session)

# -------------------- ADMIN --------------------

@app.route("/admin")
def accueil_admin():
    if 'admin_id' not in session:
        return redirect(url_for('connexion_admin', next=url_for('accueil_admin')))
    return render_template("admin/index.html")

@app.route("/admin/utilisateurs")
def list_users():
    if 'admin_id' not in session:
        return redirect(url_for('connexion_admin', next=url_for('list_users')))
    users = Utilisateurs.query.all()
    return render_template("admin/list_users.html", users=users)

@app.route("/admin/utilisateurs/Supprimer/<int:id>", methods=["POST"])
def supprimer_utilisateur(id):
    user = Utilisateurs.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
        activite = Activites(
                                utilisateur_id=session.get("admin_id"),
                                is_admin=True,
                                nom=session.get("admin_nom"),
                                operation="A suprimer un utilisateur"
                                        )
        db.session.add(activite)
        db.session.commit()
    return redirect(url_for("list_users"))

@app.route("/liste_abonnements")
def list_abonnements():
    # route conservée telle quelle (ta page admin)
    abonnements = Abonnements.query.order_by(Abonnements.date_fin.desc()).all()
    now=datetime.now()
    return render_template("admin/list_abonnement.html", abonnements=abonnements, now=now)

@app.route("/admin/liste_abonnements/supprimer_abonnement/<int:id>", methods=["POST", "GET"])
def supprimer_abonnement(id):
    abonnement = Abonnements.query.get_or_404(id)
    db.session.delete(abonnement)
    db.session.commit()
    activite = Activites(
                            utilisateur_id=abonnement.id,
                            is_admin=True,
                            nom=session.get("admin_nom"),
                            operation="A suprimer un abonnement"
                                    )
    db.session.add(activite)
    db.session.commit()
    flash("abonnement Suprimer")
    return redirect(url_for('list_abonnements'))

@app.route("/admin/liste_commentaires")
def liste_commentaires():
    if 'admin_id' not in session:
        return redirect(url_for('connexion_admin', next=url_for('liste_commentaires')))
    commentaires = Commentaire.query.all()
    return render_template("admin/commentaire.html", commentaires=commentaires)

@app.route("/admin/liste_commentaires/supprimer_commentaire/<int:id>", methods=["POST", "GET"])
def supprimer_commentaire(id):
    commentaire = Commentaire.query.get(id)
    if commentaire:
        db.session.delete(commentaire)
        db.session.commit()
        activite = Activites(
                            utilisateur_id=commentaire.id,
                            is_admin=True,
                            nom=session.get("admin_nom"),
                            operation="A suprimer un commentaire"
                                    )
        db.session.add(activite)
        db.session.commit()
    return redirect(url_for('liste_commentaires'))

@app.route("/admin/liste_paiement")
def liste_paiement():
    if 'admin_id' not in session:
        return redirect(url_for('connexion_admin', next=url_for('liste_paiement')))
    paiements = Paiement.query.order_by(Paiement.date_paiement.desc()).all()
    return render_template("admin/liste_paiement.html", paiements=paiements)

@app.route('/admin/statut', methods=['GET', 'POST'])
def admin_statut():
    if 'admin_id' not in session:
        return redirect(url_for('connexion_admin', next=url_for('admin_statut')))
    message = None
    statut_aff = Statut.query.all()
    if request.method == 'POST':
        titre = request.form['titre']
        description = request.form['description']
        image = request.files['image']
        date_post=datetime.now()
        if image and image.filename != '' and image_valide(image.filename):
            nom_fichier = secure_filename(image.filename)
            chemin_complet = os.path.join(app.config['DOSSIER_IMAGE'], nom_fichier)
            os.makedirs(app.config['DOSSIER_IMAGE'], exist_ok=True)
            image.save(chemin_complet)
            image_path = nom_fichier
        else:
            return "Fichier image non valide."
        statut = Statut(titre=titre, description=description, image=image_path,date_post=date_post)
        db.session.add(statut)
        db.session.commit()
        message = "Statut publié avec succès !"
        activite = Activites(
                            utilisateur_id=statut.id,
                            is_admin=True,
                            nom=session.get("admin_nom"),
                            operation="A ajouter un statut"
                                    )
        db.session.add(activite)
        db.session.commit()
    return render_template('admin/statut.html', message=message, statut_aff=statut_aff)

@app.route("/admin/liste_statut")
def liste_statut():
    if 'admin_id' not in session:
        return redirect(url_for('connexion_admin', next=url_for('liste_statut')))
    statut = Statut.query.all()
    return render_template("admin/liste_statut.html", statut=statut)

@app.route("/admin/statut/Supprimer/<int:id>", methods=["POST"])
def supprimer_statut(id):
    statut = Statut.query.get(id)
    if statut:
        db.session.delete(statut)
        db.session.commit()
        activite = Activites(
                            utilisateur_id=statut.id,
                            is_admin=True,
                            nom=session.get("admin_nom"),
                            operation="A suprimer un statut"
                                    )
        db.session.add(activite)
        db.session.commit()
    return redirect(url_for("admin_statut"))

@app.route("/admin/list_activite")
def list_activite():
    if 'admin_id' not in session:
        return redirect(url_for('connexion_admin', next=url_for('list_activite')))
    if 'admin_id' not in session:
        return redirect(url_for('connexion_admin'))

    admin = Administracteurs.query.get(session['admin_id'])
    # Limite à 100 activités, supprime les plus anciennes si besoin
    MAX_ACTIVITES = 100
    total = Activites.query.count()
    if total > MAX_ACTIVITES:
        # Supprime les plus anciennes
        ids_to_delete = [a.id for a in Activites.query.order_by(Activites.date_heure.asc()).limit(total - MAX_ACTIVITES).all()]
        Activites.query.filter(Activites.id.in_(ids_to_delete)).delete(synchronize_session=False)
        db.session.commit()
    activites = Activites.query.order_by(Activites.date_heure.desc()).all()
    return render_template("admin/list_activite.html", admin=admin, activites=activites,retour=page_precedentes())


# -------------------- RUN --------------------

if __name__ == '__main__':
    init_base()
    app.run(debug=True)
    
