"""
Custom Partial Dependency Functions for generating 2 way partial dependencies for DataRobot models

Created: 2019

@author: john.hawkins
"""

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


# ################################################################################
def load_config(configfile):
    """
      LOAD CONFIG DATA
      For running the batch scoring script
    """
    config = yaml.safe_load(open(configfile))
    API_TOKEN = config['API_TOKEN']
    USERNAME = config['USERNAME']
    DATAROBOT_KEY = config['DATAROBOT_KEY']
    HOST = config['HOST']
    return API_TOKEN,USERNAME,DATAROBOT_KEY,HOST

# ################################################################################
def getValuesToTest(data, col):
    """
       HELPER METHOD - Generate all the values that will be tested in the 
       partial dependence
       TODO: Make this return quantiles rather than even distribution
    """
    vals = data[col].drop_duplicates()
    if len(vals) > 25:
        col_inc = (max(vals)- min(vals))/20
        vals = np.arange(min(vals), max(vals)+col_inc, col_inc)
    return vals


# ################################################################################
def generate_2_way_pd_data(proj, mod, pdata, colone, coltwo, configfile):
    """ 
        Function to generate the required 2 way partial dependency data.
        Performs all the re-sampling variations of a dataset
        that are required and then scores against a DataRobot model, then
        returns average values for the sampled variations.
    """
    API_TOKEN, USERNAME, DATAROBOT_KEY, HOST = load_config(configfile)
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

    pdep = process_scored_records(proj, colone, coltwo, preds)

    # CLEAN UP THE CREATED FILES
    cleanup = ['rm', 'out.csv', 'datarobot_batch_scoring_main.log', 'XX_temp_data_for_scoring.csv']
    output = sp.check_output(cleanup, stderr=sp.STDOUT)
 
    return pdep



# ################################################################################
def process_scored_records(proj, colone, coltwo, preds):
    """ Process the records from the batch scoring job to create the partial dependency """

    # Fill in the blanks for pandas group by to work
    preds.loc[preds[colone].isna(), colone] = 'N/A'
    preds.loc[preds[coltwo].isna(), coltwo] = 'N/A'
 
    group_cols = [colone, coltwo]
    if (proj.target_type == 'Binary') :
       justcols = preds.loc[:,[colone, coltwo, 'true']]
       justcols.columns = [colone, coltwo, proj.target]
    else:
        justcols = preds.loc[:,[colone, coltwo, proj.target]]

    pdep = justcols.groupby( group_cols, as_index=False).mean()
    pdep.columns = [colone, coltwo, proj.target]

    return pdep


#######################################################################
# CREATE A 2 WAY PARTIAL DEPENDENCY AND SAVE IT IN A FILE
#########################################################################
def generate_2_way_pd_plot(proj, mod, pdata, colone, coltwo, configfile):
    pdep = generate_2_way_pd_data(proj, mod, pdata, colone, coltwo, configfile)

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
    return plt

#########################################################################
# CREATE A 2 WAY PARTIAL DEPENDENCY AND RETURN STRING CODE TO EMBED 
# INSIDE A FLASK WEB APPLICATION
#########################################################################
def generate_2_way_pd_embedded_image(proj, mod, pdata, colone, coltwo, configfile):
    pdep = generate_2_way_pd_data(proj, mod, pdata, colone, coltwo,configfile)
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

# ################################################################################
def generate_2_way_pd_plot_and_save(proj, mod, pdata, colone, coltwo, configfile, plotpath):
    plt = generate_2_way_pd_plot(proj, mod, pdata, colone, coltwo, configfile)
    print("PLOT GENERATED -- SAVING TO: ", plotpath)
    plt.savefig(plotpath, format='png')
    print("SAVED")
    plt.close()
