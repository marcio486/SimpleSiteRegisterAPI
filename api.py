from flask_cors import CORS
from flask_restful import  Api
from flask import Flask, request
import json
import sqlite3
from sqlite3 import connect
from sqlite3 import Error
import os.path
import csv
import configparser
config = configparser.ConfigParser()
config.read('settings.ini')

app = Flask(__name__)
api = Api(app)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
dbfile = config['DEFAULT']['DatabasePathAndName']
def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

#%%If database does not exit create and insert first registers
if not os.path.exists(dbfile):
    print('Creating DataBase')
    if not os.path.exists('sites.csv'):
        print('CSV file not found!!')
        exit()
    create_connection(dbfile)
    conn = connect(dbfile)
    create_table = """ CREATE TABLE IF NOT EXISTS sites (
                                        name text PRIMARY KEY,
                                        status text); """
    c = conn.cursor()
    c.execute(create_table)
    
    create_table = """  CREATE TABLE IF NOT EXISTS urls (
                                        name text,
                                        URL text,
                                        FOREIGN KEY(name) REFERENCES sites(name)); """
    
    c.execute(create_table)
    create_table = """  CREATE TABLE IF NOT EXISTS categories (
                                        name text,
                                        category text,
                                        FOREIGN KEY(name) REFERENCES sites(name)); """
    c.execute(create_table)
    
    with open('sites.csv') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            
            if row[3] == 'status': continue
            insert_register = '''insert into sites (name,status) 
                            values ('%s','%s')'''%(row[0],row[3])
            c.execute(insert_register)  
            for i in row[1].split(';'):
                insert_register = '''insert into urls (name,URL) 
                            values ('%s','%s')'''%(row[0],i)
                c.execute(insert_register)  
            for i in row[2].split(';'):
                if i == '': continue
                insert_register = '''insert into categories (name,category) 
                            values ('%s','%s')'''%(row[0],i)
                c.execute(insert_register)  
            conn.commit()                  
    conn = conn.close()                        
# =============================================================================
#     c.execute(''' select * from sites ''')
#     rows = c.fetchall()
#     c.execute(''' select * from categories ''')
#     rows = c.fetchall()
#     c.execute(''' select * from urls ''')
#     rows = c.fetchall()
#     
# =============================================================================
#%% API


@app.route('/item',methods = ['GET','POST'])
@app.route('/item/',methods = ['GET','POST','PATCH','DELETE'])
def item():
    try:
        conn = connect(dbfile)
        c = conn.cursor()
        #%%Get Requests
        if request.method == 'GET':
            id = request.args.get('id') # Get Id argument(site name) if exists
            dic = {}
            dicSend = {}
            if id != None: # if id is none it mean i must return all registers on database
                c.execute(''' select * from sites where name = '%s' '''%(id))
                rowsSites = c.fetchall()
                c.execute(''' select * from urls where name = '%s' '''%(id))
                rowsUrls = c.fetchall()
                c.execute(''' select * from categories where name = '%s' '''%(id))
                rowsCategories = c.fetchall()  
                
            else: # if id is not none search database for site name
                c.execute(''' select * from sites ''')
                rowsSites = c.fetchall()
                c.execute(''' select * from urls ''')
                rowsUrls = c.fetchall()
                c.execute(''' select * from categories ''')
                rowsCategories = c.fetchall()
            for site in rowsSites: # formatting data to dictionary so i can convert it to json
                urlList = []
                catList = []
                for url in rowsUrls:
                    if site[0] in url:
                        urlList.append(url[1])
                for cat in rowsCategories:                    
                    if site[0] in cat:
                        catList.append(cat[1])
                dic['Urls'] = urlList
                dic['Categories'] = catList
                dic['Active'] = site[1]       
                dicSend[site[0]] = dic
                dic = {}
            return json.dumps(dicSend)
        #%% Post Requests
        elif request.method == 'POST':
            #Parameters
            id = request.args.get('id')
            urls = request.args.get('urls')
            categories = request.args.get('categories')
            active = request.args.get('active')
            
            if active is None: active = 'inactive' # if active is 'none' them inactive 

            if id == None:# site is a primeray key, it must be informed
                return json.dumps({'POST':'Site name is required!'})
            
            if id != None:
                c.execute(''' select * from sites where name = '%s' '''%(id)) # if not none them verify if it alredy exists
                rowsSites = c.fetchall()
                
                if len(rowsSites) > 0: 
                    return json.dumps({'POST':'Site name alredy exists!'})
                
                else: 
                    insert_register = '''insert into sites (name,status) 
                                values ('%s','%s')'''%(id,active)
                    c.execute(insert_register)
                    if urls is not None:
                        for i in urls.split(';'):
                            if i == '': continue
                            c.execute(''' select * from urls where name = '%s' 
                                      and url = '%s' '''%(id,i))
                            rowsUrls = c.fetchall()
                            
                            if len(rowsUrls) > 0: continue
                            
                            insert_register = '''insert into urls (name,URL) 
                                        values ('%s','%s')'''%(id,i)
                            c.execute(insert_register)  
                    if categories is not None:    
                        for i in categories.split(';'):
                            if i =='': continue
                            c.execute(''' select * from categories where name = '%s' 
                                      and category = '%s' '''%(id,i))
                            rowsUrls = c.fetchall()
                            
                            if len(rowsUrls) > 0: continue
                            insert_register = '''insert into categories (name,category) 
                                    values ('%s','%s')'''%(id,i)
                            c.execute(insert_register)  
                    
                    conn.commit()
                    
                return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
        #%% Patch Requests
        elif request.method == 'PATCH': 
            #Parameters
            id = request.args.get('id')
            idPatch = request.args.get('idPatch')
            urls = request.args.get('urls')
            urlsPatch = request.args.get('urlsPatch')
            categories = request.args.get('categories')
            categoriesPatch = request.args.get('categoriesPatch')
            active = request.args.get('active')
            
            if id == None:# site is primary key, must be informed
                return json.dumps({'POST':'Site name is required!'})
            
            if active is not None:
                c.execute(''' update sites set status = '%s' 
                              where name = '%s'  '''%(active,id))
                
            if idPatch is not None:
                try: #Update all registers since name is primery key
                    c.execute(''' update sites set name = '%s' 
                              where name = '%s'  '''%(idPatch,id))
                    c.execute(''' update urls set name = '%s' 
                              where name = '%s'  '''%(idPatch,id))
                    c.execute(''' update categories set name = '%s' 
                              where name = '%s'  '''%(idPatch,id))
                
                except: 
                    return json.dumps({'PATCH':'''Site name alredy 
                                       existis on an other register!'''})

                id = idPatch#convenience
            
            if urls is None:#if url is none them delete all registers to insert new
                c.execute(''' delete from urls  where name = '%s'  '''%(id))
                if urlsPatch is not None:
                    for i in urlsPatch.split(';'):
                        insert_register = '''insert into urls (name,URL) 
                                        values ('%s','%s')'''%(id,i)
                        c.execute(insert_register) 
            else:# if urls is not none them update specified registers
                urls = urls.split(';')
                urlsPatch = urlsPatch.split(';')
                for x,y in zip(urls,urlsPatch):
                    c.execute(''' update  urls set url = '%s' where name = '%s' 
                              and url = '%s'  '''%(y,id,x))
                    
            if categories is None:#if categories is none them delete all registers to insert new
                c.execute(''' delete from urls  where name = '%s'  '''%(id))
                if categoriesPatch is not None:
                    for i in categoriesPatch.split(';'):
                        insert_register = '''insert into categories (name,category) 
                                        values ('%s','%s')'''%(id,i)
                        c.execute(insert_register) 
            else:# if categories is not none them update specified registers
                categories = categories.split(';')
                categoriesPatch = categoriesPatch.split(';')
                for x,y in zip(categories,categoriesPatch):
                    c.execute(''' update  categories set category = '%s' where name = '%s' 
                              and category = '%s'  '''%(y,id,x))
            conn.commit()
            return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
        #%% Delete requests
        elif request.method == 'DELETE': 
            id = request.args.get('id')
        
            if id == None:
                return json.dumps({'POST':'Site name is required!'})
            else :
                c.execute(''' delete from urls where name  = '%s' '''%(id))
                c.execute(''' delete from categories where name  = '%s' '''%(id))  
                c.execute(''' delete from sites where name  = '%s' '''%(id))
                
            conn.commit()
            return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    finally: conn.close()
app.run(port = int(config['DEFAULT']['port']),host=config['DEFAULT']['server'],threaded=True)