import React from 'react';
import './App.css';

// Conducts the refining ratings - button submits rating and loads next
export default class Refine extends React.Component {

  constructor() {
    super();
    this.state = {
      img: ""
    }
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  // React function that is called when the page loads.
  componentDidMount() {
    // Send an HTTP request to the server.
    fetch(
      '/refine_send', {method: 'GET'} // The type of HTTP request.
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
        if (data.move_on === true) {
          // Move on to testing stage
          this.nextStage()
        }
        else {
          this.setState({
            // Load next image
            img: data.img_url
          });
        }
      }, err => {
        // Print the error if there is one.
        console.log(err);
      }
    );
  }

  timeout(delay) {
    return new Promise( res => setTimeout(res, delay));
  }

  // Finish the refining stage
  nextStage()
  {
    // Call ahead to calculate testing items
    fetch('/calc_results', {
      method: 'POST',
      body: "",
    });
    window.location.href = "/end_refine"
  }

  // Submit the rating to model and refresh
  async handleSubmit(event) 
  {
    event.preventDefault();
    const data = new FormData(event.target);

    fetch('/refine_receive', {
      method: 'POST',
      body: data,
    });
    
    document.getElementById('rating').value = "";
    this.setState({
      img: ""
    });

    // Let model build before attempting to load next rating
    await this.timeout(3000);
    this.componentDidMount();
  }

  render() {
    return (
      <div className="App">
        <header className="App-header">
          <p>Please rate the following dress on a scale from 0 to 10 (higher is better):</p>
          <img src={this.state.img} className="App-photo" alt="Loading next image..."/>
          <br></br>
          <form onSubmit={this.handleSubmit}>
            <label htmlFor="rating">Enter your rating for this dress</label>
            <br></br>
            <input id="rating" name="rating" type="number" step="0.1" min="0" max="10"/>
            <button className="App-button">Submit</button>
            <br></br>
          </form>
        </header>
      </div>
    );
  }
}
