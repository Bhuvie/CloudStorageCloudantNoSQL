# -*- coding: utf-8 -*-
"""
Created on Wed Feb 01 12:05:34 2017

@author: Bhuvanesh Rajakarthikeyan ID:0051
"""

import os
from flask import Flask, render_template, request
from flask import make_response
import json  
import couchdb
import datetime
import xxhash

PORT = int(os.getenv('PORT', 8080))

app = Flask(__name__)
app.secret_key = 'somesecret'
 # couchDB/Cloudant-related global variables  
couchInfo=''  
couchServer=''  
couch=''  
   
 #get service information if on Bluemix  
if 'VCAP_SERVICES' in os.environ:  
  couchInfo = json.loads(os.environ['VCAP_SERVICES'])['cloudantNoSQLDB'][0]  
  couchServer = couchInfo["credentials"]["url"]  
  couch = couchdb.Server(couchServer)  
 #we are local  
else:  
  couchServer = "http://127.0.0.1:5984"  
  couch = couchdb.Server(couchServer) 
   
 # access the database which was created separately  
db = couch['filestorage']

@app.route("/")
def index():
    return render_template('index.html') 

#import siphash
#key = '0123456789ABCDEF'
#siphash.SipHash_2_4(key, 'a').hash()
#siphash.SipHash_2_4(key, 'a').digest()
#siphash.SipHash_2_4(key, 'a').hexdigest()
#datetime_object = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p' or %Y-%m-%d %H:%M:%S)

@app.route('/upload', methods=['POST'])
def upload():
    doc= { "CreatedBy" : "Bhuvanesh",  
    }
    file = request.files['file']
    lastmoddate = request.form['flstmod']
    file_name = file.filename
    uploaded_content = file.read()
    uploaded_content=uploaded_content.encode("base64")
    version=1
    doc["filename"]=file_name
    convmsdate=datetime.datetime.fromtimestamp(float(lastmoddate)/1000.0)
    doc["LastUpdatedOn"]=convmsdate.strftime('%Y-%m-%d %H:%M:%S')
    #doc["LastUpdatedOn"]=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    doc["filecontent"]=uploaded_content
    hashdata=xxhash.xxh64(uploaded_content).hexdigest()     #Find hash value for the file
    doc["filehash"]=hashdata
    for docs in db.view('_all_docs'):               #Loop through all the docs
        doc1=db.get(docs.id)
        if(doc1["filename"]==file_name):                #Check whether the file already exists using name and hash value
            if(doc1["filehash"]==hashdata):
                return "File already exists"
            else:
                version=version+1               #If hash value does not match, increase the version and upload
    doc["versions"]=str(version)
    db.save(doc)
    return "File Successfully Uploaded"
    
@app.route('/download', methods=['POST'])
def download():
    file_name = request.form['dfilename']
    version=request.form['dversion']
    for docs in db.view('_all_docs'):
        doc=db.get(docs.id)
        if(doc["filename"] == file_name):
            if(doc["versions"]==version):
                file=doc["filecontent"]
                #hashdat=xxhash.xxh64(file).hexdigest()              #Compare the hash value in Nosql db and the calculated hash value for the file 
                #if(hashdat!=doc["filehash"]):                   
                    #return render_template('index.html',error="Hash value Mismatch: Hash In DB: "+doc["filehash"]+"  File Hash:"+hashdat) 
                file=file.decode("base64")
                #file = doc.get_attachment(doc.id,file_name, attachment_type='binary')
                response = make_response(file)                                                      #If version and name matches return the file as response
                response.headers["Content-Disposition"] = "attachment; filename=%s"%file_name
                return response
    return render_template('index.html',error="File not available for download") 
    

@app.route('/delete', methods=['POST'])
def delete():
    file_name = request.form['defilename']
    version=request.form['deversion']
    for docs in db.view('_all_docs'):
        doc=db.get(docs.id)
        if(doc["filename"] == file_name):
            if(doc["versions"]==version):
                db.delete(doc)
                return "File Deleted Successfully"
    return "File not found"
    
@app.route('/listfiles', methods=['POST'])
def listfiles():
    response="<div class='row' style="+'"'+"padding-bottom:10px"+'"'+"><h4><div class='col-sm-5'>FileName</div><div class='col-sm-2'>File Version</div><div class='col-sm-2'>LastUpdatedOn</div><div class='col-sm-3'>Hash Value</div></h4></div>"
    for docs in db.view('_all_docs'):
        doc=db.get(docs.id)
        response=response+"<div class='row' style="+'"'+"padding-bottom:10px"+'"'+"><div class='col-sm-5'>"+doc["filename"]+"</div><div class='col-sm-2'>"
        response=response+doc["versions"]+"</div><div class='col-sm-2'>"
        response=response+doc["LastUpdatedOn"]+"</div><div class='col-sm-3'>"
        response=response+doc["filehash"]+"</div></div>"
        #<td><textarea rows='3' cols='15'>"
        #response=response+doc["filecontent"]+"</textarea></td></tr>"
    return response
            
            
            

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(PORT))