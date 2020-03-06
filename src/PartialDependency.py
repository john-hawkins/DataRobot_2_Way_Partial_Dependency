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
def generate_2_way_pd_data(proj, mod, pdata, colone, coltwo):
    """ 
        Function to generate the required 2 way partial dependency data.
        Performs all the re-sampling variations of a dataset
        that are required and then scores against a DataRobot model, then
        returns average values for the sampled variations.
    """
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
    dataset = proj.upload_dataset(partial_dependence_df)
    pred_job = mod.request_predictions(dataset.id)
    preds = dr.models.predict_job.wait_for_async_predictions(proj.id, predict_job_id=pred_job.id, max_wait=600)
    temp1 = partial_dependence_df.reset_index()[colone]
    temp2 = partial_dependence_df.reset_index()[coltwo]
    preds[colone] = temp1
    preds[coltwo] = temp2

    pdep = process_scored_records(proj, colone, coltwo, preds)

    return pdep



# ################################################################################
def process_scored_records(proj, colone, coltwo, preds):
    """ Process the records from the batch scoring job to create the partial dependency """

    # Fill in the blanks for pandas group by to work
    preds.loc[preds[colone].isna(), colone] = 'N/A'
    preds.loc[preds[coltwo].isna(), coltwo] = 'N/A'
 
    group_cols = [colone, coltwo]
    if (proj.target_type == 'Binary') :
       justcols = preds.loc[:,[colone, coltwo, 'positive_probability']]
       justcols.columns = [colone, coltwo, proj.target]
    else:
       justcols = preds.loc[:,[colone, coltwo, 'prediction']]
       justcols.columns = [colone, coltwo, proj.target]

    pdep = justcols.groupby( group_cols, as_index=False).mean()
    pdep.columns = [colone, coltwo, proj.target]

    return pdep


#######################################################################
# CREATE A 2 WAY PARTIAL DEPENDENCY AND SAVE IT IN A FILE
#########################################################################
def generate_2_way_pd_plot(proj, mod, pdata, colone, coltwo):
    pdep = generate_2_way_pd_data(proj, mod, pdata, colone, coltwo)

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
def generate_2_way_pd_embedded_image(proj, mod, pdata, colone, coltwo):
    pdep = generate_2_way_pd_data(proj, mod, pdata, colone, coltwo)
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
def generate_2_way_pd_plot_and_save(proj, mod, pdata, colone, coltwo plotpath):
    plt = generate_2_way_pd_plot(proj, mod, pdata, colone, coltwo)
    print("PLOT GENERATED -- SAVING TO: ", plotpath)
    plt.savefig(plotpath, format='png')
    print("SAVED")
    plt.close()
