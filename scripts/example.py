import sys
import datarobot as dr
import pandas as pd

sys.path.append('../src')
import PartialDependency as partd

# DEFINE THE PROJECT AND MODEL WE WANT TO USE

# A Regression Project
#PROJECT_ID = '5e3565db79dd6b1936771628'
#MODEL_ID = '5e35665d5143d8794be38896' 
# LOAD THE SAMPLE DATA THAT WILL BE USED
#data = pd.read_csv('../../DataRobot_Collinear_Partial_Dependency/data/test.csv')
#img_filename="Example1.png"
# DEFINE THE TWO COLUMNS WE WILL USE
#colone = "product_price"
#coltwo = "competitor_price"


# A Classification Project
PROJECT_ID = '5e3a329379dd6b7602771631'
MODEL_ID = '5e3a3b2c75b241123ea3516f'
# LOAD THE SAMPLE DATA THAT WILL BE USED
data = pd.read_csv('../data/test.csv')
img_filename="Example2.png"
# DEFINE THE TWO COLUMNS WE WILL USE
colone = "NUM_PI_CLAIM"
coltwo = "DISTINCT_PARTIES_ON_CLAIM"


######################################################################################
# LOAD THE PROJECT AND MODEL
proj = dr.Project.get(project_id=PROJECT_ID)
mod =  dr.Model.get(PROJECT_ID, model_id=MODEL_ID)


######################################################################################
# NOW USE THE METHOD THAT GENERATES THE 2 WAY PARTIAL DEPENDENCE PLOT AND SAVES IT
plt = partd.generate_2_way_pd_plot(proj, mod, data, colone, coltwo, "../config.yml")

plt.savefig(img_filename, format='png')


