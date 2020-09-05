import React from 'react';
import {Link} from 'react-router-dom';
import './App.css';

// Closes out refining ratings and shows instructions for testing stage
export default class EndRefine extends React.Component {

  constructor() {
    super();
    this.state = {
      num_testing: 0
    }
  }

  // React function that is called when the page loads.
  componentDidMount() {
    // Send an HTTP request to the server.
    fetch(
      '/num_testing', {method: 'GET'} // The type of HTTP request.
    ).then(
      res => {
        // Convert the response data to a JSON.
        return res.json();
      }, err => {
        // Print the error if there is one.
        console.log(err);
      }
    ).then
      (data => {
        // Act on data
        this.setState({
          // Load number of ratings in this stage
          rum_testing: data.num_testing
        });
      }, err => {
        // Print the error if there is one.
        console.log(err);
      }
    );
  }

  render() {
    return (
      <div className="App">
        <header className="App-header">
          <p>We are now going to test whether we did a good job at learning your <br></br>
             preferences. Please rate each of the following {this.state.num_testing} items, just <br></br>
             like you did in the previous stages.</p>
          <br></br>
          <p>We're almost done! After rating these items, you will be able to view <br></br>
             your personalized recommendations based on the prior ratings.</p>
          <br></br>
          <br></br>
          <p>Click the button below to begin.</p>
          <Link className="App-start" to="/test">Continue!</Link>
        </header>
      </div>
    );
  }
}
