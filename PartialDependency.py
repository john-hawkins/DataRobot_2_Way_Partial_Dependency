# #################################################################
# Methods for calculating partial dependency data and plots
# on DataRobot models
# #################################################################
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.pyplot as plt
import matplotlib as mpl
import subprocess as sp
import datarobot as dr
import pandas as pd
import numpy as np
import base64
import time
import yaml
import io

#
# LOAD CONFIG DATA
# For running the batch scoring script
config = yaml.safe_load(open('config.yml'))

API_TOKEN = config['API_TOKEN']
USERNAME = config['USERNAME']
DATAROBOT_KEY = config['DATAROBOT_KEY']
HOST = config['HOST']

# HELPER METHOD - VALUES TO TEST IN PD
# TODO: Make this return quantiles
def getValuesToTest(data, col):
    vals = data[col].drop_duplicates()
    if len(vals) < 25:
        return vals
    return vals.iloc[0:25]


def generate2WayPD_Data(proj, mod, pdata, colone, coltwo):
    PROJECT_ID=proj.id 
    MODEL_ID=mod.id
    TARGET=proj.target
    print("Rows in dataset:", len(pdata))
    colone_values = getValuesToTest(pdata, colone) 
    coltwo_values = getValuesToTest(pdata, coltwo) 
    total_variations = len(colone_values)*len(coltwo_values)
    print("Total Variations: ", total_variations)
    samples = int(30000/total_variations)
    if samples > len(pdata):
        samples = len(pdata)
    print("Number of Samples:", samples)

    # WE HAVE TO ADD A RANDOM STATE TO ENSURE THAT THE SAMPLES ARE UNIQUE 
    # EACH TIME WE EXECUTE. OTHERWISE THERE CAN BE ISSUES WHEN YOU RE_RUN THE SAME DATA
    data_sample = pdata.sample(samples, random_state=round(time.time()) )

    partial_dependence_dfs = []
    for c1_value in colone_values:
        for c2_value in coltwo_values:
            temp_data = data_sample.copy()
            temp_data[colone] = c1_value
            temp_data[coltwo] = c2_value
            partial_dependence_dfs.append(temp_data)

    partial_dependence_df = pd.concat(partial_dependence_dfs)
    partial_dependence_df.to_csv('./XX_temp_data_for_scoring.csv', index=False)
    keep_cols = [colone, coltwo]
    # SET UP THE BATCH PROCESS AND RUN 
    command = ['batch_scoring',
               '-y',
               '--host', HOST,
               '--user', USERNAME,
               '--api_token', API_TOKEN,
               '--datarobot_key', DATAROBOT_KEY,
               '--keep_cols', ','.join(keep_cols),
               PROJECT_ID,
               MODEL_ID,
               './XX_temp_data_for_scoring.csv']    

    print("EXECUTING COMMAND:", ' '.join(command))
    output = sp.check_output(command, stderr=sp.STDOUT)

    preds = pd.read_csv('./out.csv', names=['row_id'] + keep_cols + ['false', 'true'], skiprows=1)
    # Fill in the blanks for pandas group by to work
    preds.loc[preds[colone].isna(), colone] = 'N/A'
    preds.loc[preds[coltwo].isna(), coltwo] = 'N/A'

    allcols = keep_cols.copy()
    allcols.append('true')
    justcols = preds[allcols]
    allcols[2] = TARGET
    justcols.columns = allcols

    pdep = justcols.groupby(keep_cols, as_index=False).mean()
 
    # CLEAN UP THE CREATED FILES
    cleanup = ['rm', 'out.csv', 'datarobot_batch_scoring_main.log', 'XX_temp_data_for_scoring.csv']
    output = sp.check_output(cleanup, stderr=sp.STDOUT)
 
    return pdep


#######################################################################
# CREATE A 2 WAY PARTIAL DEPENDENCY AND SAVE IT IN A FILE
#########################################################################
def generate2WayPD_Plot(proj, mod, pdata, colone, coltwo, filename):
    pdep = generate2WayPD_Data(proj, mod, pdata, colone, coltwo)

    TARGET=proj.target
    dim1 = pdep[colone]
    dim2 = pdep[coltwo]
    dim3 = pdep[TARGET]
    mpl.rcParams['legend.fontsize'] = 10
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_trisurf(dim1, dim2, dim3, cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_xlabel(colone)
    ax.set_ylabel(coltwo)
    ax.set_zlabel(TARGET)
    plt.savefig(filename, format='png')    

#########################################################################
# CREATE A 2 WAY PARTIAL DEPENDENCY AND RETURN STRING CODE TO EMBED 
# INSIDE A FLASK WEB APPLICATION
#########################################################################
def generate2WayPD_Embedded_Image(proj, mod, pdata, colone, coltwo):
    pdep = generate2WayPD_Data(proj, mod, pdata, colone, coltwo)
    TARGET=proj.target
    dim1 = pdep[colone]
    dim2 = pdep[coltwo]
    dim3 = pdep[TARGET]

    img = io.BytesIO()
    mpl.rcParams['legend.fontsize'] = 10
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_trisurf(dim1, dim2, dim3, cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_xlabel(colone)
    ax.set_ylabel(coltwo)
    ax.set_zlabel(TARGET)
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    return 'data:image/png;base64,{}'.format(plot_url)


