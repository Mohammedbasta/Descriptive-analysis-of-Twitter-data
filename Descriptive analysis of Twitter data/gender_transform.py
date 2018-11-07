import sqlite3
import requests
import re
import winsound

url_code = 'https://api.namsor.com/onomastics/api/json/gender/'

# nettoyage le nom
def clean_name(text):
    # supp special char
    text = re.sub(r'(\d+)|([\(\)?\[\]\{\}\'\"!@#$&£~%])', '', text.lower())
    text = re.sub(r'/[U0001F601-U0001F64F]/u', '', text) #supp imoji char
    # decouper le nom si contient "-".....
    text = re.sub(r'([_])', ' ', text)
    text = re.sub(r'([-])', ' ', text)
    text = re.sub(r'([\^])', ' ', text)
    text = re.sub(r'([\.])', ' ', text)
    text = re.sub(r'([\\])', ' ', text)
    text = re.sub(r'([\/])', ' ', text)
    text = text.strip()
    # supp les mot < 3 lettre
    text = [i for i in text.split() if len(i)>2]
    return text


line = 40039

conn = sqlite3.connect(r'db_final.db')
cursor = conn.cursor()

cursor.execute("""select * from tweet where id > ?  """, (line,))

result = ""
rows = cursor.fetchall()
for row in rows:
    # recuperer le nom depuit la base
    name = clean_name(row[5])
    if(len(name) > 1):
        param = "/"+name[0]+"/"+name[1]
    elif(len(name)==1):
        param = "/"+name[0]+"/"+name[0]
    else:
        continue

    try:
        # appel Api pour determiner le sexe
        result = requests.get(url_code+param).json()
    except :
        print(row[5] ,' => ',result)
        winsound.PlaySound("SystemHand", winsound.SND_ALIAS) # Beep si stop script
        break

    # l'ajout du resultat dans la base
    cursor.execute("""UPDATE tweet SET user_gender = ? WHERE id = ?""", (result["gender"],row[0],))
    conn.commit()
    print(row[0] ,' : ',row[5] ,' : ',param,' =>  ',result["gender"])