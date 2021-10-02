# Image-Based Conjoint Analysis

This project implements a web application using React.js for the frontend and Flask for the backend in order to evaluate the viability of 
image-based conjoint analysis. Rather than having users choose between pairs of enumerated, categorical attribute sets, we instead use a 
multi-dimensional representation to establish a positioning map, and have users individually score each item from 0 to 10 based on a 
visual representation. These scores are then passed to the backend, where a Bayesian model implemented through PyTorth evaluates that
individual's preferences across the dimensions used to represent the data.

Any input data can be used so long as there is an excel file uploaded to the backend that contains item IDs in first column, urls to visual 
representations of the items in the second column, and a multi-dimensional representation of the items in the third column and onward. 
Originally, the application was used to study user preferences over dresses for the purposes of developing a recommendation system. However,
that positioning data based on past user purchases is proprietary and so has been removed - feel free to experiment with your own data!


## To-Do

- Improve stability for multi-user login
- Port to cloud host/server and acquire domain


## Setting Up

- Install Anaconda
- Open Anaconda terminal
    - Install pytorch
    - Install pyro
    - cd to ImageConjoint
    - npm install


## Running App

### Starting the backend

- Open Anaconda terminal (1st)
- cd to ImageConjoint/backend
- flask run

### Starting the frontend

- Open Anaconda terminal (2nd)
- cd to ImageConjoint
- npm start
