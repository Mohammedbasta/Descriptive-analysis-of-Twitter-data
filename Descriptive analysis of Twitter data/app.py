import re
import string

from flask import Flask, render_template, request, jsonify
from collections import Counter
import sqlite3
import pandas as pd
from nltk.corpus import stopwords

app = Flask(__name__)

punctuation = list(string.punctuation)

# liste des stopwodrs
stop = stopwords.words('english') + punctuation

# creation connexion
cn = sqlite3.connect(r'db_final.db', check_same_thread=False)
df = pd.read_sql_query("select * from tweet", cn)


# methode permet le nettoyage de la tweet enter en parametre
def clean_tweet(text):
    text = re.sub(r"http\S+", "", text)
    text = " ".join((re.sub(r"(\w+:\/\/\S+)|([\.\,&:;$?!'])", "", text)).split())
    return re.sub(r'\d+', '', text)


# methodes permet de rendre les templtes
def page_test():
    return render_template('master.html', selected_menu_item="q1")


def page_plus():
    return render_template('plus.html', selected_menu_item="q3")


def page_acceuil():
    return render_template('accueil.html')


def page_proba():
    return render_template('master_proba.html', selected_menu_item="q2")


# reponse a la QST 4
# return le nombre d'apparition  d'une expression et la sa moyenne

def count_expression(attr, place, text):
    req = "select * from tweet "
    req1 = "select * from tweet where"
    if (attr == "pays"):
        req += " where  user_country_code = '" + place.upper() + "'"
        req1 = req + " and "
    elif (attr == "region"):
        req += " where slug_region = '" + place + "'"
        req1 = req + " and "

    df = pd.read_sql_query(req, cn)
    txt = " ".join(df.txt)
    count = txt.lower().count(text.lower())

    df1 = pd.read_sql_query(req1 + " txt LIKE '%{}%'".format(text), cn)
    df4 = pd.read_sql_query(req1 + " txt LIKE '%{}%' limit 200 ".format(text), cn)

    list = dict(zip(df1.user_id + "-" + df1.sentiment, df1.txt.map(clean_tweet)))
    list1 = dict(zip(df4.user_id + "-" + df4.sentiment, df4.txt.map(clean_tweet)))
    moy = 0
    gen = 0

    # caclule de la moyenne
    if len(list) != 0:
        moy = count / len(list)
        gen = len(list) / len(df.index) * 100

    return jsonify(
        {"nb_frame": len(df.index), "tweets": list1, "nb_tweet": len(list), "total": count, 'moyenne_generale': gen,
         'moyenne_tweet': moy})


# fonction qui retourne la list des regions géographique
def get_regions():
    df1 = pd.read_sql_query("SELECT distinct slug_region,user_region from tweet where user_region not null ", cn)
    list = dict(zip(df1.slug_region, df1.user_region))
    return jsonify(list)


# fonction qui retourne la list des pays d'une region donnee
def get_pays(region):
    df1 = pd.read_sql_query(
        "SELECT distinct user_country_code,user_country from tweet where slug_region ='{}' ".format(region), cn)
    list = dict(zip(df1.user_country_code, df1.user_country))
    return jsonify(list)


# les langues les plus utilisers
def must_langue(attr, slug):
    req = 'select * from tweet'
    if (attr == "region"):
        req += " where slug_region = '" + slug + "'"
    elif (attr == "pays"):
        req += " where user_country_code = '" + slug.upper() + "'"

    df = pd.read_sql_query(req, cn)
    count_all = Counter()
    txt = df.lang.tolist()
    count_all.update(txt)
    list = dict(count_all.most_common(15))
    return jsonify(list)


# les utilisateurs les plus actifs
def must_user(attr, slug):
    count_all = Counter()
    req = 'select * from tweet'
    if (attr == "region"):
        req += " where slug_region = '" + slug + "'"
    elif (attr == "pays"):
        req += " where user_country_code = '" + slug.upper() + "'"

    df = pd.read_sql_query(req, cn)
    txt = df.user_name.tolist()
    count_all.update(txt)
    list = dict(count_all.most_common(10))
    # return jsonify(count_all.most_common(10))
    return jsonify(list)


# les hash-tag  les plus utilisers
def must_hash(attr, slug):
    count_all = Counter()

    req = 'select * from tweet'
    if (attr == "region"):
        req += " where slug_region = '" + slug + "'"
    elif (attr == "pays"):
        req += " where user_country_code = '" + slug.upper() + "'"

    df = pd.read_sql_query(req, cn)
    txt = " ".join(df.txt)
    w = [re.sub("([!\.,])", "", term.lower()) for term in txt.split() if term.startswith('#')]
    count_all.update(w)
    list = dict(count_all.most_common(10))
    return jsonify(list)


# les personnes  les plus taguer
def must_mention(attr, slug):
    count_all = Counter()
    req = 'select * from tweet'
    if (attr == "region"):
        req += " where slug_region = '" + slug + "'"
    elif (attr == "pays"):
        req += " where user_country_code = '" + slug.upper() + "'"

    df = pd.read_sql_query(req, cn)
    txt = " ".join(df.txt)
    w = [re.sub("([!\.,;?\d+])", "", term.lower()) for term in txt.split() if len(term) > 5 and term.startswith('@')]
    count_all.update(w)
    list = dict(count_all.most_common(10))
    return jsonify(list)


# les mots les plus utiliser
def cloud_term(attr, slug):
    count_all = Counter()
    req = 'select * from tweet'
    if (attr == "region"):
        req += " where slug_region = '" + slug + "'"
    elif (attr == "pays"):
        req += " where user_country_code = '" + slug.upper() + "'"
    df = pd.read_sql_query(req, cn)
    txt = " ".join(df.txt)
    w = [term.lower() for term in clean_tweet(txt).split() if
         term.lower() not in stop and len(term) > 2 and not term.startswith(('@', '#'))]
    count_all.update(w)
    list = dict(count_all.most_common(50))
    return jsonify(list)


# reponse Q1
# retourne le nombre de tweets
def count_tweet(attr, slug):
    req = 'select * from tweet'
    if (attr == "region"):
        req += " where slug_region = '" + slug + "'"
    elif (attr == "pays"):
        req += " where user_country_code = '" + slug.upper() + "'"

    df = pd.read_sql_query(req, cn)
    list = dict(zip(df.user_id, df.txt.map(clean_tweet)))
    return jsonify({"tweets": list, "total": len(df.index)})


# reponse Q2
# retourne la représentation géographique
def region_eff():
    df2 = df['user_region'].value_counts()
    return df2.to_json(orient='index')


def pays_region(slug):
    req = "select * from tweet "
    if (slug != "all"):
        req += "where slug_region = '" + slug + "'"

    df = pd.read_sql_query(req, cn)
    df3 = df['user_country'].value_counts()

    return df3.to_json(orient='index')


# reponse Q3
# retourne la représentation par sexe
def gendre_eff(attr, slug):
    req = 'select * from tweet'
    if (attr == "region"):
        req += " where slug_region = '" + slug + "'"
    elif (attr == "pays"):
        req += " where user_country_code = '" + slug.upper() + "'"

    df = pd.read_sql_query(req, cn)
    df2 = df['user_gender'].value_counts()
    return df2.to_json(orient='index')


def proba_exppays(pays, expe, expf):
    req = "select * from tweet "
    if (pays != "all"):
        req += " where  user_country = '" + pays + "' and txt LIKE '%{}%'".format(expf)
        req1 = req + " and "

    df = pd.read_sql_query(req, cn)
    df1 = pd.read_sql_query(req1 + " txt LIKE '%{}%'".format(expe), cn)
    prob = 0
    if len(df.index) != 0:
        prob = len(df1.index) / len(df.index)
    return jsonify({"proba": prob})


# reponse Q7
# calcule la probabilité conditionnelle de deux expressions
def proba_exp_exp(expe, expf):
    req = "select * from tweet "
    req1 = "select * from tweet where"
    if (expf != ""):
        req += " where txt LIKE '%{}%'".format(expf)
        req1 = req + " and "
    df = pd.read_sql_query(req, cn)
    df1 = pd.read_sql_query(req1 + " txt LIKE '%{}%'".format(expe), cn)
    prob = 0
    if len(df.index) != 0:
        prob = len(df1.index) / len(df.index)
    return jsonify({"proba": prob})


# reponse Q6
# calcule la probabilité conditionnelle d'une expression origine a pays
def proba_pays_exp(pays, exp):
    req = "select * from tweet "
    req1 = "select * from tweet where"
    if (pays != "all"):
        req += " where  user_country = '" + pays + "'"
        req1 = req + " and "
    df = pd.read_sql_query(req, cn)
    df1 = pd.read_sql_query(req1 + "txt LIKE '%{}%'".format(exp), cn)
    prob = 0
    if len(df.index) != 0:
        prob = len(df1.index) / len(df.index)
    return jsonify({"proba": prob})


# routes app
app.add_url_rule('/', 'index', page_acceuil, methods=['GET'])
app.add_url_rule('/master', 'mst', page_test, methods=['GET'])
app.add_url_rule('/plus', 'page_plus', page_plus, methods=['GET'])
app.add_url_rule('/master_proba', 'proba', page_proba, methods=['GET'])
# routes Api
app.add_url_rule('/api/count/<attr>/<place>/<text>', 'count_term', count_expression, methods=['GET'])
app.add_url_rule('/api/tweet/<attr>/<slug>', 'count_tweet', count_tweet, methods=['GET'])
app.add_url_rule('/api/region', 'region_eff', region_eff, methods=['GET'])
app.add_url_rule('/api/pays/<slug>', 'pays_region', pays_region, methods=['GET'])
app.add_url_rule('/api/gender/<attr>/<slug>', 'gendre_eff', gendre_eff, methods=['GET'])
app.add_url_rule('/api/lang/<attr>/<slug>', 'must_langue', must_langue, methods=['GET'])
app.add_url_rule('/api/users/<attr>/<slug>', 'must_user', must_user, methods=['GET'])
app.add_url_rule('/api/hash/<attr>/<slug>', 'must_hash', must_hash, methods=['GET'])
app.add_url_rule('/api/mention/<attr>/<slug>', 'must_mention', must_mention, methods=['GET'])
app.add_url_rule('/api/cloud/<attr>/<slug>', 'cloud_term', cloud_term, methods=['GET'])
app.add_url_rule('/api/get_regions', 'get_regions', get_regions, methods=['GET'])
app.add_url_rule('/api/get_pays/<region>', 'get_pays', get_pays, methods=['GET'])

app.add_url_rule('/api/proba/pays/<pays>/<exp>', 'proba_pays_exp', proba_pays_exp, methods=['GET'])
app.add_url_rule('/api/proba/exp/<expe>/<expf>', 'proba_exp_exp', proba_exp_exp, methods=['GET'])
app.add_url_rule('/api/proba/exppays/<pays>/<expe>/<expf>', 'proba_exppays', proba_exppays, methods=['GET'])

if __name__ == "__main__":
    app.run(debug=True)
