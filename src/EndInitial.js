import React from 'react';
import {Link} from 'react-router-dom';
import './App.css';

// Closes out initial ratings and shows instructions for refining stage
export default class EndInitial extends React.Component {

  constructor() {
    super();
    this.state = {
      num_refining: 0
    }
  }

  // React function that is called when the page loads.
  componentDidMount() {
    // Send an HTTP request to the server.
    fetch(
      '/num_refining', {method: 'GET'} // The type of HTTP request.
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
          num_refining: data.num_refining
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
          <p>We are now going to try to learn what items you like. Each item <br></br>
             we show will be based on your past ratings. Every {this.state.num_refining} ratings, <br></br>
             you can choose to stop rating items, or continue to rate more.</p>
          <br></br>
          <p>During this stage, it may take a few moments for the newest dress <br></br>
             to load. Please be patient and do not hit the refresh or back buttons.</p>
          <br></br>
          <br></br>
          <p>Click the button below to begin.</p>
          <Link className="App-start" to="/refine">Continue!</Link>
        </header>
      </div>
    );
  }
}
