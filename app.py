from flask import Flask, render_template, request, redirect, url_for, session, jsonify,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "1a6676b463603eaa5118f0a289721f25d52b7fb7be2afebccfadaa455b618b7f"
db = SQLAlchemy(app)

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
    statut = db.Column(db.Boolean, default="En attente")
    date_paiement = db.Column(db.DateTime, default=datetime.utcnow)
    utilisateur=db.relationship("Utilisateurs", backref="paiememts",lazy=True)

# -------------------- INIT DB --------------------

def init_base():
    with app.app_context():
        db.create_all()
        if Utilisateurs.query.first() is None:
            print("Taches initiales ajoutees.")
        else:
            print("La base contient deja des donnes.")

# -------------------- PAGES PUBLIQUES --------------------

@app.route("/")
def introduction():
    return render_template("users/streaming_rdc.html")

@app.route("/accueil")
def accueil():
    return render_template("users/index.html", session=session)

@app.route("/iptv")
def iptv():
    return render_template("users/iptv.html", session=session)

@app.route("/netflix")
def netflix():
    return render_template("users/netflix.html", session=session)

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

@app.route("/formulaire d'achat")
def formulaire_achat():
    if 'user_id' not in session:
        return redirect(url_for('connexion', next=url_for('formulaire_achat')))
    if request.method == "POST":
        nom = request.form['nom']
        num = request.form['num']
        prix = request.form['prix']
        abonnements = Abonnements.query.filter_by(utilisateur_id=session["user_id"]).order_by(Abonnements.date_fin.desc()).all()
        
    return render_template("users/formulaire.html", session=session)


@app.route("/mon_abonnement")
def mon_abonnement():
    if 'user_id' not in session:
        return redirect(url_for('connexion', next=url_for('mon_abonnement')))
    abonnements = Abonnements.query.filter_by(utilisateur_id=session["user_id"]).order_by(Abonnements.date_fin.desc()).all()
    return render_template("users/mon_abonnement.html", abonnements=abonnements, session=session)


# 1) Route appelée quand on clique sur "Acheter" depuis la page des offres.
#    Cette route stocke service+prix dans la session puis redirige vers la page qui contient la modale.
@app.route("/select_service", methods=["POST"])
def select_service():
    service = request.form.get("service")
    prix = request.form.get("prix")
    if not service or not prix:
        flash("Erreur: service ou prix manquant.")
        return redirect(url_for("accueil"))   # ou la page des offres
    # stocke en session
    session["service"] = service
    session["prix"] = prix
    return redirect(url_for("payment_page"))


# 2) Page qui contient le bouton "Commencer" (ouvre la modale).
@app.route("/payment_page")
def payment_page():
    service = session.get("service")
    prix = session.get("prix")
    if not service or not prix:
        # si on arrive ici directement sans avoir choisi d'offre
        flash("Choisissez d'abord une offre.")
        return redirect(url_for("accueil"))   # ou ta page d'offres

    # Optionnel : forcer connexion
    if "user_id" not in session:
        return redirect(url_for("connexion", next=url_for("payment_page")))

    return render_template("payment_page.html", service=service, prix=prix)


# 3) Route qui reçoit la soumission finale du formulaire de la modale
@app.route("/payer", methods=["POST"])
def payer():
    if "user_id" not in session:
        return redirect(url_for("connexion", next=url_for("payment_page")))

    service = request.form.get("service")
    prix = request.form.get("prix")
    moyen = request.form.get("moyen")
    nom_compte = request.form.get("nom_compte")
    numero = request.form.get("numero")
    montant = request.form.get("montant") or prix

    try:
        montant = float(montant)
    except Exception:
        montant = float(prix) if prix else 0.0

    paiement = Paiement(
        utilisateur_id=session["user_id"],
        service=service,
        moyen=moyen,
        nom_compte=nom_compte,
        numero=numero,
        montant=montant,
        statut="En attente"
    )
    db.session.add(paiement)
    db.session.commit()

    # on peut nettoyer la session (optionnel)
    session.pop("service", None)
    session.pop("prix", None)

    return render_template("users/confirmation.html", message="Votre paiement a été enregistré et est en attente de vérification.")

# Achat direct par lien (1 mois par défaut)
# @app.route("/acheter/<service>")
# def acheter(service):
#     if "user_id" not in session:
#         return redirect(url_for("connexion", next=url_for("acheter", service=service)))

#     nouvel_abonnement = Abonnements(
#         utilisateur_id=session["user_id"],
#         service=service,
#         statut=True,
#         date_debut=datetime.utcnow(),
#         date_fin=datetime.utcnow() + timedelta(days=30)
#     )
#     db.session.add(nouvel_abonnement)
#     db.session.commit()
#     return redirect(url_for("mon_abonnement"))

# # Achat via popup AJAX (optionnel si tu ajoutes le popup côté front)
# @app.route("/ajouter_abonnement", methods=["POST"])
# def ajouter_abonnement():
#     if "user_id" not in session:
#         return jsonify({"success": False, "message": "Veuillez vous connecter."}), 401

#     service = request.form.get("service", "Netflix")
#     duree = int(request.form.get("duree", 30))

#     abo = Abonnements(
#         utilisateur_id=session["user_id"],
#         service=service,
#         statut=True,
#         date_debut=datetime.utcnow(),
#         date_fin=datetime.utcnow() + timedelta(days=duree)
#     )
#     db.session.add(abo)
#     db.session.commit()
#     return jsonify({"success": True, "user_id": session["user_id"]})

# -------------------- CONTACT --------------------

@app.route("/Contact", methods=['POST','GET'])
def contacts():
    if request.method == "POST":
        nom = request.form.get('nom')
        tel = request.form['tel']
        message = request.form['message']
        nouveau_commentaire = Commentaire(nom=nom, tel=tel, message=message)
        db.session.add(nouveau_commentaire)
        db.session.commit()
        return render_template("users/confirmation.html")
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
    users = Utilisateurs.query.all()
    return render_template("admin/list_users.html", users=users)

@app.route("/admin/utilisateurs/Supprimer/<int:id>", methods=["POST"])
def supprimer_utilisateur(id):
    user = Utilisateurs.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for("list_users"))

@app.route("/liste_abonnements")
def list_abonnements():
    # route conservée telle quelle (ta page admin)
    abonnements = Abonnements.query.order_by(Abonnements.date_fin.desc()).all()
    return render_template("admin/list_abonnement.html", abonnements=abonnements)

@app.route("/admin/liste_commentaires")
def liste_commentaires():
    commentaires = Commentaire.query.all()
    return render_template("admin/commentaire.html", commentaires=commentaires)

@app.route("/admin/liste_commentaires/supprimer_commentaire/<int:id>", methods=["POST", "GET"])
def supprimer_commentaire(id):
    commentaire = Commentaire.query.get(id)
    if commentaire:
        db.session.delete(commentaire)
        db.session.commit()
    return redirect(url_for('liste_commentaires'))

# -------------------- RUN --------------------

if __name__ == '__main__':
    init_base()
    app.run(debug=True)
    