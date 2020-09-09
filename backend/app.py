## SETTINGS -----------------------------------------------------

DATA_FILE = "dresses10_urls.csv"
USERS_FILE = "dresses10_users.csv"
GP_NOISE = 0.1
NUM_INITIAL_RATINGS = 3
NUM_REFINE_RATINGS = 3
NUM_CALC_RATINGS = NUM_INITIAL_RATINGS + NUM_REFINE_RATINGS
NUM_TEST_RATINGS = 3
NUM_RECOMMENDATIONS = 3



## IMPORTS ------------------------------------------------------

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import time
import math

import torch
import torch.autograd as autograd
import torch.optim as optim
from torch.distributions import constraints, transform_to

torch.set_default_dtype(torch.float64)

import pyro
import pyro.contrib.gp as gp
pyro.set_rng_seed(1) ## Fixed seed for testing purposes

import json
import requests
from io import StringIO
from flask import Flask
from flask import request
from model import PrefOptim



## APP SETUP ----------------------------------------------------

### Initialize user dictionary and records csv
users = None
user_data = {}

### Load positioning data
dresses = pd.read_csv(DATA_FILE)
z = torch.tensor(dresses.iloc[:,2:].values)
nd = z.shape[1]



## START BACKEND SERVER -----------------------------------------

app = Flask(__name__)


### Create and send a fresh user ID to the webpage
@app.route('/create_user')

def create_user():

    ## Load users data and create new user
    global users
    users = pd.read_csv(USERS_FILE)
    last_user = users.iloc[-1,0]
    user_id = int(last_user + 1)

    ### Initialize user variables in user data dictionary
    initial_items = np.random.choice(dresses.shape[0], size=NUM_INITIAL_RATINGS) 
    user_data[user_id] = {
        'move_on': False,
        'load_model': False,
        'trial': 0,
        'initial_items': initial_items,
        'items_shown': [],
        'ratings': [],
        'pref_model': None,
        'ordered_items': None,
        'test_items': None,
        'predicted_ratings': [],
        'test_ratings': [],
        'start_time': round(time.time())
    }

    ### Add user to the historical user records
    users = users.append(pd.DataFrame({"User_ID":[user_id], "Status":"Started"}))
    users.to_csv(path_or_buf=USERS_FILE, index=False)

    print(round(time.time()))
    ### Delete users that are more than an hour old from active dictionary
    for key, value in user_data.items():
        print(value['start_time'])
        if value['start_time'] + 3600 < round(time.time()):
            del user_data[key]
    print(round(time.time()))

    ### Print for debugging and send to server
    print(user_data)
    return {'user_id': user_id}


### Send the next initial item to the webpage
@app.route('/initial_send/<user_id>')

def get_next_initial(user_id):

    user_id = int(user_id)
    user = user_data[user_id]

    if user['trial'] <= NUM_INITIAL_RATINGS:
        user['trial'] = len(user['ratings'])

    ### Switch to refining task at end of initial items
    if user['trial'] >= NUM_INITIAL_RATINGS:
        user['move_on'] = True
        if user['trial'] == NUM_INITIAL_RATINGS:
            user['load_model'] = True
            user['trial'] = user['trial'] + 1
        img_url = ""
        return {'img_url': img_url, "move_on": user['move_on']}

    ### Send item if not at end of initial items
    else:
        item_id = user['initial_items'][user['trial']]
        print(item_id)
        if (len(user['ratings']) == len(user['items_shown'])):
            user['items_shown'].append(int(item_id))
        img_url = dresses.loc[int(item_id),"URL"]
        return {'img_url': img_url, "move_on": user['move_on']}



### Load user rating for the most recent initial item
@app.route('/initial_receive/<user_id>', methods=['POST'])

def load_rating_initial(user_id):

    user_id = int(user_id)
    user = user_data[user_id]
    rating = request.form['rating']
    print(rating)

    if len(user['ratings']) < NUM_INITIAL_RATINGS:
        user['ratings'].append(float(rating))
    return {'completed': True}



### Return the number of refining ratings specified
@app.route('/num_refining')

def num_refining():

    global NUM_REFINE_RATINGS
    return {'num_refining': NUM_REFINE_RATINGS}



### Define the model and construct it from initial ratings
@app.route('/build_model/<user_id>', methods=['POST'])

def build_model(user_id):

    user_id = int(user_id)
    user = user_data[user_id]
    if user['load_model'] == True:

        user['load_model'] = False
        x = z[user['items_shown']]
        y = torch.tensor(user['ratings'])

        ### Create instance of learning model
        user['pref_model'] = PrefOptim(x, y, GP_NOISE, nd)

        ### Reset tracking variables
        user['move_on'] = False
        user['trial'] = 0

    print("OK")
    return {'completed': True}



### Send the next refining item to the webpage
@app.route('/refine_send/<user_id>')

def get_next_refine(user_id):
    
    user_id = int(user_id)
    user = user_data[user_id]

    if user['trial'] <= NUM_REFINE_RATINGS:
        user['trial'] = len(user['ratings']) - NUM_INITIAL_RATINGS

    ### Switch to refining task at end of initial items
    if user['trial'] >= NUM_REFINE_RATINGS:
        user['move_on'] = True
        if user['trial'] == NUM_REFINE_RATINGS:
            user['load_model'] = True
            user['trial'] = user['trial'] + 1
        img_url = ""
        return {'img_url': img_url, "move_on": user['move_on']}

    ### Send item if not at end of refining items
    else:
        global z
        ### If the latest item has already been rated
        if (len(user['ratings']) == len(user['items_shown'])):

            ### Find the optimal next item to show the current user
            closest_items = torch.argsort(torch.sum((z - user['pref_model'].next_x())**2, 1))
            for i in closest_items:
                if not any(int(i) == j for j in user['items_shown']):
                    item_id = i

            print(int(item_id))
            user['items_shown'].append(int(item_id))
            img_url = dresses.loc[int(item_id),"URL"]
            return {'img_url': img_url, "move_on": user['move_on']}

        ### If the latest item has not been rated yet
        else:
            item_id = user['items_shown'][-1]
            print(int(item_id))
            img_url = dresses.loc[int(item_id),"URL"]
            return {'img_url': img_url, "move_on": user['move_on']}



### Load user rating for the most recent refining item
@app.route('/refine_receive/<user_id>', methods=['POST'])

def load_rating_refine(user_id):

    user_id = int(user_id)
    user = user_data[user_id]
    rating = request.form['rating']
    print(rating)

    if len(user['ratings']) < NUM_CALC_RATINGS and len(user['ratings']) < len(user['items_shown']):

        ### Use rating to update our understanding of user's preferences
        global z
        item_id = user['items_shown'][-1]
        user['pref_model'].update_posterior(torch.tensor([float(rating)]), z[item_id])
        user['ratings'].append(float(rating))

    return {'completed': True}



### Return the number of testing ratings specified
@app.route('/num_testing')

def num_testing():

    global NUM_TEST_RATINGS
    return {'num_testing': NUM_TEST_RATINGS}



### Use model to calculate the items needed for testing and predicted ratings
@app.route('/calc_results/<user_id>', methods=['POST'])

def calc_results(user_id):

    user_id = int(user_id)
    user = user_data[user_id]
    if user['load_model'] == True:
        user['load_model'] = False

        ### Save the learning history as csv for later analysis
        np.savetxt(str(user_id) + "_learning_history.csv", np.concatenate((np.array([user_id]), user['items_shown'], user['ratings']))[np.newaxis], delimiter=",")

        ### Use model to output ordered list of items based on preferences
        global z
        final_mu = user['pref_model'].gpmodel(z, full_cov=False, noiseless=False)[0].detach().numpy()
        user['ordered_items'] = np.argsort(final_mu)
        
        ### Select items that are both highly recommended and not all recommended
        test_good_items = np.setdiff1d(user['ordered_items'][::-1], user['items_shown'], assume_unique=True)[:math.ceil(NUM_TEST_RATINGS/2)]
        test_bad_items = np.setdiff1d(user['ordered_items'], user['items_shown'], assume_unique=True)[:math.floor(NUM_TEST_RATINGS/2)]
        
        ### Shuffle the items into a random testing order
        user['test_items'] = np.concatenate((test_good_items, test_bad_items))
        np.random.shuffle(user['test_items'])
        user['predicted_ratings'] = final_mu[user['test_items']]

        ### Reset tracking variables
        user['move_on'] = False
        user['trial'] = 0

    print("OK")
    return {'completed': True}



### Send the next testing item to the webpage
@app.route('/test_send/<user_id>')

def get_next_test(user_id):

    user_id = int(user_id)
    user = user_data[user_id]

    if user['trial'] <= NUM_TEST_RATINGS:
        user['trial'] = len(user['test_ratings'])

    ### Switch to refining task at end of testing items
    if user['trial'] >= NUM_TEST_RATINGS:
        user['move_on'] = True
        img_url = ""
        return {'img_url': img_url, "move_on": user['move_on']}

    ### Send item if not at end of testing items
    else:
        item_id = user['test_items'][user['trial']]
        print(item_id)
        img_url = dresses.loc[int(item_id),"URL"]
        return {'img_url': img_url, "move_on": user['move_on']}



### Load user rating for the most recent testing item
@app.route('/test_receive/<user_id>', methods=['POST'])

def load_rating_test(user_id):

    user_id = int(user_id)
    user = user_data[user_id]
    rating = request.form['rating']
    print(rating)

    if len(user['test_ratings']) < NUM_TEST_RATINGS:
        user['test_ratings'].append(float(rating))
    return {'completed': True}



### Return personalized recommendations for the current user
@app.route('/load_recs/<user_id>')

def load_recs(user_id):

    user_id = int(user_id)
    user = user_data[user_id]

    ### Save the test results as csv for later analysis
    np.savetxt(str(user_id) + "_test.csv", np.concatenate((np.array([user_id]), user['predicted_ratings'], user['test_ratings']))[np.newaxis], delimiter=",")

    ### Flag user as completed in historical records
    global users
    users.loc[users['User_ID'] == user_id, 'Status'] = 'Completed'
    users.to_csv(path_or_buf=USERS_FILE, index=False)

    ### Select the highest ranked items to recommend (and worst for records)
    best_items = user['ordered_items'][::-1][:NUM_RECOMMENDATIONS]
    worst_items = user['ordered_items'][::NUM_RECOMMENDATIONS]

    ### Get urls of the recommended items
    img_urls = []
    for item_id in best_items:
        print(item_id)
        url = dresses.loc[int(item_id),"URL"]
        img_urls.append({"img_url": url})

    ### Format urls of the recommended items as json and return
    urls_json = {"img_urls": img_urls}
    print(urls_json)
    return json.dumps(urls_json)
