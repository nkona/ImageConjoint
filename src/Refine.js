import React from 'react';
import {instanceOf} from 'prop-types';
import {withCookies, Cookies} from 'react-cookie';
import './App.css';

// Conducts the refining ratings - button submits rating and loads next
class Refine extends React.Component {

  static propTypes = {
    cookies: instanceOf(Cookies).isRequired
  };

  constructor(props) {
    super(props);
    const {cookies} = props;
    this.state = {
      img: "",
      user: cookies.get('user')
    }
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  // React function that is called when the page loads.
  componentDidMount() {
    // Send an HTTP request to the server.
    fetch(
      '/refine_send/' + this.state.user, {method: 'GET'} // The type of HTTP request.
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
  async nextStage()
  {
    // Call ahead to calculate testing items
    const response = await fetch('/calc_results/' + this.state.user, {
      method: 'POST',
      body: "",
    });

    // Let model build then move onto testing stage if error-free
    const completed = await response.json()
    window.location.href = "/end_refine"
  }

  // Submit the rating to model and refresh
  async handleSubmit(event) 
  {
    event.preventDefault();
    const data = new FormData(event.target);

    // Unload current image and rating
    document.getElementById('rating').value = "";
    this.setState({
      img: ""
    });

    // Send rating to model and await calculation
    const response = await fetch('/refine_receive/' + this.state.user, {
      method: 'POST',
      body: data,
    });

    // Let model build before attempting to load next rating
    const completed = await response.json()
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
            <input id="rating" name="rating" type="number" step="0.1" min="0" max="10" required/>
            <button className="App-button">Submit</button>
            <br></br>
          </form>
        </header>
      </div>
    );
  }
}

export default withCookies(Refine);
