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

### Create user code
users = pd.read_csv(USERS_FILE)
last_user = users.iloc[-1,0]
user_id = int(last_user + 1)
users = users.append(pd.DataFrame({"User_ID":[user_id]}))
users.to_csv(path_or_buf=USERS_FILE, index=False)

### Load positioning data
dresses = pd.read_csv(DATA_FILE)
z = torch.tensor(dresses.iloc[:,2:].values)
nd = z.shape[1]

### Initialize application variables
move_on = False
load_model = False
trial = 0
items_shown = []
ratings = []

ordered_items = None
test_items = None
predicted_ratings = []
test_ratings = []

### May want to use more sophisticated method of selecting initial items
initial_items = np.random.choice(dresses.shape[0], size=NUM_INITIAL_RATINGS) 



## START BACKEND SERVER -----------------------------------------

app = Flask(__name__)


### Send the next initial item to the webpage
@app.route('/initial_send')

def get_next_initial():

    global move_on
    global load_model
    global trial
    global ratings

    if trial <= NUM_INITIAL_RATINGS:
        trial = len(ratings)

    ### Switch to refining task at end of initial items
    if trial >= NUM_INITIAL_RATINGS:
        move_on = True
        if trial == NUM_INITIAL_RATINGS:
            load_model = True
            trial = trial + 1
        img_url = ""
        return {'img_url': img_url, "move_on": move_on}

    ### Send item if not at end of initial items
    else:
        item_id = initial_items[trial]
        print(item_id)
        if (len(ratings) == len(items_shown)):
            items_shown.append(int(item_id))
        img_url = dresses.loc[int(item_id),"URL"]
        return {'img_url': img_url, "move_on": move_on}



### Load user rating for the most recent initial item
@app.route('/initial_receive', methods=['POST'])

def load_rating_initial():

    rating = request.form['rating']
    print(rating)

    global ratings
    if len(ratings) < NUM_INITIAL_RATINGS:
        ratings.append(float(rating))
    return {'completed': True}



### Return the number of refining ratings specified
@app.route('/num_refining')

def num_refining():

    global NUM_REFINE_RATINGS
    return {'num_refining': NUM_REFINE_RATINGS}



### Define the model and construct it from initial ratings
@app.route('/build_model', methods=['POST'])

def build_model():

    global load_model
    if load_model == True:

        load_model = False

        global items_shown
        global ratings
        x = z[items_shown]
        y = torch.tensor(ratings)

        ### Create instance of learning model
        global pref_model
        pref_model = PrefOptim(x, y, GP_NOISE, nd)

        ### Reset tracking variables
        global move_on
        move_on = False
        global trial
        trial = 0

    print("OK")
    return {'completed': True}



### Send the next refining item to the webpage
@app.route('/refine_send')

def get_next_refine():
    
    global move_on
    global load_model
    global trial
    global ratings

    if trial <= NUM_REFINE_RATINGS:
        trial = len(ratings) - NUM_INITIAL_RATINGS

    ### Switch to refining task at end of initial items
    if trial >= NUM_REFINE_RATINGS:
        move_on = True
        if trial == NUM_REFINE_RATINGS:
            load_model = True
            trial = trial + 1
        img_url = ""
        return {'img_url': img_url, "move_on": move_on}

    ### Send item if not at end of refining items
    else:
        global z
        global pref_model
        global items_shown

        ### If the latest item has already been rated
        if (len(ratings) == len(items_shown)):

            ### Find the optimal next item to show the current user
            closest_items = torch.argsort(torch.sum((z - pref_model.next_x())**2, 1))
            for i in closest_items:
                if not any(int(i) == j for j in items_shown):
                    item_id = i

            print(int(item_id))
            items_shown.append(int(item_id))
            img_url = dresses.loc[int(item_id),"URL"]
            return {'img_url': img_url, "move_on": move_on}

        ### If the latest item has not been rated yet
        else:
            item_id = items_shown[-1]
            print(int(item_id))
            img_url = dresses.loc[int(item_id),"URL"]
            return {'img_url': img_url, "move_on": move_on}



### Load user rating for the most recent refining item
@app.route('/refine_receive', methods=['POST'])

def load_rating_refine():

    rating = request.form['rating']
    print(rating)

    global ratings
    global items_shown
    if len(ratings) < NUM_CALC_RATINGS and len(ratings) < len(items_shown):

        ### Use rating to update our understanding of user's preferences
        global z
        global pref_model
        item_id = items_shown[-1]
        pref_model.update_posterior(torch.tensor([float(rating)]), z[item_id])
        ratings.append(float(rating))

    return {'completed': True}



### Return the number of testing ratings specified
@app.route('/num_testing')

def num_testing():

    global NUM_TEST_RATINGS
    return {'num_testing': NUM_TEST_RATINGS}



### Use model to calculate the items needed for testing and predicted ratings
@app.route('/calc_results', methods=['POST'])

def calc_results():

    global load_model
    if load_model == True:

        load_model = False

        ### Save the learning history as csv for later analysis
        global user_id
        global items_shown
        global ratings
        np.savetxt(str(user_id) + "_learning_history.csv", np.concatenate((np.array([user_id]), items_shown, ratings))[np.newaxis], delimiter=",")

        ### Use model to output ordered list of items based on preferences
        global z
        global pref_model
        global ordered_items
        final_mu = pref_model.gpmodel(z, full_cov=False, noiseless=False)[0].detach().numpy()
        ordered_items = np.argsort(final_mu)
        
        ### Select items that are both highly recommended and not all recommended
        test_good_items = np.setdiff1d(ordered_items[::-1], items_shown, assume_unique=True)[:math.ceil(NUM_TEST_RATINGS/2)]
        test_bad_items = np.setdiff1d(ordered_items, items_shown, assume_unique=True)[:math.floor(NUM_TEST_RATINGS/2)]
        
        ### Shuffle the items into a random testing order
        global test_items
        test_items = np.concatenate((test_good_items, test_bad_items))
        np.random.shuffle(test_items)
        
        ### Determine predicted ratings
        global predicted_ratings
        global test_ratings
        predicted_ratings = final_mu[test_items]
        test_ratings = []

        ### Reset tracking variables
        global move_on
        move_on = False
        global trial
        trial = 0

    print("OK")
    return {'completed': True}



### Send the next testing item to the webpage
@app.route('/test_send')

def get_next_test():

    global trial
    global move_on
    global test_ratings

    if trial <= NUM_TEST_RATINGS:
        trial = len(test_ratings)

    ### Switch to refining task at end of testing items
    if trial >= NUM_TEST_RATINGS:
        move_on = True
        img_url = ""
        return {'img_url': img_url, "move_on": move_on}

    ### Send item if not at end of testing items
    else:
        item_id = test_items[trial]
        print(item_id)
        img_url = dresses.loc[int(item_id),"URL"]
        return {'img_url': img_url, "move_on": move_on}



### Load user rating for the most recent testing item
@app.route('/test_receive', methods=['POST'])

def load_rating_test():

    rating = request.form['rating']
    print(rating)

    global test_ratings
    if len(test_ratings) < NUM_TEST_RATINGS:
        test_ratings.append(float(rating))
    return {'completed': True}



### Get the current user's ID for submission validation
@app.route('/get_userid')

def get_userid():

    global user_id
    return {'user_id': user_id}



### Return personalized recommendations for the current user
@app.route('/load_recs')

def load_recs():

    ### Save the test results as csv for later analysis
    global user_id
    global predicted_ratings
    global test_ratings
    np.savetxt(str(user_id) + "_test.csv", np.concatenate((np.array([user_id]), predicted_ratings, test_ratings))[np.newaxis], delimiter=",")

    ### Select the highest ranked items to recommend (and worst for records)
    global ordered_items
    best_items = ordered_items[::-1][:NUM_RECOMMENDATIONS]
    worst_items = ordered_items[::NUM_RECOMMENDATIONS]

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

