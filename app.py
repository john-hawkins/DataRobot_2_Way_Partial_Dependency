from flask import Flask, flash, request, redirect, render_template, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
import pandas as pd
import datarobot as dr
import chardet
import os

# Import the file:  src/PartialDependency.py
import src.PartialDependency as partd

app = Flask(__name__)

UPLOAD_FOLDER = './uploads'

ALLOWED_EXTENSIONS = set(['csv'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ###################################################################################
# Index Page
@app.route('/')
def index():
    # GET THE LIST OF PROJECTS
    projs = dr.Project.list()
    return render_template("index.html", projects=projs)


# ###################################################################################
# Second step 
@app.route('/configure', methods = ['POST', 'GET'])
def configure():
    if request.method == 'POST':
       project_id = request.form["project_id"]
    proj = dr.Project.get(project_id=project_id)
    proj_type = proj.target_type
    mods = proj.get_models()
    feats = mods[0].get_features_used()   
    useable_feats = removeNonNumericFeatures(project_id, feats)
    projs = dr.Project.list()
    return render_template("configure.html", project=proj, models=mods, projects=projs, features=useable_feats)

def removeNonNumericFeatures(project_id, features):
    results = []
    for feature_name in features:
        featObj = dr.Feature.get(project_id, feature_name)
        if featObj.feature_type == "Numeric":
            results.append(feature_name)
    return results

# ###################################################################################
# Generate it
@app.route('/generate', methods = ['POST', 'GET'])
def generate():
    if request.method == 'POST':
        project_id = request.form["project_id"]
        model_id = request.form["model_id"]
        colone = request.form["colone"]
        coltwo = request.form["coltwo"]

        proj = dr.Project.get(project_id=project_id)
        mods = proj.get_models()
        mod = dr.Model.get(proj.id, model_id)
        feats = mod.get_features_used()

        plotpath = "static/" + project_id + "-" + model_id + "-" + colone + "-" + coltwo + ".png"

        print("Checking for file: ", plotpath)

        my_file = Path(plotpath)
        if my_file.is_file():
            print("Found it, rendering")
            return render_template("generated.html", project=proj, model=mod, colone=colone, coltwo=coltwo, pdplot=plotpath)

        # ########################################################
        # check if the post request has the file part
        if 'file' not in request.files:
            message = 'No file supplied'
            print("Message: ", message)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            message = 'empty filname'
            print("Message: ", message)
        nrows = 0
        ncols = 0
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            # NEED TO CHECK THE ENCODING BEFORE TRYING TO OPEN
            # BECAUSE SOME PEOPLE STILL USE THINGS OTHER THAN UNICODE
            rawdata = open(filepath, "rb").read()
            enc = chardet.detect(rawdata)

            pdata = pd.read_csv(filepath, encoding=enc['encoding'], low_memory=False)
            nrows =  len(pdata)
            ncols = len(pdata.columns)

            partd.generate_2_way_pd_plot_and_save(proj, mod, pdata, colone, coltwo, plotpath)

            return render_template("generated.html", project=proj, model=mod, colone=colone, coltwo=coltwo, pdplot=plotpath)



# ###################################################################################
# About Page
@app.route('/about')
def about():
        return render_template("about.html")


# With debug=True, Flask server will auto-reload 
# when there are code changes
if __name__ == '__main__':
	app.run(port=5000, debug=True)


